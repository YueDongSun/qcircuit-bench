"""Cursor preToolUse hook. Owner-only edits are denied before the write."""

from tools.hooks.common import emit, field_str, read_event, repo_root
from tools.hooks.policy import file_edit_denial


def main() -> int:
    event = read_event()
    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    denial = file_edit_denial(
        field_str(event, "tool_name"),
        tool_input,
        repo_root=repo_root(),
    )
    if denial is None:
        emit({"permission": "allow"})
        return 0
    emit({"permission": "deny", "user_message": denial, "agent_message": denial})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
