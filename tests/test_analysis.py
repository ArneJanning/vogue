from collections import Counter
from vogue.model import Record, Field
from vogue.coding import Coding, Label
from vogue.analysis import (
    year_counts_of_records, coded_year_counts, build_overlay, Overlay, render_report)


def _rec(pid, year, field=Field.HUMANITIES):
    return Record(source="gepris", id=pid, title="t", year=year, discipline_raw="d",
                  field=field, work_type="w", url="u")


def test_year_counts_of_records_skips_none():
    recs = [_rec("1", 2020), _rec("2", 2020), _rec("3", None)]
    assert year_counts_of_records(recs) == Counter({2020: 2})


def test_coded_year_counts_joins_label_and_year():
    recs = [_rec("1", 2020), _rec("2", 2021), _rec("3", 2021)]
    codings = {
        "gepris:1": Coding(key="gepris:1", term="r", label=Label.TROPE),
        "gepris:2": Coding(key="gepris:2", term="r", label=Label.TROPE),
        "gepris:3": Coding(key="gepris:3", term="r", label=Label.HOMONYM),
    }
    assert coded_year_counts(recs, codings, Label.TROPE) == Counter({2020: 1, 2021: 1})


def test_build_overlay_assembles_series(tmp_path, monkeypatch):
    (tmp_path / "study.yaml").write_text(
        "name: d\nsources: [gepris, openalex]\nkeep_fields: [humanities]\n", encoding="utf-8")
    (tmp_path / "terms.yaml").write_text("terms: [{name: repair}]\n", encoding="utf-8")
    (tmp_path / "codings").mkdir()
    (tmp_path / "codings" / "repair.csv").write_text(
        "key,term,label,suggested,coder,coded_at,note\n"
        "gepris:1,repair,trope,,,,\n"
        "openalex:W9,repair,trope,,,,\n", encoding="utf-8")

    import vogue.analysis as an

    def fake_fetch(study, source, term, limit=None):
        if source == "gepris":
            return [_rec("1", 2019), _rec("2", 2020, Field.LIFE)]
        return [Record(source="openalex", id="W9", title="t", year=2017, discipline_raw="d",
                       field=Field.HUMANITIES, work_type="a", url="u")]
    monkeypatch.setattr(an, "fetch_term", fake_fetch)

    class FakeOA:
        def counts_by_year(self, term):
            return {2016: 100, 2017: 200}
    monkeypatch.setattr(an, "_source_for", lambda name, study: FakeOA())

    from vogue.study import Study
    ov = build_overlay(Study.load(tmp_path), "repair", limit=50)
    assert isinstance(ov, Overlay)
    assert ov.series["gepris:coded_trope"] == {2019: 1}
    assert ov.series["gepris:discipline"] == {2019: 1}        # only the humanities rec kept
    assert ov.series["openalex:coded_trope"] == {2017: 1}
    assert ov.series["openalex:raw"] == {2016: 100, 2017: 200}
    assert ov.years() == [2016, 2017, 2019]


def test_render_report_contains_series_and_figure():
    ov = Overlay(term="repair", series={"gepris:coded_trope": {2019: 1, 2021: 3}})
    md = render_report(ov, "repair-overlay.png")
    assert "# repair" in md
    assert "gepris:coded_trope" in md
    assert "![" in md and "repair-overlay.png" in md   # embedded figure
    assert "2019" in md and "2021" in md
