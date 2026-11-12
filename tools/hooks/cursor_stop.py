"""Cursor stop hook. A failed make check asks the agent to continue."""

from tools.hooks.common import emit, field_str, read_event, repo_root
from tools.hooks.policy import cursor_stop_payload, run_make_check


def main() -> int:
    event = read_event()
    status = field_str(event, "status")
    if status == "aborted":
        emit(cursor_stop_payload(status, 0, ""))
        return 0
    code, output = run_make_check(repo_root())
    emit(cursor_stop_payload(status, code, output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
