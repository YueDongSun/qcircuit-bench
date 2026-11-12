#!/usr/bin/env python3
"""Require a Conventional Commit with a scope from the allowed list."""

import re
import sys
from pathlib import Path

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)
SCOPES = (
    "task",
    "verify",
    "reference",
    "taskfmt",
    "tooling",
    "docs",
    "ci",
    "deps",
    "spec",
)
HEADER = re.compile(rf"^({'|'.join(TYPES)})\(({'|'.join(SCOPES)})\)!?: \S.*$")
TRAILER = re.compile(r"^(Co-authored-by|Generated-by|Made-with):", re.IGNORECASE)
MADE_WITH = re.compile(r"made with", re.IGNORECASE)
_PROGRAM_AND_FILE = 2


def commit_message_error(message: str) -> str | None:
    """Return an error string, or None when the message is acceptable."""
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    while lines and lines[-1] == "":
        lines.pop()
    if not lines or not lines[0].strip():
        return "commit message is empty"
    if HEADER.fullmatch(lines[0]) is None:
        types = ", ".join(TYPES)
        scopes = ", ".join(SCOPES)
        return (
            "commit message must be Conventional Commits with a required scope: "
            f"type(scope): subject. types: {types}. scopes: {scopes}."
        )
    for line in lines[1:]:
        if TRAILER.match(line) or MADE_WITH.search(line):
            return "attribution trailers are not allowed in commit messages"
    return None


def main(argv: list[str]) -> int:
    if len(argv) != _PROGRAM_AND_FILE:
        print("usage: tools/check_commit_msg.py COMMIT_MSG_FILE", file=sys.stderr)
        return 2
    message = Path(argv[1]).read_text(encoding="utf-8")
    error = commit_message_error(message)
    if error is None:
        return 0
    print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
