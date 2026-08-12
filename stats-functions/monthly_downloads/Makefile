VENV := .venv
PIP := $(VENV)/bin/pip

.PHONY: venv lint test

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r src/requirements.txt

lint:
	$(VENV)/bin/ruff check src

test:
	$(VENV)/bin/pytest tests/ --cov=src/ --cov-report=html --cov-fail-under=80
