# Date-Slug Experiment Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the sequential `NNNN-slug` experiment id with a branch-friendly `YYYY-MM-DD-slug` folder identity selected on the CLI by slug.

**Architecture:** Experiment folders become `experiments/YYYY-MM-DD-<slug>/`; `(date, slug)` is the identity, git blocks same-day-same-slug collisions structurally, and a non-failing test warns on cross-day slug reuse. The runner sorts by the ISO date prefix (already chronological) and selects by slug instead of an integer id.

**Tech Stack:** Python 3 (stdlib `re`, `pathlib`, `warnings`), pytest, Make.

## Global Constraints

- Experiment folder names: `YYYY-MM-DD-<slug>` (ISO date, `<slug>` is kebab-case). Date prefix is exactly 11 chars including the trailing `-`.
- `framework/utilities/` must never import from experiment folders.
- Every task ends green: `make test` (alias `pytest -q`) passes.
- `framework/docs/DESIGN.md` and `framework/docs/IMPLEMENTATION_PLAN.md` are archival — do NOT edit them.
- Commit messages end with the repo's Co-Authored-By trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

---

### Task 1: Slug-based selection in the runner and run CLI

**Files:**
- Modify: `framework/utilities/runner.py` (`_DIR_RE`, replace `find_by_id` with `find_by_slug`, add `_slug_of`)
- Modify: `framework/utilities/cli/run.py` (`--id` → `--slug`)
- Modify: `framework/utilities/config.py` (docstring line ~5)
- Test: `framework/tests/test_runner.py`, `framework/tests/test_cli_run.py`

**Interfaces:**
- Consumes: `_experiments(experiments_dir) -> list[Path]` (existing, name-sorted).
- Produces:
  - `find_by_slug(experiments_dir: Path, slug: str) -> Path` — returns the folder whose name after the `YYYY-MM-DD-` prefix equals `slug`; a full folder-name match wins first (escape hatch for cross-date ambiguity). Raises `FileNotFoundError` on no match, `ValueError` on >1 match.
  - `_slug_of(name: str) -> str` — `name[11:]`.
  - `run.py` CLI flag `--slug <str>` replacing `--id <int>`.

- [ ] **Step 1: Rewrite the runner tests to the new behavior**

Replace the top import and `test_find_by_id_and_next` in `framework/tests/test_runner.py`. Final file:

```python
import sys
import pytest
from pathlib import Path
from utilities.runner import find_by_slug, find_next_pending, run_experiment


def _mk(exp_root, name, status):
    d = exp_root / name; d.mkdir()
    (d / "README.md").write_text(f"---\nstatus: {status}\n---\n")
    return d


def test_find_by_slug_and_next(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    _mk(exp, "2026-06-19-a", "done"); _mk(exp, "2026-06-20-b", "pending")
    assert find_by_slug(exp, "a").name == "2026-06-19-a"
    assert find_next_pending(exp).name == "2026-06-20-b"


def test_find_by_slug_missing(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    _mk(exp, "2026-06-19-a", "done")
    with pytest.raises(FileNotFoundError):
        find_by_slug(exp, "nope")


def test_find_by_slug_ambiguous_across_dates(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    _mk(exp, "2026-06-19-a", "done"); _mk(exp, "2026-07-01-a", "pending")
    with pytest.raises(ValueError):
        find_by_slug(exp, "a")
    # the full folder name is the escape hatch
    assert find_by_slug(exp, "2026-07-01-a").name == "2026-07-01-a"


def test_run_experiment_scrubs_and_records(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    d = _mk(exp, "2026-06-19-demo", "pending")
    defaults = tmp_path / "_defaults.yaml"; defaults.write_text("seed: 1\n")
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import sys\n"
        "assert '--config' in sys.argv\n"
        "print('person_id = 7')\n"
        "print('[demo] mean = 3.14')\n"
    )
    (d / "config.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    rc = run_experiment(d, defaults)
    assert rc == 0
    summary = (d / "runs" / "summary.md").read_text()
    assert "mean = 3.14" in summary
    assert "person_id" not in summary
    assert "Session complete (exit 0)" in summary
    assert (d / "runs" / "config.yaml").exists()
```

