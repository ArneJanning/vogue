# Findings: "Kulturtechnik", coded (2026-06-26)

The media-theory `Kulturtechnik` of the Siegert/Schüttpelz school, GEPRIS + OpenAlex,
`keep_fields: [humanities, social]`. OpenAlex query: German `Kulturtechniken` (the English
"cultural techniques" is far too generic — 2.1M hits of mostly unrelated phrase use).

**Coder caveat:** coded by an AI agent from titles/abstracts, not a domain expert; small N,
borderline-sensitive. A worked demonstration, not a validated result.

## The funnel

```
GEPRIS    raw=52  → discipline=34 → coded=34 → trope=20  homonym=0  unsure=14
OpenAlex  raw=60  → discipline=51 → coded=51 → trope=36  homonym=8  unsure=7
```

Two homonyms, handled at two different layers:
- The **discipline filter** removed the older *agricultural/civil-engineering* `Kulturtechnik`
  (land melioration, water management) — it classifies as eng/life, so `keep_fields: [humanities,
  social]` drops it for free (GEPRIS homonym=0).
- **Human coding** then removed the residual *pedagogical* `Kulturtechniken` (basic skills —
  literacy/numeracy in education research; OpenAlex homonym=8) from the media-theory concept.

This is the first term where, unlike `repair`, both sources carry a substantial coded trope curve.

## Coded trope by year

```
GEPRIS    {2001:2, 2007:1, 2008:1, 2010:1, 2011:2, 2012:2, 2013:3, 2015:1, 2017:2, 2018:2, 2019:1, 2021:1, 2025:1}
OpenAlex  {2000:2, 2002:3, 2006:1, 2007:1, 2009:1, 2010:2, 2012:4, 2013:6, 2014:3, 2015:1, 2016:3, 2017:3, 2018:1, 2020:1, 2023:3, 2025:1}
```

**Both curves crest at 2013** and fade afterward. This empirically matches the dating of the
Vogl/Siegert/Schüttpelz wave (~2001–2019, peaking early 2010s) — the last German media-theory
"school" proper.

## Lead-lag: computable, but ≈ synchronous and method-sensitive

```
vogue leadlag … --lead openalex:coded_trope --lag gepris:coded_trope
  --method zscore → publications LAG funding by 1 year   (r=0.44, n=24)
  --method diff   → publications LEAD funding by 5 years  (r=0.45, n=21)
```

Unlike `repair` (uncomputable — no German funding curve), here both series exist and overlap, so
the tool returns a number. But the two detrending methods disagree (≈0 vs +5) and both are weak
(r≈0.45) — the honest reading is **roughly synchronous, with no robust publication lead.**

That is itself interpretable. `Kulturtechnik` is a tightly-coupled *national* school: the same
network (Siegert, Schüttpelz, the Weimar/Erfurt/Siegen media-theory milieu) publishes and gets
funded in the same years, so publication and funding move in lockstep — there is no years-long
lead for publication fashion to take over funding, because they are the same people doing both at
once. Contrast `repair`, an Anglophone publication phenomenon with essentially no German funding.

## Across the two studies

- **repair** — Anglophone publication trope (2002 moral/restorative; 2014 STS *Rethinking
  Repair*); German funding ≈ nil → lead-lag *uncomputable*.
- **Kulturtechnik** — German funding *and* publication in lockstep, both peaking 2013 → lead-lag
  *computable but ≈ 0*, weak, method-dependent.

Neither supports a clean "publication fashion leads funding by k years" acceleration story. What
`vogue` does deliver is honest: where the data is empty it refuses a number; where it is thin it
shows the number's fragility (two methods, two answers); and where there is a real wave it
recovers its shape and crest (Kulturtechnik, 2013) — confirming the *existence and timing* of the
last real school without inventing a lead it cannot support.

## Caveats

AI coder; OpenAlex relevance-sampled (`--limit 60`, not year-stratified); small N. The
method-sensitivity of the lead-lag is the honest signal that N is too thin for a confident lag.
A real study needs year-stratified sampling and expert inter-coder reliability.
