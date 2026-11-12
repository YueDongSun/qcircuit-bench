"""Validate Terminal-Bench-style task directories.

Timeouts in ``task.toml`` are seconds. A ``spec_reference`` must name a heading
that exists. This module does not interpret that heading. See
``docs/adr/0002-task-format.md`` and ``spec/TASKS.md``.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

from qcbench.taskfmt.ids import TASK_ID_RE

REQUIRED_PATHS = (
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "solution/solve.sh",
    "tests/test_outputs.py",
)
TASK_STATUSES = frozenset({"draft", "ready"})
_SPEC_REF_RE = re.compile(r"^spec/[A-Za-z0-9_./-]+\.md#[a-z0-9-]+$")
_IMAGE_TAG_RE = re.compile(r"^FROM\s+(\S+)", re.MULTILINE)


class TaskFormatError(Exception):
    """A task id or task directory breaks the format contract."""


@dataclass(frozen=True)
class TaskMeta:
    """Fields read from ``task.toml``. Times are seconds."""

    task_id: str
    family: str
    difficulty: str
    spec_reference: str
    author: str
    status: str
    solve_sec: int
    test_sec: int


def heading_slug(heading: str) -> str:
    """Return the GitHub-style slug for a markdown heading."""
    chars: list[str] = []
    for char in heading.strip().lower():
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-"}:
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def repo_root_from(start: Path) -> Path:
    """Walk upwards from ``start`` to the repository root."""
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "spec").is_dir():
            return candidate
    raise TaskFormatError(f"repo root not found from {start}")


def validate_tasks(tasks_root: Path, *, repo_root: Path) -> str:
    """Validate every task directory under ``tasks_root``."""
    if not tasks_root.is_dir():
        raise TaskFormatError(f"tasks root is not a directory: {tasks_root}")
    task_dirs = sorted(
        path for path in tasks_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    if not task_dirs:
        raise TaskFormatError(f"no tasks under {tasks_root}")
    lines = [validate_task(task_dir, repo_root=repo_root) for task_dir in task_dirs]
    return "\n".join(lines)


def validate_task(task_dir: Path, *, repo_root: Path) -> str:
    """Validate one task. Return a one-line pass report."""
    meta = load_task(task_dir)
    _require_spec_anchor(meta.spec_reference, repo_root=repo_root)
    _require_solution_passes(task_dir, meta)
    _require_do_nothing_fails(task_dir, meta)
    return f"pass {meta.task_id}"


def load_task(task_dir: Path) -> TaskMeta:
    """Read and check the task files. Spec anchors are checked separately."""
    for relative in REQUIRED_PATHS:
        path = task_dir / relative
        if not path.is_file():
            raise TaskFormatError(f"{task_dir.name} is missing {relative}")
        if path.stat().st_size == 0:
            raise TaskFormatError(f"{task_dir.name} has an empty {relative}")
    test_text = (task_dir / "tests" / "test_outputs.py").read_text(encoding="utf-8")
    if "def test_" not in test_text:
        raise TaskFormatError(f"{task_dir.name} tests/test_outputs.py defines no tests")
    _require_pinned_image(task_dir)
    meta = _parse_toml(task_dir / "task.toml")
    if task_dir.name != meta.task_id:
        raise TaskFormatError(f"directory {task_dir.name} does not match task id {meta.task_id}")
    return meta


def _parse_toml(path: Path) -> TaskMeta:
    with path.open("rb") as handle:
        loaded: object = tomllib.load(handle)
    table = _as_dict(loaded, path.name)
    task_id = _require_str(table, "id", label=f"{path} id")
    match = TASK_ID_RE.fullmatch(task_id)
    if match is None:
        raise TaskFormatError(f"{task_id!r} must match <family>_<nnn>_<slug>")
    family = _require_str(table, "family", label=f"{path} family")
    id_family = match.group("family")
    if family != id_family:
        raise TaskFormatError(f"{task_id} family is {family!r}, id family is {id_family!r}")
    status = _require_str(table, "status", label=f"{path} status")
    if status not in TASK_STATUSES:
        raise TaskFormatError(f"{task_id} status must be draft or ready, got {status!r}")
    spec_reference = _require_str(table, "spec_reference", label=f"{path} spec_reference")
    if _SPEC_REF_RE.fullmatch(spec_reference) is None:
        raise TaskFormatError(f"{task_id} spec_reference is not spec/<file>.md#<anchor>")
    timeouts = _as_dict(table.get("timeouts"), f"{task_id} timeouts")
    return TaskMeta(
        task_id=task_id,
        family=family,
        difficulty=_require_str(table, "difficulty", label=f"{path} difficulty"),
        spec_reference=spec_reference,
        author=_require_str(table, "author", label=f"{path} author"),
        status=status,
        solve_sec=_require_positive_int(timeouts.get("solve_sec"), f"{task_id} solve_sec"),
        test_sec=_require_positive_int(timeouts.get("test_sec"), f"{task_id} test_sec"),
    )


def _require_spec_anchor(spec_reference: str, *, repo_root: Path) -> None:
    path_part, separator, anchor = spec_reference.partition("#")
    if separator != "#":
        raise TaskFormatError(f"spec reference has no anchor: {spec_reference}")
    relative = Path(path_part)
    escaped = (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or relative.parts[0] != "spec"
    )
    if escaped:
        raise TaskFormatError(f"spec reference escapes spec/: {spec_reference}")
    path = repo_root / relative
    if not path.is_file():
        raise TaskFormatError(f"spec reference file does not exist: {path_part}")
    slugs = [
        heading_slug(line.lstrip("#").strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    ]
    if anchor not in slugs:
        raise TaskFormatError(f"{spec_reference} does not match a heading in {path_part}")


def _require_pinned_image(task_dir: Path) -> None:
    text = (task_dir / "environment" / "Dockerfile").read_text(encoding="utf-8")
    match = _IMAGE_TAG_RE.search(text)
    if match is None:
        raise TaskFormatError(f"{task_dir.name} Dockerfile has no FROM image")
    image = match.group(1)
    if ":" not in image:
        raise TaskFormatError(f"{task_dir.name} base image must include a version tag")
    tag = image.split(":", 1)[1].split("@", 1)[0]
    if tag in {"latest", "stable"} or re.search(r"\d", tag) is None:
        raise TaskFormatError(f"{task_dir.name} base image tag must include a version")


def _require_solution_passes(task_dir: Path, meta: TaskMeta) -> None:
    sandbox = _copy_task(task_dir)
    try:
        solve = _run(
            ["bash", "solution/solve.sh"],
            cwd=sandbox,
            timeout=meta.solve_sec,
        )
        if solve.returncode != 0:
            raise TaskFormatError(f"{meta.task_id} solution failed\n{solve.stdout}\n{solve.stderr}")
        tests = _pytest(sandbox, timeout=meta.test_sec)
        if tests.returncode != 0:
            raise TaskFormatError(
                f"{meta.task_id} solution did not pass tests\n{tests.stdout}\n{tests.stderr}"
            )
    finally:
        shutil.rmtree(sandbox.parent)


def _require_do_nothing_fails(task_dir: Path, meta: TaskMeta) -> None:
    sandbox = _copy_task(task_dir)
    try:
        tests = _pytest(sandbox, timeout=meta.test_sec)
    finally:
        shutil.rmtree(sandbox.parent)
    if tests.returncode == 0:
        raise TaskFormatError(
            f"{meta.task_id} verifier passed without the solution; it is vacuous\n"
            f"{tests.stdout}\n{tests.stderr}"
        )


def _copy_task(task_dir: Path) -> Path:
    root = Path(tempfile.mkdtemp(prefix="qcbench-validate-"))
    destination = root / task_dir.name
    shutil.copytree(
        task_dir,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "output"),
    )
    return destination


def _pytest(sandbox: Path, *, timeout: int) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_outputs.py",
            "--strict-markers",
            "--rootdir",
            str(sandbox),
            "-p",
            "no:cacheprovider",
            "-q",
        ],
        cwd=sandbox,
        timeout=timeout,
    )


def _run(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTEST_CURRENT_TEST", None)
    env["PYTHONHASHSEED"] = "0"
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise TaskFormatError(f"{command[0]} timed out after {timeout}s") from exc


def _as_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TaskFormatError(f"{label} must be a table")
    mapped: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TaskFormatError(f"{label} keys must be strings")
        mapped[key] = item
    return mapped


def _require_str(table: dict[str, object], key: str, *, label: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TaskFormatError(f"{label} must be a non-empty string")
    return value


def _require_positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TaskFormatError(f"{label} must be a positive int")
    return value
