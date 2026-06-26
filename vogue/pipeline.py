from dataclasses import dataclass, field as dfield
from vogue.model import Record, Field
from vogue.sources.base import PageCache
from vogue.sources.gepris import GeprisSource
from vogue.study import Study


@dataclass
class Funnel:
    raw: int = 0
    discipline: int = 0
    kept: list[Record] = dfield(default_factory=list)


def funnel_for_records(records: list[Record], keep_fields: list[Field]) -> Funnel:
    keep = set(keep_fields)
    kept = [r for r in records if r.field in keep]
    return Funnel(raw=len(records), discipline=len(kept), kept=kept)


def _source_for(name: str, study: Study):
    if name == "gepris":
        return GeprisSource(PageCache(study.cache_dir), classifier=study.classifier())
    raise ValueError(f"unknown source: {name}")


def fetch_term(study: Study, source_name: str, term_name: str) -> list[Record]:
    """Fetch all records for one term from one source (cached)."""
    src = _source_for(source_name, study)
    term = next(t for t in study.terms if t.name == term_name)
    query = term.queries.get(source_name, term.name)
    return list(src.search(query))


def funnel_term(study: Study, source_name: str, term_name: str) -> Funnel:
    return funnel_for_records(fetch_term(study, source_name, term_name), study.keep_fields)