- [ ] **Step 2: Run the runner tests to verify they fail**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_runner.py -q`
Expected: FAIL — `ImportError: cannot import name 'find_by_slug'`.

- [ ] **Step 3: Update `runner.py`**

In `framework/utilities/runner.py`: change the regex and replace `find_by_id`.

Change line 20 from:
```python
_DIR_RE = re.compile(r"^(\d{4})-.+$")
```
to:
```python
_DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-.+$")
```

Replace the whole `find_by_id` function (lines 29-34) with:
```python
def _slug_of(name: str) -> str:
    return name[11:]  # strip the "YYYY-MM-DD-" prefix


def find_by_slug(experiments_dir: Path, slug: str) -> Path:
    exps = _experiments(experiments_dir)
    for p in exps:  # exact full-name match is the escape hatch for cross-date dupes
        if p.name == slug:
            return p
    matches = [p for p in exps if _slug_of(p.name) == slug]
    if not matches:
        raise FileNotFoundError(f"no experiment with slug {slug!r} in {experiments_dir}")
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise ValueError(
            f"slug {slug!r} is ambiguous across dates: {names}; "
            f"pass the full folder name instead"
        )
    return matches[0]
```

- [ ] **Step 4: Run the runner tests to verify they pass**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_runner.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Update the run CLI**

In `framework/utilities/cli/run.py`:

Change the import (line 9):
```python
from utilities.runner import find_by_slug, find_next_pending, run_experiment
```

Change the `--id` argument (line 16) to:
```python
    sel.add_argument("--slug", help="run experiment with this slug (or full YYYY-MM-DD-slug folder name)")
```

Change the dispatch else-branch (line 28) from `exp = find_by_id(exp_root, args.id)` to:
```python
        exp = find_by_slug(exp_root, args.slug)
```

Update the `--next` help text (line 15) from `"run lowest-id pending experiment"` to `"run earliest pending experiment"`.

- [ ] **Step 6: Update the config.py docstring**

In `framework/utilities/config.py`, change the line reading `experiments/<NNNN-slug>/config.yaml   # this experiment's config` to:
```python
    experiments/<YYYY-MM-DD-slug>/config.yaml   # this experiment's config
```

- [ ] **Step 7: Update `test_cli_run.py`**

In `framework/tests/test_cli_run.py`, change the fixture folder name and add a `--slug` invocation. Final file:

```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _mk_exp(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "_defaults.yaml").write_text("seed: 1\n")
    d = exp / "2026-06-19-demo"; d.mkdir()
    (d / "README.md").write_text("---\nstatus: pending\n---\n")
    stub = tmp_path / "stub.py"; stub.write_text("print('[demo] ok')\n")
    (d / "config.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    return exp, d


def _run(exp, *args):
    return subprocess.run(
        [sys.executable, "-m", "utilities.cli.run", *args,
         "--experiments-dir", str(exp), "--defaults", str(exp / "_defaults.yaml")],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_run_cli_dispatches_next(tmp_path):
    exp, d = _mk_exp(tmp_path)
    r = _run(exp, "--next")
    assert r.returncode == 0, r.stderr
    assert (d / "runs" / "summary.md").exists()


def test_run_cli_dispatches_slug(tmp_path):
    exp, d = _mk_exp(tmp_path)
    r = _run(exp, "--slug", "demo")
    assert r.returncode == 0, r.stderr
    assert (d / "runs" / "summary.md").exists()
```

- [ ] **Step 8: Run the full suite**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest -q`
Expected: PASS (demo config + new-experiment tests still reference `0001-demo`, which still exists — those are untouched here).

- [ ] **Step 9: Commit**

```bash
git add framework/utilities/runner.py framework/utilities/cli/run.py framework/utilities/config.py framework/tests/test_runner.py framework/tests/test_cli_run.py
git commit -m "feat: select experiments by slug over a date-prefixed folder

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Date-slug scaffolding in new-experiment + template

