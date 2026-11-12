"""spec/ stays headings plus TODO(owner), and data/gold stays empty."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_HEADINGS = {
    "SCIENCE.md": [
        "Scope",
        "Closeness metrics and global-phase convention",
        "Resource accounting conventions",
        "Qubit ordering / endianness convention",
    ],
    "TASKS.md": [
        "Task families (state preparation, unitary synthesis under a gate set/topology, "
        "resource-constrained optimisation)",
    ],
    "TOLERANCES.md": ["Tolerances"],
    "SOURCES.md": ["Sources"],
}


def test_spec_sections_are_owner_todos() -> None:
    for name, headings in _HEADINGS.items():
        text = (ROOT / "spec" / name).read_text(encoding="utf-8")
        for heading in headings:
            assert f"## {heading}\n" in text
        for line in text.splitlines():
            if line.startswith("#") or line.strip() == "":
                continue
            assert line == "TODO(owner)"


def test_gold_has_no_curated_rows() -> None:
    files = [path for path in (ROOT / "data" / "gold").rglob("*") if path.is_file()]
    assert [path.name for path in files] == [".gitkeep"]
    assert (ROOT / "data" / "gold" / ".gitkeep").read_text(encoding="utf-8") == ""
