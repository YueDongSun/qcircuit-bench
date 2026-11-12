"""Run every task solution against its verifier, and require an empty run to fail."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.validate_tasks import validate_all

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_every_task_solution_passes_and_empty_solution_fails() -> None:
    lines = validate_all(ROOT)
    assert "example-000-smoke: solution passed" in lines
    assert "example-000-smoke: empty solution failed (as required)" in lines
