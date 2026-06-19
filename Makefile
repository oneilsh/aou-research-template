.PHONY: help install test lint precommit-install run-exp setup-workspace new-exp
default: help

help:
	@echo "Common targets:"
	@echo "  install           - editable install with dev tools"
	@echo "  test              - run the fast Python unit suite"
	@echo "  lint              - run pre-commit on all files"
	@echo "  precommit-install - install git hooks + nbstripout filter"

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	pre-commit run --all-files

precommit-install:
	pre-commit install
	nbstripout --install

# Run an experiment: `make run-exp` (next pending) or `make run-exp ID=2`.
run-exp:
	python scripts/run_experiment.py $(if $(ID),--id $(ID),--next)

# Discover Verily Workbench resources into .workspace_env (run inside AoU).
setup-workspace:
	python scripts/setup_workspace.py $(if $(CDR),--cdr $(CDR),)

.PHONY: new-exp

# Scaffold the next experiment record: make new-exp SLUG=my-run
new-exp:
	@test -n "$(SLUG)" || { echo "ERROR: set SLUG=<kebab-slug>"; exit 1; }
	python scripts/new_experiment.py $(SLUG)

.PHONY: setup-data

# Local only: fetch Eunomia into data/eunomia.duckdb (gitignored).
setup-data:
	Rscript scripts/setup_data.R
