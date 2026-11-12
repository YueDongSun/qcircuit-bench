"""Required files for one task directory."""

from __future__ import annotations

from pathlib import Path

from qcbench.taskfmt.schema import TASK_ID_PATTERN, TaskFormatError, load_task

REQUIRED_RELATIVE_PATHS = (
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "solution/solve.sh",
    "tests/test_outputs.py",
)


def check_layout(task_dir: Path, repo_root: Path) -> None:
    """Raise ``TaskFormatError`` when ``task_dir`` does not match ADR 0002."""
    missing = [rel for rel in REQUIRED_RELATIVE_PATHS if not (task_dir / rel).is_file()]
    if missing:
        raise TaskFormatError(f"{task_dir.name}: missing {missing}")
    if TASK_ID_PATTERN.fullmatch(task_dir.name) is None:
        raise TaskFormatError(f"{task_dir.name} is not <family>-<nnn>-<slug>")
    meta = load_task(task_dir / "task.toml")
    if meta.id != task_dir.name:
        raise TaskFormatError(f"{task_dir.name}: task.toml id is {meta.id!r}")
    spec_file = meta.spec_reference.split("#", 1)[0]
    if not (repo_root / spec_file).is_file():
        raise TaskFormatError(f"{task_dir.name}: spec file {spec_file} does not exist")
