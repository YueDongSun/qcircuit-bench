# Contributing

Humans and agents follow the same bar. The contract is `AGENTS.md`. Scientific
definitions live in `spec/` and are written by Yuedong Sun (@YueDongSun).

## Setup

Install `uv` and Python 3.12, then:

```bash
make setup && make check
```

`make setup` syncs `uv.lock` and installs the pre-commit, commit-msg, and
pre-push hooks. The pre-push hook also refuses any push whose remote ref is
`refs/heads/main`.

## Commits

Conventional Commits, with a required scope:

```text
type(scope): subject
```

Scopes: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`,
`deps`, `spec`.

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`, `revert`.

No `Co-authored-by`, `Generated-by`, or "made with X" trailers. Do not commit
on `main`. Do not use `git commit --no-verify` or `git push --force`.

`spec/` and `data/gold/` are owner-only. A staged change there is rejected
unless the owner sets `OWNER_SPEC_EDIT=1` for that command. Agents never set
that variable. When a spec line is missing or ambiguous, open an issue with
the label `needs-science-decision`, quote the line, list the options, and stop
that piece of work.

## Branches and review

One issue, one branch, one PR. Name the branch `<agent>/<issue_number>_<slug>`.
Comment `claim` and add `in-progress` before editing. Do not push or rebase
another agent's branch. Do not discard dirty work you do not own.

Keep a PR under 400 changed lines excluding `data/` and lockfiles, or explain
the size in the body. Rebase on `main` before review. The owner squash-merges.
Agents do not merge.

Fill in every section of the pull request template. For each claim, say
whether it is prepared, installed, registered, called, or verified. A verified
claim includes the command output. Update `README.md`, `PROGRESS.md`, and any
affected doc in the same PR, and only with behaviour you have verified.

A change to the task format, the public API, or the directory layout needs a
new ADR in `docs/adr/`.

## Tasks

```bash
uv run python tools/new_task.py <family>_<nnn>_<slug>
```

The id pattern is the one in `docs/adr/0002-task-format.md`. The scaffold is a
draft format placeholder. Replace it from `spec/` before asking for review.
Do not invent a tolerance. `make validate` must pass: the solution's tests
pass, and a run that does not execute the solution fails.

`example_000_smoke` is the format demo. Leave its science empty.

## Checks

`make check` is the gate: format, lint, `mypy --strict` on `src/`, pytest
(including `@pytest.mark.slow`), and `make validate`. The pre-push hook runs
it. GitHub Actions runs the same command. Paste the local output in the PR.
