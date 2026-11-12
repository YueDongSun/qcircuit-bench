# 3. Tooling and hooks

Date: 2026-11-12

## Status

Accepted

## Context

Parallel agents need one way to install, check, and commit. The contract asks
for `uv`, ruff, mypy, pytest, a Makefile, pre-commit, Cursor hooks, and Claude
Code hooks, and for those three hook layers to agree.

## Decision

Python is 3.12 or newer. `uv` manages the environment. `uv.lock` is committed.
Direct runtime dependencies are empty in M0: no numerical routine is specified
yet, so numpy, scipy, Qiskit, and Cirq are not added. Dev tools are pinned in
`pyproject.toml` and in the lockfile: ruff 0.17.4, mypy 2.4.1, pytest 9.2.0,
pre-commit 4.7.0, nbstripout 0.9.1.

`make setup` runs `uv sync --all-groups --frozen` and
`tools/install_git_hooks.py`. `make check` runs, in order, `fmt-check`,
`lint`, `type` (`mypy --strict src`), `test` (`pytest --strict-markers`,
slow tests included), and `validate`.

Ruff selects E, F, W, I, B, UP, SIM, RUF, N, and PL, with line length 100.
The pre-commit `ruff-check` hook does not pass `--fix`. `ruff-format` may
rewrite Python files.

Git hooks, installed by pre-commit:

- pre-commit: ruff format, ruff check, mypy on `src/`, nbstripout, check-yaml,
  check-toml, end-of-file-fixer, trailing-whitespace,
  check-added-large-files at 500 KiB with `data/gold/` excluded,
  `tools/check_gold_file_size.py` at 5120 KiB for `data/gold/`,
  `tools/check_spec_untouched.py`, and no-commit-to-branch on `main`.
- commit-msg: `tools/check_commit_msg.py`.
- pre-push: `tools/pre_push.py` runs `make check` and refuses the push when
  the current branch is `main`. `make setup` additionally wraps the git
  pre-push hook so a push whose remote ref is `refs/heads/main` is refused
  before `make check`. pre-commit itself does not forward that ref list.

`tools/check_spec_untouched.py` looks at `git diff --cached`, not at every
file on disk. A later `pre-commit run --all-files` therefore does not fail
just because the M0 skeleton exists. Creating that skeleton is part of M0.
After the hooks are installed, an agent commit that stages `spec/` or
`data/gold/` is rejected. The owner bypass is the environment variable
`OWNER_SPEC_EDIT=1`. Agents must not set it.

Cursor and Claude Code call the scripts in `tools/hooks/`. Policy functions
live in `tools/hooks/policy.py` so the two agents cannot drift. Denied shell
commands and owner-only edits are listed in `AGENTS.md`. The stop hook runs
`make check`. On failure, Cursor receives `followup_message` and Claude Code
receives `decision: block`. Cursor's stop hook sets `loop_limit` to 5 so a
failing check cannot loop forever. An aborted Cursor turn does not run the
check.

GitHub Actions (`.github/workflows/check.yml`) runs the same `make check`.
Local output remains the source of truth when Actions is unavailable.

Commit subjects use the type and scope lists in `CONTRIBUTING.md`. Attribution
trailers are rejected.

## Consequences

A clean `make check` is the engineering gate for every PR. Hook failures are
intentional. M1 can add numpy or a simulator only when a filled spec section
or a new ADR calls for that dependency.