**Files:**
- Modify: `framework/utilities/cli/new.py` (drop `next_id`/`_DIR_RE`, date-slug `scaffold`, refuse existing)
- Modify: `experiments/_template/config.yaml`, `experiments/_template/README.md`
- Test: `framework/tests/test_new_experiment.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `scaffold(slug: str, experiments_dir: Path, template_dir: Path, today: str) -> Path` — creates `experiments/<today>-<slug>/`, substitutes `{date}` and `{slug}` into template files, raises `FileExistsError` if the folder exists. `next_id` no longer exists.

- [ ] **Step 1: Rewrite the new-experiment tests**

Replace `framework/tests/test_new_experiment.py` entirely:

```python
from pathlib import Path
import pytest
from utilities.cli.new import scaffold


def _tmpl(tmp_path):
    t = tmp_path / "_template"; t.mkdir()
    (t / "README.md").write_text(
        "---\nstatus: pending\ncreated: {date}\n---\n\n# Experiment {date} — {slug}\n")
    (t / "config.yaml").write_text(
        "entrypoint: Rscript experiments/{date}-{slug}/analysis.R\n")
    return t


def test_scaffold_writes_date_slug_folder(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    out = scaffold("my-run", exp, _tmpl(tmp_path), today="2026-06-19")
    assert out.name == "2026-06-19-my-run"
    readme = (out / "README.md").read_text()
    assert "Experiment 2026-06-19 — my-run" in readme
    assert "created: 2026-06-19" in readme
    cfg = (out / "config.yaml").read_text()
    assert "experiments/2026-06-19-my-run/analysis.R" in cfg


def test_scaffold_refuses_existing(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    tmpl = _tmpl(tmp_path)
    scaffold("dup", exp, tmpl, today="2026-06-19")
    with pytest.raises(FileExistsError):
        scaffold("dup", exp, tmpl, today="2026-06-19")
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_new_experiment.py -q`
Expected: FAIL — `test_scaffold_writes_date_slug_folder` asserts `2026-06-19-my-run` but current code produces `0002-my-run`; the `ImportError` for `next_id` is gone but behavior mismatches.

- [ ] **Step 3: Rewrite `new.py`**

Replace `framework/utilities/cli/new.py` with:

```python
#!/usr/bin/env python
"""Scaffold a dated experiment folder from experiments/_template/."""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path


def scaffold(slug: str, experiments_dir: Path, template_dir: Path, today: str) -> Path:
    out_dir = experiments_dir / f"{today}-{slug}"
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} already exists")
    out_dir.mkdir(parents=True)
    subs = dict(slug=slug, date=today)
    for src in sorted(template_dir.iterdir()):
        if src.is_file():
            (out_dir / src.name).write_text(src.read_text().format(**subs))
    return out_dir


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug", help="short kebab-case slug, e.g. 'sex-condition-count'")
    p.add_argument("--experiments-dir", default="experiments")
    p.add_argument("--template-dir", default="experiments/_template")
    args = p.parse_args(argv)
    today = _dt.date.today().isoformat()
    out = scaffold(args.slug, Path(args.experiments_dir), Path(args.template_dir), today)
    print(f"Wrote {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_new_experiment.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Update the template files**

`experiments/_template/config.yaml` — change the two path lines to:
```yaml
entrypoint: Rscript experiments/{date}-{slug}/analysis.R
sql_file: experiments/{date}-{slug}/cohort.sql
```

`experiments/_template/README.md` — change the heading line from `# Experiment {id_padded} — {slug}` to:
```markdown
# Experiment {date} — {slug}
```
and the Results line from `<after running, paste the scrubbed contents of experiments/{id_padded}-{slug}/runs/summary.md here>` to:
```markdown
<after running, paste the scrubbed contents of experiments/{date}-{slug}/runs/summary.md here>
```

- [ ] **Step 6: Sanity-check the real scaffolder end to end**

Run:
```bash
cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && \
python -m utilities.cli.new scratch-check --experiments-dir experiments && \
ls -d experiments/*-scratch-check && cat experiments/*-scratch-check/config.yaml && \
rm -rf experiments/*-scratch-check
```
Expected: prints `Wrote experiments/<today>-scratch-check/`, the config shows the dated path substituted, then the folder is removed. (Confirm no `*-scratch-check` folder remains before committing.)

- [ ] **Step 7: Run the full suite**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add framework/utilities/cli/new.py framework/tests/test_new_experiment.py experiments/_template/config.yaml experiments/_template/README.md
git commit -m "feat: scaffold experiments as YYYY-MM-DD-slug folders

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Rename the demo experiment to date-slug

**Files:**
- Rename: `experiments/0001-demo/` → `experiments/2026-06-19-demo/` (git mv, preserves all contents including `runs/` and `demo_exploration.ipynb`)
- Modify: `experiments/2026-06-19-demo/config.yaml`, `experiments/2026-06-19-demo/README.md`
- Test: `framework/tests/test_demo_config.py`

**Interfaces:**
- Consumes: `effective_config` (unchanged).
- Produces: demo folder at `experiments/2026-06-19-demo/` with internal paths pointing at itself.

- [ ] **Step 1: Update the demo config test**

Replace the two path assertions in `framework/tests/test_demo_config.py`:

```python
def test_demo_effective_config():
    cfg = effective_config(
        ROOT / "experiments" / "2026-06-19-demo",
        ROOT / "experiments" / "_defaults.yaml",
    )
    assert cfg["entrypoint"] == "Rscript experiments/2026-06-19-demo/demo_effect.R"
    assert cfg["sql_file"] == "experiments/2026-06-19-demo/demo_cohort.sql"
    assert cfg["seed"] == 42
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_demo_config.py -q`
Expected: FAIL — folder `2026-06-19-demo` does not exist yet.

- [ ] **Step 3: Rename the folder**

Run:
```bash
cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && \
git mv experiments/0001-demo experiments/2026-06-19-demo
```

- [ ] **Step 4: Update the demo's internal paths**

In `experiments/2026-06-19-demo/config.yaml`, change both `experiments/0001-demo/...` paths to `experiments/2026-06-19-demo/...`:
```yaml
entrypoint: Rscript experiments/2026-06-19-demo/demo_effect.R
sql_file: experiments/2026-06-19-demo/demo_cohort.sql
```
Also update the comment line `# Run configuration for experiment 0001-demo.` to `# Run configuration for experiment 2026-06-19-demo.`

In `experiments/2026-06-19-demo/README.md`:
- Heading `# Experiment 0001 — demo` → `# Experiment 2026-06-19 — demo`
- Results line `<after `make run-exp ID=1`, paste the scrubbed experiments/0001-demo/runs/summary.md here>` → `<after `make run-exp SLUG=demo`, paste the scrubbed experiments/2026-06-19-demo/runs/summary.md here>`

- [ ] **Step 5: Run the full suite**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A experiments/2026-06-19-demo framework/tests/test_demo_config.py
git commit -m "refactor: rename 0001-demo to 2026-06-19-demo

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Cross-day slug-reuse warning check

**Files:**
- Create: `framework/utilities/slugcheck.py`
- Test: `framework/tests/test_slug_uniqueness.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `duplicate_slugs(experiments_dir: Path) -> dict[str, list[str]]` — maps each slug used under more than one date to its sorted list of folder names; empty dict when all slugs are unique.

- [ ] **Step 1: Write the failing test**

Create `framework/tests/test_slug_uniqueness.py`:

```python
import warnings
from pathlib import Path
from utilities.slugcheck import duplicate_slugs

ROOT = Path(__file__).resolve().parent.parent.parent


def test_detects_slug_reused_across_dates(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "2026-06-19-a").mkdir()
    (exp / "2026-07-01-a").mkdir()
    (exp / "2026-06-19-b").mkdir()
    (exp / "_template").mkdir()  # non-dated dirs are ignored
    dups = duplicate_slugs(exp)
    assert set(dups) == {"a"}
    assert dups["a"] == ["2026-06-19-a", "2026-07-01-a"]


def test_unique_slugs_return_empty(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "2026-06-19-a").mkdir()
    (exp / "2026-06-20-b").mkdir()
    assert duplicate_slugs(exp) == {}


def test_repo_experiments_slugs_unique():
    # Non-failing guard: warns (does not fail) if the committed tree reuses a
    # slug across dates, surfacing accidental twins without blocking re-runs.
    dups = duplicate_slugs(ROOT / "experiments")
    if dups:
        warnings.warn(f"experiment slugs reused across dates: {dups}", stacklevel=2)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_slug_uniqueness.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'utilities.slugcheck'`.

- [ ] **Step 3: Implement the helper**

Create `framework/utilities/slugcheck.py`:

```python
"""Detect experiment slugs reused across different dates (a warning-level check).

A folder name is `YYYY-MM-DD-<slug>`. The filesystem and git already prevent two
folders with the identical name, so this only surfaces the harmless-but-usually-
accidental case of the same slug under two different dates.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

_DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def duplicate_slugs(experiments_dir: Path) -> dict[str, list[str]]:
    by_slug: dict[str, list[str]] = defaultdict(list)
    for p in experiments_dir.iterdir():
        if not p.is_dir():
            continue
        m = _DIR_RE.match(p.name)
        if m:
            by_slug[m.group(2)].append(p.name)
    return {slug: sorted(names) for slug, names in by_slug.items() if len(names) > 1}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest framework/tests/test_slug_uniqueness.py -q`
Expected: PASS (3 tests, no warning — the repo tree has only `2026-06-19-demo`).

- [ ] **Step 5: Commit**

```bash
git add framework/utilities/slugcheck.py framework/tests/test_slug_uniqueness.py
git commit -m "feat: warn when an experiment slug is reused across dates

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Update Makefile and user-facing docs

**Files:**
- Modify: `Makefile` (`run-exp` target + comment)
- Modify: `CLAUDE.md`, `GETTING_STARTED.md`, `README.md`

**Interfaces:**
- Consumes: the `--slug` CLI from Task 1, `SLUG=` scaffolding from Task 2, the demo rename from Task 3.
- Produces: docs and Make targets consistent with date-slug naming. (No automated test; verified by `make test` staying green and manual grep.)

- [ ] **Step 1: Update the Makefile `run-exp` target**

In `Makefile`, replace the comment + target (lines ~24-25):
```makefile
# Run an experiment: `make run-exp` (next pending) or `make run-exp SLUG=my-run`.
run-exp:
	run-experiment $(if $(SLUG),--slug $(SLUG),--next)
```

- [ ] **Step 2: Update `CLAUDE.md`**

Change the bullet `- `experiments/<NNNN-slug>/` — each experiment is self-contained:` to `- `experiments/<YYYY-MM-DD-slug>/` — each experiment is self-contained:`.

- [ ] **Step 3: Update `GETTING_STARTED.md`**

- Both occurrences of `make run-exp ID=1` → `make run-exp SLUG=demo`.
- All `experiments/0001-demo/...` paths → `experiments/2026-06-19-demo/...` (three lines: `runs/summary.md`, `runs/demo_effect.png`, `demo_cohort.sql`).
- The line `This runs experiment `0001-demo`: ...` → `This runs experiment `2026-06-19-demo`: ...`.
- The line `This creates `experiments/NNNN-my-question/` with a `config.yaml` and `README.md`.` → `This creates `experiments/<today>-my-question/` (a dated folder) with a `config.yaml` and `README.md`.`

- [ ] **Step 4: Update `README.md`**

Change `The shipped `0001-demo` experiment is a worked example ...` → `The shipped `2026-06-19-demo` experiment is a worked example ...`.

- [ ] **Step 5: Verify no stale live references remain**

Run:
```bash
cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && \
grep -rn "0001-demo\|NNNN\|run-exp ID\|--id\|id_padded" \
  CLAUDE.md GETTING_STARTED.md README.md Makefile experiments/ framework/utilities/ framework/tests/ ; \
echo "exit: $?"
```
Expected: no matches (grep exit 1 / prints only `exit: 1`). Archival `framework/docs/*` is intentionally excluded.

- [ ] **Step 6: Run the full suite**

Run: `cd /Users/oneilsh/Documents/projects/tislab/aou-research-template && python -m pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add Makefile CLAUDE.md GETTING_STARTED.md README.md
git commit -m "docs: switch run-exp and guides to slug-based date-slug naming

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notes for the executor

- Run every command from the repo root: `/Users/oneilsh/Documents/projects/tislab/aou-research-template`.
- The pre-commit hooks (nbstripout, large-file, data-file guard) run on commit; none of these changes touch data or notebooks-with-output, so they should pass clean.
- Do NOT edit `framework/docs/DESIGN.md` or `framework/docs/IMPLEMENTATION_PLAN.md` — they are archival records of the original build and describe a superseded layout.
