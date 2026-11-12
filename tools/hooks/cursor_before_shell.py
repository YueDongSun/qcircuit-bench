"""Cursor beforeShellExecution hook."""

from tools.hooks.common import branch_for_cwd, emit, field_str, read_event
from tools.hooks.policy import shell_denial


def main() -> int:
    event = read_event()
    denial = shell_denial(
        field_str(event, "command"),
        current_branch=branch_for_cwd(field_str(event, "cwd")),
    )
    if denial is None:
        emit({"permission": "allow"})
        return 0
    emit({"permission": "deny", "user_message": denial, "agent_message": denial})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
