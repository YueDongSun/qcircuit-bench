#!/bin/sh
set -eu
if [ -z "${QCBENCH_CIRCUIT_PATH:-}" ]; then
  echo "QCBENCH_CIRCUIT_PATH is not set" >&2
  exit 1
fi
python -c 'import os; from qcbench.reference.bell import write_qasm; write_qasm(os.environ["QCBENCH_CIRCUIT_PATH"])'
