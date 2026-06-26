# vogue — Design Spec

**Date:** 2026-06-26
**Status:** Approved design, pre-implementation
**Working title / package:** `vogue` (import name `vogue`; if the PyPI name is taken, distribute as `vogue-tracker` with import name `vogue`)

## 1. Purpose

`vogue` measures the **Begriffskonjunktur** — the rise-and-fall lifecycle of a scholarly concept ("trope") — across funded research and publications. It is built for the sociology of science / STS community as an installable, documented, reproducible open-source tool.

The motivating finding: a *trope is not a word*. The same string (`repair`) indexes a fashionable STS gesture, a 50-year-old conversation-analytic terminus, and a literal activity in archaeology — and is, across all disciplines, ~98% biomedical/engineering noise. A naive keyword count measures molecular biology, not intellectual fashion. Isolating the real trope requires (a) a discipline filter and (b) human reading of the residue.

**Design invariant:** `vogue` never reports a "trope count" derived from words alone. The headline figure is always the *coded* count, and every figure can display the funnel so the reduction `word → discipline → trope` stays visible. This is an architectural commitment, not merely a feature.

## 2. Scope

- **v0.1:** Two sources at launch — **GEPRIS** (DFG funded projects) and **OpenAlex** (publications). Funnel, human coding, analysis including funding-vs-publication lead-lag, plus the `repair` study shipped as a worked example.
- **v0.2:** Optional LLM-assisted pre-classification (`suggest`).
- **Later:** Web UI for coding, layered over the same plaintext files.

Out of scope for now: Crossref, Google Books Ngrams, multi-user/hosted services.

## 3. Core decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Audience | Published open-source tool (pip-installable, documented) |
| Disambiguation | Funnel + human coding as a first-class step; LLM pre-classification an optional plugin whose output is always human-confirmed and stored in plaintext |
| Sources | GEPRIS **and** OpenAlex from the start |
| Architecture | "Study-as-directory" + CLI + library; plaintext is the source of truth; DuckDB only as an analysis engine over the files; web UI deferred |
| Discipline granularity | **Two levels kept**: fine `discipline_raw` (first-class, queryable/facetable) **and** coarse normalized `field` |

## 4. Record schema (common denominator)

A pydantic v2 model that every source normalizes to:

| Field | Type | Notes |
|---|---|---|
| `source` | str | `"gepris"` \| `"openalex"` |
| `id` | str | source-native id |
| `key` | str | derived, stable: `f"{source}:{id}"` |
| `title` | str | |
| `year` | int \| None | GEPRIS: funding start year; OpenAlex: publication year |
| `discipline_raw` | str | fine source discipline (e.g. GEPRIS Fachkollegium/Fachliche Zuordnung; OpenAlex `primary_topic.field`) — **retained and first-class** |
| `field` | enum | normalized coarse field: `humanities \| social \| life \| phys \| eng \| other \| unknown` |
| `work_type` | str | project type (DFG-Verfahren) or publication type |
| `url` | str | |
| `abstract` | str \| None | OpenAlex (from inverted index); usually absent for GEPRIS |
| `raw` | dict | original payload, for re-derivation without re-fetching |

## 5. Study layout (source of truth, git-tracked except `cache/`)

```
my-study/
  study.yaml          # name, enabled sources, fields-to-keep (e.g. [humanities, social])
  terms.yaml          # terms, each with optional per-source query overrides + notes
  disciplines.yaml    # mapping overrides; shipped defaults cover GEPRIS + OpenAlex
  cache/              # raw fetches, per source+term+query, date-stamped; snapshot-freezable
  codings/<term>.csv  # key, term, label{trope|homonym|literal|unsure}, suggested, coder, coded_at, note
  out/                # generated tables + figures
```

A study is therefore a citable, version-controllable artifact. `cache/` is reproducibility scaffolding (raw responses); a frozen snapshot can be committed for archival citation.

## 6. Module map

```
vogue/
  sources/
    base.py        # Source protocol; Record model; pagination/cache/rate-limit helpers
    gepris.py      # HTML scrape + parse -> Record
    openalex.py    # REST /works + parse -> Record
    registry.py    # name -> Source
  disciplines/
    classify.py    # discipline_raw -> field, via YAML mappings (defaults + study overrides)
  study.py         # load/validate a study dir (pydantic); path resolution
  pipeline.py      # fetch; funnel stages A(raw) -> B(discipline) -> C(coded)
  coding.py        # coding store (CSV); idempotent surfacing of uncoded; codebook
  suggest/         # v0.2: optional LLM pre-classification (off by default)
  analysis.py      # time series; funnel stats; normalization; lead-lag
  plotting.py      # matplotlib figures
  cli.py           # typer CLI
tests/             # recorded HTTP fixtures per source
examples/repair/   # the repair study, runnable end-to-end
```

