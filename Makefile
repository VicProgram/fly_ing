MYPY_FLAGS  = --warn-return-any \
              --warn-unused-ignores \
              --ignore-missing-imports \
              --disallow-untyped-defs \
              --check-untyped-defs

VENV        := venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
SCRIPT      = fly_ing.py

FLAKE8_EXCLUDE = --exclude=$(VENV)
MYPY_EXCLUDE   = --exclude $(VENV)

all: install

$(VENV)/bin/python:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

install: $(VENV)/bin/python
	@echo "Entorno $(VENV) listo. Dependencias instaladas."

# run: $(VENV)/bin/python
# 	$(PYTHON) $(SCRIPT) $(MAP)


debug: $(VENV)/bin/python
	$(PYTHON) -m pdb $(SCRIPT) $(MAP)


lint: $(VENV)/bin/python
	@echo "Comprobando linter..."
	@status=0; \
	echo ""; \
	echo "========== FLAKE8 =========="; \
	$(VENV)/bin/flake8 . $(FLAKE8_EXCLUDE) || status=1; \
	echo ""; \
	echo "=========== MYPY ===========" ; \
	$(VENV)/bin/mypy . $(MYPY_FLAGS) $(MYPY_EXCLUDE) || status=1; \
	echo ""; \
	exit $$status

lint-strict: $(VENV)/bin/python
	@echo "Comprobando linter (estricto)..."
	@status=0; \
	echo ""; \
	echo "========== FLAKE8 =========="; \
	$(VENV)/bin/flake8 . $(FLAKE8_EXCLUDE) || status=1; \
	echo ""; \
	echo "=========== MYPY ===========" ; \
	$(VENV)/bin/mypy . --strict $(MYPY_EXCLUDE) || status=1; \
	echo ""; \
	exit $$status


clean:
	@echo "Cleaning temporary files..."
	rm -rf $(VENV)
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "Done."


re: clean all

.PHONY: all install debug lint lint-strict clean re
