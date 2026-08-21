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

# Run an experiment: `make run-exp` (next pending) or `make run-exp SLUG=my-run`.
run-exp:
	run-experiment $(if $(SLUG),--slug $(SLUG),--next)

# Discover Verily Workbench resources into .workspace_env (run inside AoU).
# Installs the R run-path packages first (binaries when available, only if missing).
setup-workspace:
	Rscript framework/scripts/ensure_r_packages.R
	setup-workspace $(if $(CDR),--cdr $(CDR),)

.PHONY: new-exp

# Scaffold the next experiment record: make new-exp SLUG=my-run
new-exp:
	@test -n "$(SLUG)" || { echo "ERROR: set SLUG=<kebab-slug>"; exit 1; }
	new-experiment $(SLUG)

.PHONY: setup-data

# Local only: fetch Eunomia into data/eunomia.duckdb (gitignored).
setup-data:
	Rscript framework/scripts/setup_data.R

# --- Optional meta-process logs (opt-in; see docs/META_process.md) -----------
# Each system is OFF until its artifact exists. `enable-*` scaffolds it (idempotent);
# delete the artifact to turn it back off.
.PHONY: enable-decisions enable-insights enable-reviews enable-meta-process new-decision new-insight

enable-decisions:
	@mkdir -p docs/decisions
	@test -f docs/decisions/README.md || cp framework/meta_process/decisions_README.md docs/decisions/README.md
	@echo "Enabled decisions log at docs/decisions/ (see docs/META_process.md)"

enable-insights:
	@mkdir -p docs/insights
	@test -f docs/insights/README.md || cp framework/meta_process/insights_README.md docs/insights/README.md
	@echo "Enabled insights log at docs/insights/ (see docs/META_process.md)"

enable-reviews:
	@test -f docs/REVIEW_LOG.md || cp framework/meta_process/REVIEW_LOG.md docs/REVIEW_LOG.md
	@echo "Enabled review log at docs/REVIEW_LOG.md (see docs/META_process.md)"

enable-meta-process: enable-decisions enable-insights enable-reviews

# Scaffold a dated log entry (needs the system enabled): make new-decision SLUG=my-choice
new-decision:
	@test -n "$(SLUG)" || { echo "ERROR: set SLUG=<kebab-slug>"; exit 1; }
	new-decision $(SLUG)

new-insight:
	@test -n "$(SLUG)" || { echo "ERROR: set SLUG=<kebab-slug>"; exit 1; }
	new-insight $(SLUG)
