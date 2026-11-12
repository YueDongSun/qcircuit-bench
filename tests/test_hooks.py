"""Unit tests for the git and agent hook scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.check_spec_untouched import _changed_paths, staged_owner_paths
from tools.hooks.policy import (
    OWNER_SPEC_MESSAGE,
    CmdResult,
    commit_subject_error,
    file_hook_output,
    is_owner_only_path,
    push_to_main_ref,
    shell_decision,
    shell_hook_output,
    stop_hook_output,
)

ROOT = Path(__file__).resolve().parents[1]
_DENY_EXIT = 2


def test_shell_denylist() -> None:
    denied = [
        "git push --force origin feature",
        "git push --force-with-lease",
        "git push -f origin feature",
        "git push origin main",
        "git commit -m 'chore(tooling): x' --no-verify",
        "OWNER_SPEC_EDIT=1 git status",
        "pip install numpy",
        "pip3 install numpy",
        "python -m pip install numpy",
        "python3 -m pip install numpy",
        "uv pip install numpy",
    ]
    for command in denied:
        decision = shell_decision(command, branch="cursor/m0-scaffold")
        assert decision.deny, command


def test_shell_allows_normal_commands() -> None:
    allowed = [
        "git status",
        "uv add numpy",
        "git push -u origin cursor/m0-scaffold",
        "git commit -m 'chore(tooling): M0 scaffold'",
        "git reset --hard HEAD",
    ]
    for command in allowed:
        decision = shell_decision(command, branch="cursor/m0-scaffold")
        assert not decision.deny, command


def test_reset_hard_on_main_is_denied() -> None:
    decision = shell_decision("git reset --hard HEAD", branch="main")
    assert decision.deny
    decision = shell_decision("git reset --hard origin/main", branch="cursor/m0-scaffold")
    assert decision.deny


def test_cursor_and_claude_shell_payloads() -> None:
    denied = shell_decision("pip install numpy", branch="feature")
    cursor = shell_hook_output(
        {"hook_event_name": "beforeShellExecution", "command": "pip install numpy"},
        denied,
    )
    assert cursor is not None
    assert cursor["permission"] == "deny"
    claude = shell_hook_output(
        {
            "hook_event_name": "PreToolUse",
            "tool_input": {"command": "pip install numpy"},
        },
        denied,
    )
    assert claude is not None
    specific = claude["hookSpecificOutput"]
    assert isinstance(specific, dict)
    assert specific["permissionDecision"] == "deny"
    allowed = shell_decision("git status", branch="feature")
    assert shell_hook_output({"hook_event_name": "PreToolUse"}, allowed) is None
    assert shell_hook_output({"hook_event_name": "beforeShellExecution"}, allowed) == {
        "permission": "allow"
    }


def test_owner_paths() -> None:
    root = "/workspace"
    assert is_owner_only_path("spec/SCIENCE.md")
    assert is_owner_only_path("data/gold/levels.csv")
    assert is_owner_only_path("/workspace/spec/SCIENCE.md", roots=[root])
    assert is_owner_only_path("/workspace/data/gold/levels.csv", roots=[root])
    assert not is_owner_only_path("src/qcbench/__init__.py")
    assert not is_owner_only_path("specs/SCIENCE.md")
    assert not is_owner_only_path("data/golden/x.csv")


def test_reads_of_spec_are_allowed_and_writes_are_denied() -> None:
    read = file_hook_output(
        {
            "hook_event_name": "beforeReadFile",
            "file_path": "/workspace/spec/SCIENCE.md",
            "workspace_roots": ["/workspace"],
        }
    )
    assert read == {"permission": "allow"}
    write = file_hook_output(
        {
            "hook_event_name": "preToolUse",
            "tool_input": {"file_path": "/workspace/spec/SCIENCE.md"},
            "workspace_roots": ["/workspace"],
        }
    )
    assert write is not None
    assert write["permission"] == "deny"
    assert OWNER_SPEC_MESSAGE in str(write["agent_message"])
    claude = file_hook_output(
        {
            "hook_event_name": "PreToolUse",
            "tool_input": {"file_path": "data/gold/x.csv"},
            "cwd": "/workspace",
        }
    )
    assert claude is not None
    specific = claude["hookSpecificOutput"]
    assert isinstance(specific, dict)
    assert specific["permissionDecision"] == "deny"
    assert "needs-science-decision" in str(specific["permissionDecisionReason"])


def test_commit_subjects() -> None:
    assert commit_subject_error("chore(tooling): M0 scaffold\n") is None
    assert commit_subject_error("feat(task): add example-000-smoke\n\nbody\n") is None
    assert commit_subject_error("feat(task)!: change the format\n") is None
    assert commit_subject_error("# comment\n\nfix(verify): seed the simulator\n") is None
    for message in ("fixed stuff", "feat: add task", "chore(physics): guess a tolerance", ""):
        assert commit_subject_error(message) is not None


def test_push_refs() -> None:
    assert push_to_main_ref("") is None
    feature = "refs/heads/cursor/m0-scaffold abc refs/heads/cursor/m0-scaffold def"
    assert push_to_main_ref(feature) is None
    main = "refs/heads/cursor/m0-scaffold abc refs/heads/main def"
    assert push_to_main_ref(main) == "refs/heads/main"


def test_stop_hook_reports_make_check_failure() -> None:
    failure = CmdResult(returncode=1, stdout="lint failed", stderr="")
    cursor = stop_hook_output({"hook_event_name": "stop", "status": "completed"}, failure)
    assert cursor is not None
    assert "make check failed" in str(cursor["followup_message"])
    claude = stop_hook_output({"hook_event_name": "Stop"}, failure)
    assert claude is not None
    assert claude["decision"] == "block"
    assert stop_hook_output({"hook_event_name": "stop"}, CmdResult(0, "", "")) is None
    assert stop_hook_output({"hook_event_name": "stop", "status": "aborted"}, failure) is None
    assert stop_hook_output({"hook_event_name": "Stop", "stop_hook_active": True}, failure) is None


def test_shell_guard_cli_denies_pip() -> None:
    payload = json.dumps(
        {"hook_event_name": "beforeShellExecution", "command": "pip install numpy"}
    )
    completed = _run_hook("tools.hooks.shell_guard", payload)
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["permission"] == "deny"


def test_format_hook_rejects_spec_edit(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "hook_event_name": "afterFileEdit",
            "file_path": str(tmp_path / "spec" / "SCIENCE.md"),
            "workspace_roots": [str(tmp_path)],
        }
    )
    completed = _run_hook("tools.hooks.format_file", payload)
    assert completed.returncode == _DENY_EXIT
    assert "needs-science-decision" in completed.stderr


def test_commit_msg_script_rejects_unscoped_subject(tmp_path: Path) -> None:
    message = tmp_path / "msg"
    message.write_text("added stuff\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "tools.check_commit_msg", str(message)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    message.write_text("chore(tooling): M0 scaffold\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "tools.check_commit_msg", str(message)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0


def test_staged_spec_is_rejected(tmp_path: Path) -> None:
    _git_init(tmp_path)
    spec = tmp_path / "spec"
    spec.mkdir()
    (spec / "SCIENCE.md").write_text("# Science\n\n## Scope\n\nTODO(owner)\n", encoding="utf-8")
    subprocess.run(["git", "add", "spec/SCIENCE.md"], cwd=tmp_path, check=True)
    assert staged_owner_paths(tmp_path) == ["spec/SCIENCE.md"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["OWNER_SPEC_EDIT"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "tools.check_spec_untouched"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    env.pop("OWNER_SPEC_EDIT")
    completed = subprocess.run(
        [sys.executable, "-m", "tools.check_spec_untouched"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert "needs-science-decision" in completed.stderr


def test_rename_record_keeps_both_paths() -> None:
    payload = b"R100\0spec/SCIENCE.md\0docs/SCIENCE.md\0M\0src/a.py\0"
    assert _changed_paths(payload) == ["spec/SCIENCE.md", "docs/SCIENCE.md", "src/a.py"]


def test_rename_out_of_spec_is_rejected(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _git(tmp_path, "config", "user.email", "owner@example.com")
    _git(tmp_path, "config", "user.name", "Owner")
    spec = tmp_path / "spec"
    spec.mkdir()
    text = "# Science\n\n## Scope\n\nTODO(owner)\n"
    (spec / "SCIENCE.md").write_text(text, encoding="utf-8")
    _git(tmp_path, "add", "spec/SCIENCE.md")
    _git(tmp_path, "commit", "-m", "chore(tooling): add spec skeleton")
    (tmp_path / "docs").mkdir()
    _git(tmp_path, "mv", "spec/SCIENCE.md", "docs/SCIENCE.md")
    assert "spec/SCIENCE.md" in staged_owner_paths(tmp_path)


def test_staged_source_is_allowed(tmp_path: Path) -> None:
    _git_init(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/mod.py"], cwd=tmp_path, check=True)
    assert staged_owner_paths(tmp_path) == []


def _run_hook(module: str, payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)
