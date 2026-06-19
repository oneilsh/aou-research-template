# AoU Research Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `aou-research-template/`, a copy-and-customize template repo that lets an All of Us researcher collaborate with an LLM agent on safe, reproducible analysis under a human-enforced air-gap.

**Architecture:** A small pure-Python package (`utilities/`) does orchestration only — output scrubbing, layered config, a language-agnostic experiment runner, and Verily Workbench discovery. The actual analysis is R+SQL (Python works identically). Local execution uses a DuckDB-backed Eunomia fixture; AoU execution uses BigQuery over the real CDR; the same SQL runs both via a `pick_connection()` shim.

**Tech Stack:** Python 3.11+ (pyyaml, pytest, ruff, pre-commit, nbstripout), R (DBI, duckdb, bigrquery, Eunomia, digest), DuckDB, pre-commit hooks.

## Global Constraints

- **Build location:** everything lives under `aou-research-template/` inside the CHARMPheno repo; paths below are relative to that folder. Commits during the build are scoped to that subtree.
- **No Spark, topic modeling, phenotyping, eval/NPMI, dashboard, or checkpoint/resume machinery.** Verily Workbench only (the `wb` CLI); no Terra support.
- **Never commit data or secrets.** No real OMOP/vocabulary data is ever committed; the Eunomia DuckDB is gitignored. `.env.example` carries placeholders only.
- **Reusable Python package name is `utilities`.** Analysis code lives in `analysis/` and must never be imported by `utilities/` (one-way dependency).
- **What may cross the air-gap:** aggregates, estimates, and aggregate-only plots. No row-level output. Hashing an ID is only a fallback.
- **Prose voice for `README.md` and `GETTING_STARTED.md`:** plain, direct, terse, technical-colleague register. No marketing cadence ("comprehensive/seamless/robust/whether-you're-X-or-Y"), no emoji-bulleted feature grids, no symmetrical tricolons.
- **Agent chat renders as plain text** — no LaTeX in `CLAUDE.md` chat-facing guidance; plain Greek/ASCII only.

---

## File Structure

```
aou-research-template/
├── pyproject.toml                # Task 1
├── .python-version .gitignore .gitattributes .pre-commit-config.yaml .env.example   # Task 1
├── .claude/settings.json         # Task 1
├── scripts/check_no_data_files.sh# Task 1
├── Makefile                      # Task 1 (infra targets), extended Tasks 6,7,9
├── utilities/__init__.py         # Task 2
├── utilities/sanitize.py         # Task 2
├── utilities/config.py           # Task 3
├── utilities/runner.py           # Task 4
├── utilities/workspace.py        # Task 5
├── scripts/run_experiment.py     # Task 6
├── scripts/setup_workspace.py    # Task 6
├── scripts/new_experiment.py     # Task 7
├── docs/experiments/{README.md,_template.md}   # Task 7
├── experiments/defaults/{_base.yaml,demo.yaml} # Task 8
├── docs/experiments/0001-demo.md # Task 8
├── analysis/{utilities.R,demo_cohort.sql,demo_effect.R}  # Task 9
├── scripts/setup_data.R          # Task 9
├── CLAUDE.md                     # Task 10
├── README.md GETTING_STARTED.md  # Task 11
├── notebooks/demo_exploration.ipynb  # Task 12
└── tests/{test_sanitize.py,test_config.py,test_runner.py,data/}  # Tasks 2-4
```

---

## Task 1: Repo scaffolding & hygiene

**Files:**
- Create: `aou-research-template/pyproject.toml`, `.python-version`, `.gitignore`, `.gitattributes`, `.pre-commit-config.yaml`, `.env.example`, `.claude/settings.json`, `scripts/check_no_data_files.sh`, `Makefile`
- Test: `aou-research-template/tests/test_scaffolding.py`

**Interfaces:**
- Produces: a Python project rooted at `aou-research-template/` installable via `pip install -e ".[dev]"`; `scripts/check_no_data_files.sh` that exits non-zero for data files outside `tests/*/data/` or `docs/`.

- [ ] **Step 1: Create the project metadata and hygiene files**

`pyproject.toml`:
```toml
[project]
name = "aou-research-template"
version = "0.1.0"
description = "Safe, reproducible AoU research scaffold for human+agent collaboration"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "pre-commit>=3.7", "nbstripout>=0.7"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["utilities*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

(The `pythonpath = ["."]` line puts the repo root on `sys.path` during tests so
`from utilities...` and `from scripts...` imports resolve without relying on the
editable install picking up `scripts/`.)

`.python-version`:
```
3.11
```

`.gitignore`:
```
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
.ruff_cache/
.DS_Store
.ipynb_checkpoints/

# Secrets and per-workspace env
.env
.env.*
!.env.example
.workspace_env

# Run artifacts and local synthetic data (never committed)
runs/
data/