### Source protocol
```python
class Source(Protocol):
    name: str
    def count(self, term: str, **filters) -> int: ...
    def search(self, term: str, **filters) -> Iterator[Record]: ...
```
Each adapter owns its pagination, polite rate-limiting, and on-disk caching of raw responses.

## 7. Pipeline / funnel

- **`fetch`** — for each term × enabled source: query, paginate, cache raw responses, normalize to records. Polite rate-limiting; resumable from cache.
- **Funnel** — Stage A (raw) → Stage B (discipline filter: keep records whose `field` ∈ study's keep-set) → Stage C (coded: join with `codings/`).
- **`code`** — surfaces Stage-B records lacking a label; shows title / discipline_raw / year / url; one keystroke assigns `trope|homonym|literal|unsure`. **Idempotent**: each run only surfaces new records; reports "X new to code, Y already coded." Appends to `codings/<term>.csv`.
- **`suggest`** (v0.2) — fills the `suggested` column via a configurable LLM provider (rule-based fallback). `code` then offers the suggestion as default (Enter = accept). Suggestion and human label are stored in separate columns so provenance is auditable; model id + timestamp recorded.

## 8. Analysis outputs

- **Funnel report** per term: raw N → discipline-filtered N → trope-coded N (counts + %). (Repair: 1955 → 40 → ~13.)
- **Time series** at each funnel stage; normalization selectable: absolute, share-within-study, or vs a baseline series (to control the database/funding growth confound).
- **Cross-source lead-lag**: GEPRIS funding-start-year vs OpenAlex publication-year, overlaid; cross-correlation peak estimates "publications lead funding by ~k years." This is the analysis that makes the acceleration thesis testable — funding start-years alone are right-censored.
- **`report`** — one command emits Markdown with embedded figures + funnel tables, paste-ready for a paper.
- Exports: tidy CSV/Parquet; figures as PNG/SVG.

## 9. Source specifics

### GEPRIS
- HTML scrape of `gepris.dfg.de/gepris/OCTOPUS` simple search; 10 results/page (the view that carries the discipline field); cursor via `index`.
- Per result: title (from `<h2>`), discipline (`Fachkollegium` **or** `Fachliche Zuordnung`), `DFG-Verfahren`, funding year string.
- Year parsing handles `in YYYY` / `von X bis Y` / `Seit Y` → start year.
- Thousands separator (`1.234`) handled in result-count parsing.
- Caching + politeness; dedupe across term variants by `id`.

### OpenAlex
- REST `/works`, cursor pagination, `search=<term>`, `filter=publication_year:…`; polite pool via `mailto`. No API key.
- Discipline via `primary_topic.field` (+ `concepts` fallback) → `field`. Abstract reconstructed from `abstract_inverted_index`.
- Caveat: OpenAlex `search` is broad → discipline filter + human coding are *even more* necessary here.

## 10. Disambiguation philosophy (invariant, restated)

The tool's headline number is the **coded** count. Word-level and discipline-level counts exist only as funnel stages, always shown alongside the coded figure. The codebook (label definitions for `trope/homonym/literal/unsure`) ships in the repo and is part of any study's citable record.

## 11. Testing & reproducibility

- Recorded HTTP fixtures (saved real responses) → parser tests run deterministically and offline.
- Tests: discipline mapping; coding idempotency; analysis golden-files; year/count parsing edge cases.
- Cache + dated snapshots for citability.
- CI (GitHub Actions): lint (ruff) + pytest.

## 12. Stack & packaging

Python ≥ 3.11 · httpx · pydantic v2 · typer · pandas · duckdb (analysis over CSV/Parquet) · matplotlib · pytest · ruff. Packaging via hatch / `pyproject.toml`. Licenses: MIT (code) + CC-BY-4.0 (shipped data/codings). Docs: README + the runnable `examples/repair/` study.

## 13. Release roadmap

- **v0.1** — GEPRIS + OpenAlex, funnel, coding, analysis incl. lead-lag, repair example, tests, CI.
- **v0.2** — LLM `suggest` plugin.
- **Later** — web UI over the same files; additional sources (Crossref, Ngrams).
