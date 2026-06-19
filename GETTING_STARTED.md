# Getting started

This walks the whole loop once, on synthetic data, before you touch any real
data. A colleague can read it top to bottom; or open it with Claude and ask it
to walk you through.

## 1. Install

You need Python 3.10+ and R. Then:

```
make install            # Python infra + dev tools
make precommit-install  # git hooks that block data/secrets and strip notebooks
```

Install the R packages the demo uses:

```
R -e 'install.packages(c("DBI","duckdb","bigrquery","Eunomia","digest","yaml"), repos="https://cloud.r-project.org")'
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

This runs experiment `0001-demo`: a t-test of per-person condition counts
between the two most populous gender groups (labeled from the `concept` table),
plus one aggregate plot. Look at what it wrote:

- `experiments/0001-demo/runs/summary.md` — the scrubbed record. This is what's
  safe to copy back. Notice it has the t-test and CI, but no per-person rows.
- `experiments/0001-demo/runs/demo_effect.png` — an aggregate-only plot.

The query in `experiments/0001-demo/demo_cohort.sql` returns per-person rows,
but those stay inside the R process; only aggregates are printed, so only
aggregates land in `summary.md`. That's the safety model in miniature.

## 4. The same code in AoU

Inside Verily Workbench, after pulling this repo:

```
make setup-workspace    # installs R run-path packages (binaries) + discovers
                        #   your project/CDR/buckets into .workspace_env
source .workspace_env
make run-exp ID=1
```

`setup-workspace` installs the R packages the BigQuery path needs (`DBI`,
`bigrquery`, `digest`, `yaml`) — only the missing ones, as precompiled binaries
via Posit Package Manager when your image's distro is detected. So the manual
`install.packages` in step 1 is the laptop set; in AoU you don't need to run it.

`pick_connection()` (in `framework/shared/utilities.R`) sees `WORKSPACE_CDR` is
set and connects to BigQuery instead of DuckDB — the same `demo_cohort.sql` runs
against the real CDR. Review `experiments/0001-demo/runs/summary.md`, then copy
the aggregate result back to your laptop / the agent.

Note on SQL: the demo SQL is kept simple so one query runs on both DuckDB and
BigQuery. A real analysis may need dataset-qualified table names in BigQuery;
adjust the SQL for the AoU path if so.

## 5. Your own experiment

```
make new-exp SLUG=my-question
```

This creates `experiments/NNNN-my-question/` with a `config.yaml` and `README.md`.
Edit the config to point `entrypoint` at your script (which you put in the same
folder or anywhere repo-relative), and `make run-exp`.

## Plots and the air-gap

A plot is a binary file you can't line-scrub, so treat it carefully: only ever
plot aggregates (means, distributions, counts), never one mark per person, and
look at any plot before you bring it out of the workbench.
