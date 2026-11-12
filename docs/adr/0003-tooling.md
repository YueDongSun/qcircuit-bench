# ADR 0003: Tooling and hooks

## Status

Accepted

## Context

Governance spec sections 4, 5, and 7 require one pinned Python toolchain, three
hook layers that agree, and `make check` as the local source of truth.

## Decision

- Python 3.11, dependencies pinned in `pyproject.toml`, lockfile `uv.lock`.
- `ruff` format and lint (E, F, W, I, B, UP, SIM, RUF, N, PL; line length 100).
  Lint hooks do not pass `--fix`.
- `mypy --strict` on `src/` only.
- `pytest --strict-markers`. Slow tests use the `slow` marker and are included
  in the default run.
- `make check` is `fmt-check`, `lint`, `type`, `test`, and `validate`.
- Git hooks are installed by `make setup` through `pre-commit` (pre-commit and
  commit-msg). The pre-push git hook is `tools/git_hooks/pre-push`, which runs
  `tools/pre_push.py` with the ref list on stdin. pre-commit's own pre-push
  wrapper consumes that list before a local hook can see it, so `make setup`
  replaces `.git/hooks/pre-push` after `pre-commit install`. The same script is
  the pre-push stage in `.pre-commit-config.yaml`.
- `tools/check_spec_untouched.py` rejects staged paths under `spec/` or
  `data/gold/` unless `OWNER_SPEC_EDIT=1`. Agents must not set that variable.
- Commit subjects are Conventional Commits with a mandatory scope:
  `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`,
  `spec`.
- Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`) call
  the same scripts in `tools/hooks/`. Reads of `spec/` are allowed. Writes are
  denied. `afterFileEdit` / PostToolUse format Python with `ruff format`.
  `stop` / Stop runs `make check` and, on failure, tells the agent to continue.
- Hook commands run as `python3 -m tools...` from the repository root so the
  scripts can import `tools`. They are stdlib-only. Formatting and
  `make check` call `uv`.

## Consequences

Pushing to `main` is refused by `tools/pre_push.py` before `make check`.
A push of any other branch runs `make check` and stops on failure.
CI (`.github/workflows/check.yml`) runs the same `make check`. If Actions is
unavailable, the local output is the source of truth.
