"""Run every task solution against its verifier, and require an empty run to fail."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tools.validate_tasks import ValidationError, _run, validate_all

ROOT = Path(__file__).resolve().parents[1]
_TIMEOUT_SEC = 1


def test_run_kills_the_group_on_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match=f"timed out after {_TIMEOUT_SEC}s"):
        _run(
            ["sleep", "30"],
            cwd=tmp_path,
            env=os.environ.copy(),
            timeout_sec=_TIMEOUT_SEC,
            label="sleep",
        )


@pytest.mark.slow
def test_every_task_solution_passes_and_empty_solution_fails() -> None:
    lines = validate_all(ROOT)
    assert "example-000-smoke: solution passed" in lines
    assert "example-000-smoke: empty solution failed (as required)" in lines
