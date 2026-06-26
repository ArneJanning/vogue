from vogue.model import Field
from vogue.sources.openalex import parse_work, reconstruct_abstract

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
