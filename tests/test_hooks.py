"""Unit tests for the git and agent hook scripts."""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from tools.check_commit_msg import commit_message_error
from tools.check_commit_msg import main as commit_main
from tools.check_gold_file_size import GOLD_MAX_BYTES, oversized_gold_files
from tools.check_spec_untouched import main as spec_main
from tools.check_spec_untouched import owner_only_relative
from tools.hooks.common import repo_root
from tools.hooks.policy import (
    OWNER_ONLY_MESSAGE,
    claude_pre_tool_payload,
    claude_stop_payload,
    cursor_stop_payload,
    is_owner_only_path,
    push_targets_main,
    read_permission,
    shell_denial,
)
from tools.pre_push import main as pre_push_main

ROOT = repo_root()
CURSOR_BLOCK_EXIT = 2
DENY_COMMANDS = (
    "git push --force origin cursor/m0_scaffold",
    "git push --force-with-lease origin feature",
    "git push --force-if-includes",
    "git push -f origin feature",
    "git push origin main",
    "git push origin feature:main",
    "git push origin HEAD:refs/heads/main",
    "git commit --no-verify -m 'chore(tooling): x'",
    "git commit -n -m 'chore(tooling): x'",
    "git -C /tmp commit --no-verify -m 'chore(tooling): x'",
    "OWNER_SPEC_EDIT=1 git status",
    "pip install numpy",
    "pip3 install numpy",
    "python -m pip install numpy",
    "python3 -m pip install numpy",
)
ALLOW_COMMANDS = (
    "git status",
    "git push -u origin cursor/m0_scaffold",
    "git commit -m 'chore(tooling): M0 scaffold'",
    "uv add numpy",
    "uv pip install numpy",
    "make check",
    "git reset --hard",
    "git reset --hard HEAD~1",
)


def _run_module(
    module: str,
    payload: dict[str, object],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
    )


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)


@pytest.mark.parametrize("command", DENY_COMMANDS)
def test_shell_denial_blocks_listed_commands(command: str) -> None:
    reason = shell_denial(command, current_branch="cursor/m0_scaffold")
    assert reason is not None
    assert reason != ""


@pytest.mark.parametrize("command", ALLOW_COMMANDS)
def test_shell_denial_allows_ordinary_commands(command: str) -> None:
    assert shell_denial(command, current_branch="cursor/m0_scaffold") is None


def test_reset_hard_on_main_is_refused() -> None:
    reason = shell_denial("git reset --hard", current_branch="main")
    assert reason is not None
    assert "main" in reason


def test_reset_hard_on_origin_ref_is_refused() -> None:
    reason = shell_denial("git reset --hard origin/main", current_branch="cursor/m0_scaffold")
    assert reason is not None


def test_cursor_and_claude_share_force_push_denial() -> None:
    command = "git push --force origin feature"
    cursor = _run_module(
        "tools.hooks.cursor_before_shell",
        {"command": command, "cwd": str(ROOT)},
    )
    claude = _run_module(
        "tools.hooks.claude_pre_tool",
        {
            "tool_name": "Bash",
            "cwd": str(ROOT),
            "tool_input": {"command": command},
        },
    )
    assert cursor.returncode == 0
    assert json.loads(cursor.stdout)["permission"] == "deny"
    body = json.loads(claude.stdout)
    decision = body["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
    assert "force" in body["hookSpecificOutput"]["permissionDecisionReason"]


def test_cursor_before_read_allows_spec() -> None:
    proc = _run_module(
        "tools.hooks.cursor_before_read",
        {"file_path": str(ROOT / "spec" / "SCIENCE.md")},
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"permission": "allow"}
    assert read_permission(str(ROOT / "spec" / "SCIENCE.md"), repo_root=ROOT) == "allow"


def test_cursor_after_edit_denies_spec_without_changing_it() -> None:
    target = ROOT / "spec" / "SCIENCE.md"
    before = target.read_bytes()
    proc = _run_module(
        "tools.hooks.cursor_after_edit",
        {"file_path": str(target), "edits": []},
    )
    assert proc.returncode == CURSOR_BLOCK_EXIT
    assert OWNER_ONLY_MESSAGE in proc.stderr
    assert json.loads(proc.stdout)["permission"] == "deny"
    assert target.read_bytes() == before


def test_claude_pre_tool_denies_spec_write() -> None:
    proc = _run_module(
        "tools.hooks.claude_pre_tool",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(ROOT / "data" / "gold" / "values.csv"),
                "content": "x",
            },
        },
    )
    body = json.loads(proc.stdout)
    assert body["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "needs-science-decision" in body["hookSpecificOutput"]["permissionDecisionReason"]


def test_claude_post_tool_blocks_spec_edit() -> None:
    proc = _run_module(
        "tools.hooks.claude_post_tool",
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(ROOT / "spec" / "TOLERANCES.md")},
        },
    )
    body = json.loads(proc.stdout)
    assert body["decision"] == "block"
    assert "needs-science-decision" in body["reason"]


