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
- When inspecting per-person data interactively, reduce to an aggregate first
  (e.g. group counts or means) rather than printing raw rows — the scrubber drops
  a `person_id` header line but cannot catch the bare numeric rows beneath a raw
  `print(df)` or `df.show()`.

## Prefer the runner

Run analyses through `make run-exp` (which calls scripts/run_experiment.py).
It streams output live but writes only a *scrubbed* copy to
`runs/<exp>/summary.md`. That scrubbing — `utilities/sanitize.py` — is what
makes the paste-back step trustworthy. If you add output that prints anything
per-person, extend `PATIENT_PATTERNS` there. Experiment `entrypoint` values must
be repo-relative paths (not absolute), since the runner records them verbatim
into the committed `summary.md`.

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
