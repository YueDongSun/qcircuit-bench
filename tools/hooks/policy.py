"""Decisions shared by the Cursor and Claude Code hooks.

See ``docs/adr/0003-tooling.md`` and ``AGENTS.md``. Shell denials match the
command text. They do not try to fully parse shell quoting.
"""

import re
import subprocess
from pathlib import Path

OWNER_ONLY_MESSAGE = (
    "spec/ and data/gold/ are owner-only. Agents cannot edit them. "
    "Open a GitHub issue labelled needs-science-decision, quote the exact spec line, "
    "list the concrete options, and stop work on that piece."
)
KEEP_WORKING = "make check failed. Keep working until it passes."

_FORCE = re.compile(r"(?:^|\s)(?:--force(?:-with-lease|-if-includes)?(?:=|\s|$)|-f(?:=|\s|$))")
_GIT_PUSH = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+push\b")
_GIT_RESET_HARD = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+reset\s+--hard\b")
_GIT_COMMIT = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+commit\b")
_NO_VERIFY = re.compile(r"(?:^|\s)--no-verify(?:=|\s|$)")
_SHORT_NO_VERIFY = re.compile(r"(?:^|\s)-n(?:=|\s|$)")
_PIP_INSTALL = re.compile(r"(?:^|[\s;&|`(])(?:python3?\s+-m\s+)?pip3?\s+install\b")
_UV_PIP_INSTALL = re.compile(r"\buv\s+pip\s+install\b")
_OWNER_SPEC = re.compile(r"OWNER_SPEC_EDIT\s*=")
_MAIN_REFS = frozenset({"main", "refs/heads/main"})
_DATA_GOLD_PARTS = 2
_MIN_PUSH_FIELDS = 3
_REMOTE_REF_INDEX = 2


def shell_denial(command: str, *, current_branch: str) -> str | None:
    """Return a denial reason, or None when the command is allowed."""
    if _OWNER_SPEC.search(command):
        return (
            "OWNER_SPEC_EDIT is reserved for the owner. "
            "Agents must not set it. Open a needs-science-decision issue instead."
        )
    if _pip_install(command):
        return "pip install is refused. Add dependencies with uv add."
    for segment in re.split(r"&&|\|\||;|\n", command):
        denial = _git_denial(segment, current_branch=current_branch)
        if denial is not None:
            return denial
    return None


def is_owner_only_path(path: str, *, repo_root: Path) -> bool:
    """Return True when ``path`` is under ``spec/`` or ``data/gold/``."""
    if not path.strip():
        return False
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        relative = candidate.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    parts = relative.parts
    if not parts:
        return False
    if parts[0] == "spec":
        return True
    return len(parts) >= _DATA_GOLD_PARTS and parts[0] == "data" and parts[1] == "gold"


def read_permission(path: str, *, repo_root: Path) -> str:
    """Return the Cursor beforeReadFile permission.

    Reads stay allowed, including ``spec/``, so an agent can quote a line.
    ``path`` and ``repo_root`` are part of the hook signature for callers.
    """
    del path, repo_root
    return "allow"


def format_python_file(path: Path, *, repo_root: Path) -> None:
    """Run ``ruff format`` on a Python file. Other suffixes are ignored."""
    if path.suffix not in {".py", ".pyi"} or not path.is_file():
        return
    if is_owner_only_path(str(path), repo_root=repo_root):
        return
    subprocess.run(
        ["uv", "run", "ruff", "format", str(path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )


def run_make_check(repo_root: Path) -> tuple[int, str]:
    """Run ``make check``. Return the exit code and the tail of the output."""
    completed = subprocess.run(
        ["make", "check"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    return completed.returncode, output[-4000:]


def cursor_stop_payload(status: str, returncode: int, output: str) -> dict[str, object]:
    """Map a make-check result to a Cursor stop response."""
    if status == "aborted" or returncode == 0:
        return {}
    return {"followup_message": f"{KEEP_WORKING}\n{output}"}


def claude_stop_payload(returncode: int, output: str) -> dict[str, object]:
    """Map a make-check result to a Claude Code stop response."""
    if returncode == 0:
        return {}
    return {"decision": "block", "reason": f"{KEEP_WORKING}\n{output}"}


def claude_pre_tool_payload(decision: str, reason: str) -> dict[str, object]:
    """Build a Claude Code PreToolUse response."""
    specific: dict[str, object] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
    }
    if reason:
        specific["permissionDecisionReason"] = reason
    return {"hookSpecificOutput": specific}


def paths_from_tool_input(tool_input: dict[str, object]) -> list[str]:
    """Collect file paths from an Edit, Write, or MultiEdit payload."""
    found: list[str] = []
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            found.append(value)
    return found


def push_targets_main(stdin_text: str, current_branch: str) -> bool:
    """Return True when a pre-push payload updates ``refs/heads/main``.

    ``stdin_text`` is the git pre-push line list:
    ``<local ref> <local sha> <remote ref> <remote sha>``.
    """
    if current_branch == "main":
        return True
    for line in stdin_text.splitlines():
        parts = line.split()
        if len(parts) >= _MIN_PUSH_FIELDS and parts[_REMOTE_REF_INDEX] == "refs/heads/main":
            return True
    return False


def _pip_install(command: str) -> bool:
    scrubbed = _UV_PIP_INSTALL.sub("", command)
    return _PIP_INSTALL.search(scrubbed) is not None


def _git_denial(segment: str, *, current_branch: str) -> str | None:
    if _GIT_PUSH.search(segment):
        if _FORCE.search(segment):
            return "git push --force is refused"
        if _push_ref_is_main(segment):
            return "git push to main is refused"
    if _GIT_COMMIT.search(segment) and (
        _NO_VERIFY.search(segment) or _SHORT_NO_VERIFY.search(segment)
    ):
        return "git commit --no-verify is refused"
    if _GIT_RESET_HARD.search(segment):
        return _reset_hard_denial(segment, current_branch=current_branch)
    return None


def _push_ref_is_main(segment: str) -> bool:
    match = _GIT_PUSH.search(segment)
    if match is None:
        return False
    for token in segment[match.end() :].split():
        if token.startswith("-"):
            continue
        if token.split(":")[-1] in _MAIN_REFS:
            return True
    return False


def _reset_hard_denial(segment: str, *, current_branch: str) -> str | None:
    if current_branch == "main":
        return "git reset --hard on main is refused"
    if re.search(r"\borigin/", segment) or "main" in segment.split():
        return "git reset --hard on a shared ref is refused"
    return None
