#!/usr/bin/env python3
"""Install pre-commit hooks and chain the main-branch guard onto pre-push."""

import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = "# qcbench-pre-push-guard"


def hooks_dir() -> Path:
    """Return ``<git-common-dir>/hooks``, where pre-commit writes its scripts.

    ``git rev-parse --git-path hooks`` follows ``core.hooksPath`` and is not
    the directory pre-commit installs into.
    """
    completed = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    path = Path(completed.stdout.strip())
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path / "hooks"


def install_pre_commit() -> None:
    subprocess.run(
        [
            "uv",
            "run",
            "pre-commit",
            "install",
            "--overwrite",
            "--install-hooks",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "commit-msg",
            "--hook-type",
            "pre-push",
        ],
        cwd=REPO_ROOT,
        check=True,
    )


def wrap_pre_push(hooks: Path) -> None:
    pre_push = hooks / "pre-push"
    chained = hooks / "pre-push.pre-commit"
    text = pre_push.read_text(encoding="utf-8")
    wrapper = (REPO_ROOT / "tools" / "pre_push_wrapper.sh").read_text(encoding="utf-8")
    if MARKER not in text.splitlines()[:3]:
        chained.write_text(text, encoding="utf-8")
        chained.chmod(chained.stat().st_mode | stat.S_IEXEC)
    pre_push.write_text(wrapper, encoding="utf-8")
    pre_push.chmod(pre_push.stat().st_mode | stat.S_IEXEC)


def main() -> int:
    install_pre_commit()
    wrap_pre_push(hooks_dir())
    print("git hooks installed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
