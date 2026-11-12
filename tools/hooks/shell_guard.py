#!/usr/bin/env python3
"""Deny shell commands listed in the governance spec."""

from __future__ import annotations

import json
import subprocess
import sys

from tools.hooks.policy import command_from, shell_decision, shell_hook_output


def current_branch() -> str:
    """Return the current git branch name."""
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    payload = json.load(sys.stdin)
    decision = shell_decision(command_from(payload), branch=current_branch())
    output = shell_hook_output(payload, decision)
    if output is not None:
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
