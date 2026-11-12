#!/usr/bin/env python3
"""Run the task-format gate. See docs/adr/0002-task-format.md."""

import argparse
import sys
from pathlib import Path

from qcbench.taskfmt.validate import TaskFormatError, repo_root_from, validate_tasks


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate task directories.")
    parser.add_argument(
        "--tasks-root",
        type=Path,
        default=None,
        help="Directory of task folders. Defaults to tasks/.",
    )
    args = parser.parse_args(argv[1:])
    root = repo_root_from(Path(__file__).resolve())
    tasks_root = args.tasks_root if args.tasks_root is not None else root / "tasks"
    try:
        report = validate_tasks(tasks_root, repo_root=root)
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
