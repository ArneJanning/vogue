# Example study: the "repair turn"

A starter study tracking `repair` across GEPRIS (DFG funding) and OpenAlex (publications).

```bash
# raw -> discipline funnel for one source
uv run vogue funnel examples/repair --source gepris --term repair

# interactively label the discipline-filtered residue (the human step)
uv run vogue code examples/repair --source gepris --term repair --coder you

# raw -> discipline -> coded, by label
uv run vogue tally examples/repair --source gepris --term repair

# build the funding-vs-publication overlay + a Markdown report into out/
uv run vogue report examples/repair --term repair --limit 2000
```

`--limit` caps how many records are fetched per source (OpenAlex has millions of `repair`
hits). The overlay's `openalex:raw` curve is the full lexical-prevalence-by-year (cheap, via
`group_by`), while `:coded_trope` reflects only what a human has labeled `trope`. The honest
figure is always the coded one.
