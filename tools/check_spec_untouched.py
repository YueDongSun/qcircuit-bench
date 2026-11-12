#!/usr/bin/env python3
"""Reject staged changes under spec/ or data/gold/ unless the owner opts in."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tools.hooks.policy import OWNER_SPEC_MESSAGE, is_owner_only_path

_RENAME_PATHS = 2


def staged_owner_paths(repo: Path) -> list[str]:
    """Return staged paths that are owner-only, including both sides of a rename."""
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "-z", "-M"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return [path for path in _changed_paths(completed.stdout) if is_owner_only_path(path)]


def _changed_paths(diff_z: bytes) -> list[str]:
    """Return every path in a ``git diff --name-status -z`` payload.

    Rename and copy records carry the old path and the new path. ``--name-only``
    keeps only the destination, which would let a move out of ``spec/`` through.
    """
    tokens = diff_z.decode().split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if status[:1] in {"R", "C"}:
            paths.extend(tokens[index : index + _RENAME_PATHS])
            index += _RENAME_PATHS
        else:
            paths.append(tokens[index])
            index += 1
    return paths


def main() -> int:
    if os.environ.get("OWNER_SPEC_EDIT") == "1":
        return 0
    blocked = staged_owner_paths(Path.cwd())
    if not blocked:
        return 0
    print(OWNER_SPEC_MESSAGE, file=sys.stderr)
    for path in blocked:
        print(path, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
