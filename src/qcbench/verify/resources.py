"""Format-demo resource counters.

Counts are dimensionless. Depth is Qiskit's ``QuantumCircuit.depth`` layer
count. ``spec/SCIENCE.md`` ("Resource accounting conventions") is
``TODO(owner)``. These counters are not that convention.
"""

from __future__ import annotations

from qiskit import QuantumCircuit

_TWO_QUBIT_WIDTH = 2


def gate_count(circuit: QuantumCircuit) -> int:
    """Return ``QuantumCircuit.size()`` (instruction count, no parameters)."""
    return int(circuit.size())


def circuit_depth(circuit: QuantumCircuit) -> int:
    """Return ``QuantumCircuit.depth()`` (parallel-instruction layers)."""
    return int(circuit.depth())


def two_qubit_count(circuit: QuantumCircuit) -> int:
    """Return how many instructions act on two qubits."""
    return sum(1 for instruction in circuit.data if len(instruction.qubits) == _TWO_QUBIT_WIDTH)
