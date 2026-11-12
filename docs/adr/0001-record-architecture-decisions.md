# 1. Record architecture decisions

Date: 2026-11-12

## Status

Accepted

## Context

Several agents will change this repository in parallel. Task format, the
public Python API, and the directory layout need a written decision that later
agents can point at. Scientific choices do not belong here. Those stay in
`spec/`, which agents do not edit.

## Decision

Engineering decisions that change the task format, the package public API, or
the directory layout are recorded as ADRs in `docs/adr/`.

- Number files `NNNN-snake-or-hyphen-title.md`. The first three are
  `0001-record-architecture-decisions.md`, `0002-task-format.md`, and
  `0003-tooling.md`, matching the names fixed for every sibling bench.
- Write ADRs in English.
- Do not rewrite an accepted ADR to change its meaning. Supersede it with a
  new ADR.
- A pull request that changes one of those contracts links the ADR in the
  "Contract changes" section.
- Behaviour that is not a contract change does not need an ADR, but it still
  needs a spec line or an existing ADR.

## Consequences

Reviewers can reject a contract change that has no ADR. Agents stop and open a
`needs-science-decision` issue when the missing decision is scientific rather
than engineering.
