#!/usr/bin/env python3
"""Scaffold a draft task directory. See docs/adr/0002-task-format.md."""

import sys
from pathlib import Path

from qcbench.taskfmt.scaffold import scaffold_task
from qcbench.taskfmt.validate import TaskFormatError, repo_root_from

_PROGRAM_AND_TASK_ID = 2


def main(argv: list[str]) -> int:
    if len(argv) != _PROGRAM_AND_TASK_ID:
        print("usage: tools/new_task.py <task_id>", file=sys.stderr)
        return 2
    root = repo_root_from(Path(__file__).resolve())
    try:
        path = scaffold_task(argv[1], tasks_root=root / "tasks")
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
