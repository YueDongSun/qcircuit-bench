#!/usr/bin/env python3
"""Reject staged changes under spec/ or data/gold/.

The owner bypass is the environment variable OWNER_SPEC_EDIT=1.
Agents must never set it. See docs/adr/0003-tooling.md.
"""

import os
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def staged_paths(cwd: Path) -> list[str]:
    """Return every path in the staged diff, including both sides of a rename.

    ``--name-only`` keeps only the destination of a rename, so moving
    ``spec/SCIENCE.md`` out of ``spec/`` would look unprotected. Exit if git
    cannot answer.
    """
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-status",
            "--find-renames",
            "--diff-filter=ACMRD",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git diff --cached failed"
        raise SystemExit(detail)
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        paths.extend(field for field in fields[1:] if field)
    return paths


def owner_only_relative(path: str) -> bool:
    """Return True for a repo-relative owner-only path."""
    norm = path.replace("\\", "/").lstrip("./")
    if norm in {"spec", "data/gold"}:
        return True
    return norm.startswith("spec/") or norm.startswith("data/gold/")


def main(cwd: Path | None = None) -> int:
    root = repo_root() if cwd is None else cwd
    if os.environ.get("OWNER_SPEC_EDIT") == "1":
        print("OWNER_SPEC_EDIT=1 set; owner-only paths may be staged", file=sys.stderr)
        return 0
    blocked = [path for path in staged_paths(root) if owner_only_relative(path)]
    if not blocked:
        return 0
    print("refusing staged owner-only paths:", file=sys.stderr)
    for path in blocked:
        print(f"  {path}", file=sys.stderr)
    print(
        "spec/ and data/gold/ are owner-only. Open a needs-science-decision issue.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
