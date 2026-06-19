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

- `framework/utilities/` — the Python that makes the loop safe and repeatable:
  output scrubbing, layered run config, a language-agnostic runner, workspace setup.
- `experiments/` — each experiment is a self-contained folder with its config,
  analysis scripts, and a gitignored `runs/` output directory.
- `framework/shared/utilities.R` — shared R helpers (`pick_connection`, `hash_id`).

## Using this template

This is a GitHub template repository. Click **Use this template** to create your
own study repo from it — a clean copy with its own history, not a fork. Then
rename the project in `pyproject.toml` and work through `GETTING_STARTED.md`, or
open it with Claude and say "walk me through getting started."

The shipped `0001-demo` experiment is a worked example you run once to see the
loop; keep it as a reference or replace it with your own.
