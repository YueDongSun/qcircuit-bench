# FORMAT DEMO — not a scientific task

This task exercises the harness. It does not define the benchmark's physics,
tolerances, or conventions. Those headings in `spec/` are `TODO(owner)`.

## Goal

Prepare the 2-qubit Bell state `(|00> + |11>) / sqrt(2)`.

Write an OpenQASM 2.0 program to the path in the environment variable
`QCBENCH_CIRCUIT_PATH`.

## How this demo is graded

The grader is demo wiring, not `spec/SCIENCE.md`:

- The program is loaded with Qiskit. Qiskit's statevector index is
  little-endian in the register: `q[0]` is the least significant bit, so the
  target amplitudes sit on basis states 0 and 3. Bench endianness is not
  decided.
- Closeness is the norm-normalized overlap modulus with that target. A global
  phase is accepted. A different relative phase is not. Bench closeness and
  global-phase rules are not decided.
- Gate count, depth, and two-qubit count use Qiskit's `size()`, `depth()`, and
  the number of instructions that act on two qubits. They must sit within
  `[format_demo_limits]` in `task.toml`. Bench resource accounting is not
  decided.

Do not copy these rules into another task.
