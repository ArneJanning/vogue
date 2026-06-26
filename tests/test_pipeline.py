from vogue.model import Record, Field
from vogue.pipeline import Funnel, funnel_for_records
from vogue.coding import Coding, Label
from vogue.pipeline import coded_tally


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


def test_coded_tally_counts_labels_of_kept():
    kept = [_rec("1", Field.HUMANITIES), _rec("2", Field.HUMANITIES),
            _rec("3", Field.HUMANITIES)]
    codings = {
        "gepris:1": Coding(key="gepris:1", term="repair", label=Label.TROPE),
        "gepris:2": Coding(key="gepris:2", term="repair", label=Label.HOMONYM),
        # gepris:3 deliberately uncoded
    }
    tally = coded_tally(kept, codings)
    assert tally[Label.TROPE] == 1
    assert tally[Label.HOMONYM] == 1
    assert tally[Label.LITERAL] == 0
    assert sum(tally.values()) == 2  # uncoded records are not counted


def test_source_for_knows_openalex(tmp_path):
    (tmp_path / "study.yaml").write_text("name: d\nsources: [openalex]\n", encoding="utf-8")
    (tmp_path / "terms.yaml").write_text("terms: [{name: repair}]\n", encoding="utf-8")
    from vogue.study import Study
    from vogue.pipeline import _source_for
    s = Study.load(tmp_path)
    assert _source_for("openalex", s).name == "openalex"
