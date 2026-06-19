# Design: `aou-research-template`

**Status:** approved design, pre-implementation
**Date:** 2026-06-19

A copy-and-customize template repository that lets an All of Us researcher
collaborate with an LLM coding agent on **safe, reproducible** analysis code,
under a human-enforced air-gap. Extracted from CHARMPheno's infrastructure but
carrying none of its Spark / topic-modeling / phenotyping domain code.

The template is built as a folder inside CHARMPheno
(`aou-research-template/`) during development, then moved out and `git init`ed
as its own repository.

---

## 1. The workflow this template serves

The defining constraint. The agent (and the developer's laptop) **never touch
raw patient data**. The human is the only bridge across the air-gap:

```
  edit code locally, with the agent
        │  git push
        ▼
  GitHub
        │  git pull  (inside Verily Workbench)
        ▼
  Verily Workbench (AoU secure env) ── run experiment against the CDR
        │  human copies ONLY scrubbed, aggregate results back
        ▼
  back to the local repo / agent chat
```

The template's whole job is to make the paste-back step **safe by
construction** (what you would copy back is already scrubbed of patient-level
rows) and **reproducible** (a run is fully described by committed config +
code). Safety is enforced by the human, but the tooling makes the safe path
the easy path.

## 2. Decisions locked during brainstorming

- **Form:** plain copy-and-customize template repo (no cookiecutter). Renamed
  on `git init`.
- **Target environment:** Verily Workbench (the `wb` CLI). Not Terra/AoU
  Researcher Workbench.
- **Primary analysis language:** R + SQL (the common case for these
  colleagues); Python works identically because the runner is language-agnostic.
- **The sanitizing runner is the centerpiece**, not an optional add-on — it is
  the safety argument for paste-back.
- **Agent doc:** a fuller `CLAUDE.md` covering the safety contract, air-gap
  loop, project layout, testing, and a finish-checklist — but **without** the
  ADR / insights-log / REVIEW_LOG machinery from CHARMPheno.
- **Worked example == experiment `0001`:** the demo doubles as the tutorial for
  the experiment-tracking feature.
- **Onboarding:** one dual-audience `GETTING_STARTED.md`; `CLAUDE.md` points to
  it so "walk me through getting started" works.
- **Local/remote SQL parity via DuckDB + DBI** (no local Spark).
- **Reusable Python package name:** `utilities`.
- **Local synthetic data: fetched from OHDSI Eunomia at setup time** into a
  gitignored DuckDB — never vendored into the repo (so the template
  redistributes no restricted vocabulary).

## 3. Architecture

A small **Python infrastructure package** (`utilities/`) does orchestration
only. The *analysis* is whatever language the researcher writes (R first-class).
Capture/scrubbing happens at the subprocess-stdout boundary, which is why the
runner is language-agnostic.

Four independently testable units:

### `utilities/sanitize.py` — the crown jewel
`PATIENT_PATTERNS` / `NOISE_PATTERNS`, `sanitize_line(line, patterns) -> str |
None`, and a tee-capture wrapper (`run_subprocess_tee_sanitize`) that streams a
child process's stdout live to the terminal while writing a **scrubbed** copy
to a file. Pure-Python, no domain assumptions, exhaustively unit-tested. Ported
from CHARMPheno `scripts/run_experiment.py:159-360` and cleaned of LDA/Spark
references.

- `PATIENT_PATTERNS`: drop any line that looks like row-level patient output
  (person_id assignments, `hash:<hex>`, "transform sample" phase markers, etc.).
- `NOISE_PATTERNS`: drop cluster/log4j noise from the committed copy while still
  teeing it live.
- The split between the two lists is documentary; callers pass the composed
  `DROP_PATTERNS`.

### `utilities/config.py` — layered config
`read_frontmatter(path)` (YAML frontmatter from a markdown record) and
`merge_config` / `load_defaults` implementing the layering
`_base.yaml -> <group>.yaml -> per-experiment frontmatter`. Ported and
de-LDA'd from CHARMPheno.

### `utilities/runner.py` — generic experiment runner
Reads an experiment record (`docs/experiments/NNNN-slug.md`), merges layered
config, then **dispatches the command the experiment itself declares** (an
`entrypoint` field, e.g. `Rscript analysis/demo_effect.R`), passing the
effective config to the child (as a written `--config <path>` JSON/YAML and/or
env). It tee-captures the child's **scrubbed** stdout, appending an accumulating
`## Fit session N` block to the record's `summary.md`. Keeps the proven
ergonomics: auto-discover the next `status: pending` experiment, write the
effective merged config into the summary so later edits don't retroactively
change past runs.

Explicitly NOT included: `spark-submit`, `build_lda_args`, resume/checkpoint
semantics, eval/NPMI, dashboard build. The entrypoint contract replaces all of
it.

### `utilities/workspace.py` — Verily Workbench bring-up
`wb`-CLI discovery of `GOOGLE_CLOUD_PROJECT` / `WORKSPACE_CDR` /
`WORKSPACE_BUCKET` / `WORKSPACE_TEMP_BUCKET` into a sourceable `.workspace_env`.
Ported from `analysis/cloud/setup_workspace.py`, with bucket-name matching
loosened and a visible "VERIFY/ADAPT in your workspace" marker. Marked
best-effort; to be validated in a fresh VM/workspace. The demo does not require
it (the local path needs no workspace).

**Two distinct setups — keep them apart.** `workspace.py` is the *AoU*
environment bring-up (discover the real CDR + buckets via `wb`); it ships no
synthetic data. **Local data setup is a separate concern** (§6): a step on the
laptop that fetches Eunomia into a gitignored DuckDB. `pick_connection()` in the
R helper chooses DuckDB-over-Eunomia locally vs BigQuery-over-CDR in AoU, so the
same SQL runs in both. Two `make` targets, one per environment.

## 4. Repo skeleton

```
aou-research-template/            (placeholder name; rename on git init)
├── README.md                     # high-level, human-voiced (see §8)
├── GETTING_STARTED.md            # dual-audience guided first run
├── CLAUDE.md                     # agent safety contract + workflow + conventions
├── Makefile                      # install · test · lint · setup-data · setup-workspace · new-exp · run-exp
├── pyproject.toml                # infra deps only: pyyaml, pytest, ruff, pre-commit
├── .python-version
├── .gitignore                    # data/, .env*, .workspace_env, caches; !tests/data/
├── .gitattributes                # nbstripout clean filter
├── .pre-commit-config.yaml       # nbstripout, large-files (1MB), no-data-files
├── .env.example                  # placeholders only, never real keys
├── .claude/
│   └── settings.json             # conservative permission allowlist
├── utilities/                    # the reusable Python core
│   ├── __init__.py
│   ├── sanitize.py
│   ├── config.py
│   ├── runner.py
│   └── workspace.py
├── scripts/
│   ├── new_experiment.py         # scaffold docs/experiments/NNNN-slug.md from template
│   ├── run_experiment.py         # thin CLI -> utilities.runner
│   ├── setup_workspace.py        # thin CLI -> utilities.workspace (AoU CDR discovery)
│   ├── setup_data.R              # local: fetch Eunomia -> data/eunomia.duckdb (gitignored)
│   └── check_no_data_files.sh
├── analysis/                     # where researchers put entrypoints (R/SQL/Python)
│   ├── demo_cohort.sql           # dialect-portable query (DuckDB local / BigQuery AoU)
│   ├── demo_effect.R             # connection-agnostic: t.test + one aggregate plot
│   └── utilities.R               # tiny R helper: hash_id(), pick_connection()
├── experiments/
│   └── defaults/
│       ├── _base.yaml
│       └── demo.yaml
├── docs/
│   └── experiments/
│       ├── README.md             # the record format
│       ├── _template.md          # frontmatter skeleton new_experiment copies
│       └── 0001-demo.md          # the worked example == tutorial
├── notebooks/
│   └── demo_exploration.ipynb    # thin R-kernel companion; outputs stripped on commit
└── tests/
    ├── test_sanitize.py          # exhaustive scrubber tests
    ├── test_config.py            # layered-merge + frontmatter tests
    ├── test_runner.py            # dispatch + capture, against a fake entrypoint
    └── data/                     # tiny fully-synthetic smoke fixtures (fake log lines,
                                  #   YAML, a stub entrypoint) — NO real OMOP/vocab data

# data/eunomia.duckdb is fetched by `make setup-data`, gitignored, not committed.
```

## 5. The demo (experiment `0001`)

As simple as possible while still querying OMOP tables and producing output:

- **Question:** does some simple continuous measure differ between two groups
  defined from OMOP (e.g. mean number of condition occurrences, or age, between
  a drug-exposed group and an unexposed group)?
- **`demo_cohort.sql`:** joins `person` / `condition_occurrence` /
  `drug_exposure` to produce a per-person, two-group aggregate table. Written in
  dialect-simple SQL that runs unchanged on DuckDB and BigQuery.
- **`demo_effect.R`:** opens a `DBI` connection chosen by environment (DuckDB
  over the local CSV fixture, or `bigrquery` in AoU), runs the SQL, computes a
  **`t.test`**, prints the aggregate result, and writes **one aggregate-only
  plot** (group means with error bars / boxplot) to the run's output dir.
- **Output that crosses back:** the t.test statistic + the plot. Both aggregate.
  Running it appends a scrubbed `summary.md` block to `0001-demo.md`,
  demonstrating the tracking + safety loop end-to-end.

Same config runs **two ways**: locally against the Eunomia DuckDB
(`data/eunomia.duckdb`, built by `make setup-data`) so a colleague can run it
before ever touching AoU, and in AoU against the CDR via BigQuery.

### Plot safety rule (new constraint the demo introduces)
A plot is a binary artifact that cannot be line-scrubbed and could leak
row-level data (e.g. a scatter of individuals). The rule, stated in `CLAUDE.md`
and `GETTING_STARTED.md`: **plots that cross the air-gap must be aggregate-only
(distributions/means/counts, never one-mark-per-person) and get a human eyeball
before export.** The demo plot models this (group summaries, not individuals).
Plot files are written to a gitignored output dir; bringing one out is a
deliberate manual step after visual review.

## 6. Synthetic OMOP fixture — fetched from Eunomia, never vendored

Local execution needs an OMOP-shaped fixture so local and AoU code match. We get
it from **OHDSI Eunomia** (a synthetic, SynPUF-derived OMOP CDM dataset with a
bundled vocabulary subset, maintained by OHDSI for exactly this purpose) rather
than building or committing our own.

- **`scripts/setup_data.R`** (run by `make setup-data`) fetches Eunomia and
  materializes it into **`data/eunomia.duckdb`**, which is **gitignored** —
  nothing licensed is ever committed to the template. This is the decisive
  licensing posture: we do not redistribute SNOMED/CPT/RxNorm ourselves; each
  user pulls OHDSI's already-public dataset, which they are entitled to.
- **Language-agnostic:** the resulting `.duckdb` file is read identically by R
  (`DBI`+`duckdb`), Python, or raw SQL — so the same fixture serves any analysis
  language a colleague chooses.
- **Local/remote parity:** `pick_connection()` returns a DuckDB connection over
  `data/eunomia.duckdb` locally, or a `bigrquery` connection over the CDR in
  AoU. `demo_cohort.sql` runs against both (kept ANSI-simple; see §9).
- **Unit tests don't need it.** The `utilities/` fast suite tests scrubbing,
  config-merge, and runner-dispatch on tiny fully-synthetic fixtures
  (`tests/data/`: fake log lines, small YAML, a stub entrypoint) with **no real
  OMOP or vocabulary data**. Only the run-once demo (`0001`) depends on the
  fetched Eunomia DB.

## 7. Agent doc (`CLAUDE.md`) — contents

Keeps:
- The air-gap workflow contract and diagram.
- **What may cross back:** aggregates, estimates, and aggregate-only plots.
  **No row-level output crosses back at all.** Hashing an ID is only the
  fallback for the rare case a single ID must be named — in practice row-level
  output simply is not copied out.
- "Prefer the runner" — running through `run_experiment.py` means output is
  scrubbed and the run is recorded.
- Project layout and boundaries (`utilities/` = infra, `analysis/` = the
  researcher's code, never the reverse).
- Testing expectations (fast local tests against the synthetic fixture).
- A finish-checklist (tests pass, no data/secrets staged, hooks installed).
- The "agent chat renders as plain text — no LaTeX" note.

Drops: ADRs, insights log, REVIEW_LOG.

## 8. README / prose voice (hard constraint)

`README.md` and `GETTING_STARTED.md` must read as **human-written**: plain,
direct, technical-colleague register. No marketing cadence, no "comprehensive /
seamless / robust / whether-you're-X-or-Y," no emoji-bulleted feature grids, no
symmetrical tricolons. Short, specific, slightly terse. The README states what
the repo is, shows the air-gap diagram, and points to `GETTING_STARTED.md`.

## 9. Open caveats (carry into implementation, not blockers)

1. **`workspace.py` generalization** — `wb` discovery + loosened bucket
   matching, "VERIFY/ADAPT" marker. Validate with Shawn in a fresh VM/workspace.
2. **Eunomia fetch** — `setup_data.R` depends on the `Eunomia` R package and a
   one-time network fetch (Eunomia caches it). Confirm the dataset it pulls is
   small enough to build quickly; pin the Eunomia dataset/version for
   reproducibility. No licensed data is committed, so there is no redistribution
   caveat.
3. **R dependency management** — assume base R + a few CRAN packages (`DBI`,
   `duckdb`, `bigrquery`, `Eunomia`), documented in `GETTING_STARTED`. Mention
   `renv` as optional; do not commit the template to it.
4. **SQL dialect drift** — keep demo SQL ANSI-simple so one query runs on both
   DuckDB and BigQuery. Document where dialects diverge if a real analysis needs
   backend-specific SQL.

## 10. Non-goals

- No Spark, topic modeling, phenotyping, dashboard, eval/NPMI, or
  checkpoint/resume machinery.
- No cookiecutter/templating engine — it is a plain repo you copy.
- No Terra / AoU Researcher Workbench support in v1 (Verily Workbench only).
- Not a published package — it is a starting-point repo.
