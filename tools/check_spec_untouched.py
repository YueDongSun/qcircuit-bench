#!/usr/bin/env python3
"""Reject staged changes under spec/ or data/gold/ unless the owner opts in."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tools.hooks.policy import OWNER_SPEC_MESSAGE, is_owner_only_path


def staged_owner_paths(repo: Path) -> list[str]:
    """Return staged paths that are owner-only."""
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    names = [item for item in completed.stdout.decode().split("\0") if item]
    return [name for name in names if is_owner_only_path(name)]


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
