# vogue

Track the **Begriffskonjunktur** — the rise-and-fall lifecycle of a scholarly concept ("trope") — across funded research and publications.

> **Status: v0.1, in progress.** GEPRIS source + human coding are implemented and tested. OpenAlex source and the analysis/plotting layer are next. APIs may still change.

## Why

A *trope is not a word*. The same string (`repair`) indexes a fashionable STS gesture, a 50-year-old conversation-analytic term, and a literal activity in archaeology — and across all disciplines is ~98% biomedical/engineering noise. A naive keyword count measures molecular biology, not intellectual fashion.

`vogue` makes the reduction explicit and honest:

```
raw hits  →  discipline filter  →  human coding  →  the count that means something
  1955    →        40           →      ~13        →   "the repair turn"
```

**Design invariant:** the headline figure is always the *coded* count, never the raw word count, and every figure can show the full funnel.

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
  study.yaml          # name, enabled sources, fields to keep (default [humanities])
  terms.yaml          # the terms to track
  disciplines.yaml    # optional discipline-mapping overrides
  cache/              # raw fetched responses (git-ignored; snapshot-freezable)
  codings/<term>.csv  # human labels: trope | adjacent | homonym | literal | unsure
  out/                # generated tables and figures
```

Everything but `cache/` is plaintext and git-tracked, so a study is a citable, reproducible artifact.

## CLI (so far)

```bash
uv run vogue funnel my-study --source gepris --term repair   # raw -> discipline
uv run vogue code   my-study --source gepris --term repair   # interactively label the residue
uv run vogue tally  my-study --source gepris --term repair   # raw -> discipline -> coded, by label
```

## Documentation

- Design spec: [`docs/superpowers/specs/2026-06-26-vogue-design.md`](docs/superpowers/specs/2026-06-26-vogue-design.md)
- Implementation plans: [`docs/superpowers/plans/`](docs/superpowers/plans/)

## License

Code: MIT. Shipped data/codings: CC-BY-4.0.
