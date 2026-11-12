"""Format-demo Bell circuit.

``spec/TASKS.md`` (task families) and ``spec/SCIENCE.md`` (scope, closeness,
resource accounting, qubit ordering) are ``TODO(owner)``. This module only
serves ``tasks/example-000-smoke``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

BELL_QUBITS = 2
BELL_DIMENSION = 4

BELL_QASM = """\
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
"""


def bell_qasm() -> str:
    """Return the format-demo OpenQASM 2.0 program.

    The program prepares ``(|00> + |11>) / sqrt(2)`` under Qiskit's
    little-endian register order. That order is demo wiring, not
    ``spec/SCIENCE.md`` ("Qubit ordering / endianness convention").
    """
    return BELL_QASM


def write_qasm(path: str) -> None:
    """Write :func:`bell_qasm` to ``path``, creating parent directories."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(bell_qasm(), encoding="utf-8")


def bell_target_state() -> np.ndarray:
    """Return ``(|00> + |11>) / sqrt(2)`` as a length-4 statevector.

    Index 0 is ``|q1 q0> = |00>`` and index 3 is ``|11>`` in Qiskit
    little-endian order. Dimensionless amplitudes. Demo target only;
    ``spec/SCIENCE.md`` ("Qubit ordering / endianness convention") is
    ``TODO(owner)``.
    """
    amplitude = 1.0 / np.sqrt(2.0)
    state = np.zeros(BELL_DIMENSION, dtype=np.complex128)
    state[0] = amplitude
    state[BELL_DIMENSION - 1] = amplitude
    return state
