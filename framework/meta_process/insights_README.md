# Modeling & Experimental Insights

Numbered by date: `YYYY-MM-DD-<slug>.md`. Insights record *empirical* findings —
what was learned by running the system, not by designing it: a failure mode, a
metric that measures something other than its name, a default that only holds in
one data regime. They complement ADRs, which record forward-looking *decisions*;
insights are backward-looking *observations*.

Create one with `make new-insight SLUG=<slug>`. Format skeleton:

    # YYYY-MM-DD — Short Title
    **Date:** YYYY-MM-DD
    **Topic:** <area>
    **Status:** Observed | Confirmed | Tentative | Refuted by <YYYY-MM-DD-slug>

    [Narrative: the finding, the mechanism (why), the implications.]

    **Setting context:** the regime it was observed in (dataset, sample, key
    parameters), detailed enough that a future reader can judge whether it
    generalizes or was regime-specific.

Always include the setting context — an empirical claim quoted without its regime
is a trap. A later insight can revisit or overturn an earlier one; mark the old
one "Refuted by <filename>" rather than deleting it, so the trajectory of what
was believed and when stays legible.
