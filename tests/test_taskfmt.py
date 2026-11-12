"""Tests for task ids, scaffolding, and the validate gate."""

import shutil
from pathlib import Path

import pytest

from qcbench.taskfmt.ids import TASK_ID_RE
from qcbench.taskfmt.scaffold import dockerfile_text, scaffold_task
from qcbench.taskfmt.validate import (
    TaskFormatError,
    heading_slug,
    repo_root_from,
    validate_task,
    validate_tasks,
)

ROOT = repo_root_from(Path(__file__).resolve())


@pytest.mark.parametrize(
    ("task_id", "family"),
    [
        ("example_000_smoke", "example"),
        ("cf_t2_001_laf3_er_levels", "cf_t2"),
    ],
)
def test_task_id_pattern(task_id: str, family: str) -> None:
    match = TASK_ID_RE.fullmatch(task_id)
    assert match is not None
    assert match.group("family") == family


@pytest.mark.parametrize(
    "task_id",
    ["Example_000_smoke", "example_00_smoke", "example_000_", "000_smoke"],
)
def test_task_id_pattern_rejects(task_id: str) -> None:
    assert TASK_ID_RE.fullmatch(task_id) is None


def test_heading_slugs_match_the_skeleton() -> None:
    assert heading_slug("Task families") == "task-families"
    assert heading_slug("Circuit conventions (qubit ordering, global phase)") == (
        "circuit-conventions-qubit-ordering-global-phase"
    )
    assert heading_slug("Fidelity and distance definitions") == (
        "fidelity-and-distance-definitions"
    )


def test_smoke_dockerfile_matches_scaffold() -> None:
    dockerfile = ROOT / "tasks" / "example_000_smoke" / "environment" / "Dockerfile"
    assert dockerfile.read_text(encoding="utf-8") == dockerfile_text()


def test_validate_smoke_task() -> None:
    report = validate_tasks(ROOT / "tasks", repo_root=ROOT)
    assert report == "pass example_000_smoke"


def test_scaffold_then_validate(tmp_path: Path) -> None:
    task_dir = scaffold_task("demo_001_placeholder", tasks_root=tmp_path)
    assert validate_task(task_dir, repo_root=ROOT) == "pass demo_001_placeholder"
    with pytest.raises(TaskFormatError, match="already exists"):
        scaffold_task("demo_001_placeholder", tasks_root=tmp_path)


def test_scaffold_rejects_a_bad_id(tmp_path: Path) -> None:
    with pytest.raises(TaskFormatError, match="task id"):
        scaffold_task("NotATask", tasks_root=tmp_path)


def test_vacuous_verifier_is_rejected() -> None:
    task_dir = ROOT / "tests" / "fixtures" / "vacuous_000_ok"
    with pytest.raises(TaskFormatError, match="vacuous"):
        validate_task(task_dir, repo_root=ROOT)


def test_empty_solution_fails(tmp_path: Path) -> None:
    source = ROOT / "tasks" / "example_000_smoke"
    task_dir = tmp_path / "example_000_smoke"
    shutil.copytree(source, task_dir)
    solve = task_dir / "solution" / "solve.sh"
    solve.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    with pytest.raises(TaskFormatError, match="did not pass tests"):
        validate_task(task_dir, repo_root=ROOT)


def test_missing_dockerfile_fails(tmp_path: Path) -> None:
    task_dir = tmp_path / "example_000_smoke"
    task_dir.mkdir()
    (task_dir / "task.toml").write_text("id = 'example_000_smoke'\n", encoding="utf-8")
    with pytest.raises(TaskFormatError, match="missing"):
        validate_task(task_dir, repo_root=ROOT)
