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
