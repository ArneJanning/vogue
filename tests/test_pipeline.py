from vogue.model import Record, Field
from vogue.pipeline import Funnel, funnel_for_records


def _rec(pid, field):
    return Record(source="gepris", id=pid, title=f"t{pid}", year=2020,
                  discipline_raw="d", field=field, work_type="w", url="u")


def test_funnel_counts_and_filters():
    recs = [_rec("1", Field.HUMANITIES), _rec("2", Field.LIFE),
            _rec("3", Field.HUMANITIES), _rec("4", Field.PHYS)]
    f = funnel_for_records(recs, keep_fields=[Field.HUMANITIES])
    assert isinstance(f, Funnel)
    assert f.raw == 4
    assert f.discipline == 2
    assert {r.id for r in f.kept} == {"1", "3"}
