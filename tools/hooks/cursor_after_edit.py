"""Cursor afterFileEdit hook. Owner-only paths are denied."""

import sys
from pathlib import Path

from tools.hooks.common import emit, field_str, read_event, repo_root
from tools.hooks.policy import OWNER_ONLY_MESSAGE, format_python_file, is_owner_only_path


def main() -> int:
    event = read_event()
    file_path = field_str(event, "file_path")
    root = repo_root()
    if file_path and is_owner_only_path(file_path, repo_root=root):
        print(OWNER_ONLY_MESSAGE, file=sys.stderr)
        emit(
            {
                "permission": "deny",
                "user_message": OWNER_ONLY_MESSAGE,
                "agent_message": OWNER_ONLY_MESSAGE,
            }
        )
        return 2
    if file_path:
        format_python_file(Path(file_path), repo_root=root)
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
