# Design: date-slug experiment identity

**Date:** 2026-08-10
**Status:** approved, pending implementation plan

## Problem

Experiments are identified by a zero-padded sequential counter:
`experiments/NNNN-slug/`. The next id is computed as `max(existing) + 1`
([new.py](../../../framework/utilities/cli/new.py) `next_id`). This is not
branch-friendly: two branches taken off `main` each compute the same next
number, so experiments created independently collide on their folder name (and
on the counter) when the branches are later merged. The same problem would hit
any other serially-numbered component, though experiment folders are currently
the only one.

## Goals

In priority order, as established during brainstorming:

1. **Collisions are effectively impossible in a reusable repo** — a user should
   not get bitten by silent duplicates across branches.
2. **A sense of order** — listing experiments and picking "the next one" should
   follow a sensible chronological order, including after merges.
3. **Short and typeable ids** — the id is typed into `make` targets and written
   into READMEs by hand; no long timestamps or sha substrings.
4. The **slug** is the natural disambiguator and should carry that weight.

These goals are in genuine tension: nothing that is both short and
human-chronologically-ordered is mathematically collision-proof without
coordination. The design resolves this with a date prefix (order) + slug
(identity/typeability) + a uniqueness warning (loud detection of the residual).

## Chosen approach

**Folder naming:** `experiments/YYYY-MM-DD-<slug>/` (ISO date prefix). The
`(date, slug)` pair is the experiment's identity. There is no sequential counter
anywhere in the repo.

- **Order** comes from the ISO date prefix. Because ISO dates sort
  lexicographically in chronological order, the existing name-sort in
  `_experiments()` already yields chronological order — across branches, after
  merge — with no logic change.
- **Collision resistance** comes from `(date, slug)`. Two branches collide only
  if they create the *same slug on the same day*. Git blocks that structurally:
  two branches adding the identical path `YYYY-MM-DD-<slug>/` produce a merge
  conflict. Two branches using the same slug on *different* days produce two
  distinct, harmless folders.
- **Typeability**: the CLI selects an experiment by **slug**, not by typing the
  date. The bare integer `--id` is removed.

**Uniqueness rule:** unique `(date, slug)` is enforced by the filesystem (one
branch) and git (across branches). A slug reused on a *different* day is allowed
(a legitimate re-run/iteration). `make test` adds a check that **warns** (does
not fail) when a slug appears under more than one date, listing the offenders,
so accidental twins surface without blocking intentional re-runs.

## Component changes

### `framework/utilities/cli/new.py`
- Remove `next_id()` and the `_DIR_RE` counter regex.
- `scaffold(slug, experiments_dir, template_dir, today)` builds
  `out_dir = experiments_dir / f"{today}-{slug}"`.
- Refuse to scaffold if `out_dir` already exists (clear error, no overwrite).
- Template substitutions become `{date}` and `{slug}` only; `{id}` and
  `{id_padded}` are removed.

### `framework/utilities/runner.py`
- `_DIR_RE` changes from `^(\d{4})-.+$` to a date-prefixed pattern,
  `^(\d{4}-\d{2}-\d{2})-.+$`.
- `_experiments()` keeps sorting by `p.name` (ISO prefix → chronological).
- Replace `find_by_id(experiments_dir, exp_id: int)` with
  `find_by_slug(experiments_dir, slug: str)`, which matches the folder whose
  name after the `YYYY-MM-DD-` prefix equals `slug`. Raise a clear error on zero
  matches; raise a clear error on >1 match (should only happen on same slug,
  different dates) listing the candidates so the user can re-run by full name if
  they truly mean an older one.
- `find_next_pending()` is unchanged apart from the regex (still "first pending
  in sorted order" = earliest-dated pending).

### `framework/utilities/cli/run.py`
- Replace `--id (type=int)` with `--slug (type=str)`.
- `--next` keeps its meaning ("earliest pending"); help text updated from
  "lowest-id" to "earliest pending".
- Dispatch calls `find_by_slug` instead of `find_by_id`.

### `framework/utilities/config.py`
- Update the docstring reference from `experiments/<NNNN-slug>/config.yaml` to
  `experiments/<YYYY-MM-DD-slug>/config.yaml`.

### Uniqueness check
- New fast unit test (or a small helper invoked by an existing `make test`
  target) that scans `experiments/` for slugs (name minus the date prefix)
  appearing under more than one date and emits a warning listing them. It must
  **not** fail the suite. Design note: since `make test` should stay green, this
  is implemented as a test that always passes but prints the warning, or a tiny
  reporting step wired into the `test` target — implementation plan to pick the
  cleaner of the two.

### `experiments/_template/`
- `config.yaml`: `entrypoint` / `sql_file` paths use `{date}-{slug}` instead of
  `{id_padded}-{slug}`.
- `README.md`: heading and body use `{date}` / `{slug}`; drop `{id_padded}`.
  Paths that pointed at `experiments/{id_padded}-{slug}/runs/summary.md` become
  `experiments/{date}-{slug}/runs/summary.md`.

### Existing demo experiment
- Rename `experiments/0001-demo/` → `experiments/2026-06-19-demo/` (its recorded
  `created:` date), preserving all contents (`config.yaml`, `README.md`,
  `demo_cohort.sql`, `demo_effect.R`, `demo_exploration.ipynb`, `runs/`).
- Update the internal `entrypoint` and `sql_file` paths in its `config.yaml`
  from `experiments/0001-demo/...` to `experiments/2026-06-19-demo/...`.
- Update its `README.md` heading/paths accordingly.

### Makefile
- `new-exp` and `run-exp` help/comment text: `--id` → `SLUG=`, and the
  scaffold/run examples reflect date-slug folders.

### Documentation
- `CLAUDE.md`: `experiments/<NNNN-slug>/` → `experiments/<YYYY-MM-DD-slug>/`;
  note that the entrypoint path recorded into `summary.md` is date-slug based.
- `GETTING_STARTED.md`, `README.md`, `framework/docs/DESIGN.md`,
  `framework/docs/IMPLEMENTATION_PLAN.md`: update any `0001-demo` / `NNNN`
  references and the `make run-exp --id` usage to slug-based.

### Tests to update
- `framework/tests/test_new_experiment.py`: drop `next_id` tests; assert
  `scaffold` writes `YYYY-MM-DD-slug`, substitutes `{date}`/`{slug}`, and refuses
  a pre-existing folder.
- `framework/tests/test_runner.py`: replace `find_by_id` tests with
  `find_by_slug` (found, not-found, ambiguous-across-dates); update fixtures
  from `0001-a` to date-slug names.
- `framework/tests/test_cli_run.py`: fixtures and the `--next` invocation use
  date-slug folders; add a `--slug` invocation.
- `framework/tests/test_demo_config.py`: paths point at `2026-06-19-demo`.
- New: the cross-day slug-reuse warning check.

## Out of scope

- No renumbering/migration tooling for historical experiments beyond renaming
  the single existing demo.
- No minute-resolution timestamps (Approach B) — the `(date, slug)` + warning
  combination is sufficient given the slug's disambiguating role.
- No change to run-session timestamps in `summary.md` (already timestamped).

## Success criteria

- `make new-exp SLUG=foo` creates `experiments/<today>-foo/` and refuses a
  duplicate.
- `make run-exp SLUG=foo` runs it; `make run-exp` with `--next` runs the
  earliest-dated pending experiment.
- Two branches off `main` can each create an experiment with a different slug
  (or same slug/different day) and merge with no conflict; identical
  slug-same-day produces a git merge conflict rather than a silent duplicate.
- `make test` passes and prints a warning if any slug is reused across dates.
