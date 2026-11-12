"""Scaffold a draft task directory.

The generated verifier checks a sentinel file. That sentinel is a format
placeholder, not a physical result. See ``docs/adr/0002-task-format.md``.
Timeouts written into ``task.toml`` are seconds.
"""

import stat
from pathlib import Path

from qcbench.taskfmt.ids import TASK_ID_RE
from qcbench.taskfmt.validate import TaskFormatError

# Index digest for python:3.12.12-slim-bookworm, read from Docker Hub on 2026-11-12.
BASE_IMAGE = (
    "python:3.12.12-slim-bookworm"
    "@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c"
)

SOLVE_SEC = 60
TEST_SEC = 60


def dockerfile_text() -> str:
    """Return the pinned format-demo Dockerfile."""
    return f"FROM {BASE_IMAGE}\n\nWORKDIR /task\n"


def scaffold_task(task_id: str, *, tasks_root: Path) -> Path:
    """Create ``tasks_root/task_id`` and return that path.

    Raises ``TaskFormatError`` when the id is illegal or the directory exists.
    """
    match = TASK_ID_RE.fullmatch(task_id)
    if match is None:
        raise TaskFormatError(f"task id must match <family>_<nnn>_<slug>, got {task_id!r}")
    family = match.group("family")
    destination = tasks_root / task_id
    if destination.exists():
        raise TaskFormatError(f"task already exists: {destination}")
    (destination / "environment").mkdir(parents=True)
    (destination / "solution").mkdir()
    (destination / "tests").mkdir()
    (destination / "task.toml").write_text(
        _task_toml(task_id, family),
        encoding="utf-8",
    )
    (destination / "instruction.md").write_text(
        _instruction(task_id),
        encoding="utf-8",
    )
    (destination / "environment" / "Dockerfile").write_text(
        dockerfile_text(),
        encoding="utf-8",
    )
    solve = destination / "solution" / "solve.sh"
    solve.write_text(_solve(task_id), encoding="utf-8")
    solve.chmod(solve.stat().st_mode | stat.S_IEXEC)
    (destination / "tests" / "test_outputs.py").write_text(
        _test_outputs(task_id),
        encoding="utf-8",
    )
    return destination


def _task_toml(task_id: str, family: str) -> str:
    return (
        "# Draft format scaffold. Not a science task.\n"
        f'id = "{task_id}"\n'
        f'family = "{family}"\n'
        'difficulty = "unspecified"\n'
        'spec_reference = "spec/TASKS.md#task-families"\n'
        'author = "scaffold"\n'
        'status = "draft"\n'
        "\n"
        "[timeouts]\n"
        f"solve_sec = {SOLVE_SEC}\n"
        f"test_sec = {TEST_SEC}\n"
    )


def _instruction(task_id: str) -> str:
    return (
        f"# {task_id}\n"
        "\n"
        "Format scaffold, not a science task. Do not invent a physical\n"
        "quantity. Replace this file from `spec/` before review.\n"
        "\n"
        "Write `output/sentinel.txt` containing exactly this line:\n"
        "\n"
        "```text\n"
        f"{task_id}\n"
        "```\n"
    )


def _solve(task_id: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "mkdir -p output\n"
        f"printf '%s\\n' '{task_id}' > output/sentinel.txt\n"
    )


def _test_outputs(task_id: str) -> str:
    return (
        '"""Format placeholder verifier.\n'
        "\n"
        "Not a physical check. Named tolerances belong in spec/TOLERANCES.md.\n"
        "See docs/adr/0002-task-format.md.\n"
        '"""\n'
        "\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def test_sentinel() -> None:\n"
        '    text = Path("output/sentinel.txt").read_text(encoding="utf-8")\n'
        f'    assert text == "{task_id}\\n"\n'
    )
