#!/usr/bin/env python3
"""Run ruff format on an agent edit. Refuse owner-only paths."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.hooks.policy import OWNER_SPEC_MESSAGE, edited_paths, is_owner_only_path, workspace_roots

_PYTHON_SUFFIXES = {".py", ".pyi"}


def format_python(path: Path) -> int:
    """Format one Python file. Non-Python paths are ignored."""
    if path.suffix not in _PYTHON_SUFFIXES:
        return 0
    if shutil.which("uv") is None:
        print("uv is not on PATH; cannot ruff-format", file=sys.stderr)
        return 2
    completed = subprocess.run(["uv", "run", "ruff", "format", str(path)], check=False)
    return completed.returncode


def main() -> int:
    payload = json.load(sys.stdin)
    roots = workspace_roots(payload)
    paths = edited_paths(payload)
    for path in paths:
        if is_owner_only_path(path, roots=roots):
            print(OWNER_SPEC_MESSAGE, file=sys.stderr)
            return 2
    status = 0
    for path in paths:
        code = format_python(Path(path))
        if code != 0:
            status = code
    return status


if __name__ == "__main__":
    raise SystemExit(main())
