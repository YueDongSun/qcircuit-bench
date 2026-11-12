# Agent contract (qcircuit-bench)

This file is the working contract for coding agents. The binding text is the
shared governance spec; this repository's science is `spec/`. `CLAUDE.md` is a
symlink to this file.

Package name: `qcbench`. Owner: Yuedong Sun (@YueDongSun). Agents never merge.

## Owner-only paths

`spec/` and `data/gold/` are owner-only. Do not edit them. Do not set
`OWNER_SPEC_EDIT`. If a spec point is missing or ambiguous, open a GitHub
issue labelled `needs-science-decision`, quote the exact spec line, list the
concrete options, and stop that piece of work. Do not guess a convention,
tolerance, endianness rule, resource-accounting rule, or physical constant.

`example-000-smoke` is a format demo. Its numbers are task wiring in
`task.toml`, not bench science. Do not promote them into `spec/` or into other
tasks.

## Where code may live

`src/`, `tasks/`, `tests/`, `tools/`, and `docs/` are agent territory. Every
behaviour traces to a line in `spec/` or an ADR in `docs/adr/`. A change to
task format, public API, or directory layout needs a new ADR.

## Engineering rules

- Python 3.11, `uv`, pinned deps, `uv.lock` committed. Add deps with `uv add`,
  never `pip install`.
- `ruff` (E, F, W, I, B, UP, SIM, RUF, N, PL; line length 100) and
  `mypy --strict` on `src/`.
- Tests are deterministic and seeded. Slow tests use `@pytest.mark.slow`.
- No broad `try/except`, no silent fallbacks, no speculative abstraction, no
  checksum manifests, no notebooks under `src/` or `tasks/`, no live or paid
  LLM calls in the suite.
- Type hints on `src/`. Docstrings name units and point at the spec section.

## Tasks

`tools/new_task.py <family>-<nnn>-<slug>` scaffolds `tasks/<task-id>/`.
`instruction.md` must not contain the answer. Verifiers read thresholds by
name from `spec/TOLERANCES.md` once the owner has written them. `make validate`
runs the reference solution and requires a do-nothing run to fail.

## Git

- `main` stays green. One issue, one branch, one PR. Branch:
  `<agent>/<issue-number>-<slug>`. Comment `claim` and add `in-progress`
  before starting. Stay inside the issue's files.
- Commit subjects: `type(scope): subject`. Scope is one of `task`, `verify`,
  `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`.
- No force-push, no `git commit --no-verify`, no `git push origin main`, no
  `git reset --hard` on `main`.
- PR template sections are mandatory. Aim for under 400 changed lines excluding
  `data/` and lockfiles. Rebase on `main` before review. Squash merge is the
  owner's action.
- Update `PROGRESS.md` in the same PR when milestone or task status changes.

## Checks

`make setup && make check` is the gate. `make check` is format, lint, mypy,
pytest (including slow), and validate. The pre-push hook runs it and refuses
`refs/heads/main`.
