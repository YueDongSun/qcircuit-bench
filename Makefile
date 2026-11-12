# qcbench developer commands. See docs/adr/0003-tooling.md.

.PHONY: setup fmt fmt-check lint type test validate check

setup:
	uv sync --all-groups --frozen
	python3 tools/install_git_hooks.py

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

type:
	uv run mypy --strict src

test:
	uv run pytest --strict-markers

validate:
	uv run python tools/validate_tasks.py

check: fmt-check lint type test validate
