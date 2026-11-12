"""Claude Code Stop hook. A failed make check blocks the stop."""

from tools.hooks.common import emit, read_event, repo_root
from tools.hooks.policy import claude_stop_payload, run_make_check


def main() -> int:
    read_event()
    code, output = run_make_check(repo_root())
    emit(claude_stop_payload(code, output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
