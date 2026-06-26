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
    monkeypatch.setattr(pipeline, "fetch_term", lambda study, s, t: recs)
    res = runner.invoke(app, ["funnel", str(tmp_path), "--source", "gepris", "--term", "repair"])
    assert res.exit_code == 0
    assert "raw=5" in res.stdout
    assert "discipline=2" in res.stdout


def test_code_writes_labels_and_is_idempotent(tmp_path, monkeypatch):
    _study(tmp_path)
    recs = [Record(source="gepris", id=str(i), title=f"t{i}", year=2020,
                   discipline_raw="Literaturwissenschaft", field=Field.HUMANITIES,
                   work_type="w", url="u") for i in range(3)]
    monkeypatch.setattr(pipeline, "fetch_term", lambda study, s, t: recs)

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
