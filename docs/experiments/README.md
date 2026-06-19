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
