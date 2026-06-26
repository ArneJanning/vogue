from pathlib import Path
from typing import Callable, Iterator, Protocol
import hashlib
from vogue.model import Record


class Source(Protocol):
    name: str
    def count(self, term: str) -> int: ...
    def search(self, term: str) -> Iterator[Record]: ...


class PageCache:
    """On-disk cache of raw responses, keyed by source/term/page. Reproducibility scaffolding."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, source: str, term: str, page: int) -> Path:
        h = hashlib.sha1(term.encode("utf-8")).hexdigest()[:12]
        return self.root / source / f"{h}_{page:05d}.html"

    def get_or_fetch(self, source: str, term: str, page: int, fetch: Callable[[], str]) -> str:
        p = self._path(source, term, page)
        if p.exists():
            return p.read_text(encoding="utf-8")
        text = fetch()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return text
