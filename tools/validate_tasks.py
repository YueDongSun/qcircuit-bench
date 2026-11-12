#!/usr/bin/env python3
"""Check every task: layout, reference solution passes, empty solution fails."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from qcbench.taskfmt.layout import check_layout
from qcbench.taskfmt.schema import TaskFormatError, load_task

REPO_ROOT = Path(__file__).resolve().parents[1]


class ValidationError(RuntimeError):
    """A task failed structural or behavioural validation."""


def task_dirs(root: Path) -> list[Path]:
    """Return task directories under ``root/tasks``."""
    tasks = root / "tasks"
    return sorted(path for path in tasks.iterdir() if path.is_dir())


def run_solution_and_tests(task_dir: Path) -> None:
    """Run ``solution/solve.sh`` and require ``tests/test_outputs.py`` to pass.

    ``[timeouts].agent_sec`` bounds the solution. ``verifier_sec`` bounds pytest.
    Both are seconds from ``task.toml``.
    """
    timeouts = load_task(task_dir / "task.toml").timeouts
    with tempfile.TemporaryDirectory() as tmp:
        circuit = Path(tmp) / "circuit.qasm"
        _run_solution(task_dir, circuit, timeout_sec=timeouts.agent_sec)
        completed = _pytest(task_dir, circuit, timeout_sec=timeouts.verifier_sec)
        if completed.returncode != 0:
            raise ValidationError(
                f"{task_dir.name}: solution failed tests (exit {completed.returncode})\n"
                f"{completed.stdout}\n{completed.stderr}"
            )


def require_empty_solution_fails(task_dir: Path) -> None:
    """Require the verifier to fail when no circuit file exists."""
    timeouts = load_task(task_dir / "task.toml").timeouts
    with tempfile.TemporaryDirectory() as tmp:
        circuit = Path(tmp) / "circuit.qasm"
        completed = _pytest(task_dir, circuit, timeout_sec=timeouts.verifier_sec)
        if completed.returncode == 0:
            raise ValidationError(
                f"{task_dir.name}: empty solution passed (vacuous verifier)\n"
                f"{completed.stdout}\n{completed.stderr}"
            )


def validate_all(root: Path) -> list[str]:
    """Validate every task. Return summary lines."""
    lines: list[str] = []
    for task_dir in task_dirs(root):
        try:
            check_layout(task_dir, root)
        except TaskFormatError as exc:
            raise ValidationError(str(exc)) from exc
        run_solution_and_tests(task_dir)
        lines.append(f"{task_dir.name}: solution passed")
        require_empty_solution_fails(task_dir)
        lines.append(f"{task_dir.name}: empty solution failed (as required)")
    if not lines:
        raise ValidationError(f"no tasks under {root / 'tasks'}")
    return lines


def _run_solution(task_dir: Path, circuit: Path, *, timeout_sec: int) -> None:
    env = os.environ.copy()
    env["QCBENCH_CIRCUIT_PATH"] = str(circuit)
    completed = _run(
        ["sh", "solution/solve.sh"],
        cwd=task_dir,
        env=env,
        timeout_sec=timeout_sec,
        label=f"{task_dir.name}: solution",
    )
    if completed.returncode != 0:
        raise ValidationError(
            f"{task_dir.name}: solution exited {completed.returncode}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    if not circuit.is_file():
        raise ValidationError(f"{task_dir.name}: solution did not write {circuit}")


def _pytest(task_dir: Path, circuit: Path, *, timeout_sec: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["QCBENCH_CIRCUIT_PATH"] = str(circuit)
    test_file = task_dir / "tests" / "test_outputs.py"
    return _run(
        [sys.executable, "-m", "pytest", str(test_file), "-q"],
        cwd=task_dir,
        env=env,
        timeout_sec=timeout_sec,
        label=f"{task_dir.name}: verifier",
    )


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_sec: int,
    label: str,
) -> subprocess.CompletedProcess[str]:
    """Run ``args`` in its own session and kill the group when ``timeout_sec`` elapses."""
    process = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        _kill_group(process.pid)
        stdout, stderr = process.communicate()
        raise ValidationError(
            f"{label} timed out after {timeout_sec}s\n{stdout or ''}\n{stderr or ''}"
        ) from None
    returncode = process.returncode
    if returncode is None:
        raise ValidationError(f"{label} exited without a return code")
    return subprocess.CompletedProcess(args, returncode, stdout or "", stderr or "")


def _kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def main() -> int:
    try:
        for line in validate_all(REPO_ROOT):
            print(line)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
