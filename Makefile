.PHONY: setup fmt fmt-check lint type test validate check

setup:
	uv sync --all-groups
	@hooks_path="$$(git config --get core.hooksPath || true)"; \
	if [ -n "$$hooks_path" ]; then git config --unset core.hooksPath; fi; \
	uv run pre-commit install --install-hooks; \
	status=$$?; \
	if [ -n "$$hooks_path" ]; then git config core.hooksPath "$$hooks_path"; fi; \
	exit $$status
	install -m 0755 tools/git_hooks/pre-push .git/hooks/pre-push

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

type:
	uv run mypy src

test:
	uv run pytest

validate:
	uv run python tools/validate_tasks.py

check: fmt-check lint type test validate
