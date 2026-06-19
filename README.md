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
