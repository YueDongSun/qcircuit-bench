#!/usr/bin/env python3
"""Run one task's reference solution and verifier on the host."""

from __future__ import annotations

import sys
from pathlib import Path

from qcbench.taskfmt.layout import check_layout
from qcbench.taskfmt.schema import TaskFormatError

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.validate_tasks import ValidationError, run_solution_and_tests  # noqa: E402

_USAGE_ARGC = 2
_USAGE_EXIT = 2


def main() -> int:
    if len(sys.argv) != _USAGE_ARGC:
        print("usage: run_task_locally.py <task-id>", file=sys.stderr)
        return _USAGE_EXIT
    task_dir = _REPO_ROOT / "tasks" / sys.argv[1]
    if not task_dir.is_dir():
        print(f"no task directory {task_dir}", file=sys.stderr)
        return 1
    try:
        check_layout(task_dir, _REPO_ROOT)
        run_solution_and_tests(task_dir)
    except (TaskFormatError, ValidationError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"{task_dir.name}: solution passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
