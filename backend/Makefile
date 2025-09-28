SHELL := /bin/zsh

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install lint format type test ci

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -e '.[dev]'

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

format:
	$(VENV)/bin/ruff format .

type:
	$(VENV)/bin/mypy .

test:
	$(PY) -m pytest -q

ci: lint type test
	@echo 'All checks passed'
