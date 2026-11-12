"""Format-demo Aer statevector simulation.

``spec/SCIENCE.md`` ("Closeness metrics and global-phase convention" and
"Qubit ordering / endianness convention") is ``TODO(owner)``. The statevector
axis is whatever Qiskit Aer returns for the loaded OpenQASM register.
"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, qasm2
from qiskit_aer import AerSimulator

SIMULATOR_SEED = 1


def load_openqasm2(source: str) -> QuantumCircuit:
    """Parse an OpenQASM 2.0 program with Qiskit's loader."""
    return qasm2.loads(source)


def simulate_statevector(circuit: QuantumCircuit, *, seed: int) -> np.ndarray:
    """Return the Aer ``statevector`` method amplitudes of ``circuit``.

    ``seed`` is passed to Aer ``seed_simulator`` so the run is deterministic.
    It is not a physical parameter. A copy of ``circuit`` receives
    ``save_statevector``; count resources on the original circuit.
    """
    simulated = circuit.copy()
    simulated.save_statevector()
    simulator = AerSimulator(method="statevector")
    result = simulator.run(simulated, seed_simulator=seed).result()
    vector = result.get_statevector(simulated)
    return np.asarray(vector, dtype=np.complex128)
