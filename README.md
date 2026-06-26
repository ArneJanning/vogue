# vogue

Track the **Begriffskonjunktur** — the rise-and-fall lifecycle of a scholarly concept ("trope") — across funded research and publications.

> **Status: v0.2.** v0.1 — GEPRIS (DFG funding) and OpenAlex (publications) sources, discipline filtering, human coding, and the funding-vs-publication overlay — plus detrended **lead-lag estimation** (`vogue leadlag`) and optional **LLM-assisted coding** (`vogue suggest`, via OpenRouter; human-confirmed). 50 tests. APIs may still change.

## Why vogue exists

This tool began in an argument about why so much academic writing had come to feel interchangeable — and why one can often guess a paper's fashionable keyword from its funding source before reading a line.

The suspicion was this. A scholarly field under grant-renewal pressure does not, on the whole, accumulate knowledge; it *rotates* through concepts. Every few years a new master-trope arrives — a "turn," a single suggestive word raised to a paradigm and defined against some strawman of the orthodoxy it claims to overthrow. The mirror, errancy, the material, infrastructure, resilience, repair, care. Each is effectively unfalsifiable — "X is a mirror of our assumptions" can be said of anything; it costs nothing and threatens no one. Each borrows the prestige of a Kuhnian rupture for what is really a product refresh. And each is selected less for explanatory power than for fundability: the word that fits the next call for proposals. This is Simmel's theory of fashion — the dialectic of novelty and recognizability — driving a discipline that has stopped going deeper and learned to go in circles instead, calling the rotation progress.

If that is even partly true, it should be *measurable*. A trope rises, crests, and fades; its lifecycle should be visible in the record of what gets funded and published.

But here is the catch the tool is built around: **a trope is not a word.** Try to measure the "repair turn" by counting the string `repair` and you measure molecular biology — DNA repair, tissue repair, vascular repair — because the humanities are a rounding error in the corpus. Filter to the humanities and the word lies again: in linguistics `repair` is a fifty-year-old technical term for *conversation* repair; in archaeology it is the literal mending of a pot. The fashionable concept — maintenance, care, decolonial repair — is a small residue you can find only by reading each title and judging what it means.

So the honest count is small and hard-won. For DFG-funded `repair`: **1,955 hits → 40 in humanities disciplines → roughly 13 that are actually the trope.**

```
raw hits  →  discipline filter  →  human coding  →  the count that means something
  1955    →        40           →      ~13        →   "the repair turn"
```

The first reduction is mechanical; the last is not. `vogue` makes the whole funnel explicit and reproducible: it fetches, filters by discipline, and then asks a human to code the residue — and it treats that judgment as a first-class, versioned artifact.

**Design invariant:** the headline figure is always the *coded* count, never the raw word count, and every figure can show the reduction that produced it. The one thing the tool refuses to do is the thing the trope-machine does best: mistake a word for a thought.

## Install

Managed with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
uv run pytest -q          # run the test suite
uv run vogue --help       # CLI
```

## A study is a directory

```
my-study/
  study.yaml          # name, enabled sources, fields to keep (default [humanities]), suggest_model
  terms.yaml          # the terms to track
  disciplines.yaml    # optional discipline-mapping overrides
  cache/              # raw fetched responses (git-ignored; snapshot-freezable)
  codings/<term>.csv  # human labels: trope | adjacent | homonym | literal | unsure
  out/                # generated tables and figures (git-ignored)
```

Everything but `cache/` and `out/` is plaintext and git-tracked, so a study is a citable, reproducible artifact. A runnable starter is in [`examples/repair/`](examples/repair/).

## CLI

```bash
uv run vogue funnel  my-study --source gepris --term repair   # raw -> discipline
uv run vogue suggest my-study --source gepris --term repair   # optional: LLM pre-labels (OpenRouter)
uv run vogue code    my-study --source gepris --term repair   # confirm/label the residue (1 keystroke)
uv run vogue tally   my-study --source gepris --term repair   # raw -> discipline -> coded, by label
uv run vogue report  my-study --term repair --limit 2000      # funding-vs-publication overlay + report
uv run vogue leadlag my-study --term repair                   # detrended cross-correlation: does
                                                              # publication fashion precede funding?
```

`suggest` needs `OPENROUTER_API_KEY` (or use `--model rules` for an offline no-op baseline);
the model comes from `suggest_model:` in `study.yaml` (default `z-ai/glm-5.2`) unless `--model`
overrides it, and is recorded per suggestion for provenance. Its proposals are written to a side
file and are never authoritative — `code` shows each as a default you confirm with one keystroke.

The overlay normalizes each series to its own peak, so curves of wildly different magnitude (a dozen funded projects vs. millions of publications) can be compared by *shape* — which is where any lead-lag between publication fashion and funding would show. The `openalex:raw` curve is raw word-prevalence by year (cheap, via `group_by`); `:coded_trope` reflects only what a human has labeled `trope`.

## Limitations

- **GEPRIS exposes project *counts*, not funding amounts.** Verified across project types: DFG
  project pages carry only `DFG-Verfahren`, subject area, funding *period*, and a project id —
  there is no per-grant `Fördersumme`. So funding curves are counts of funded projects per year,
  never euros. (The DFG is aggregate-transparent via the *Förderatlas* but, unlike NIH RePORTER,
  NSF, EU CORDIS or UKRI Gateway to Research, does not publish per-grant amounts — a real
  transparency gap, and itself a datum about the funder.)
- **OpenAlex `search` is broad and relevance-ranked**; a year-stratified fetch is needed for a
  year-representative publication curve (the shipped examples use a capped relevance sample).
- **The trope count is only as good as the coding.** It is human judgment, borderline-sensitive at
  small N; the shipped example codings were done by an AI agent and are demonstrations, not
  validated results.

## Documentation

- Design spec: [`docs/superpowers/specs/2026-06-26-vogue-design.md`](docs/superpowers/specs/2026-06-26-vogue-design.md)
- Implementation plans: [`docs/superpowers/plans/`](docs/superpowers/plans/)

## License

Code: MIT. Shipped data/codings: CC-BY-4.0.
