"""Parse ``task.toml``.

Missing keys raise ``TaskFormatError``. There is no default tolerance.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

TASK_ID_PATTERN = re.compile(
    r"^(?P<family>[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*)"
    r"-(?P<number>[0-9]{3})-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
_TASK_STATUSES = frozenset({"draft", "ready"})


class TaskFormatError(ValueError):
    """``task.toml`` or the task directory does not match the task format."""


@dataclass(frozen=True)
class Timeouts:
    """Harness timeouts in seconds. Not a physical tolerance."""

    agent_sec: int
    verifier_sec: int


@dataclass(frozen=True)
class FormatDemoLimits:
    """Numeric wiring for ``example-000-smoke`` only.

    Not read from ``spec/TOLERANCES.md``. Fidelity is dimensionless. Gate
    count, depth, and two-qubit count are dimensionless demo caps.
    """

    min_state_fidelity: float
    max_gate_count: int
    max_depth: int
    max_two_qubit_count: int


@dataclass(frozen=True)
class TaskMeta:
    """Required ``task.toml`` fields from governance spec section 3."""

    id: str
    family: str
    difficulty: str
    spec_reference: str
    author: str
    status: str
    timeouts: Timeouts
    format_demo: bool
    format_demo_limits: FormatDemoLimits | None


def load_task(path: Path) -> TaskMeta:
    """Load ``path`` and return the task metadata."""
    table = tomllib.loads(path.read_text(encoding="utf-8"))
    task_id = _require_str(table, "id")
    if TASK_ID_PATTERN.fullmatch(task_id) is None:
        raise TaskFormatError(f"{path}: id {task_id!r} is not <family>-<nnn>-<slug>")
    status = _require_str(table, "status")
    if status not in _TASK_STATUSES:
        raise TaskFormatError(f"{path}: status {status!r} is not draft or ready")
    spec_reference = _require_str(table, "spec_reference")
    if not spec_reference.startswith("spec/"):
        raise TaskFormatError(f"{path}: spec_reference must start with spec/")
    timeouts = _timeouts(table.get("timeouts"), path)
    format_demo = table.get("format_demo", False)
    if not isinstance(format_demo, bool):
        raise TaskFormatError(f"{path}: format_demo must be a boolean")
    limits = _demo_limits(table.get("format_demo_limits"), path)
    if format_demo and limits is None:
        raise TaskFormatError(f"{path}: format_demo requires [format_demo_limits]")
    if not format_demo and limits is not None:
        raise TaskFormatError(f"{path}: [format_demo_limits] is only valid for a format demo")
    return TaskMeta(
        id=task_id,
        family=_require_str(table, "family"),
        difficulty=_require_str(table, "difficulty"),
        spec_reference=spec_reference,
        author=_require_str(table, "author"),
        status=status,
        timeouts=timeouts,
        format_demo=format_demo,
        format_demo_limits=limits,
    )


def require_format_demo(task: TaskMeta) -> FormatDemoLimits:
    """Return demo limits or raise if this task is not a format demo."""
    if task.format_demo_limits is None:
        raise TaskFormatError(f"{task.id} has no [format_demo_limits]")
    return task.format_demo_limits


def _require_str(table: dict[str, object], key: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise TaskFormatError(f"task.toml missing non-empty string {key}")
    return value


def _timeouts(value: object, path: Path) -> Timeouts:
    if not isinstance(value, dict):
        raise TaskFormatError(f"{path}: [timeouts] is required")
    return Timeouts(
        agent_sec=_positive_int(value, "agent_sec", path),
        verifier_sec=_positive_int(value, "verifier_sec", path),
    )


def _demo_limits(value: object, path: Path) -> FormatDemoLimits | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TaskFormatError(f"{path}: [format_demo_limits] must be a table")
    fidelity = value.get("min_state_fidelity")
    if isinstance(fidelity, bool) or not isinstance(fidelity, (int, float)):
        raise TaskFormatError(f"{path}: min_state_fidelity must be a number")
    return FormatDemoLimits(
        min_state_fidelity=float(fidelity),
        max_gate_count=_positive_int(value, "max_gate_count", path),
        max_depth=_positive_int(value, "max_depth", path),
        max_two_qubit_count=_positive_int(value, "max_two_qubit_count", path),
    )


def _positive_int(table: dict[str, object], key: str, path: Path) -> int:
    value = table.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TaskFormatError(f"{path}: {key} must be a positive integer")
    return value
