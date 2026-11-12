"""Claude Code PreToolUse hook for Bash and file edits."""

from tools.hooks.common import branch_for_cwd, emit, field_str, read_event, repo_root
from tools.hooks.policy import (
    OWNER_ONLY_MESSAGE,
    claude_pre_tool_payload,
    is_owner_only_path,
    paths_from_tool_input,
    shell_denial,
)


def main() -> int:
    event = read_event()
    tool = field_str(event, "tool_name")
    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    root = repo_root()
    if tool in {"Bash", "PowerShell"}:
        command = tool_input.get("command")
        command_text = command if isinstance(command, str) else ""
        denial = shell_denial(
            command_text,
            current_branch=branch_for_cwd(field_str(event, "cwd")),
        )
        if denial is None:
            emit(claude_pre_tool_payload("allow", ""))
            return 0
        emit(claude_pre_tool_payload("deny", denial))
        return 0
    if tool in {"Edit", "Write", "MultiEdit"}:
        for path in paths_from_tool_input(tool_input):
            if is_owner_only_path(path, repo_root=root):
                emit(claude_pre_tool_payload("deny", OWNER_ONLY_MESSAGE))
                return 0
    emit(claude_pre_tool_payload("allow", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
