# ADR 0002: Task format

## Status

Accepted

## Context

Governance spec section 3 requires a Terminal-Bench-style directory per task
and a validator that runs the reference solution and rejects a do-nothing run.
`spec/` is still `TODO(owner)`, so M0 cannot define real pass criteria.

## Decision

Each `tasks/<task-id>/` contains:

- `task.toml` with `id`, `family`, `difficulty`, `spec_reference`, `author`,
  `status` (`draft` or `ready`), and `[timeouts]` (`agent_sec`, `verifier_sec`)
- `instruction.md` (what the agent under test sees)
- `environment/Dockerfile` (build context is the repository root)
- `solution/solve.sh`
- `tests/test_outputs.py`

Task ids match `<family>-<nnn>-<slug>`.

The agent writes OpenQASM 2.0 to the path in `QCBENCH_CIRCUIT_PATH`.
`make validate` checks the file layout, runs `solution/solve.sh` then
`tests/test_outputs.py`, and runs the tests again with no solution. The empty
run must fail. `agent_sec` bounds the solution and `verifier_sec` bounds the
verifier, both in seconds. On expiry the process group is killed and
validation fails.

`example-000-smoke` is a format demo: prepare `(|00> + |11>) / sqrt(2)`.
Its numeric floors live in that task's `[format_demo_limits]` table because
`spec/TOLERANCES.md` has no values. Those floors are not bench tolerances.
The demo grader uses a norm-normalized overlap modulus (global-phase
invariant) and Qiskit's little-endian statevector, and it counts gates with
Qiskit's `size()`, `depth()`, and the number of 2-qubit instructions. Those
choices are demo wiring, not `spec/SCIENCE.md`.

`tools/new_task.py` scaffolds a draft that does not pass `make validate`
until a solution and a failing-on-empty verifier exist.

## Consequences

Real tasks must not copy `[format_demo_limits]` numbers into `spec/` or treat
the demo overlap, endianness, or resource counters as the bench convention.
Promoting any of them requires the owner to fill the matching `spec/` section
and a new ADR if the task format changes.
