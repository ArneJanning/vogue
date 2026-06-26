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
