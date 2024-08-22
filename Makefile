.PHONY: help bootstrap dev lint outdated clean

VENV=.venv
PYTHON=$(VENV)/bin/python

help:
	@echo "Available targets:"
	@echo "  bootstrap - prepare virtual environment and install dependencies"
	@echo "  dev       - run project in development mode"
	@echo "  lint      - run static code analysis"
	@echo "  outdated  - show outdated dependencies"
	@echo "  clean     - remove virtual environment and development artifacts"

bootstrap: $(PYTHON)
$(PYTHON):
	python -m venv $(VENV)
	$(VENV)/bin/python -m pip install pip==24.2 setuptools==73.0.1 wheel==0.44.0
	$(VENV)/bin/python -m pip install -e .[dev]

dev: bootstrap
	$(PYTHON) -m punquote

lint: bootstrap
	$(PYTHON) -m ruff check --fix punquote

outdated: bootstrap
	$(PYTHON) -m pip list --outdated

clean:
	rm -rf $(VENV) punquote.egg-info .ruff_cache
	find ./ -name "__pycache__" -type d | xargs rm -rf
