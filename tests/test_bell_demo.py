"""Format-demo Bell grader. Not a bench convention."""

from __future__ import annotations

import tomllib
from pathlib import Path

import cirq
import numpy as np
import pytest
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit

from qcbench.reference.bell import bell_qasm, bell_target_state
from qcbench.taskfmt.schema import load_task, require_format_demo
from qcbench.verify.resources import circuit_depth, gate_count, two_qubit_count
from qcbench.verify.simulate import SIMULATOR_SEED, load_openqasm2, simulate_statevector
from qcbench.verify.state import state_fidelity

ROOT = Path(__file__).resolve().parents[1]


def test_reference_bell_meets_demo_limits() -> None:
    limits = require_format_demo(load_task(ROOT / "tasks" / "example-000-smoke" / "task.toml"))
    circuit = load_openqasm2(bell_qasm())
    prepared = simulate_statevector(circuit, seed=SIMULATOR_SEED)
    assert state_fidelity(prepared, bell_target_state()) >= limits.min_state_fidelity
    assert gate_count(circuit) <= limits.max_gate_count
    assert circuit_depth(circuit) <= limits.max_depth
    assert two_qubit_count(circuit) <= limits.max_two_qubit_count


def test_relative_phase_misses_the_target() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.z(0)
    circuit.cx(0, 1)
    prepared = simulate_statevector(circuit, seed=SIMULATOR_SEED)
    limits = require_format_demo(load_task(ROOT / "tasks" / "example-000-smoke" / "task.toml"))
    assert state_fidelity(prepared, bell_target_state()) < limits.min_state_fidelity


def test_zero_vector_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero vector"):
        state_fidelity(np.zeros(4, dtype=np.complex128), bell_target_state())


def test_instruction_does_not_contain_the_reference_program() -> None:
    instruction = (ROOT / "tasks" / "example-000-smoke" / "instruction.md").read_text(
        encoding="utf-8"
    )
    assert bell_qasm() not in instruction
    assert "h q[0]" not in instruction


def test_pinned_sdk_versions_match_pyproject() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pins = {}
    for dep in project["project"]["dependencies"]:
        name, version = dep.split("==")
        pins[name] = version
    assert cirq.__version__ == pins["cirq"]
    assert qiskit.__version__ == pins["qiskit"]
    assert qiskit_aer.__version__ == pins["qiskit-aer"]
    assert np.__version__ == pins["numpy"]


def test_smoke_image_pins_match_pyproject() -> None:
    text = (ROOT / "tasks" / "example-000-smoke" / "environment" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    for dep in project["project"]["dependencies"]:
        assert f'"{dep}"' in text
    for dep in project["dependency-groups"]["dev"]:
        if dep.startswith("pytest=="):
            assert f'"{dep}"' in text
    for dep in project["build-system"]["requires"]:
        assert f'"{dep}"' in text
