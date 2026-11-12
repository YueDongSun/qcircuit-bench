#!/usr/bin/env python3
"""Deny agent writes under spec/ and data/gold/. Reads stay allowed."""

from __future__ import annotations

import json
import sys

from tools.hooks.policy import file_hook_output


def main() -> int:
    payload = json.load(sys.stdin)
    output = file_hook_output(payload)
    if output is not None:
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
