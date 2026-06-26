from collections import Counter
from dataclasses import dataclass, field as dfield
from vogue.model import Record
from vogue.coding import Coding, Label, CodingStore
from vogue.study import Study
from vogue.pipeline import fetch_term, funnel_for_records, _source_for


def year_counts_of_records(records: list[Record]) -> Counter:
    return Counter(r.year for r in records if r.year is not None)


def coded_year_counts(records: list[Record], codings: dict[str, Coding],
                      label: Label) -> Counter:
    by_key = {r.key: r for r in records}
    c: Counter = Counter()
    for key, cod in codings.items():
        if cod.label is label and key in by_key and by_key[key].year is not None:
            c[by_key[key].year] += 1
    return c


@dataclass
class Overlay:
    term: str
    series: dict[str, dict[int, int]] = dfield(default_factory=dict)

    def years(self) -> list[int]:
        ys: set[int] = set()
        for ser in self.series.values():
            ys.update(ser)
        return sorted(ys)


def build_overlay(study: Study, term: str, limit: int | None = None,
                  openalex_raw: bool = True) -> Overlay:
    """Assemble per-year series (option C): discipline + coded-trope per source,
    plus OpenAlex raw lexical-prevalence curve."""
    ov = Overlay(term=term)
    for source in study.sources:
        records = fetch_term(study, source, term, limit=limit)
        kept = funnel_for_records(records, study.keep_fields).kept
        codings = CodingStore(study.codings_dir / f"{term}.csv").load()
        ov.series[f"{source}:discipline"] = dict(year_counts_of_records(kept))
        ov.series[f"{source}:coded_trope"] = dict(
            coded_year_counts(kept, codings, Label.TROPE))
        if source == "openalex" and openalex_raw:
            ov.series[f"{source}:raw"] = _source_for(source, study).counts_by_year(term)
    # drop empty series so the report/figure stay clean
    ov.series = {k: v for k, v in ov.series.items() if v}
    return ov


def render_report(overlay: Overlay, figure_name: str) -> str:
    """Markdown report: a header, the embedded figure, and a year x series table.
    The headline is always the coded count — raw series are labeled as raw."""
    years = overlay.years()
    names = list(overlay.series)
    lines = [f"# {overlay.term}", "", f"![{overlay.term} normalized curves]({figure_name})", ""]
    if years:
        lines.append("| year | " + " | ".join(names) + " |")
        lines.append("|---|" + "|".join(["---"] * len(names)) + "|")
        for y in years:
            cells = " | ".join(str(overlay.series[n].get(y, 0)) for n in names)
            lines.append(f"| {y} | {cells} |")
    else:
        lines.append("_No data._")
    lines += ["", "Series ending in `:raw` are raw word-prevalence counts (uncoded); "
              "`:coded_trope` are human-coded trope counts; `:discipline` are "
              "discipline-filtered counts. The honest figure is the coded one."]
    return "\n".join(lines) + "\n"


MIN_PAIRS = 4  # minimum aligned year-pairs to trust a correlation at a given lag


def detrend(values: list[float], method: str) -> list[float]:
    """Remove the level/trend so cross-correlation sees shape, not shared growth."""
    if method == "none":
        return list(values)
    if method == "peak":
        m = max(values) if values else 0
        return [v / m for v in values] if m else list(values)
    if method == "diff":
        return [values[i] - values[i - 1] for i in range(1, len(values))]
    if method == "zscore":
        n = len(values)
        if n == 0:
            return []
        mu = sum(values) / n
        sd = (sum((v - mu) ** 2 for v in values) / n) ** 0.5
        return [(v - mu) / sd for v in values] if sd > 0 else [0.0] * n
    raise ValueError(f"unknown detrend method: {method}")


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return 0.0
    return cov / (vx * vy) ** 0.5


@dataclass
class LeadLag:
    best_lag: int           # +k => series b leads series a by k years
    best_corr: float
    profile: dict[int, float]
    method: str
    n_pairs: int            # aligned year-pairs at best_lag


def cross_correlate(a: dict[int, int], b: dict[int, int],
                    max_lag: int = 8, method: str = "zscore") -> LeadLag | None:
    """Best lag k maximizing corr(a[y], b[y-k]) over detrended, year-aligned series.
    Positive best_lag means b precedes a (b leads a) by that many years. None if too thin."""
    if not a or not b:
        return None
    a_years = range(min(a), max(a) + 1)
    b_years = set(range(min(b), max(b) + 1))
    profile: dict[int, float] = {}
    pairs_at: dict[int, int] = {}
    for k in range(-max_lag, max_lag + 1):
        xs, ys = [], []
        for y in a_years:
            if (y - k) in b_years:
                xs.append(a.get(y, 0))
                ys.append(b.get(y - k, 0))
        dx, dy = detrend(xs, method), detrend(ys, method)
        if len(dx) >= MIN_PAIRS:
            profile[k] = pearson(dx, dy)
            pairs_at[k] = len(xs)
    if not profile:
        return None
    best = max(profile, key=lambda k: profile[k])
    return LeadLag(best_lag=best, best_corr=profile[best], profile=profile,
                   method=method, n_pairs=pairs_at[best])
