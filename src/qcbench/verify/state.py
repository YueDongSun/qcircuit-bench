"""Format-demo pure-state overlap.

``spec/SCIENCE.md`` ("Closeness metrics and global-phase convention") is
``TODO(owner)``. This is not that convention.
"""

from __future__ import annotations

import numpy as np

_ZERO_NORM_SQ = 0.0


def state_fidelity(prepared: np.ndarray, target: np.ndarray) -> float:
    """Return ``|<prepared|target>|^2 / (||prepared||^2 ||target||^2)``.

    Dimensionless, in ``[0, 1]`` up to floating-point roundoff. The modulus
    makes the value invariant under a relative global phase. Relative phase
    between basis states is not removed. Demo metric only.
    """
    left = np.asarray(prepared, dtype=np.complex128).reshape(-1)
    right = np.asarray(target, dtype=np.complex128).reshape(-1)
    if left.shape != right.shape:
        raise ValueError(f"state dimension mismatch: {left.shape[0]} vs {right.shape[0]}")
    left_norm_sq = complex(np.vdot(left, left)).real
    right_norm_sq = complex(np.vdot(right, right)).real
    if _ZERO_NORM_SQ in (left_norm_sq, right_norm_sq):
        raise ValueError("state fidelity is undefined for a zero vector")
    overlap = complex(np.vdot(left, right))
    return float(abs(overlap) ** 2 / (left_norm_sq * right_norm_sq))
