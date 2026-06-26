import csv as _csv
from pathlib import Path
from typer.testing import CliRunner
from vogue.cli import app
import vogue.pipeline as pipeline
from vogue.model import Record, Field

runner = CliRunner()


def _study(tmp_path: Path):
    (tmp_path / "study.yaml").write_text("name: d\nsources: [gepris]\n", encoding="utf-8")
    (tmp_path / "terms.yaml").write_text("terms: [{name: repair}]\n", encoding="utf-8")


def test_funnel_command_reports_counts(tmp_path, monkeypatch):
    _study(tmp_path)
    recs = [Record(source="gepris", id=str(i), title="t", year=2020, discipline_raw="d",
                   field=(Field.HUMANITIES if i < 2 else Field.LIFE), work_type="w", url="u")
            for i in range(5)]
    monkeypatch.setattr(pipeline, "fetch_term", lambda study, s, t, limit=None: recs)
    res = runner.invoke(app, ["funnel", str(tmp_path), "--source", "gepris", "--term", "repair"])
    assert res.exit_code == 0
    assert "raw=5" in res.stdout
    assert "discipline=2" in res.stdout


def test_code_writes_labels_and_is_idempotent(tmp_path, monkeypatch):
    _study(tmp_path)
    recs = [Record(source="gepris", id=str(i), title=f"t{i}", year=2020,
                   discipline_raw="Literaturwissenschaft", field=Field.HUMANITIES,
                   work_type="w", url="u") for i in range(3)]
    monkeypatch.setattr(pipeline, "fetch_term", lambda study, s, t, limit=None: recs)

    # First pass: code record 0 = trope, 1 = homonym, then quit (record 2 left uncoded)
    res = runner.invoke(app, ["code", str(tmp_path), "--source", "gepris", "--term", "repair"],
                        input="t\nh\nq\n")
    assert res.exit_code == 0
    assert "3 new to code, 0 already coded" in res.stdout

    csv_path = tmp_path / "codings" / "repair.csv"
    rows = list(_csv.DictReader(csv_path.open(encoding="utf-8")))
    assert {r["key"]: r["label"] for r in rows} == {"gepris:0": "trope", "gepris:1": "homonym"}

    # Second pass: idempotent — only the 1 remaining uncoded record is surfaced
    res2 = runner.invoke(app, ["code", str(tmp_path), "--source", "gepris", "--term", "repair"],
                         input="l\n")
    assert "1 new to code, 2 already coded" in res2.stdout
    rows2 = list(_csv.DictReader(csv_path.open(encoding="utf-8")))
    assert {r["key"]: r["label"] for r in rows2} == {
        "gepris:0": "trope", "gepris:1": "homonym", "gepris:2": "literal"}


def test_tally_reports_full_funnel(tmp_path, monkeypatch):
    _study(tmp_path)
    recs = [Record(source="gepris", id=str(i), title="t", year=2020, discipline_raw="d",
                   field=(Field.HUMANITIES if i < 3 else Field.LIFE), work_type="w", url="u")
            for i in range(5)]
    monkeypatch.setattr(pipeline, "fetch_term", lambda study, s, t, limit=None: recs)
    codings_dir = tmp_path / "codings"
    codings_dir.mkdir()
    (codings_dir / "repair.csv").write_text(
        "key,term,label,suggested,coder,coded_at,note\n"
        "gepris:0,repair,trope,,,,\n"
        "gepris:1,repair,homonym,,,,\n", encoding="utf-8")

    res = runner.invoke(app, ["tally", str(tmp_path), "--source", "gepris", "--term", "repair"])
    assert res.exit_code == 0
    assert "raw=5" in res.stdout
    assert "discipline=3" in res.stdout
    assert "coded=2" in res.stdout
    assert "trope=1" in res.stdout
    assert "homonym=1" in res.stdout
    assert "literal=0" in res.stdout


def test_funnel_limit_option(tmp_path, monkeypatch):
    _study(tmp_path)
    seen = {}
    def fake_fetch(study, s, t, limit=None):
        seen["limit"] = limit
        return [Record(source="gepris", id="1", title="t", year=2020, discipline_raw="d",
                       field=Field.HUMANITIES, work_type="w", url="u")]
    monkeypatch.setattr(pipeline, "fetch_term", fake_fetch)
    res = runner.invoke(app, ["funnel", str(tmp_path), "--source", "gepris",
                              "--term", "repair", "--limit", "7"])
    assert res.exit_code == 0
    assert seen["limit"] == 7


def test_report_command_writes_files(tmp_path, monkeypatch):
    _study(tmp_path)
    import vogue.cli as climod
    from vogue.analysis import Overlay
    monkeypatch.setattr(climod, "build_overlay",
                        lambda study, term, limit=None: Overlay(
                            term="repair", series={"gepris:coded_trope": {2020: 2}}))
    res = runner.invoke(app, ["report", str(tmp_path), "--term", "repair"])
    assert res.exit_code == 0
    assert (tmp_path / "out" / "repair-report.md").exists()
    assert (tmp_path / "out" / "repair-overlay.png").exists()


def test_leadlag_command_reports_lag(tmp_path, monkeypatch):
    _study(tmp_path)
    import vogue.cli as climod
    from vogue.analysis import Overlay

    def bump(center, lo=2000, hi=2020):
        return {y: max(0, 10 - abs(y - center)) for y in range(lo, hi + 1)}

    ov = Overlay(term="repair", series={
        "gepris:coded_trope": bump(2010),     # lags
        "openalex:raw": bump(2007),           # leads by 3
    })
    monkeypatch.setattr(climod, "build_overlay", lambda study, term, limit=None: ov)

    res = runner.invoke(app, ["leadlag", str(tmp_path), "--term", "repair",
                              "--lead", "openalex:raw", "--lag", "gepris:coded_trope"])
    assert res.exit_code == 0
    assert "by 3 years" in res.stdout
    assert "openalex:raw" in res.stdout and "gepris:coded_trope" in res.stdout


def test_leadlag_missing_series_errors(tmp_path, monkeypatch):
    _study(tmp_path)
    import vogue.cli as climod
    from vogue.analysis import Overlay
    monkeypatch.setattr(climod, "build_overlay",
                        lambda study, term, limit=None: Overlay(term="repair", series={}))
    res = runner.invoke(app, ["leadlag", str(tmp_path), "--term", "repair"])
    assert res.exit_code == 1
    assert "series" in res.stdout.lower()
