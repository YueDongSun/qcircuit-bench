#!/usr/bin/env python3
"""Reject data/gold files larger than 5120 KiB.

The 500 KiB cap is the pre-commit check-added-large-files hook, which excludes
this directory. See docs/adr/0003-tooling.md.
"""

import sys
from pathlib import Path

GOLD_MAX_BYTES = 5120 * 1024


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def oversized_gold_files(paths: list[Path], *, repo_root: Path, max_bytes: int) -> list[str]:
    """Return descriptions of gold files over ``max_bytes``."""
    too_big: list[str] = []
    root = repo_root.resolve()
    for path in paths:
        candidate = path if path.is_absolute() else root / path
        if not candidate.is_file():
            continue
        relative = candidate.resolve().relative_to(root).as_posix()
        if relative != "data/gold" and not relative.startswith("data/gold/"):
            continue
        size = candidate.stat().st_size
        if size > max_bytes:
            too_big.append(f"{relative} is {size} bytes")
    return too_big


def main(argv: list[str]) -> int:
    root = repo_root()
    too_big = oversized_gold_files(
        [Path(arg) for arg in argv[1:]],
        repo_root=root,
        max_bytes=GOLD_MAX_BYTES,
    )
    if not too_big:
        return 0
    print("data/gold files must be <= 5120 KiB:", file=sys.stderr)
    for line in too_big:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
