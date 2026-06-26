import re
from typing import Iterator
import httpx
from vogue.model import Record, Field
from vogue.sources.base import PageCache
from vogue.disciplines.classify import Classifier

BASE = "https://gepris.dfg.de/gepris/OCTOPUS"
_TAGS = re.compile(r"<[^>]+>")
_COUNT = re.compile(r'data-result-count="([\d.]+)"')
_ENTRY = re.compile(r"<!-- eintrag -->")
_H2 = re.compile(r'<h2><a href="/gepris/projekt/(\d+)">(.*?)</a>', re.S)
_DISC = re.compile(r'(?:Fachkollegium|Fachliche Zuordnung)</span> <span class="value">([^<]*)')
_VERF = re.compile(r'DFG-Verfahren</span> <span class="value">([^<]*)')
_YEAR = re.compile(r'F\xf6rderung</span> <span class="value2">([^<]*)')


def result_count(html: str) -> int:
    m = _COUNT.search(html)
    return int(m.group(1).replace(".", "")) if m else 0


def parse_results(html: str, classifier: Classifier | None = None) -> list[Record]:
    clf = classifier or Classifier.default()
    out: list[Record] = []
    for part in _ENTRY.split(html):
        mt = _H2.search(part)
        if not mt:
            continue
        pid = mt.group(1)
        title = _TAGS.sub("", mt.group(2)).strip()
        md = _DISC.search(part)
        disc = md.group(1).strip() if md else ""
        mv = _VERF.search(part)
        verf = mv.group(1).strip() if mv else ""
        my = _YEAR.search(part)
        year = None
        if my:
            ym = re.search(r"(19|20)\d\d", my.group(1))
            year = int(ym.group(0)) if ym else None
        out.append(Record(
            source="gepris", id=pid, title=title, year=year,
            discipline_raw=disc, field=clf.classify(disc),
            work_type=verf, url=f"https://gepris.dfg.de/gepris/projekt/{pid}",
        ))
    return out


class GeprisSource:
    name = "gepris"

    def __init__(self, cache: PageCache, classifier: Classifier | None = None,
                 client: httpx.Client | None = None, delay: float = 0.1):
        self.cache = cache
        self.classifier = classifier or Classifier.default()
        self.client = client or httpx.Client(
            headers={"User-Agent": "vogue (research; +https://github.com/)"}, timeout=40)
        self.delay = delay

    def _params(self, term: str, index: int) -> dict:
        return {"context": "projekt", "findButton": "historyCall", "hitsPerPage": "10",
                "index": str(index), "keywords_criterion": term, "task": "doSearchSimple"}

    def _page(self, term: str, index: int) -> str:
        def fetch() -> str:
            r = self.client.get(BASE, params=self._params(term, index),
                                follow_redirects=True)
            r.raise_for_status()
            return r.text
        return self.cache.get_or_fetch(self.name, term, index, fetch)

    def count(self, term: str) -> int:
        return result_count(self._page(term, 0))

    def search(self, term: str) -> Iterator[Record]:
        import time
        total = self.count(term)
        index = 0
        seen: set[str] = set()
        while index < total:
            for rec in parse_results(self._page(term, index), self.classifier):
                if rec.id not in seen:
                    seen.add(rec.id)
                    yield rec
            index += 10
            if index < total:
                time.sleep(self.delay)
