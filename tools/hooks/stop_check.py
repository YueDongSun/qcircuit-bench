#!/usr/bin/env python3
"""Run make check when an agent session stops."""

from __future__ import annotations

import json
import subprocess
import sys

from tools.hooks.policy import CmdResult, stop_hook_output


def run_make_check() -> CmdResult:
    """Run ``make check`` in the current directory."""
    completed = subprocess.run(["make", "check"], check=False, capture_output=True, text=True)
    return CmdResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def main() -> int:
    payload = json.load(sys.stdin)
    output = stop_hook_output(payload, run_make_check())
    if output is not None:
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