def test_after_edit_formats_python(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("x=1\n", encoding="utf-8")
    proc = _run_module(
        "tools.hooks.cursor_after_edit",
        {"file_path": str(target), "edits": []},
    )
    assert proc.returncode == 0
    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_owner_only_path_rules(tmp_path: Path) -> None:
    assert is_owner_only_path("spec/SCIENCE.md", repo_root=ROOT)
    assert is_owner_only_path(str(ROOT / "data" / "gold" / "x.csv"), repo_root=ROOT)
    assert not is_owner_only_path(str(tmp_path / "spec" / "SCIENCE.md"), repo_root=ROOT)
    assert not is_owner_only_path("src/qcbench/__init__.py", repo_root=ROOT)


def test_stop_payloads() -> None:
    assert cursor_stop_payload("aborted", 1, "nope") == {}
    assert cursor_stop_payload("completed", 0, "") == {}
    failed = cursor_stop_payload("completed", 1, "lint failed")
    assert "Keep working" in str(failed["followup_message"])
    assert claude_stop_payload(0, "") == {}
    blocked = claude_stop_payload(1, "lint failed")
    assert blocked["decision"] == "block"
    allow = claude_pre_tool_payload("allow", "")
    assert allow["hookSpecificOutput"] == {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
    }


def test_cursor_stop_aborted_does_not_run_make() -> None:
    proc = _run_module("tools.hooks.cursor_stop", {"status": "aborted"})
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {}


def test_stop_hooks_follow_a_failed_check(tmp_path: Path) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake_make = bindir / "make"
    fake_make.write_text("#!/bin/sh\necho check-failed\nexit 1\n", encoding="utf-8")
    fake_make.chmod(fake_make.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ)
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    cursor = _run_module("tools.hooks.cursor_stop", {"status": "completed"}, env=env)
    claude = _run_module("tools.hooks.claude_stop", {"hook_event_name": "Stop"}, env=env)
    assert cursor.returncode == 0
    assert "Keep working" in json.loads(cursor.stdout)["followup_message"]
    assert json.loads(claude.stdout)["decision"] == "block"


def test_commit_message_rules(tmp_path: Path) -> None:
    assert commit_message_error("chore(tooling): M0 scaffold\n") is None
    assert commit_message_error("feat(task)!: change the task format\n") is None
    assert commit_message_error("update stuff\n") is not None
    assert commit_message_error("chore: missing scope\n") is not None
    assert commit_message_error("chore(nope): bad scope\n") is not None
    trailer = "chore(tooling): M0 scaffold\n\nCo-authored-by: Bot <bot@example.com>\n"
    assert commit_message_error(trailer) is not None
    made = "chore(tooling): M0 scaffold\n\nMade with a bot.\n"
    assert "made with" in made.lower()
    assert commit_message_error(made) is not None
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("chore(tooling): M0 scaffold\n", encoding="utf-8")
    assert commit_main(["check_commit_msg.py", str(path)]) == 0
    path.write_text("nope\n", encoding="utf-8")
    assert commit_main(["check_commit_msg.py", str(path)]) == 1


def test_owner_only_relative_paths() -> None:
    assert owner_only_relative("spec/SCIENCE.md")
    assert owner_only_relative("data/gold/values.csv")
    assert not owner_only_relative("src/qcbench/__init__.py")
    assert not owner_only_relative("specs/SCIENCE.md")


def test_staged_spec_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path, "init", "-b", "main")
    spec = tmp_path / "spec"
    spec.mkdir()
    (spec / "SCIENCE.md").write_text("# Scope\n\nTODO(owner)\n", encoding="utf-8")
    _git(tmp_path, "add", "spec/SCIENCE.md")
    monkeypatch.delenv("OWNER_SPEC_EDIT", raising=False)
    assert spec_main(tmp_path) == 1
    monkeypatch.setenv("OWNER_SPEC_EDIT", "1")
    assert spec_main(tmp_path) == 0


def test_staged_source_is_allowed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path, "init", "-b", "main")
    source = tmp_path / "src"
    source.mkdir()
    (source / "demo.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "src/demo.py")
    monkeypatch.delenv("OWNER_SPEC_EDIT", raising=False)
    assert spec_main(tmp_path) == 0


def test_pre_push_module_refuses_main() -> None:
    sha = "0" * 40
    line = f"refs/heads/cursor/m0_scaffold {sha} refs/heads/main {sha}\n"
    proc = subprocess.run(
        [sys.executable, "-m", "tools.pre_push", "--refs-only"],
        input=line,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert proc.returncode == 1
    assert "refusing push to main" in proc.stderr
    allowed = subprocess.run(
        [sys.executable, "-m", "tools.pre_push", "--refs-only"],
        input=f"refs/heads/cursor/m0_scaffold {sha} refs/heads/cursor/m0_scaffold {sha}\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert allowed.returncode == 0


def test_push_ref_rules() -> None:
    line = "refs/heads/cursor/m0_scaffold abc refs/heads/main def"
    assert push_targets_main(line, "cursor/m0_scaffold")
    assert push_targets_main("", "main")
    assert not push_targets_main(
        "refs/heads/cursor/m0_scaffold abc refs/heads/cursor/m0_scaffold def",
        "cursor/m0_scaffold",
    )
    assert pre_push_main(["pre_push.py", "--refs-only"], line) == 1
    assert pre_push_main(["pre_push.py", "--refs-only"], "") == 0


def test_gold_file_size_limit(tmp_path: Path) -> None:
    gold = tmp_path / "data" / "gold"
    gold.mkdir(parents=True)
    small = gold / "small.csv"
    small.write_bytes(b"a")
    large = gold / "large.csv"
    large.write_bytes(b"a" * (GOLD_MAX_BYTES + 1))
    assert oversized_gold_files([small], repo_root=tmp_path, max_bytes=GOLD_MAX_BYTES) == []
    found = oversized_gold_files([large], repo_root=tmp_path, max_bytes=GOLD_MAX_BYTES)
    assert len(found) == 1
    assert "large.csv" in found[0]
