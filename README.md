# qcircuit-bench

Execution-graded agent benchmark for quantum circuit design. An agent under
test writes circuit code. A simulator grades it. Scientific definitions are
owner-written in [`spec/`](spec/). Package name: `qcbench`.

## Status

| Item | State |
| --- | --- |
| M0 scaffold | in review |
| `spec/` | headings only, `TODO(owner)` |
| Tasks | `example_000_smoke` format demo |

Milestone detail is in [`PROGRESS.md`](PROGRESS.md).

## Quickstart

Install [uv](https://docs.astral.sh/uv/) and Python 3.12, then:

```bash
make setup && make check
```

## Add a task

```bash
uv run python tools/new_task.py <family>_<nnn>_<slug>
```

Write the task from `spec/`. Do not edit `spec/` or `data/gold/`.
`example_000_smoke` shows the directory shape. It is not a science task.

## Contracts

- [AGENTS.md](AGENTS.md) for agents and reviewers
- [CONTRIBUTING.md](CONTRIBUTING.md) for branches, commits, and reviews
- [spec/](spec/) for the science the owner still has to fill
