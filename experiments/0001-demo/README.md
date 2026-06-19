---
status: pending
created: 2026-06-19
---

# Experiment 0001 — demo

## Intent
End-to-end demonstration of the safe-run loop. Asks a deliberately simple
question against OMOP tables: does the mean number of recorded condition
occurrences per person differ between the two most populous gender groups?
Runs locally against the Eunomia synthetic dataset and, unchanged, in AoU
against the CDR. Produces a Welch t-test and one aggregate-only plot — both safe
to carry back across the air-gap.

## Results
<after `make run-exp ID=1`, paste the scrubbed experiments/0001-demo/runs/summary.md here>

## Interpretation
<aggregate t-test result and what it shows about the loop, not the biology>
