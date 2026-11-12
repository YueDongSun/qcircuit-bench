"""JSON stdin and stdout for agent hook scripts."""

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """Return the repository root (parent of ``tools/``)."""
    return Path(__file__).resolve().parents[2]


def read_event() -> dict[str, object]:
    """Read one JSON object from stdin. An empty stdin is an empty object."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    loaded: object = json.loads(raw)
    if not isinstance(loaded, dict):
        raise SystemExit("hook input must be a JSON object")
    event: dict[str, object] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise SystemExit("hook input keys must be strings")
        event[key] = value
    return event


def field_str(event: dict[str, object], key: str) -> str:
    """Return a string field, or an empty string when it is absent."""
    value = event.get(key)
    if isinstance(value, str):
        return value
    return ""


def emit(payload: dict[str, object]) -> None:
    """Write one JSON document to stdout for the agent hook runner."""
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def current_branch(cwd: Path) -> str:
    """Return the current git branch. Exit if git cannot answer."""
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git rev-parse failed"
        raise SystemExit(detail)
    return completed.stdout.strip()


def branch_for_cwd(cwd_text: str) -> str:
    """Resolve ``cwd_text`` and return its git branch."""
    root = repo_root()
    cwd = Path(cwd_text) if cwd_text else root
    if not cwd.is_absolute():
        cwd = root / cwd
    if not cwd.is_dir():
        cwd = root
    return current_branch(cwd)
