#!/usr/bin/env python3
"""Refuse a push to main, then run make check."""

from __future__ import annotations

import subprocess
import sys

from tools.hooks.policy import push_to_main_ref


def main() -> int:
    remote_ref = push_to_main_ref(sys.stdin.read())
    if remote_ref is not None:
        print(f"push to {remote_ref} is refused", file=sys.stderr)
        return 1
    completed = subprocess.run(["make", "check"], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
