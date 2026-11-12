# qcircuit-bench

Execution-graded benchmark for agents that write quantum circuits (Qiskit / Cirq).
A task is graded by a simulator (state or unitary closeness) and by resource
counts (gate count, depth, two-qubit count). Scientific definitions live in
[`spec/`](spec/) and are owner-written.

## Status

| Item | State |
| --- | --- |
| M0 scaffold | in review |
| `spec/` | `TODO(owner)` |
| `example-000-smoke` | format demo only |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11.

```bash
make setup && make check
```

## Add a task

```bash
uv run python tools/new_task.py <family>-<nnn>-<slug>
```

The scaffold does not pass `make validate` until `solution/solve.sh` and
`tests/test_outputs.py` are real. Point `spec_reference` at a heading in
[`spec/`](spec/). Do not invent a tolerance; if the heading is still
`TODO(owner)`, open a `needs-science-decision` issue and stop.

## Contract

- [AGENTS.md](AGENTS.md)
- [spec/](spec/)
- [CONTRIBUTING.md](CONTRIBUTING.md)
