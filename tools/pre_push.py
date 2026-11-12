#!/usr/bin/env python3
"""Refuse a push to main, then run make check.

``--refs-only`` checks the git pre-push ref list and does not run make check.
See docs/adr/0003-tooling.md.
"""

import subprocess
import sys
from pathlib import Path

from tools.hooks.common import current_branch
from tools.hooks.policy import push_targets_main


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str], stdin_text: str) -> int:
    root = repo_root()
    if push_targets_main(stdin_text, current_branch(root)):
        print("refusing push to main", file=sys.stderr)
        return 1
    if "--refs-only" in argv:
        return 0
    print("pre-push: running make check", file=sys.stderr)
    completed = subprocess.run(["make", "check"], cwd=root, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv, sys.stdin.read()))
