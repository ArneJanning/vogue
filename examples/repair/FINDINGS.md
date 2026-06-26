# Findings: the "repair turn", coded (2026-06-26)

A real run of the full pipeline on `repair`, GEPRIS + OpenAlex, `keep_fields: [humanities]`.

**Coder caveat:** the 30 records were coded by an AI agent reading titles/abstracts against the
codebook, not by a domain expert. Borderline calls (noted in `codings/repair.csv`) materially
affect counts this small. Treat this as a worked demonstration, not a validated result.

## The funnel (what the tool reports)

```
GEPRIS    raw=876   → discipline=14 → coded=14 → trope=1  adjacent=2  homonym=4  literal=3  unsure=4
OpenAlex  raw=1000  → discipline=16 → coded=16 → trope=5  adjacent=0  homonym=11 literal=0  unsure=0
```

- **GEPRIS humanities-strict is almost empty of the trope.** Of 14 humanities `Reparatur`
  projects, the repair *turn* proper is ~1 (a borderline lifecycle-of-antiquity study), plus 2
  adjacent (maintenance/`Wartung`; "Fixing Futures"). The rest are conversation-analytic or
  syntactic `repair` (homonym, 4), literal archaeology (3), or unclear (4).
- **OpenAlex's humanities hits are dominated by a different homonym.** 11 of 16 are the
  conversation-analysis canon (Schegloff et al.). The 5 genuine trope hits cluster at **2002**
  (narrative repair / social repair / transitional justice) and **2014** (Jackson, *Rethinking
  Repair* — the STS maintenance-and-repair turn).

## Lead-lag: not estimable

```
vogue leadlag … --lead openalex:coded_trope --lag gepris:coded_trope
→ "insufficient overlapping data for a lead-lag estimate"
```

The coded trope series are `OpenAlex {2002: 3, 2014: 2}` and `GEPRIS {2022: 1}`. No overlapping
years, fewer aligned pairs than `MIN_PAIRS`. **The tool refuses to produce a number** — correctly.

What the raw shape weakly suggests (an anecdote, not an estimate): the publication trope-nodes
(2002, 2014) precede the single GEPRIS humanities funding instance (2022), i.e. publication
fashion appears to lead funding. With N=1 on the funding side this cannot be quantified, and the
tool declines to dignify it with a lag.

## Why it is thin, and what a real study needs

1. **`keep_fields: [humanities]` is too strict for this trope.** The repair turn lives largely in
   the *social sciences / anthropology*; the strict humanities filter (14) excludes the broader
   GSW set (~40, incl. empirical social research and architecture) where more of it sits. That the
   repair turn is barely a *humanities* phenomenon is itself a finding.
2. **OpenAlex was relevance-sampled** (top 1000 by relevance), so it over-represents the most-cited
   papers — the CA classics and the two famous *Rethinking Repair* hits — and is not
   year-representative. A year-stratified fetch (per `publication_year` filter) is required.
3. **Sample too small and singly-coded.** Hundreds of records, expert coders, and inter-coder
   reliability would be needed before a lead-lag over enough overlapping years could be trusted.

## The point

Run for real, the tool did exactly what it was built to do: it refused to mistake a word for a
thought (raw 876/1000 → coded 1/5 trope), and then refused to mistake noise for a finding
(no lead-lag from thin, biased series). The honest output of a serious attempt to measure the
repair turn's lead is: *the data does not support the claim yet — and here is precisely why.*
