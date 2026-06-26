from pathlib import Path
import httpx
from vogue.model import Field
from vogue.sources.base import PageCache
from vogue.sources.openalex import OpenAlexSource, parse_work, reconstruct_abstract

WORK = {
    "id": "https://openalex.org/W42",
    "display_name": "Cultures of Repair",
    "publication_year": 2021,
    "type": "article",
    "primary_topic": {"field": {"display_name": "Arts and Humanities"}},
    "abstract_inverted_index": {"Repair": [0], "as": [1], "practice": [2]},
}


def test_parse_work_maps_fields():
    r = parse_work(WORK)
    assert r.source == "openalex"
    assert r.id == "W42"
    assert r.title == "Cultures of Repair"
    assert r.year == 2021
    assert r.discipline_raw == "Arts and Humanities"
    assert r.field is Field.HUMANITIES
    assert r.work_type == "article"
    assert r.url == "https://openalex.org/W42"
    assert r.abstract == "Repair as practice"


def test_parse_work_missing_topic_is_unknown():
    w = {"id": "https://openalex.org/W7", "display_name": "X", "publication_year": None,
         "type": "article", "primary_topic": None, "abstract_inverted_index": None}
    r = parse_work(w)
    assert r.discipline_raw == ""
    assert r.field is Field.UNKNOWN
    assert r.abstract is None


def test_reconstruct_abstract_orders_by_index():
    inv = {"b": [1], "a": [0], "c": [2, 4], "d": [3]}
    assert reconstruct_abstract(inv) == "a b c d c"


def _mock_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")

        def w(i):
            return {"id": f"https://openalex.org/W{i}", "display_name": f"t{i}",
                    "publication_year": 2020, "type": "article",
                    "primary_topic": {"field": {"display_name": "Arts and Humanities"}},
                    "abstract_inverted_index": None}
        if cursor == "*":
            return httpx.Response(200, json={"meta": {"count": 3, "next_cursor": "C2"},
                                             "results": [w(1), w(2)]})
        if cursor == "C2":
            return httpx.Response(200, json={"meta": {"count": 3, "next_cursor": "C3"},
                                             "results": [w(3)]})
        return httpx.Response(200, json={"meta": {"count": 3, "next_cursor": None}, "results": []})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_count_reads_meta(tmp_path: Path):
    src = OpenAlexSource(PageCache(tmp_path), client=_mock_client(), delay=0)
    assert src.count("repair") == 3


def test_search_pages_by_cursor_and_dedupes(tmp_path: Path):
    src = OpenAlexSource(PageCache(tmp_path), client=_mock_client(), delay=0)
    recs = list(src.search("repair"))
    assert [r.id for r in recs] == ["W1", "W2", "W3"]
    assert all(r.source == "openalex" for r in recs)
