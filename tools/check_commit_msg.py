#!/usr/bin/env python3
"""Reject commit subjects that are not scoped Conventional Commits."""

from __future__ import annotations

import sys
from pathlib import Path

from tools.hooks.policy import commit_subject_error


def message_text(argv: list[str], stdin: str) -> str:
    """Read the message file git passed, or stdin when no path was given."""
    if len(argv) > 1:
        return Path(argv[1]).read_text(encoding="utf-8")
    return stdin


def main() -> int:
    error = commit_subject_error(message_text(sys.argv, sys.stdin.read()))
    if error is None:
        return 0
    print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