# Allow tiny synthetic test fixtures only
!**/tests/data/
```

`.gitattributes`:
```
*.ipynb filter=nbstripout
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks:
      - id: nbstripout
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ['--maxkb=1024']
  - repo: local
    hooks:
      - id: no-data-files-outside-tests
        name: Prevent data files outside tests/*/data/ or docs/
        entry: scripts/check_no_data_files.sh
        language: script
        files: '\.(parquet|csv|feather|arrow|npz|duckdb)$'
```

`.env.example`:
```
# Copy to .env and fill in. .env is gitignored. Never commit real values.
# Example: an API key for an optional LLM-labeling step.
# EXAMPLE_API_KEY=replace-me
```

`.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(git add *)",
      "Bash(pytest *)",
      "Bash(make test*)",
      "Bash(make lint*)"
    ]
  }
}
```

- [ ] **Step 2: Create `scripts/check_no_data_files.sh`**

```bash
#!/usr/bin/env bash
# Reject staged data files outside tests/*/data/ and docs/.
# Pre-commit passes candidate file paths as arguments.
set -euo pipefail
status=0
for f in "$@"; do
  case "$f" in
    tests/*/data/*|*/tests/data/*|*/tests/*/data/*|docs/*)
      ;;
    *)
      echo "ERROR: data file outside allowed paths: $f"
      status=1
      ;;
  esac
done
exit $status
```

Make it executable: `chmod +x aou-research-template/scripts/check_no_data_files.sh`

- [ ] **Step 3: Create the `Makefile` with infra targets**

```makefile
.PHONY: help install test lint precommit-install
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
```

- [ ] **Step 4: Write the failing test**

`tests/test_scaffolding.py`:
```python
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_no_data_files.sh"


def test_rejects_data_file_outside_tests():
    r = subprocess.run([str(SCRIPT), "analysis/leak.csv"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "outside allowed paths" in r.stdout


def test_allows_data_file_in_tests_data():
    r = subprocess.run([str(SCRIPT), "tests/data/fixture.csv"], capture_output=True, text=True)
    assert r.returncode == 0
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd aou-research-template && pip install -e ".[dev]" && pytest tests/test_scaffolding.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add aou-research-template
git commit -m "feat(template): scaffold repo hygiene, build config, data-file guard"
```

---

## Task 2: `utilities/sanitize.py` — output scrubber

**Files:**
- Create: `aou-research-template/utilities/__init__.py`, `aou-research-template/utilities/sanitize.py`
- Test: `aou-research-template/tests/test_sanitize.py`

**Interfaces:**
- Produces:
  - `PATIENT_PATTERNS`, `NOISE_PATTERNS`, `DROP_PATTERNS: list[re.Pattern]`
  - `sanitize_line(line: str, patterns: list[re.Pattern]) -> str | None`
  - `run_subprocess_tee_sanitize(cmd: list[str], summary_path: Path, patterns: list[re.Pattern] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

`tests/test_sanitize.py`:
```python
import re
import sys
from pathlib import Path

from utilities.sanitize import (
    DROP_PATTERNS,
    sanitize_line,
    run_subprocess_tee_sanitize,
)


def test_drops_row_level_lines():
    assert sanitize_line("person_id = 12345", DROP_PATTERNS) is None
    assert sanitize_line("person_hash deadbeef", DROP_PATTERNS) is None
    assert sanitize_line("token hash:deadbeef12", DROP_PATTERNS) is None


def test_drops_log_noise():
    assert sanitize_line("24/01/02 10:11:12 INFO Foo: hi", DROP_PATTERNS) is None


def test_passes_aggregates():
    line = "[demo] mean(n_conditions) by group: 3.1 / 4.2"
    assert sanitize_line(line, DROP_PATTERNS) == line


def test_tee_sanitize_writes_only_clean_lines(tmp_path):
    out = tmp_path / "summary.md"
    code = (
        "print('person_id = 999'); "
        "print('[demo] mean = 4.2')"
    )
    rc = run_subprocess_tee_sanitize([sys.executable, "-c", code], out)
    assert rc == 0
    text = out.read_text()
    assert "mean = 4.2" in text
    assert "person_id" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_sanitize.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'utilities'`.

- [ ] **Step 3: Write the implementation**

`utilities/__init__.py`:
```python
"""Reusable infrastructure for safe, reproducible AoU research."""
```

`utilities/sanitize.py`:
```python
"""Scrub subprocess output so committed run records carry no patient-level rows.

The air-gap workflow has a human copy results out of the secure environment by
hand. This module makes that safe by construction: when an analysis runs through
the runner, its stdout is streamed live to the terminal but only a *sanitized*
copy is written to the committed summary.md. Any line that looks like row-level
patient output is dropped; aggregates, estimates, and summary statistics pass
through.

Extend PATIENT_PATTERNS for the output shapes your analysis produces.
"""
from __future__ import annotations

import re
import signal
import subprocess
import sys
from pathlib import Path

# Lines that look like per-subject / row-level output. Dropped from the record.
PATIENT_PATTERNS: list[re.Pattern] = [
    re.compile(r"person_id\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"\bperson_hash\b", re.IGNORECASE),
    re.compile(r"\bhash:[0-9a-f]{6,}", re.IGNORECASE),
    re.compile(r"\brow\s+\d+\s*[:|]", re.IGNORECASE),
]

# Environment log noise with no value in the committed record. Still teed live.
NOISE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} (INFO|WARN|DEBUG) "),
    re.compile(r"\[CONTEXT ratelimit_period="),
]

DROP_PATTERNS: list[re.Pattern] = PATIENT_PATTERNS + NOISE_PATTERNS


def sanitize_line(line: str, patterns: list[re.Pattern]) -> str | None:
    """Return the line unchanged if safe to commit, or None to drop it."""
    for pat in patterns:
        if pat.search(line):
            return None
    return line


class _SignalReceived(Exception):
    def __init__(self, signum: int):
        super().__init__(f"signal {signum}")
        self.signum = signum


def run_subprocess_tee_sanitize(
    cmd: list[str], summary_path: Path, patterns: list[re.Pattern] | None = None,
) -> int:
    """Run `cmd`; stream stdout live; append only sanitized lines to summary_path.

    Every line is echoed to this process's stdout (live debugging). Lines that
    survive `sanitize_line` are also appended to `summary_path`. On SIGTERM/SIGINT
    a `### Killed (signal: N)` marker is written and 130 is returned; otherwise
    the child's exit code is returned.
    """
    if patterns is None:
        patterns = DROP_PATTERNS

    def _handler(signum, frame):  # noqa: ARG001 — frame unused
        raise _SignalReceived(signum)

    prev_term = signal.signal(signal.SIGTERM, _handler)
    prev_int = signal.signal(signal.SIGINT, _handler)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True,
    )
    assert proc.stdout is not None
    try:
        with summary_path.open("a") as fout:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                clean = sanitize_line(line, patterns)
                if clean is not None:
                    fout.write(clean)
                    fout.flush()
        return proc.wait()
    except _SignalReceived as sig:
        with summary_path.open("a") as fout:
            fout.write(f"\n### Killed (signal: {sig.signum})\n")
            fout.flush()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return 130
    finally:
        signal.signal(signal.SIGTERM, prev_term)
        signal.signal(signal.SIGINT, prev_int)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_sanitize.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/utilities aou-research-template/tests/test_sanitize.py
git commit -m "feat(template): output scrubber (sanitize_line + tee-sanitize runner)"
```

---

## Task 3: `utilities/config.py` — layered configuration

**Files:**
- Create: `aou-research-template/utilities/config.py`
- Test: `aou-research-template/tests/test_config.py`

**Interfaces:**
- Produces:
  - `read_frontmatter(path: Path) -> dict`
  - `merge_config(base: dict, override: dict) -> dict`
  - `load_defaults(group: str, defaults_dir: Path) -> dict`
  - `effective_config(record_path: Path, defaults_dir: Path) -> dict` (requires a `group` key in the record frontmatter)

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
from pathlib import Path

import pytest

from utilities.config import (
    read_frontmatter,
    merge_config,
    load_defaults,
    effective_config,
)


def _write(p: Path, text: str) -> Path:
    p.write_text(text)
    return p


def test_read_frontmatter_ok(tmp_path):
    rec = _write(tmp_path / "r.md", "---\nid: 1\ngroup: demo\n---\n\nbody\n")
    assert read_frontmatter(rec) == {"id": 1, "group": "demo"}


def test_read_frontmatter_missing_raises(tmp_path):
    rec = _write(tmp_path / "r.md", "no frontmatter here\n")
    with pytest.raises(ValueError):
        read_frontmatter(rec)


def test_merge_precedence():
    assert merge_config({"a": 1, "b": 2}, {"b": 9}) == {"a": 1, "b": 9}


def test_load_defaults_layers(tmp_path):
    _write(tmp_path / "_base.yaml", "seed: 42\nk: 1\n")
    _write(tmp_path / "demo.yaml", "k: 7\n")
    assert load_defaults("demo", tmp_path) == {"seed": 42, "k": 7}


def test_effective_config_full_stack(tmp_path):
    _write(tmp_path / "_base.yaml", "seed: 42\nentrypoint: base\n")
    _write(tmp_path / "demo.yaml", "entrypoint: Rscript x.R\n")
    rec = _write(tmp_path / "0001-demo.md", "---\nid: 1\ngroup: demo\nseed: 7\n---\n\nbody\n")
    cfg = effective_config(rec, tmp_path)
    assert cfg["entrypoint"] == "Rscript x.R"
    assert cfg["seed"] == 7  # record frontmatter wins
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'utilities.config'`.

- [ ] **Step 3: Write the implementation**

`utilities/config.py`:
```python
"""Layered experiment configuration.

Resolution order (lowest to highest precedence):
    experiments/defaults/_base.yaml
    experiments/defaults/<group>.yaml
    the experiment record's YAML frontmatter

The record's frontmatter names its defaults file via a required `group` key.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def read_frontmatter(path: Path) -> dict:
    """Parse the YAML frontmatter block (delimited by leading/trailing '---')."""
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter block (expected leading '---')")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter block (no trailing '---')")
    return yaml.safe_load(text[4:end]) or {}


def merge_config(base: dict, override: dict) -> dict:
    """Shallow merge; override wins."""
    out = dict(base)
    out.update(override)
    return out


def load_defaults(group: str, defaults_dir: Path) -> dict:
    """Load `_base.yaml` then `<group>.yaml` and merge."""
    base_path = defaults_dir / "_base.yaml"
    group_path = defaults_dir / f"{group}.yaml"
    if not base_path.exists():
        raise FileNotFoundError(f"missing defaults file: {base_path}")
    if not group_path.exists():
        raise FileNotFoundError(f"missing defaults file: {group_path}")
    base = yaml.safe_load(base_path.read_text()) or {}
    group_overrides = yaml.safe_load(group_path.read_text()) or {}
    return merge_config(base, group_overrides)


def effective_config(record_path: Path, defaults_dir: Path) -> dict:
    """Merge _base -> <group>.yaml -> record frontmatter into one config dict."""
    fm = read_frontmatter(record_path)
    group = fm.get("group")
    if not group:
        raise ValueError(f"{record_path}: frontmatter missing required 'group' key")
    return merge_config(load_defaults(group, defaults_dir), fm)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_config.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/utilities/config.py aou-research-template/tests/test_config.py
git commit -m "feat(template): layered experiment config (_base -> group -> frontmatter)"
```

---

## Task 4: `utilities/runner.py` — generic experiment runner

**Files:**
- Create: `aou-research-template/utilities/runner.py`
- Test: `aou-research-template/tests/test_runner.py`

**Interfaces:**
- Consumes: `effective_config` (Task 3), `run_subprocess_tee_sanitize`, `DROP_PATTERNS` (Task 2)
- Produces:
  - `find_by_id(experiments_dir: Path, exp_id: int) -> Path`
  - `find_next_pending(experiments_dir: Path) -> Path | None`
  - `run_experiment(record_path: Path, defaults_dir: Path, runs_dir: Path) -> int`
  - Each run writes `runs_dir/<slug>/config.yaml` and appends scrubbed output to `runs_dir/<slug>/summary.md`. The effective config gets an injected `out_dir` (= the run dir) before dispatch. The entrypoint is invoked as `<entrypoint tokens> --config <config.yaml>`.

- [ ] **Step 1: Write the failing test**

`tests/test_runner.py`:
```python
from pathlib import Path

from utilities.runner import find_by_id, find_next_pending, run_experiment


def _setup(tmp_path):
    exp = tmp_path / "experiments"
    exp.mkdir()
    defaults = tmp_path / "defaults"
    defaults.mkdir()
    (defaults / "_base.yaml").write_text("seed: 1\n")
    (defaults / "demo.yaml").write_text("entrypoint: STUB\n")
    return exp, defaults


def test_find_by_id_and_next(tmp_path):
    exp, _ = _setup(tmp_path)
    (exp / "0001-a.md").write_text("---\nid: 1\ngroup: demo\nstatus: done\n---\n")
    (exp / "0002-b.md").write_text("---\nid: 2\ngroup: demo\nstatus: pending\n---\n")
    assert find_by_id(exp, 1).name == "0001-a.md"
    assert find_next_pending(exp).name == "0002-b.md"


def test_run_experiment_scrubs_and_records(tmp_path):
    exp, defaults = _setup(tmp_path)
    # A stub entrypoint that prints one row-level line and one aggregate line,
    # and proves it received --config.
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import sys\n"
        "assert '--config' in sys.argv\n"
        "print('person_id = 7')\n"
        "print('[demo] mean = 3.14')\n"
    )
    import sys as _sys
    (defaults / "demo.yaml").write_text(f"entrypoint: {_sys.executable} {stub}\n")
    rec = exp / "0001-demo.md"
    rec.write_text("---\nid: 1\ngroup: demo\nstatus: pending\n---\n")
    runs = tmp_path / "runs"
    rc = run_experiment(rec, defaults, runs)
    assert rc == 0
    summary = (runs / "0001-demo" / "summary.md").read_text()
    assert "mean = 3.14" in summary
    assert "person_id" not in summary
    assert "Session complete (exit 0)" in summary
    assert (runs / "0001-demo" / "config.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'utilities.runner'`.

- [ ] **Step 3: Write the implementation**

`utilities/runner.py`:
```python
"""Run an experiment record: merge config, dispatch its declared entrypoint,
and capture *scrubbed* output into an accumulating per-run summary.md.

The entrypoint can be any command in any language. The effective config is
written to <run_dir>/config.yaml and passed to the entrypoint as
`--config <path>`; the runner injects `out_dir` (the run dir) into the config so
the entrypoint knows where to write artifacts.
"""
from __future__ import annotations

import datetime as _dt
import re
import shlex
from pathlib import Path

import yaml

from .config import effective_config
from .sanitize import DROP_PATTERNS, run_subprocess_tee_sanitize

_RECORD_RE = re.compile(r"^(\d{4})-.+\.md$")


def _records(experiments_dir: Path) -> list[Path]:
    out = [p for p in experiments_dir.iterdir() if _RECORD_RE.match(p.name)]
    out.sort(key=lambda p: p.name)
    return out


def find_by_id(experiments_dir: Path, exp_id: int) -> Path:
    """Return the record whose filename starts with the zero-padded id."""
    prefix = f"{exp_id:04d}-"
    for p in _records(experiments_dir):
        if p.name.startswith(prefix):
            return p
    raise FileNotFoundError(f"no experiment record with id {exp_id} in {experiments_dir}")


def find_next_pending(experiments_dir: Path) -> Path | None:
    """Return the lowest-id record with `status: pending`, or None."""
    from .config import read_frontmatter
    for p in _records(experiments_dir):
        try:
            fm = read_frontmatter(p)
        except ValueError:
            continue
        if fm.get("status") == "pending":
            return p
    return None


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_experiment(record_path: Path, defaults_dir: Path, runs_dir: Path) -> int:
    """Dispatch one experiment; return the entrypoint's exit code."""
    cfg = effective_config(record_path, defaults_dir)
    entrypoint = cfg.get("entrypoint")
    if not entrypoint:
        raise ValueError(f"{record_path}: effective config missing 'entrypoint'")

    slug = record_path.stem
    run_dir = runs_dir / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg["out_dir"] = str(run_dir)

    config_path = run_dir / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=True))

    summary_path = run_dir / "summary.md"
    with summary_path.open("a") as f:
        f.write(f"\n## Run session — {_utc_now()}\n")
        f.write(f"entrypoint: {entrypoint}\n\n")

    cmd = shlex.split(entrypoint) + ["--config", str(config_path)]
    rc = run_subprocess_tee_sanitize(cmd, summary_path, DROP_PATTERNS)

    with summary_path.open("a") as f:
        f.write(f"\n### Session complete (exit {rc})\n")
    return rc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_runner.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/utilities/runner.py aou-research-template/tests/test_runner.py
git commit -m "feat(template): generic experiment runner with scrubbed capture"
```

---

## Task 5: `utilities/workspace.py` — Verily Workbench discovery

**Files:**
- Create: `aou-research-template/utilities/workspace.py`
- Test: `aou-research-template/tests/test_workspace.py`

**Interfaces:**
- Produces:
  - `discover(wb=...) -> dict[str, str]` — `wb` is an injectable callable `(*"args") -> parsed-json` (defaults to the real `wb` CLI) so the discovery logic is testable without the CLI.
  - `render_env(values: dict[str, str]) -> str` — the sourceable `.workspace_env` text.

- [ ] **Step 1: Write the failing test**

`tests/test_workspace.py`:
```python
from utilities.workspace import discover, render_env


def fake_wb(*args):
    if args[:2] == ("workspace", "describe"):
        return {"googleProjectId": "proj-123"}
    if args[:2] == ("resource", "list"):
        return [
            {"resourceType": "GCS_BUCKET", "id": "workspace-bucket", "bucketName": "wb-main"},
            {"resourceType": "GCS_BUCKET", "id": "temporary-workspace-bucket", "bucketName": "wb-tmp"},
            {"resourceType": "BQ_DATASET", "projectId": "cdr-proj", "datasetId": "R2024"},
        ]
    raise AssertionError(args)


def test_discover_maps_resources():
    out = discover(wb=fake_wb)
    assert out["GOOGLE_CLOUD_PROJECT"] == "proj-123"
    assert out["WORKSPACE_CDR"] == "cdr-proj.R2024"
    assert out["WORKSPACE_BUCKET"] == "gs://wb-main"
    assert out["WORKSPACE_TEMP_BUCKET"] == "gs://wb-tmp"


def test_render_env_is_sourceable():
    text = render_env({"GOOGLE_CLOUD_PROJECT": "p", "WORKSPACE_CDR": "a.b"})
    assert "export GOOGLE_CLOUD_PROJECT='p'" in text
    assert "export WORKSPACE_CDR='a.b'" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_workspace.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'utilities.workspace'`.

- [ ] **Step 3: Write the implementation**

`utilities/workspace.py`:
```python
"""Discover Verily Workbench resources and write a sourceable .workspace_env.

VERIFY/ADAPT IN YOUR WORKSPACE: the `wb resource list` shapes (bucket ids, how
the CDR is surfaced) vary between workspaces. This covers the common case; if
your CDR is an external read-only project not in `wb resource list`, pass it
explicitly with --cdr. Validate the discovered values before relying on them.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_VAR_ORDER = (
    "GOOGLE_CLOUD_PROJECT",
    "WORKSPACE_CDR",
    "WORKSPACE_BUCKET",
    "WORKSPACE_TEMP_BUCKET",
)


def _wb(*args: str):
    """Run `wb <args> --format=json` and parse stdout as JSON."""
    cmd = ["wb", *args, "--format=json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("ERROR: 'wb' CLI not found. Are you on a Verily Workbench cluster?",
              file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: `{' '.join(cmd)}` failed (exit {exc.returncode})", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        sys.exit(2)
    return json.loads(proc.stdout)


def discover(wb=_wb) -> dict[str, str]:
    """Pull workspace-shape values from the wb CLI (injectable for testing)."""
    out: dict[str, str] = {}
    workspace = wb("workspace", "describe")
    out["GOOGLE_CLOUD_PROJECT"] = workspace["googleProjectId"]
    for r in wb("resource", "list"):
        rt = r.get("resourceType", "")
        if rt == "GCS_BUCKET":
            rid, bucket = r.get("id", ""), r.get("bucketName")
            if not bucket:
                continue
            # Order matters: the temp bucket id also contains "workspace-bucket".
            if "temporary-workspace-bucket" in rid:
                out["WORKSPACE_TEMP_BUCKET"] = f"gs://{bucket}"
            elif "workspace-bucket" in rid:
                out["WORKSPACE_BUCKET"] = f"gs://{bucket}"
        elif rt in ("BQ_DATASET", "BIGQUERY_DATASET"):
            if "WORKSPACE_CDR" not in out:
                out["WORKSPACE_CDR"] = f"{r['projectId']}.{r['datasetId']}"
    return out


def render_env(values: dict[str, str]) -> str:
    """Render discovered values as sourceable `export` lines."""
    lines = [
        "# Generated by setup_workspace.py — do not edit by hand.\n",
        "# Regenerate via: make setup-workspace  (optionally CDR=<project>.<dataset>)\n",
    ]
    for k in _VAR_ORDER:
        if values.get(k):
            lines.append(f"export {k}='{values[k]}'\n")
    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cdr", default=None,
                        help="override WORKSPACE_CDR as <project>.<dataset>")
    parser.add_argument("--out", default=".workspace_env", help="output file path")
    args = parser.parse_args(argv)

    values = discover()
    if args.cdr:
        values["WORKSPACE_CDR"] = args.cdr
    if not values.get("WORKSPACE_CDR"):
        print("ERROR: WORKSPACE_CDR not found. Pass it: make setup-workspace "
              "CDR='<project>.<dataset>'", file=sys.stderr)
        return 1

    Path(args.out).write_text(render_env(values))
    summary = ", ".join(f"{k}={values[k]}" for k in _VAR_ORDER if values.get(k))
    print(f"Wrote {args.out}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_workspace.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/utilities/workspace.py aou-research-template/tests/test_workspace.py
git commit -m "feat(template): Verily Workbench discovery -> .workspace_env"
```

---

## Task 6: Thin CLIs for run + workspace, and Makefile wiring

**Files:**
- Create: `aou-research-template/scripts/run_experiment.py`, `aou-research-template/scripts/setup_workspace.py`
- Modify: `aou-research-template/Makefile`
- Test: `aou-research-template/tests/test_cli_run.py`

**Interfaces:**
- Consumes: `utilities.runner` (Task 4), `utilities.workspace.main` (Task 5)
- Produces: `python scripts/run_experiment.py [--id N | --next]` runs an experiment; `python scripts/setup_workspace.py` delegates to `utilities.workspace.main`.

- [ ] **Step 1: Write the failing test**

`tests/test_cli_run.py`:
```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_run_cli_dispatches_next(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    defaults = tmp_path / "defaults"; defaults.mkdir()
    (defaults / "_base.yaml").write_text("seed: 1\n")
    stub = tmp_path / "stub.py"
    stub.write_text("print('[demo] ok')\n")
    (defaults / "demo.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    (exp / "0001-demo.md").write_text("---\nid: 1\ngroup: demo\nstatus: pending\n---\n")
    runs = tmp_path / "runs"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_experiment.py"),
         "--next", "--experiments-dir", str(exp),
         "--defaults-dir", str(defaults), "--runs-dir", str(runs)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
    assert (runs / "0001-demo" / "summary.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_cli_run.py -v`
Expected: FAIL (script not found / non-zero exit).

- [ ] **Step 3: Write the CLIs**

`scripts/run_experiment.py`:
```python
#!/usr/bin/env python
"""Thin CLI over utilities.runner: pick an experiment and run it."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utilities.runner import find_by_id, find_next_pending, run_experiment

REPO = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sel = p.add_mutually_exclusive_group(required=True)
    sel.add_argument("--next", action="store_true", help="run lowest-id pending experiment")
    sel.add_argument("--id", type=int, help="run experiment with this id")
    p.add_argument("--experiments-dir", default=str(REPO / "docs" / "experiments"))
    p.add_argument("--defaults-dir", default=str(REPO / "experiments" / "defaults"))
    p.add_argument("--runs-dir", default=str(REPO / "runs"))
    args = p.parse_args(argv)

    exp_dir = Path(args.experiments_dir)
    if args.next:
        rec = find_next_pending(exp_dir)
        if rec is None:
            print("No pending experiments.", file=sys.stderr)
            return 1
    else:
        rec = find_by_id(exp_dir, args.id)

    print(f"[run] {rec.name}")
    return run_experiment(rec, Path(args.defaults_dir), Path(args.runs_dir))


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/setup_workspace.py`:
```python
#!/usr/bin/env python
"""Thin CLI over utilities.workspace."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utilities.workspace import main

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Extend the Makefile**

Append to `Makefile`:
```makefile
.PHONY: run-exp setup-workspace

# Run an experiment: `make run-exp` (next pending) or `make run-exp ID=2`.
run-exp:
	python scripts/run_experiment.py $(if $(ID),--id $(ID),--next)

# Discover Verily Workbench resources into .workspace_env (run inside AoU).
setup-workspace:
	python scripts/setup_workspace.py $(if $(CDR),--cdr $(CDR),)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_cli_run.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add aou-research-template/scripts/run_experiment.py aou-research-template/scripts/setup_workspace.py aou-research-template/Makefile aou-research-template/tests/test_cli_run.py
git commit -m "feat(template): run-exp / setup-workspace CLIs + Makefile targets"
```

---

## Task 7: New-experiment scaffolder + record format docs

**Files:**
- Create: `aou-research-template/scripts/new_experiment.py`, `aou-research-template/docs/experiments/_template.md`, `aou-research-template/docs/experiments/README.md`
- Modify: `aou-research-template/Makefile`
- Test: `aou-research-template/tests/test_new_experiment.py`

**Interfaces:**
- Consumes: nothing from prior tasks (standalone).
- Produces: `scaffold(slug: str, experiments_dir: Path, template_path: Path, today: str) -> Path` — writes `docs/experiments/NNNN-<slug>.md` with the next zero-padded id, filling `{id}`, `{id_padded}`, `{slug}`, `{date}` in the template.

- [ ] **Step 1: Write the failing test**

`tests/test_new_experiment.py`:
```python
from pathlib import Path

from scripts.new_experiment import scaffold, next_id


def _tmpl(tmp_path):
    t = tmp_path / "_template.md"
    t.write_text("---\nid: {id}\nslug: {slug}\ngroup: demo\nstatus: pending\n"
                 "created: {date}\n---\n\n# Experiment {id_padded} — {slug}\n")
    return t


def test_next_id_increments(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-a.md").write_text("x")
    (exp / "0002-b.md").write_text("x")
    assert next_id(exp) == 3


def test_next_id_empty_is_one(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    assert next_id(exp) == 1


def test_scaffold_writes_record(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-demo.md").write_text("x")
    out = scaffold("my-run", exp, _tmpl(tmp_path), today="2026-06-19")
    assert out.name == "0002-my-run.md"
    text = out.read_text()
    assert "id: 2" in text and "slug: my-run" in text
    assert "created: 2026-06-19" in text
    assert "Experiment 0002 — my-run" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_new_experiment.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.new_experiment'`.

Note: add an empty `aou-research-template/scripts/__init__.py` so `scripts` is importable in tests.

- [ ] **Step 3: Write the scaffolder, template, and README**

`scripts/__init__.py`: (empty file)

`scripts/new_experiment.py`:
```python
#!/usr/bin/env python
"""Scaffold the next experiment record from docs/experiments/_template.md."""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

_RECORD_RE = re.compile(r"^(\d{4})-.+\.md$")
REPO = Path(__file__).resolve().parent.parent


def next_id(experiments_dir: Path) -> int:
    ids = [int(m.group(1)) for p in experiments_dir.iterdir()
           if (m := _RECORD_RE.match(p.name))]
    return (max(ids) + 1) if ids else 1


def scaffold(slug: str, experiments_dir: Path, template_path: Path, today: str) -> Path:
    nid = next_id(experiments_dir)
    body = template_path.read_text().format(
        id=nid, id_padded=f"{nid:04d}", slug=slug, date=today,
    )
    out = experiments_dir / f"{nid:04d}-{slug}.md"
    out.write_text(body)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug", help="short kebab-case slug, e.g. 'sex-condition-count'")
    p.add_argument("--experiments-dir", default=str(REPO / "docs" / "experiments"))
    p.add_argument("--template", default=str(REPO / "docs" / "experiments" / "_template.md"))
    args = p.parse_args(argv)
    today = _dt.date.today().isoformat()
    out = scaffold(args.slug, Path(args.experiments_dir), Path(args.template), today)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`docs/experiments/_template.md`:
```markdown
---
id: {id}
slug: {slug}
group: demo
status: pending
created: {date}
---

# Experiment {id_padded} — {slug}

## Intent
<one short paragraph: the question this run answers>

## Results
<after running, paste the scrubbed contents of runs/{id_padded}-{slug}/summary.md here>

## Interpretation
<what you concluded; safe aggregate numbers only>
```

`docs/experiments/README.md`:
```markdown
# Experiment records

Each run is described by one markdown file `NNNN-<slug>.md` whose YAML
frontmatter is the highest-precedence config layer (over
`experiments/defaults/<group>.yaml` over `experiments/defaults/_base.yaml`).

Lifecycle:
1. `make new-exp SLUG=<slug>` scaffolds the next record (`status: pending`).
2. Edit the frontmatter (set `group`, override any defaults) and the Intent.
3. `make run-exp` (or `make run-exp ID=N`) dispatches the entrypoint and writes
   a scrubbed `runs/NNNN-<slug>/summary.md`.
4. Review that summary, paste the relevant part into the record's Results
   section, set `status: done`, and commit.

Required frontmatter keys: `id`, `slug`, `group`, `status`. The `group` selects
the defaults file. `entrypoint` (from defaults or frontmatter) is the command to
run; the runner appends `--config <run_dir>/config.yaml`.
```

- [ ] **Step 4: Add the `new-exp` Makefile target**

Append to `Makefile`:
```makefile
.PHONY: new-exp

# Scaffold the next experiment record: make new-exp SLUG=my-run
new-exp:
	@test -n "$(SLUG)" || { echo "ERROR: set SLUG=<kebab-slug>"; exit 1; }
	python scripts/new_experiment.py $(SLUG)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_new_experiment.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add aou-research-template/scripts aou-research-template/docs/experiments aou-research-template/Makefile aou-research-template/tests/test_new_experiment.py
git commit -m "feat(template): experiment scaffolder + record format docs"
```

---

## Task 8: Demo experiment config + record

**Files:**
- Create: `aou-research-template/experiments/defaults/_base.yaml`, `aou-research-template/experiments/defaults/demo.yaml`, `aou-research-template/docs/experiments/0001-demo.md`
- Test: `aou-research-template/tests/test_demo_config.py`

**Interfaces:**
- Consumes: `utilities.config.effective_config` (Task 3)
- Produces: a `demo` group whose effective config for `0001-demo.md` carries `entrypoint: Rscript analysis/demo_effect.R` and `sql_file: analysis/demo_cohort.sql`.

- [ ] **Step 1: Write the failing test**

`tests/test_demo_config.py`:
```python
from pathlib import Path

from utilities.config import effective_config

ROOT = Path(__file__).resolve().parent.parent


def test_demo_effective_config():
    cfg = effective_config(
        ROOT / "docs" / "experiments" / "0001-demo.md",
        ROOT / "experiments" / "defaults",
    )
    assert cfg["entrypoint"] == "Rscript analysis/demo_effect.R"
    assert cfg["sql_file"] == "analysis/demo_cohort.sql"
    assert cfg["group"] == "demo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aou-research-template && pytest tests/test_demo_config.py -v`
Expected: FAIL (`FileNotFoundError` on the defaults / record).

- [ ] **Step 3: Write the config and record**

`experiments/defaults/_base.yaml`:
```yaml
# Cross-experiment defaults.
# Layered: _base.yaml -> <group>.yaml -> record frontmatter.
# The runner also injects `out_dir` (the per-run directory) at dispatch time.
seed: 42
```

`experiments/defaults/demo.yaml`:
```yaml
# Defaults for the 'demo' experiment group.
entrypoint: Rscript analysis/demo_effect.R
sql_file: analysis/demo_cohort.sql
```

`docs/experiments/0001-demo.md`:
```markdown
---
id: 1
slug: demo
group: demo
status: pending
created: 2026-06-19
---

# Experiment 0001 — demo

## Intent
End-to-end demonstration of the safe-run loop. Asks a deliberately simple
question against OMOP tables: does the mean number of recorded condition
occurrences per person differ between two groups (here, by recorded sex)?
Runs locally against the Eunomia synthetic dataset and, unchanged, in AoU
against the CDR. Produces a Welch t-test and one aggregate-only plot — both safe
to carry back across the air-gap.

## Results
<after `make run-exp`, paste the scrubbed runs/0001-demo/summary.md here>

## Interpretation
<aggregate t-test result and what it shows about the loop, not the biology>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aou-research-template && pytest tests/test_demo_config.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/experiments aou-research-template/docs/experiments/0001-demo.md aou-research-template/tests/test_demo_config.py
git commit -m "feat(template): demo experiment defaults + 0001-demo record"
```

---

## Task 9: R analysis (the worked example) + Eunomia data setup

**Files:**
- Create: `aou-research-template/analysis/utilities.R`, `aou-research-template/analysis/demo_cohort.sql`, `aou-research-template/analysis/demo_effect.R`, `aou-research-template/scripts/setup_data.R`
- Modify: `aou-research-template/Makefile`

**Interfaces:**
- Consumes: a `--config <path>` YAML file from the runner (Task 4) carrying `sql_file` and `out_dir`.
- Produces: `data/eunomia.duckdb` (via `make setup-data`); `demo_effect.R` prints aggregate-only stats and writes `<out_dir>/demo_effect.png`.

**Note on testing:** R is verified by a *manual smoke run* (no pytest). The steps below build the fixture and run the demo locally end-to-end. The exact Eunomia API call may need adjusting to the installed `Eunomia` version — Step 4 verifies the resulting DuckDB has OMOP tables.

- [ ] **Step 1: Write `analysis/utilities.R`**

```r
# Shared helpers for analysis entrypoints. Sourced with CWD at the repo root.
suppressPackageStartupMessages(library(DBI))

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

# Choose the data backend from the environment:
#   - in AoU (WORKSPACE_CDR set): BigQuery over the real CDR
#   - locally: DuckDB over the Eunomia synthetic dataset
# Both return a DBI connection, so the same SQL runs against either.
pick_connection <- function() {
  cdr <- Sys.getenv("WORKSPACE_CDR", "")
  if (nzchar(cdr)) {
    suppressPackageStartupMessages(library(bigrquery))
    parts <- strsplit(cdr, "\\.")[[1]]
    DBI::dbConnect(
      bigrquery::bigquery(),
      project = parts[1], dataset = parts[2],
      billing = Sys.getenv("GOOGLE_CLOUD_PROJECT")
    )
  } else {
    suppressPackageStartupMessages(library(duckdb))
    DBI::dbConnect(duckdb::duckdb(), dbdir = "data/eunomia.duckdb", read_only = TRUE)
  }
}

# SHA-256 truncated — fallback only, for the rare case an id must be named in
# output. Row-level output should not cross the air-gap at all.
hash_id <- function(x) {
  suppressPackageStartupMessages(library(digest))
  substr(digest::digest(as.character(x), algo = "sha256"), 1, 12)
}
```

- [ ] **Step 2: Write `analysis/demo_cohort.sql`**

```sql
-- Per-person condition counts, grouped by recorded sex.
-- Standard OMOP gender concepts: 8507 = MALE, 8532 = FEMALE.
-- Unqualified table names resolve on local DuckDB (Eunomia) and, with a default
-- dataset set on the BigQuery connection, on the AoU CDR. (See GETTING_STARTED
-- for the AoU dialect note.)
SELECT person_id, grp, n_conditions
FROM (
  SELECT
    p.person_id,
    CASE WHEN p.gender_concept_id = 8507 THEN 'male' ELSE 'female' END AS grp,
    COUNT(co.condition_occurrence_id) AS n_conditions
  FROM person p
  LEFT JOIN condition_occurrence co ON co.person_id = p.person_id
  GROUP BY p.person_id, p.gender_concept_id
) t;
```

- [ ] **Step 3: Write `analysis/demo_effect.R`**

```r
#!/usr/bin/env Rscript
# Demo entrypoint. Invoked by the runner as:
#   Rscript analysis/demo_effect.R --config runs/0001-demo/config.yaml
# Row-level query results stay in this process; only aggregates are printed,
# so the scrubbed summary.md carries nothing patient-level.
suppressPackageStartupMessages({ library(DBI); library(yaml) })
source("analysis/utilities.R")

args <- commandArgs(trailingOnly = TRUE)
cfg_path <- args[which(args == "--config") + 1]
cfg <- yaml::read_yaml(cfg_path)

con <- pick_connection()
on.exit(try(DBI::dbDisconnect(con, shutdown = TRUE), silent = TRUE), add = TRUE)

sql <- paste(readLines(cfg$sql_file), collapse = "\n")
dat <- DBI::dbGetQuery(con, sql)            # row-level; stays in memory

res <- t.test(n_conditions ~ grp, data = dat)
grp_means <- tapply(dat$n_conditions, dat$grp, mean)
cat(sprintf("[demo] group sizes: %s\n",
            paste(names(table(dat$grp)), table(dat$grp), sep="=", collapse=" ")))
cat(sprintf("[demo] mean(n_conditions): %s\n",
            paste(names(grp_means), round(grp_means, 2), sep="=", collapse=" ")))
cat(sprintf("[demo] Welch t = %.3f, df = %.1f, p = %.4g\n",
            res$statistic, res$parameter, res$p.value))
cat(sprintf("[demo] 95%% CI of mean difference: [%.3f, %.3f]\n",
            res$conf.int[1], res$conf.int[2]))

# Aggregate-only plot: group means +/- standard error. No per-person marks.
out_dir <- cfg$out_dir %||% "runs/0001-demo"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
ses <- tapply(dat$n_conditions, dat$grp, function(v) sd(v) / sqrt(length(v)))
png(file.path(out_dir, "demo_effect.png"), width = 600, height = 400)
bp <- barplot(grp_means, ylim = c(0, max(grp_means + 2 * ses)),
              ylab = "mean condition count",
              main = "Mean conditions by group (aggregate)")
arrows(bp, grp_means - ses, bp, grp_means + ses, angle = 90, code = 3, length = 0.05)
invisible(dev.off())
cat(sprintf("[demo] wrote aggregate plot to %s\n", file.path(out_dir, "demo_effect.png")))
```

- [ ] **Step 4: Write `scripts/setup_data.R` and add the Makefile target**

`scripts/setup_data.R`:
```r
#!/usr/bin/env Rscript
# Fetch the OHDSI Eunomia synthetic OMOP dataset and persist it as a DuckDB
# file at data/eunomia.duckdb. Nothing licensed is committed — each user pulls
# OHDSI's public, Apache-2.0 dataset. data/ is gitignored.
#
# VERIFY: the exact Eunomia API differs across versions. This targets Eunomia
# 2.x (DuckDB backend). If the call below errors, check
# `?Eunomia::getEunomiaConnectionDetails` for your installed version.
suppressPackageStartupMessages({ library(DBI); library(duckdb); library(Eunomia) })

dir.create("data", showWarnings = FALSE)
out <- "data/eunomia.duckdb"

# getEunomiaConnectionDetails builds (or downloads then builds) a DuckDB-backed
# synthetic CDM at the given path.
cd <- Eunomia::getEunomiaConnectionDetails(databaseFile = out)
message("Wrote ", out)

# Sanity check: confirm core OMOP tables are present.
con <- DBI::dbConnect(duckdb::duckdb(), dbdir = out, read_only = TRUE)
tbls <- tolower(DBI::dbListTables(con))
DBI::dbDisconnect(con, shutdown = TRUE)
stopifnot(all(c("person", "condition_occurrence") %in% tbls))
message("OK: person + condition_occurrence present.")
```

Append to `Makefile`:
```makefile
.PHONY: setup-data

# Local only: fetch Eunomia into data/eunomia.duckdb (gitignored).
setup-data:
	Rscript scripts/setup_data.R
```

- [ ] **Step 5: Manual smoke — build fixture and run the demo locally**

Run:
```bash
cd aou-research-template
Rscript scripts/setup_data.R                 # builds data/eunomia.duckdb
python scripts/run_experiment.py --id 1       # dispatches Rscript demo_effect.R
```
Expected:
- `data/eunomia.duckdb` exists and the script printed "OK: person + condition_occurrence present."
- `runs/0001-demo/summary.md` contains the `[demo] Welch t = ...` and `[demo] 95% CI ...` aggregate lines and `### Session complete (exit 0)`.
- `runs/0001-demo/demo_effect.png` exists.
- `summary.md` contains **no** `person_id` lines.

If `Eunomia` / R packages are not installed: `R -e 'install.packages(c("DBI","duckdb","bigrquery","Eunomia","digest","yaml"))'` (Eunomia may require the OHDSI repo; see its README). Record any API adjustment in the commit message.

- [ ] **Step 6: Commit**

```bash
git add aou-research-template/analysis aou-research-template/scripts/setup_data.R aou-research-template/Makefile
git commit -m "feat(template): R demo (t-test + aggregate plot) + Eunomia data setup"
```

---

## Task 10: `CLAUDE.md` — agent safety contract

**Files:**
- Create: `aou-research-template/CLAUDE.md`

**Interfaces:** none (documentation).

- [ ] **Step 1: Write `CLAUDE.md`**

```markdown
# CLAUDE.md

Guidance for an LLM coding agent working in this repo. The human collaborator
runs all code; you never touch raw data.

## The air-gap workflow (read this first)

You and the developer's laptop never see patient-level data. The human is the
only bridge into and out of the secure environment:

1. We edit code here, together.
2. The human pushes to GitHub.
3. The human pulls inside Verily Workbench (the AoU secure environment).
4. The human runs the experiment there, against the real CDR.
5. The human copies ONLY scrubbed, aggregate results back to us.

Your job is to make the safe path the easy path.

## What may cross back

- OK: aggregate counts, summary statistics, effect estimates, p-values, and
  aggregate-only plots (group means/distributions — never one mark per person).
- NOT OK: any row-level / per-person output. It does not cross back at all.
- Hashing an id (`hash_id()` in analysis/utilities.R) is only a fallback for the
  rare case a single id must be named — not a license to emit row-level data.

## Prefer the runner

Run analyses through `make run-exp` (which calls scripts/run_experiment.py).
It streams output live but writes only a *scrubbed* copy to
`runs/<exp>/summary.md`. That scrubbing — `utilities/sanitize.py` — is what
makes the paste-back step trustworthy. If you add output that prints anything
per-person, extend `PATIENT_PATTERNS` there.

## Layout and boundaries

- `utilities/` — pure-Python infrastructure (scrubbing, layered config, runner,
  workspace discovery). Must never import from `analysis/`.
- `analysis/` — the researcher's code (R/SQL/Python). May be any language; the
  runner dispatches the experiment's declared `entrypoint`.
- `experiments/defaults/` + `docs/experiments/` — layered config and the
  per-run records. See docs/experiments/README.md.
- `data/`, `runs/`, `.env`, `.workspace_env` are gitignored. Never commit data
  or secrets.

## Local vs AoU

The same SQL runs both places via `pick_connection()`: DuckDB over the local
Eunomia fixture (`make setup-data`) on the laptop, BigQuery over the CDR in AoU.
Develop and test locally; the human runs the AoU pass.

## Testing

`make test` runs the fast Python unit suite (scrubber, config, runner) with no
data dependency. Add a failing test before implementing (TDD). The R demo is
verified by running it locally against the Eunomia fixture.

## Before you call work done

- `make test` passes.
- No data files, secrets, or large binaries staged (`make lint` runs the hooks).
- Any new per-person output is covered by a `PATIENT_PATTERNS` entry.

## Chat rendering

Agent chat here renders as plain text — no LaTeX. Use plain Greek letters and
ASCII math (E[x], sum_k) in chat. New to the repo? See GETTING_STARTED.md; you
can walk the developer through it step by step.
```

- [ ] **Step 2: Verify it has no LaTeX and references real paths**

Run: `cd aou-research-template && grep -n '\$' CLAUDE.md; ls utilities/sanitize.py analysis/utilities.R docs/experiments/README.md`
Expected: no `$...$` math; all listed paths exist.

- [ ] **Step 3: Commit**

```bash
git add aou-research-template/CLAUDE.md
git commit -m "docs(template): agent safety contract (CLAUDE.md)"
```

---

## Task 11: `README.md` + `GETTING_STARTED.md` (human voice)

**Files:**
- Create: `aou-research-template/README.md`, `aou-research-template/GETTING_STARTED.md`

**Interfaces:** none (documentation). Apply the prose-voice constraint from Global Constraints.

- [ ] **Step 1: Write `README.md`**

```markdown
# AoU Research Template

A starting point for writing analysis code with an AI coding agent and running
it safely in the All of Us secure environment (Verily Workbench).

The idea is a deliberate air-gap. You and the agent write code on your laptop.
You push it to GitHub, pull it inside the workbench, run it there against the
real data, and copy back only aggregate results. The agent never sees a row of
patient data. This repo's tooling is built so the results you copy back are
already scrubbed of anything patient-level.

```
edit locally (you + agent) -> push -> pull in Verily -> run vs CDR -> copy aggregates back
```

What's here:

- `utilities/` — the Python that makes the loop safe and repeatable: output
  scrubbing, layered run config, a language-agnostic runner, workspace setup.
- `analysis/` — where your code goes. The demo is R + SQL; Python works too.
- `experiments/` + `docs/experiments/` — each run is one config + one record.

Start with `GETTING_STARTED.md`. Or open it with Claude and say "walk me through
getting started."
```

- [ ] **Step 2: Write `GETTING_STARTED.md`**

```markdown
# Getting started

This walks the whole loop once, on synthetic data, before you touch any real
data. A colleague can read it top to bottom; or open it with Claude and ask it
to walk you through.

## 1. Install

You need Python 3.11+ and R. Then:

```
make install            # Python infra + dev tools
make precommit-install  # git hooks that block data/secrets and strip notebooks
```

Install the R packages the demo uses:

```
R -e 'install.packages(c("DBI","duckdb","bigrquery","Eunomia","digest","yaml"))'
```

(`Eunomia` is the OHDSI synthetic-data package; see its README if it needs the
OHDSI package repo.)

## 2. Build the local synthetic dataset

```
make setup-data
```

This pulls OHDSI's Eunomia synthetic OMOP data into `data/eunomia.duckdb`
(gitignored — nothing licensed is committed). It's a real OMOP-shaped database
you can query exactly like the CDR.

## 3. Run the demo experiment

```
make run-exp ID=1
```

This runs experiment `0001-demo` (see `docs/experiments/0001-demo.md`): a
t-test of per-person condition counts by sex, plus one aggregate plot. Look at
what it wrote:

- `runs/0001-demo/summary.md` — the scrubbed record. This is what's safe to copy
  back. Notice it has the t-test and CI, but no per-person rows.
- `runs/0001-demo/demo_effect.png` — an aggregate-only plot.

The query in `analysis/demo_cohort.sql` returns per-person rows, but those stay
inside the R process; only aggregates are printed, so only aggregates land in
`summary.md`. That's the safety model in miniature.

## 4. The same code in AoU

Inside Verily Workbench, after pulling this repo:

```
make setup-workspace    # discovers your project/CDR/buckets into .workspace_env
source .workspace_env
make run-exp ID=1
```

`pick_connection()` (in `analysis/utilities.R`) sees `WORKSPACE_CDR` is set and
connects to BigQuery instead of DuckDB — the same `demo_cohort.sql` runs against
the real CDR. Review `runs/0001-demo/summary.md`, then copy the aggregate result
back to your laptop / the agent.

Note on SQL: the demo SQL is kept simple so one query runs on both DuckDB and
BigQuery. A real analysis may need dataset-qualified table names in BigQuery;
adjust the SQL for the AoU path if so.

## 5. Your own experiment

```
make new-exp SLUG=my-question
```

Edit the new `docs/experiments/NNNN-my-question.md` (set its Intent, tweak
config in the frontmatter), point its `entrypoint` at your script in
`analysis/`, and `make run-exp`.

## Plots and the air-gap

A plot is a binary file you can't line-scrub, so treat it carefully: only ever
plot aggregates (means, distributions, counts), never one mark per person, and
look at any plot before you bring it out of the workbench.
```

- [ ] **Step 3: Self-check the prose voice**

Re-read both files against the Global Constraints voice rule. Run:
`cd aou-research-template && grep -niE "comprehensive|seamless|robust|whether you|leverage|in today's|effortless" README.md GETTING_STARTED.md`
Expected: no matches. Fix any that appear.

- [ ] **Step 4: Commit**

```bash
git add aou-research-template/README.md aou-research-template/GETTING_STARTED.md
git commit -m "docs(template): README + GETTING_STARTED (the air-gap walkthrough)"
```

---

## Task 12: Notebook companion + final end-to-end verification

**Files:**
- Create: `aou-research-template/notebooks/demo_exploration.ipynb`
- Test: full-suite + lint verification

**Interfaces:** none new.

- [ ] **Step 1: Create the thin R-kernel notebook**

Create `notebooks/demo_exploration.ipynb` as a minimal nbformat-4 notebook with an R kernel and outputs already empty (so nbstripout has nothing to strip). Use this exact JSON:
```json
{
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": [
    "# Demo exploration (local only)\n",
    "\n",
    "Thin companion to `analysis/demo_effect.R`. For interactive, LOCAL\n",
    "exploration against the Eunomia fixture. Run `make setup-data` first.\n",
    "Outputs are stripped on commit; the committed, scrubbed record of a run is\n",
    "`runs/0001-demo/summary.md`, produced by `make run-exp`."
  ]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": [
    "source(\"../analysis/utilities.R\")\n",
    "con <- pick_connection()\n",
    "sql <- paste(readLines(\"../analysis/demo_cohort.sql\"), collapse = \"\\n\")\n",
    "dat <- DBI::dbGetQuery(con, sql)\n",
    "# Aggregates only when sharing anything out:\n",
    "tapply(dat$n_conditions, dat$grp, mean)"
  ]}
 ],
 "metadata": {
  "kernelspec": {"display_name": "R", "language": "R", "name": "ir"},
  "language_info": {"name": "R"}
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

- [ ] **Step 2: Verify nbstripout leaves it clean and hooks pass**

Run:
```bash
cd aou-research-template
git add notebooks/demo_exploration.ipynb
pre-commit run --all-files
```
Expected: nbstripout, check-added-large-files, and no-data-files all pass (the notebook has no outputs to strip).

- [ ] **Step 3: Run the full Python suite**

Run: `cd aou-research-template && pytest -q`
Expected: all tests pass (scaffolding, sanitize, config, runner, workspace, cli_run, new_experiment, demo_config).

- [ ] **Step 4: Final tree check against the spec**

Run: `cd aou-research-template && find . -type f -not -path './.git/*' -not -path './runs/*' -not -path './data/*' -not -path '*/__pycache__/*' | sort`
Expected: matches the File Structure list in this plan (no stray files, nothing under data/ or runs/ staged).

- [ ] **Step 5: Commit**

```bash
git add aou-research-template/notebooks/demo_exploration.ipynb
git commit -m "docs(template): thin R notebook companion + final verification"
```

---

## Self-Review

**Spec coverage** (each spec section → task):
- §1 air-gap workflow → CLAUDE.md (T10), README/GETTING_STARTED (T11)
- §3 sanitize.py → T2; config.py → T3; runner.py → T4; workspace.py → T5
- §4 skeleton → all tasks; hygiene/CI → T1
- §5 demo (t-test + aggregate plot, local+AoU, scrubbed summary) → T8 (config/record), T9 (R/SQL/data), plot-safety rule → CLAUDE/GETTING_STARTED (T10/T11)
- §6 Eunomia fetch → DuckDB, no vendored vocab, unit tests need no OMOP data → T9 (setup_data.R), T2–T7 (data-free tests)
- §7 CLAUDE.md contents → T10
- §8 prose voice → T11 (enforced + grep check)
- §9 caveats (workspace markers, Eunomia version, R deps, SQL dialect) → T5 (markers), T9 (version note), T11 (R deps + SQL note)
- §10 non-goals → respected throughout (no Spark/LDA/eval/dashboard)

**Placeholder scan:** the only intentional fill-ins are inside the experiment-record *template* (`<...>` prompts a human fills per run) and the demo record's Results/Interpretation (filled after the run) — these are content authored at use time, not plan gaps. No code step is left unwritten.

**Type consistency:** `effective_config(record_path, defaults_dir)`, `run_experiment(record_path, defaults_dir, runs_dir)`, `run_subprocess_tee_sanitize(cmd, summary_path, patterns=None)`, `discover(wb=...)`, `scaffold(slug, experiments_dir, template_path, today)`, `next_id(experiments_dir)` are used consistently across the tasks and their callers (CLIs in T6/T7). The runner injects `out_dir`; the R entrypoint reads `cfg$out_dir` and `cfg$sql_file` — names match T8's config.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-19-aou-research-template.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — I execute tasks in this session using executing-plans, with checkpoints for review.

Which approach?
