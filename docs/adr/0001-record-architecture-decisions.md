# ADR 0001: Record architecture decisions

## Status

Accepted

## Context

Several agents will change this repository in parallel. Task format, the public
Python API, and the directory layout need a written record so later changes do
not drift from `spec/` or from each other.

## Decision

Architecture decisions are files in `docs/adr/`, numbered `NNNN-title.md`.
Any change to the task format, the package public API, or the directory layout
adds a new ADR in the same pull request.

ADRs do not decide physics, tolerances, or conventions. Those belong in `spec/`
and are owner-only.

## Consequences

Reviewers reject layout, API, or task-format changes that do not add an ADR.
Scientific questions still go to a `needs-science-decision` issue.
