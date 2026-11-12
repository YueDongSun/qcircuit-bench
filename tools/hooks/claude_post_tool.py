"""Claude Code PostToolUse hook. Formats Python and blocks owner-only edits."""

from pathlib import Path

from tools.hooks.common import emit, read_event, repo_root
from tools.hooks.policy import (
    OWNER_ONLY_MESSAGE,
    format_python_file,
    is_owner_only_path,
    paths_from_tool_input,
)


def main() -> int:
    event = read_event()
    tool_input = event.get("tool_input", {})
    root = repo_root()
    if isinstance(tool_input, dict):
        for path in paths_from_tool_input(tool_input):
            if is_owner_only_path(path, repo_root=root):
                emit({"decision": "block", "reason": OWNER_ONLY_MESSAGE})
                return 0
            format_python_file(Path(path), repo_root=root)
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
