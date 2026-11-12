# Agent contract

This repository is `qcircuit-bench` (import package `qcbench`), an execution-graded
benchmark for quantum circuit design. Yuedong Sun (@YueDongSun) owns the science.
Agents build the engineering around it. This file is the working contract.
`CLAUDE.md` points at this file.

## 4.0 Owner workflow standard

This section overrides any default coding habit.

- snake_case for every project-owned path and identifier: directories, modules,
  task ids, scripts, and labels where the platform allows it.
- Keep external or required names at their boundaries: `AGENTS.md`, `README.md`,
  `Dockerfile`, `pyproject.toml`, `task.toml`, `.pre-commit-config.yaml`,
  `.cursor/`, `.claude/`, GitHub template filenames, and the repository name.
- Code comments, docs, ADRs, and agent instructions are written in English.
- Ordinary commits contain no attribution trailers. No `Co-authored-by`,
  `Generated-by`, or "made with X" lines.
- One mutable owner per resource. One agent owns one issue, one branch, and one
  worktree at a time. Never edit, rebase, or push another agent's branch.
  Preserve concurrent and unknown dirty work. Never force-remove a worktree or
  a branch.
- Preparation, installation, registration, a successful call, and end-to-end
  acceptance are separate states. Every PR says which state each claim reached.
  Nothing is "verified" without the command output that shows it.
- Never commit credentials, real host inventories, personal chat histories,
  tokens, or token-bearing URLs. When vendoring, keep the upstream license and
  origin note in `THIRD_PARTY_NOTICES.md`.
- Update `README.md` and affected docs with verified behaviour only, in the
  same PR.
- Repository visibility is decided by the owner only.

## Owner-only paths

- `spec/` holds scientific definitions: the physics and maths of each task
  family, conventions, tolerances, gold-data provenance, and the task list.
- `data/gold/` holds owner-curated literature values with citations.
- Agents never edit those trees and never set `OWNER_SPEC_EDIT`.
- If a spec point is missing or ambiguous, open a GitHub issue labelled
  `needs-science-decision`, quote the exact spec line, list the concrete
  options, and stop work on that piece.
- Never guess a convention, a tolerance, or a physical constant that the spec
  does not state.
- `src/`, `tasks/`, `tests/`, `tools/`, and `docs/` are agent territory. Every
  behaviour still traces to a line in `spec/` or an ADR in `docs/adr/`.

## Layout and tasks

`docs/adr/0002-task-format.md` is the task-format decision.
`docs/adr/0003-tooling.md` is the tooling decision.

Each `tasks/<task_id>/` contains `task.toml`, `instruction.md`,
`environment/Dockerfile`, `solution/solve.sh`, and `tests/test_outputs.py`.
Task ids match `<family>_<nnn>_<slug>` in snake_case.
`python tools/new_task.py <task_id>` scaffolds a draft.
`make validate` checks structure, runs the reference solution against its
tests, and checks that a do-nothing run fails those tests.

`example_000_smoke` is a format demo. It is not a science result.
`spec/TOLERANCES.md` is still `TODO(owner)`. Do not hard-code a numeric
tolerance. Science tasks cite a named tolerance from that file once the owner
has written it.

## Code

- Python 3.12 or newer, dependencies through `uv`, `uv.lock` committed, no
  unpinned dependencies.
- `ruff` lints and formats. Rule set: E, F, W, I, B, UP, SIM, RUF, N, PL.
  Line length 100. Lint hooks do not pass `--fix`.
- `mypy --strict` on `src/`.
- `pytest --strict-markers`. Tests are deterministic (explicit seeds when a
  test draws randomness). Slow tests use `@pytest.mark.slow`. `make test` and
  `make check` include slow tests.
- Type hints everywhere in `src/`. Docstrings state units and conventions and
  point at the spec section or the ADR.
- No defensive programming: no broad `try/except`, no silent fallbacks, no
  "just in case" branches, no hand-rolled sanitising beyond what the spec
  requires. Fail loudly with a clear error.
- No speculative abstraction. Build what the current spec needs.
- No checksum or sha256 manifests, signing, or certificate bureaucracy.
- No notebooks in `src/` or `tasks/`. Exploratory notebooks go in `notebooks/`
  with outputs stripped (`nbstripout`).
- Numerical code uses numpy and scipy when a spec section defines the
  calculation. Prefer exact diagonalisation for references. Document the
  matrix basis order from the spec. Do not invent that order.
- No live or paid LLM inference anywhere in the test suite.

## Hooks

Three layers share `tools/hooks/`. `make setup` installs the git layer.

Git pre-commit rejects unformatted or unlinted Python, mypy failures,
notebook outputs, bad YAML or TOML, whitespace errors, files over 500 KiB
(`data/gold/` is capped at 5 MiB instead), staged changes under `spec/` or
`data/gold/`, and commits made on `main`.

Git commit-msg requires Conventional Commits with a scope from this list:
`task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`,
`spec`. Example: `feat(task): add example_000_smoke`.

Git pre-push runs `make check` and refuses a push to `main`.

Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`) deny:

- `git push --force`, `--force-with-lease`, `--force-if-includes`, and `-f`
- `git push` whose destination ref is `main`
- `git commit --no-verify` (including `git commit -n`)
- `git reset --hard` when the current branch is `main` or the command targets
  `main` or any `origin/` ref
- any command that sets `OWNER_SPEC_EDIT`
- `pip install` (add dependencies with `uv add`; `uv pip install` is allowed)

Edits under `spec/` or `data/gold/` are denied before the write: Cursor
`preToolUse` and Claude Code `PreToolUse`. The message points at the
`needs-science-decision` issue flow. Reads of `spec/` stay allowed so an agent
can quote a line. `afterFileEdit` repeats that denial if an owner-only edit is
already on disk, and it runs `ruff format` on other Python files. The stop hook runs `make check` and, on failure, tells the agent to keep
working.

## Branches and pull requests

- `main` stays green. Agents never merge. The owner merges with a squash.
- One issue, one branch, one PR. Branch name: `<agent>/<issue_number>_<slug>`,
  for example `cursor/12_example_smoke`.
- Comment `claim` on the issue and add the label `in-progress` before editing.
  Stay inside the issue's file scope. If two issues need the same file, the
  second waits or splits the change.
- Aim for under 400 changed lines excluding `data/` and lockfiles. A larger
  diff needs a reason in the PR body.
- Rebase on `main` before requesting review.
- The PR template sections are mandatory. Name the spec anchors. Say which
  claims are verified and paste the command output. List what is not verified.
- A change to the task format, the package public API, or the directory layout
  needs a new ADR in `docs/adr/`.
- Update `PROGRESS.md` in the same PR when a milestone or task status changes.

## Commands

`make setup` installs the locked environment and the git hooks.
`make check` runs `fmt-check`, `lint`, `type`, `test` (including slow), and
`validate`. Paste that output in the PR. If CI is down, the local output is
the source of truth. Do not spend the task debugging Actions billing.
