from vogue.coding import Label, Coding, CodingStore, uncoded, Suggestion, SuggestionStore
from vogue.model import Record, Field


def _rec(pid):
    return Record(source="gepris", id=pid, title=f"t{pid}", year=2020,
                  discipline_raw="Literaturwissenschaft", field=Field.HUMANITIES,
                  work_type="w", url="u")


def test_append_then_load_roundtrip(tmp_path):
    store = CodingStore(tmp_path / "repair.csv")
    assert store.load() == {}
    store.append(Coding(key="gepris:1", term="repair", label=Label.TROPE, coder="arne"))
    store.append(Coding(key="gepris:2", term="repair", label=Label.HOMONYM))
    loaded = store.load()
    assert set(loaded) == {"gepris:1", "gepris:2"}
    assert loaded["gepris:1"].label is Label.TROPE
    assert loaded["gepris:1"].coder == "arne"
    assert loaded["gepris:2"].label is Label.HOMONYM


def test_coded_keys(tmp_path):
    store = CodingStore(tmp_path / "repair.csv")
    store.append(Coding(key="gepris:1", term="repair", label=Label.TROPE))
    assert store.coded_keys() == {"gepris:1"}


def test_uncoded_filters_by_key():
    recs = [_rec("1"), _rec("2"), _rec("3")]
    assert {r.id for r in uncoded(recs, {"gepris:2"})} == {"1", "3"}


def test_suggestion_store_roundtrip(tmp_path):
    store = SuggestionStore(tmp_path / "repair.suggestions.csv")
    assert store.load() == {}
    store.append(Suggestion(key="gepris:1", term="repair", suggested=Label.TROPE,
                            model="google/gemini-2.0-flash-001", suggested_at="2026-06-26"))
    store.append(Suggestion(key="openalex:W2", term="repair", suggested=Label.HOMONYM,
                            model="m", suggested_at="2026-06-26"))
    loaded = store.load()
    assert loaded["gepris:1"].suggested is Label.TROPE
    assert loaded["gepris:1"].model == "google/gemini-2.0-flash-001"
    assert loaded["openalex:W2"].suggested is Label.HOMONYM
    assert store.suggested_keys() == {"gepris:1", "openalex:W2"}
