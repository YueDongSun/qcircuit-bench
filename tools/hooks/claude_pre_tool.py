"""Claude Code PreToolUse hook for Bash and file edits."""

from tools.hooks.common import branch_for_cwd, emit, field_str, read_event, repo_root
from tools.hooks.policy import claude_pre_tool_payload, file_edit_denial, shell_denial


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
    denial = file_edit_denial(tool, tool_input, repo_root=root)
    if denial is not None:
        emit(claude_pre_tool_payload("deny", denial))
        return 0
    emit(claude_pre_tool_payload("allow", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
