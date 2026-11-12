"""Task schema, layout, and the scaffolder."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from qcbench.taskfmt.layout import check_layout
from qcbench.taskfmt.schema import TASK_ID_PATTERN, TaskFormatError, load_task
from tools.new_task import scaffold

ROOT = Path(__file__).resolve().parents[1]


def test_task_id_pattern_matches_the_governance_example() -> None:
    assert TASK_ID_PATTERN.fullmatch("example-000-smoke")
    assert TASK_ID_PATTERN.fullmatch("cf-t2-001-laf3-er-levels")
    assert TASK_ID_PATTERN.fullmatch("Example-000-smoke") is None
    assert TASK_ID_PATTERN.fullmatch("example-00-smoke") is None


def test_smoke_task_loads() -> None:
    task = load_task(ROOT / "tasks" / "example-000-smoke" / "task.toml")
    assert task.id == "example-000-smoke"
    assert task.format_demo is True
    assert task.format_demo_limits is not None
    assert task.timeouts.agent_sec > 0
    check_layout(ROOT / "tasks" / "example-000-smoke", ROOT)


def test_missing_field_raises(tmp_path: Path) -> None:
    path = tmp_path / "task.toml"
    path.write_text(
        "\n".join(
            [
                'id = "example-000-smoke"',
                'difficulty = "demo"',
                'spec_reference = "spec/TASKS.md#Task families"',
                'author = "m0"',
                'status = "draft"',
                "",
                "[timeouts]",
                "agent_sec = 60",
                "verifier_sec = 60",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(TaskFormatError, match="family"):
        load_task(path)


def test_new_task_scaffolds_a_draft_that_is_not_a_format_demo(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "tasks").mkdir()
    destination = scaffold("cf-t2-001-laf3-er-levels", tmp_path)
    task = load_task(destination / "task.toml")
    assert task.family == "cf-t2"
    assert task.status == "draft"
    assert task.format_demo is False
    assert task.format_demo_limits is None
    solve = destination / "solution" / "solve.sh"
    assert stat.S_IXUSR & solve.stat().st_mode
    dockerfile = (destination / "environment" / "Dockerfile").read_text(encoding="utf-8")
    assert "qiskit==2.6.2" in dockerfile
    with pytest.raises(TaskFormatError):
        scaffold("not a task", tmp_path)
