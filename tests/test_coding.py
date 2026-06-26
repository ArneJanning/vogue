from vogue.coding import Label, Coding, CodingStore, uncoded
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
