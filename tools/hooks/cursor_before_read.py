"""Cursor beforeReadFile hook. Reads of spec/ stay allowed."""

from tools.hooks.common import emit, field_str, read_event, repo_root
from tools.hooks.policy import read_permission


def main() -> int:
    event = read_event()
    permission = read_permission(field_str(event, "file_path"), repo_root=repo_root())
    emit({"permission": permission})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
