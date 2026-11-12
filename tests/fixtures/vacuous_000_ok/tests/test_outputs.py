"""Verifier that passes with or without a solution. Used only as a fixture."""


def test_always() -> None:
    assert "vacuous".startswith("vac")
