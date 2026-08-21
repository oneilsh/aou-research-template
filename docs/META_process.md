# Keeping an agentically-coded repo legible (optional)

A repo developed with heavy AI-agent assistance has a specific failure mode:
**the cost of agent-assisted velocity is that reasoning evaporates faster than
code accumulates.** An agent produces a correct-looking change in seconds, but
the "why" — the alternatives weighed, the empirical result that motivated a
default, the review that vetted it — is gone unless something durable captures
it. Six months later the code is still there and the reasoning is not.

This template ships three lightweight systems that prevent that, plus a fourth
(experiment tracking) that is already built in. **The three here are opt-in** —
a fresh clone carries none of them, and the agent ignores them until you turn
them on. Adopt whichever fit; skip the rest.

## How opt-in works

Each system switches on when its artifact exists, and off when you delete it —
there is no config file. Enable with a `make` target (idempotent):

```
make enable-decisions      # docs/decisions/   (ADRs)
make enable-insights       # docs/insights/    (empirical findings)
make enable-reviews        # docs/REVIEW_LOG.md (walkthrough audit trail)
make enable-meta-process   # all three at once
```

`CLAUDE.md` has a short "Optional meta-process logs" section whose guidance is
written conditionally ("*if `docs/decisions/` exists…*"), so enabling a system
is all it takes for the agent to start maintaining it. To disable, delete the
directory or file.

All entries are **numbered by date** — `YYYY-MM-DD-<slug>.md` — matching this
template's experiment naming, so parallel work on branches never collides.
Cross-references are by filename (there is no short number).

## 1. Decision log — ADRs (`docs/decisions/`)

Records *why* a structural or design choice was made, in dated files. Each
follows a fixed skeleton — **Status / Date / Context / Decision / Alternatives
considered / Consequences** — so the record preserves not just what was chosen
but what was *rejected and why*. That "alternatives" section is the payoff: the
difference between "this is weird, let me rewrite it" and "this is weird
*because* the obvious alternative was tried and broke X."

- Create an entry: `make new-decision SLUG=<slug>`.
- Significant structural or mathematical choices get an ADR **as they land**,
  not reconstructed afterward.
- Edit in place for corrections, but never silently overwrite a past decision.
  When one materially supersedes another, add a dated amendment at the top of
  the old file naming the superseding ADR by filename, and keep the old
  reasoning readable as the historical record.

## 2. Insights log (`docs/insights/`)

Where ADRs record *engineering* decisions, insights record *empirical* findings
— things learned by running the system, not by designing it: a hyperparameter
that traps the optimizer, a metric that measures something other than its name,
a default that only holds in one data regime. Each carries a **Date / Topic /
Status** header and, critically, a **setting context** block recording the
regime it was observed in. An empirical claim quoted without its regime is a
trap; the setting block is what stops the same lesson being re-learned or
misapplied.

- Create an entry: `make new-insight SLUG=<slug>`.
- Always include the setting context; prefer stating the *mechanism* over just
  the observation, so the finding is falsifiable and transferable.
- A later insight can overturn an earlier one — mark the old one "Refuted by
  <filename>" rather than deleting it.

## 3. Periodic walkthroughs + a review log (`docs/REVIEW_LOG.md`)

The human-in-the-loop system that ties the others together. Periodically a
maintainer is walked bottom-up through a slice of the codebase — a guided
reading, not a skim — with the agent doing the exposition and the human
interrogating it. Reading code aloud with intent is where latent bugs actually
surface; fixes ship as in-line detours during the review. Each session is then
recorded as a dated section at the **top** of the review log (newest first):
what was reviewed, what shipped, which pre-existing issues were caught.

- Guided walkthroughs are driven by the **bundled `code-walkthrough` skill**
  (`.claude/skills/code-walkthrough/`) — no install; Claude Code auto-discovers
  it in any clone. Say "walk me through `<area>`" to start; it tracks a
  curriculum across sessions. That curriculum/progress state lives in per-user
  project memory *outside* the repo, so it is never committed and each clone
  starts fresh.
- The `REVIEW_LOG.md` convention stands on its own: even without the skill, a
  human can append entries by hand. Keep entries **dated, newest-first, and
  impersonal** (project-scoped, not per-contributor).

## The fourth system: experiments (already built in)

Experiment *runs* are this template's core loop, not an add-on: `make new-exp
SLUG=<slug>` scaffolds a dated `experiments/YYYY-MM-DD-<slug>/`, and `make
run-exp` dispatches it and captures scrubbed output. See the top-level
`README.md` and `GETTING_STARTED.md`. The three optional systems above make the
*reasoning* around those runs durable the same way the runner makes the runs
themselves durable.
