"""Format-demo verifier for example-000-smoke.

Floors are read from this task's ``[format_demo_limits]`` table.
``spec/TOLERANCES.md`` is ``TODO(owner)`` and is not a source of numbers.
See ``docs/adr/0002-task-format.md``.
"""

from __future__ import annotations

import os
from pathlib import Path

from qcbench.reference.bell import bell_target_state
from qcbench.taskfmt.schema import load_task, require_format_demo
from qcbench.verify.resources import circuit_depth, gate_count, two_qubit_count
from qcbench.verify.simulate import SIMULATOR_SEED, load_openqasm2, simulate_statevector
from qcbench.verify.state import state_fidelity

_TASK_DIR = Path(__file__).resolve().parents[1]


def test_bell_state_and_resources() -> None:
    circuit_path = Path(os.environ["QCBENCH_CIRCUIT_PATH"])
    if not circuit_path.is_file():
        raise AssertionError(f"missing circuit at {circuit_path}")
    limits = require_format_demo(load_task(_TASK_DIR / "task.toml"))
    circuit = load_openqasm2(circuit_path.read_text(encoding="utf-8"))
    prepared = simulate_statevector(circuit, seed=SIMULATOR_SEED)
    fidelity = state_fidelity(prepared, bell_target_state())
    assert fidelity >= limits.min_state_fidelity
    assert gate_count(circuit) <= limits.max_gate_count
    assert circuit_depth(circuit) <= limits.max_depth
    assert two_qubit_count(circuit) <= limits.max_two_qubit_count
