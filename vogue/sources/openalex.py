import json
import time
from typing import Iterator
import httpx
from vogue.model import Record
from vogue.disciplines.classify import Classifier
from vogue.sources.base import PageCache


def reconstruct_abstract(inverted: dict | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text in order."""
    if not inverted:
        return None
    pos: dict[int, str] = {}
    for word, idxs in inverted.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos)) or None


def parse_work(work: dict, classifier: Classifier | None = None) -> Record:
    clf = classifier or Classifier.default()
    wid = work["id"].rsplit("/", 1)[-1]
    topic = work.get("primary_topic") or {}
    disc = ((topic.get("field") or {}).get("display_name")) or ""
    return Record(
        source="openalex",
        id=wid,
        title=work.get("display_name") or "",
        year=work.get("publication_year"),
        discipline_raw=disc,
        field=clf.classify(disc),
        work_type=work.get("type") or "",
        url=work["id"],
        abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
        raw=work,
    )


BASE = "https://api.openalex.org/works"


class OpenAlexSource:
    name = "openalex"

    def __init__(self, cache: PageCache, classifier: Classifier | None = None,
                 client: httpx.Client | None = None, mailto: str = "vogue@example.org",
                 per_page: int = 200, delay: float = 0.1):
        self.cache = cache
        self.classifier = classifier or Classifier.default()
        self.client = client or httpx.Client(
            headers={"User-Agent": "vogue (research)"}, timeout=40)
        self.mailto = mailto
        self.per_page = per_page
        self.delay = delay

    def _page(self, term: str, cursor: str, page_index: int) -> dict:
        def fetch() -> str:
            r = self.client.get(BASE, params={
                "search": term, "per-page": self.per_page,
                "cursor": cursor, "mailto": self.mailto})
            r.raise_for_status()
            return r.text
        return json.loads(self.cache.get_or_fetch(self.name, term, page_index, fetch, ext="json"))

    def count(self, term: str) -> int:
        return self._page(term, "*", 0)["meta"]["count"]

    def counts_by_year(self, term: str) -> dict[int, int]:
        """Raw publication count per year via OpenAlex group_by (one request, no paging)."""
        def fetch() -> str:
            r = self.client.get(BASE, params={
                "search": term, "group_by": "publication_year", "mailto": self.mailto})
            r.raise_for_status()
            return r.text
        text = self.cache.get_or_fetch(self.name, f"{term}::groupyear", 0, fetch, ext="json")
        data = json.loads(text)
        out: dict[int, int] = {}
        for g in data.get("group_by", []):
            key = str(g.get("key", ""))
            if key.isdigit():
                out[int(key)] = g["count"]
        return out

    def search(self, term: str) -> Iterator[Record]:
        cursor = "*"
        page_index = 0
        seen: set[str] = set()
        while cursor:
            data = self._page(term, cursor, page_index)
            results = data.get("results", [])
            if not results:
                break
            for w in results:
                rec = parse_work(w, self.classifier)
                if rec.id not in seen:
                    seen.add(rec.id)
                    yield rec
            cursor = data["meta"].get("next_cursor")
            page_index += 1
            if cursor and self.delay:
                time.sleep(self.delay)
