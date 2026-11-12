# 2. Task format

Date: 2026-11-12

## Status

Accepted

## Context

Tasks are execution-graded and shaped like Terminal-Bench task directories.
The governance contract fixes the files, the id pattern, and the validate
gate. It does not define a physics convention, a tolerance value, or a
difficulty scale. Those headings in `spec/` are `TODO(owner)`.

## Decision

A task lives at `tasks/<task_id>/` and contains only these required paths:

- `task.toml`
- `instruction.md`
- `environment/Dockerfile`
- `solution/solve.sh`
- `tests/test_outputs.py`

`task_id` matches `<family>_<nnn>_<slug>`:

```text
^(?P<family>[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*)_(?P<number>\d{3})_(?P<slug>[a-z][a-z0-9_]*)$
```

`cf_t2_001_laf3_er_levels` has family `cf_t2`, number `001`, and slug
`laf3_er_levels`. `example_000_smoke` has family `example`, number `000`, and
slug `smoke`. The `family` field in `task.toml` must equal the family captured
from the id. The directory name must equal the id.

`task.toml` fields:

- `id`, `family`, `difficulty`, `spec_reference`, `author`: non-empty strings
- `status`: `draft` or `ready`
- `[timeouts] solve_sec` and `test_sec`: positive integers, in seconds

`difficulty` is an author label. The scale is `TODO(owner)` in
`spec/TASKS.md#task-families`. This ADR does not define one. The format demo
uses `demo`. The scaffolder writes `unspecified`.

`spec_reference` is `spec/<file>.md#<heading-slug>`. The file must exist and
must contain a heading whose slug matches. Slugs are lowercase, with
punctuation dropped and spaces turned into hyphens.
`example_000_smoke` points at `spec/TASKS.md#task-families`.

`instruction.md` is what the agent under test sees. It does not include a
hidden answer. `environment/Dockerfile` starts from a base image tagged with
a version that contains a digit, not `latest`. Tests run without network
access. `solution/solve.sh` is the reference solution. `tests/test_outputs.py`
is the hidden verifier: deterministic pytest, and any numeric comparison in a
science task uses a tolerance named in `spec/TOLERANCES.md` rather than a
literal threshold. M0 does not add a tolerance loader, because that file has
no values yet. Inventing a number there is out of bounds.

`make validate` (see `qcbench.taskfmt.validate`) does all of the following for
every task directory:

1. Checks the required files, the toml fields, and the spec anchor.
2. Copies the task to a temporary directory, runs `solution/solve.sh`, and
   requires `pytest tests/test_outputs.py` to pass.
3. Copies the task again, does not run the solution, and requires that pytest
   to fail. A verifier that passes on an empty directory is rejected.

`tools/new_task.py` scaffolds a `draft` that satisfies this gate with a
sentinel file. The sentinel is a format placeholder. It is not a result.
Replace it from `spec/` before review, and do not mark the task `ready` while
the cited spec section is still `TODO(owner)`.

`example_000_smoke` is that format demo, checked in on purpose. Its solution
writes `output/smoke.txt` containing the line `example_000_smoke`. The
instruction states that requirement because the requirement is the whole task.
There is no physical quantity and no numeric tolerance.

The directory is meant to be wrappable by a Terminal-Bench runner later
(`instruction.md`, `environment/Dockerfile`, `solution/solve.sh`,
`tests/test_outputs.py`). This ADR does not add the upstream Terminal-Bench
metadata tables. Those fields are not part of the current contract.

## Consequences

`make check` fails when a task is vacuous or when its solution fails. Science
tasks cannot record a real pass criterion until the owner fills `spec/`.
Agents scaffold engineering only, and they stop at a `needs-science-decision`
issue when a tolerance or convention is required.
