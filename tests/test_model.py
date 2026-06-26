from vogue.model import Record, Field


def test_key_is_source_colon_id():
    r = Record(source="gepris", id="250291591", title="X", year=2013,
               discipline_raw="Molekülchemie", field=Field.PHYS,
               work_type="Sachbeihilfen", url="http://example/250291591")
    assert r.key == "gepris:250291591"


def test_year_and_abstract_optional():
    r = Record(source="gepris", id="1", title="Y", year=None,
               discipline_raw="", field=Field.UNKNOWN, work_type="", url="u")
    assert r.year is None
    assert r.abstract is None
    assert r.raw == {}
