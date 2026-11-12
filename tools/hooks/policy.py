"""Decisions shared by the Cursor and Claude Code hooks.

See ``docs/adr/0003-tooling.md`` and ``AGENTS.md``. Shell segments are split
with ``shlex`` so a quoted flag is a flag, and a commit message that merely
mentions a flag is not.
"""

import re
import shlex
import subprocess
from pathlib import Path

OWNER_ONLY_MESSAGE = (
    "spec/ and data/gold/ are owner-only. Agents cannot edit them. "
    "Open a GitHub issue labelled needs-science-decision, quote the exact spec line, "
    "list the concrete options, and stop work on that piece."
)
KEEP_WORKING = "make check failed. Keep working until it passes."

_OWNER_SPEC = re.compile(r"OWNER_SPEC_EDIT\s*=")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_GIT_GLOBAL_WITH_VALUE = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
)
_COMMIT_MESSAGE_OPTIONS = frozenset({"-m", "--message"})
_FORCE_FLAGS = frozenset({"-f", "--force", "--force-with-lease", "--force-if-includes"})
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
    for segment in re.split(r"&&|\|\||;|\n", command):
        if not segment.strip():
            continue
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            return "shell command could not be parsed"
        denial = _segment_denial(_strip_assignments(tokens), current_branch=current_branch)
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


FILE_EDIT_TOOLS = frozenset(
    {
        "ApplyPatch",
        "Delete",
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "StrReplace",
        "Write",
    }
)


def file_edit_denial(
    tool_name: str,
    tool_input: dict[str, object],
    *,
    repo_root: Path,
) -> str | None:
    """Return the owner-only denial when a file-edit tool targets spec or gold."""
    if tool_name not in FILE_EDIT_TOOLS:
        return None
    for path in paths_from_tool_input(tool_input):
        if is_owner_only_path(path, repo_root=repo_root):
            return OWNER_ONLY_MESSAGE
    return None


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


def _strip_assignments(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and _ASSIGNMENT.match(tokens[index]):
        index += 1
    return tokens[index:]


def _segment_denial(tokens: list[str], *, current_branch: str) -> str | None:
    pip_denial = _pip_denial(tokens)
    if pip_denial is not None:
        return pip_denial
    parsed = _git_command(tokens)
    if parsed is None:
        return None
    subcommand, args = parsed
    if subcommand == "push":
        return _push_denial(args)
    if subcommand == "commit" and _commit_skips_verify(args):
        return "git commit --no-verify is refused"
    if subcommand == "reset":
        return _reset_hard_denial(args, current_branch=current_branch)
    return None


def _push_denial(args: list[str]) -> str | None:
    if _has_force_flag(args):
        return "git push --force is refused"
    if _push_ref_is_main(args):
        return "git push to main is refused"
    return None


def _pip_denial(tokens: list[str]) -> str | None:
    if (
        len(tokens) >= _MIN_PUSH_FIELDS
        and tokens[0] == "uv"
        and tokens[1] == "pip"
        and tokens[2] == "install"
    ):
        return "uv pip install is refused. Add dependencies with uv add."
    if len(tokens) >= _DATA_GOLD_PARTS and tokens[0] in {"pip", "pip3"} and tokens[1] == "install":
        return "pip install is refused. Add dependencies with uv add."
    python_module = 4
    if (
        len(tokens) >= python_module
        and tokens[0] in {"python", "python3"}
        and tokens[1] == "-m"
        and tokens[2] in {"pip", "pip3"}
        and tokens[3] == "install"
    ):
        return "pip install is refused. Add dependencies with uv add."
    return None


def _git_command(tokens: list[str]) -> tuple[str, list[str]] | None:
    if not tokens or (tokens[0] != "git" and not tokens[0].endswith("/git")):
        return None
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token in _GIT_GLOBAL_WITH_VALUE:
            index += _DATA_GOLD_PARTS
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token, tokens[index + 1 :]
    return None


def _commit_skips_verify(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        token = args[index]
        if token in _COMMIT_MESSAGE_OPTIONS or token.startswith("--message="):
            index += _DATA_GOLD_PARTS if token in _COMMIT_MESSAGE_OPTIONS else 1
            continue
        if token in {"--no-verify", "-n"} or token.startswith("--no-verify="):
            return True
        index += 1
    return False


def _has_force_flag(args: list[str]) -> bool:
    for token in args:
        if token in _FORCE_FLAGS:
            return True
        if (
            token.startswith("-f=")
            or token.startswith("--force=")
            or token.startswith("--force-with-lease=")
            or token.startswith("--force-if-includes=")
        ):
            return True
    return False


def _push_ref_is_main(args: list[str]) -> bool:
    for token in args:
        if token.startswith("-"):
            continue
        if token.split(":")[-1] in _MAIN_REFS:
            return True
    return False


def _reset_hard_denial(args: list[str], *, current_branch: str) -> str | None:
    if "--hard" not in args:
        return None
    if current_branch == "main":
        return "git reset --hard on main is refused"
    if any(token == "main" or "origin/" in token for token in args):
        return "git reset --hard on a shared ref is refused"
    return None
