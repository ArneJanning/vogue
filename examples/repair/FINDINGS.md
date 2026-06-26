# Findings: the "repair turn", coded (2026-06-26)

A real run of the full pipeline on `repair`, GEPRIS + OpenAlex, run at two scopes:
`keep_fields: [humanities]` and `keep_fields: [humanities, social]`.

**Coder caveat:** the records were coded by an AI agent reading titles/abstracts against the
codebook, not by a domain expert. Borderline calls (noted in `codings/repair.csv`) materially
affect counts this small. Treat this as a worked demonstration, not a validated result.
Coding rule used: **trope** = the *connected* critical repair concept (STS maintenance-and-repair
à la Jackson; moral / social / restorative / narrative repair); **homonym** = separate technical
lineages that merely share the word (conversation-analytic repair, organizational trust/image
repair, repairable-systems reliability, psycholinguistic self-repair, mood/alliance repair);
**adjacent** = care / maintenance / "fixing"; **literal** = physical mending of an object.

## The funnel (what the tool reports)

```
humanities only:
  GEPRIS    raw=876   → discipline=14 → coded=14 → trope=1  adjacent=2  homonym=4  literal=3  unsure=4
  OpenAlex  raw=1000  → discipline=16 → coded=16 → trope=5  homonym=11

humanities + social:
  GEPRIS    raw=876   → discipline=16 → coded=16 → trope=1  adjacent=3  homonym=4  literal=3  unsure=5
  OpenAlex  raw=1000  → discipline=43 → coded=43 → trope=9  homonym=34
```

Broadening to the social sciences roughly **tripled** the OpenAlex trope signal (5 → 9) but added
**zero** GEPRIS trope (still 1). And even at the broader scope, **79 % (34/43)** of OpenAlex
humanities+social `repair` is homonym — the word still overwhelmingly names other things
(conversation-analytic repair, trust/image repair in management, repairable systems in operations
research, psychotherapy "alliance repair"). The discipline filter alone never isolates the trope.

## Coded trope by year

```
OpenAlex coded_trope : {2002: 4, 2006: 1, 2007: 1, 2009: 1, 2014: 2}   (n=9)
GEPRIS   coded_trope : {2022: 1}                                       (n=1)
```

A real publication signature emerges: the critical "repair" concept clusters at **2002**
(restorative / narrative / social repair) and **2006–2009** (Walker's *Moral Repair* and its
uptake), then the STS node at **2014** (Jackson, *Rethinking Repair*).

## Lead-lag: still not estimable — and now we know why

```
vogue leadlag … --lead openalex:coded_trope --lag gepris:coded_trope
→ "insufficient overlapping data for a lead-lag estimate"   (both scopes)
```

The German **funding** side of the repair turn is essentially empty: one coded trope project
(2022), across all of humanities *and* social science. There is no GEPRIS series to lead or lag.
You cannot measure a lead between publication and funding when one side does not exist.

That absence is itself the finding: as far as the DFG record shows, **the repair turn is an
Anglophone *publication* phenomenon that has not (yet) become a German funding line.** The thing
the lead-lag was meant to quantify — publication fashion preceding funding — can be *seen*
(publications 2002–2014, the lone German grant 2022) but not *measured*, because there is barely a
German funding curve at all.

## Why still thin, and what a real study needs

1. **Scope helped on the publication side, not the funding side.** `[humanities, social]` widened
   OpenAlex but the DFG simply has not funded this trope.
2. **OpenAlex was relevance-sampled** (top 1000), so it over-represents the most-cited papers and
   is not year-representative. A year-stratified fetch (per `publication_year`) is required for a
   real curve.
3. **Singly coded by an AI**, small N, borderline-sensitive. Hundreds of records, expert coders,
   and inter-coder reliability would be needed before a lead-lag over enough overlapping years
   could be trusted — and a German funding curve that actually contains the trope.

## The point

Run for real, twice, the tool did exactly what it was built to do: it refused to mistake a word
for a thought (raw 876/1000 → coded 1/9 trope even at the broad scope), and then refused to
mistake noise for a finding (no lead-lag from a funding series that is, for this trope, empty).
The honest output of a serious attempt to measure the repair turn's lead is: *the data does not
support the claim — and here is precisely why.*
