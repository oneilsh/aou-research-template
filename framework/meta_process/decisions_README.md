# Architecture Decision Records

Numbered by date: `YYYY-MM-DD-<slug>.md`. Each ADR records *why* a non-obvious
structural or design choice was made — including the alternatives that were
rejected and why — so a puzzling bit of code later resolves to a durable answer
instead of a rewrite.

Create one with `make new-decision SLUG=<slug>`. Format skeleton:

    # YYYY-MM-DD — Short Title
    **Status:** Accepted | Superseded by <YYYY-MM-DD-slug>
    **Date:** YYYY-MM-DD
    ## Context
    ## Decision
    ## Alternatives considered
    ## Consequences

Edit ADRs in place for corrections (fix a link, flip Status), but never silently
overwrite a past decision. When one materially supersedes another, add a dated
amendment at the top of the old file pointing to the superseding ADR, and keep
the old reasoning readable as the historical record. Cross-reference by filename
(there is no short number), e.g. "supersedes 2026-07-01-old-slug".
