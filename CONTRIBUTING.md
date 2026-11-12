# Contributing

Humans and agents follow the same rules. Agents never merge.

## Branches and commits

- `main` is protected: pull request, linear history, no force-push, CODEOWNERS
  review.
- One issue, one branch, one pull request. Branch name:
  `<agent>/<issue-number>-<slug>` (example: `cursor/12-bell-resources`).
- Claim work by commenting `claim` on the issue and adding the `in-progress`
  label. Do not edit files outside the issue's scope.
- Subjects are Conventional Commits with a mandatory scope:

  `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`

  Scope: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`,
  `deps`, `spec`.

  Example: `feat(task): add example-000-smoke`.

## Pull requests

Use the pull request template. Every section is mandatory. Rebase on `main`
before review. Target under 400 changed lines excluding `data/` and lockfiles;
a larger diff needs a reason in the body. Squash merge only, by the owner.
Paste the tail of `make check`. Update `PROGRESS.md` when status changes.

A change to task format, public API, or directory layout needs a new ADR in
`docs/adr/`.

## Science

Do not edit `spec/` or `data/gold/`. Do not set `OWNER_SPEC_EDIT`. Open a
`needs-science-decision` issue instead: quote the spec line, list the options,
and stop that piece of work.

## Setup

```bash
make setup && make check
```

`make setup` installs the pre-commit hooks and the pre-push hook. `uv` must be
on `PATH`. Dependencies are added with `uv add`.
