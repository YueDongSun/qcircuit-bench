"""Format-demo verifier for example_000_smoke.

Not a physical check. Named tolerances belong in spec/TOLERANCES.md, which is
still TODO(owner). See docs/adr/0002-task-format.md.
"""

from pathlib import Path


def test_smoke_sentinel() -> None:
    text = Path("output/smoke.txt").read_text(encoding="utf-8")
    assert text == "example_000_smoke\n"
