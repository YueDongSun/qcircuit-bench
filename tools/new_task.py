#!/usr/bin/env python3
"""Scaffold ``tasks/<family>-<nnn>-<slug>/``. The draft does not pass validate."""

from __future__ import annotations

import stat
import sys
import tomllib
from pathlib import Path

from qcbench.taskfmt.schema import TASK_ID_PATTERN, TaskFormatError

REPO_ROOT = Path(__file__).resolve().parents[1]
_IMAGE = "python:3.11.11-slim-bookworm"


def scaffold(task_id: str, root: Path) -> Path:
    """Create a draft task directory and return it."""
    match = TASK_ID_PATTERN.fullmatch(task_id)
    if match is None:
        raise TaskFormatError(f"{task_id!r} is not <family>-<nnn>-<slug>")
    destination = root / "tasks" / task_id
    if destination.exists():
        raise TaskFormatError(f"{destination} already exists")
    family = match.group("family")
    (destination / "environment").mkdir(parents=True)
    (destination / "solution").mkdir()
    (destination / "tests").mkdir()
    (destination / "task.toml").write_text(_task_toml(task_id, family), encoding="utf-8")
    (destination / "instruction.md").write_text(_instruction(task_id), encoding="utf-8")
    (destination / "environment" / "Dockerfile").write_text(
        _dockerfile(root, task_id),
        encoding="utf-8",
    )
    solve = destination / "solution" / "solve.sh"
    solve.write_text(_solve(), encoding="utf-8")
    solve.chmod(solve.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (destination / "tests" / "test_outputs.py").write_text(_test(), encoding="utf-8")
    return destination


def dependency_lines(root: Path) -> list[str]:
    """Return pinned requirements the task image installs."""
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    lines = [str(dep) for dep in data["project"]["dependencies"]]
    for dep in data["dependency-groups"]["dev"]:
        text = str(dep)
        if text.startswith("pytest=="):
            lines.append(text)
    lines.extend(str(dep) for dep in data["build-system"]["requires"])
    return lines


def _task_toml(task_id: str, family: str) -> str:
    return (
        f'id = "{task_id}"\n'
        f'family = "{family}"\n'
        'difficulty = "TODO"\n'
        'spec_reference = "spec/TASKS.md#Task families (state preparation, '
        'unitary synthesis under a gate set/topology, resource-constrained optimisation)"\n'
        'author = "TODO"\n'
        'status = "draft"\n'
        "format_demo = false\n"
        "\n"
        "[timeouts]\n"
        "agent_sec = 60\n"
        "verifier_sec = 60\n"
    )


def _instruction(task_id: str) -> str:
    return (
        f"# {task_id}\n"
        "\n"
        "TODO: describe the task by quoting a heading in `spec/`. Do not invent\n"
        "conventions or tolerances. If the heading is still `TODO(owner)`, open a\n"
        "`needs-science-decision` issue and stop.\n"
        "\n"
        "Write OpenQASM 2.0 to the path in `QCBENCH_CIRCUIT_PATH`.\n"
    )


def _dockerfile(root: Path, task_id: str) -> str:
    quoted = " \\\n    ".join(f'"{line}"' for line in dependency_lines(root))
    return (
        f"FROM {_IMAGE}\n"
        "\n"
        "# Build from the repository root:\n"
        f"#   docker build -f tasks/{task_id}/environment/Dockerfile .\n"
        "# Packages are installed at image build. Do not use the network at test time.\n"
        "\n"
        "RUN pip install --no-cache-dir \\\n"
        f"    {quoted}\n"
        "\n"
        "COPY pyproject.toml README.md LICENSE /opt/qcbench/\n"
        "COPY src /opt/qcbench/src\n"
        "RUN pip install --no-cache-dir --no-build-isolation --no-deps /opt/qcbench\n"
        "\n"
        "WORKDIR /workspace\n"
    )


def _solve() -> str:
    return """\
#!/bin/sh
set -eu
echo "TODO: write the reference solution" >&2
exit 1
"""


def _test() -> str:
    return '''\
"""Verifier scaffold. Replace this with a real check. An empty solution must fail."""

from __future__ import annotations


def test_not_implemented() -> None:
    raise AssertionError("TODO: implement the verifier")
'''


_USAGE_ARGC = 2
_USAGE_EXIT = 2


def main() -> int:
    if len(sys.argv) != _USAGE_ARGC:
        print("usage: new_task.py <family>-<nnn>-<slug>", file=sys.stderr)
        return _USAGE_EXIT
    try:
        destination = scaffold(sys.argv[1], REPO_ROOT)
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
