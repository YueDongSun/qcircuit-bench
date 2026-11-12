"""Decisions shared by the git hooks and the agent-hook scripts."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

OWNER_SPEC_MESSAGE = (
    "spec/ and data/gold/ are owner-only. Open a GitHub issue labelled "
    "needs-science-decision, quote the exact spec line, list the concrete "
    "options, and stop. Do not set OWNER_SPEC_EDIT."
)

_COMMIT_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)
_COMMIT_SCOPES = (
    "task",
    "verify",
    "reference",
    "taskfmt",
    "tooling",
    "docs",
    "ci",
    "deps",
    "spec",
)
COMMIT_SUBJECT = re.compile(
    r"^(?:" + "|".join(_COMMIT_TYPES) + r")\((?:" + "|".join(_COMMIT_SCOPES) + r")\)!?: \S.*$"
)

_SHARED_BRANCHES = frozenset({"main", "master"})
_SEGMENT = re.compile(r"&&|\|\||;|\n")
_PIP_INSTALL = re.compile(r"(?:^|\s)(?:pip3?\s+install|python3?\s+-m\s+pip\s+install)\b")
_GIT_PUSH = re.compile(r"\bgit\s+push\b")
_FORCE_FLAG = re.compile(r"(?:^|\s)(?:-f|--force-with-lease|--force)(?:\s|$)")
_PUSH_ORIGIN_MAIN = re.compile(r"\bgit\s+push\b[^\n]*\borigin\s+main(?:\s|$)")
_COMMIT_NO_VERIFY = re.compile(r"\bgit\s+commit\b[^\n]*--no-verify\b")
_RESET_HARD = re.compile(r"\bgit\s+reset\b[^\n]*--hard\b")
_SHARED_REV = re.compile(r"(?:^|\s)(?:(?:origin|refs/heads)/)?(?:main|master)(?:\s|$)")
_MAIN_REMOTE_REF = "refs/heads/main"
_REMOTE_REF_INDEX = 2
_MIN_PRE_PUSH_FIELDS = 3


@dataclass(frozen=True)
class ShellDecision:
    """Whether one shell command is allowed."""

    deny: bool
    reason: str


def shell_decision(command: str, *, branch: str) -> ShellDecision:
    """Deny commands the governance spec lists for agent shell hooks."""
    reasons: list[str] = []
    if "OWNER_SPEC_EDIT=" in command:
        reasons.append("OWNER_SPEC_EDIT is reserved for the owner; agents must not set it")
    if _PIP_INSTALL.search(command):
        reasons.append("install dependencies with uv add, not pip install")
    for segment in _SEGMENT.split(command):
        if _GIT_PUSH.search(segment) and _FORCE_FLAG.search(segment):
            reasons.append("force-push is refused")
        if _PUSH_ORIGIN_MAIN.search(segment):
            reasons.append("pushing to origin main is refused")
        if _COMMIT_NO_VERIFY.search(segment):
            reasons.append("git commit --no-verify is refused")
        if _RESET_HARD.search(segment) and (
            branch in _SHARED_BRANCHES or _SHARED_REV.search(segment) is not None
        ):
            reasons.append("git reset --hard on a shared branch is refused")
    if not reasons:
        return ShellDecision(deny=False, reason="")
    return ShellDecision(deny=True, reason="; ".join(reasons))


def is_owner_only_path(path: str, *, roots: Sequence[str] = ()) -> bool:
    """Return whether ``path`` is ``spec/`` or ``data/gold/``."""
    normalized = path.replace("\\", "/")
    relatives = [normalized]
    for root in roots:
        root_norm = root.replace("\\", "/").rstrip("/")
        prefix = f"{root_norm}/"
        if normalized.startswith(prefix):
            relatives.append(normalized[len(prefix) :])
    return any(_is_owner_relative(relative) for relative in relatives)


def commit_subject_error(message: str) -> str | None:
    """Return an error when ``message`` is not a scoped Conventional Commit."""
    subject = _subject(message)
    if COMMIT_SUBJECT.fullmatch(subject):
        return None
    scopes = ", ".join(_COMMIT_SCOPES)
    return (
        "commit subject must be a Conventional Commit with a scope from "
        f"[{scopes}], for example 'feat(task): add example-000-smoke'; got {subject!r}"
    )


def push_to_main_ref(stdin_text: str) -> str | None:
    """Return ``refs/heads/main`` when a pre-push line updates it."""
    for line in stdin_text.splitlines():
        if line.strip() == "":
            continue
        parts = line.split()
        if len(parts) >= _MIN_PRE_PUSH_FIELDS and parts[_REMOTE_REF_INDEX] == _MAIN_REMOTE_REF:
            return parts[_REMOTE_REF_INDEX]
    return None


def command_from(payload: Mapping[str, object]) -> str:
    """Read the shell command from a Cursor or Claude hook payload."""
    event = str(payload.get("hook_event_name", ""))
    if event == "beforeShellExecution":
        return str(payload["command"])
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and "command" in tool_input:
        return str(tool_input["command"])
    raise KeyError("shell hook payload has no command")


def shell_hook_output(
    payload: Mapping[str, object], decision: ShellDecision
) -> dict[str, object] | None:
    """JSON object for the hook, or None when Claude should stay silent on allow."""
    event = str(payload.get("hook_event_name", ""))
    if event == "PreToolUse":
        if not decision.deny:
            return None
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }
    if decision.deny:
        return {
            "permission": "deny",
            "user_message": decision.reason,
            "agent_message": decision.reason,
        }
    return {"permission": "allow"}


def edited_paths(payload: Mapping[str, object]) -> list[str]:
    """Paths a file hook is about to read or has edited."""
    event = str(payload.get("hook_event_name", ""))
    if event in {"beforeReadFile", "afterFileEdit"}:
        return [str(payload["file_path"])]
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "notebook_path"):
            if key in tool_input:
                return [str(tool_input[key])]
    return []


def workspace_roots(payload: Mapping[str, object]) -> list[str]:
    """Workspace roots from a Cursor or Claude payload."""
    roots = payload.get("workspace_roots")
    if isinstance(roots, list):
        return [item for item in roots if isinstance(item, str)]
    cwd = payload.get("cwd")
    if isinstance(cwd, str):
        return [cwd]
    return []


def file_hook_output(payload: Mapping[str, object]) -> dict[str, object] | None:
    """Allow reads. Deny writes under spec/ or data/gold/."""
    event = str(payload.get("hook_event_name", ""))
    owner_hit = any(
        is_owner_only_path(path, roots=workspace_roots(payload)) for path in edited_paths(payload)
    )
    if event == "beforeReadFile":
        return {"permission": "allow"}
    if event == "preToolUse":
        if owner_hit:
            return {
                "permission": "deny",
                "user_message": OWNER_SPEC_MESSAGE,
                "agent_message": OWNER_SPEC_MESSAGE,
            }
        return {"permission": "allow"}
    if event == "PreToolUse":
        if owner_hit:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": OWNER_SPEC_MESSAGE,
                }
            }
        return None
    raise ValueError(f"file_guard does not handle {event}")


@dataclass(frozen=True)
class CmdResult:
    """Subprocess result the stop hook inspects."""

    returncode: int
    stdout: str
    stderr: str


def stop_hook_output(payload: Mapping[str, object], result: CmdResult) -> dict[str, object] | None:
    """Follow-up or block payload when ``make check`` fails. None allows stopping."""
    if payload.get("stop_hook_active") is True:
        return None
    status = payload.get("status")
    if status in {"aborted", "error"}:
        return None
    if result.returncode == 0:
        return None
    summary = f"{result.stdout}\n{result.stderr}".strip()
    message = "make check failed. Keep working until it passes.\n" + summary[-4000:]
    event = str(payload.get("hook_event_name", "stop"))
    if event == "Stop":
        return {"decision": "block", "reason": message}
    return {"followup_message": message}


def _is_owner_relative(path: str) -> bool:
    trimmed = path
    while trimmed.startswith("./"):
        trimmed = trimmed[2:]
    return (
        trimmed == "spec"
        or trimmed.startswith("spec/")
        or trimmed == "data/gold"
        or trimmed.startswith("data/gold/")
    )


def _subject(message: str) -> str:
    for line in message.splitlines():
        if line.startswith("#") or line.strip() == "":
            continue
        return line
    return ""
