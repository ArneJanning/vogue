from pathlib import Path
from vogue.model import Field
from vogue.study import Study


def _write_study(root: Path):
    (root / "study.yaml").write_text(
        "name: demo\nsources: [gepris]\nkeep_fields: [humanities]\n", encoding="utf-8")
    (root / "terms.yaml").write_text(
        "terms:\n  - name: repair\n    notes: the repair turn\n", encoding="utf-8")


def test_loads_defaults(tmp_path):
    _write_study(tmp_path)
    s = Study.load(tmp_path)
    assert s.name == "demo"
    assert s.sources == ["gepris"]
    assert s.keep_fields == [Field.HUMANITIES]
    assert [t.name for t in s.terms] == ["repair"]
    assert (s.cache_dir).name == "cache"


def test_keep_fields_defaults_to_humanities(tmp_path):
    (tmp_path / "study.yaml").write_text("name: d\nsources: [gepris]\n", encoding="utf-8")
    (tmp_path / "terms.yaml").write_text("terms: [{name: x}]\n", encoding="utf-8")
    s = Study.load(tmp_path)
    assert s.keep_fields == [Field.HUMANITIES]


def test_suggest_model_defaults_and_overrides(tmp_path):
    (tmp_path / "terms.yaml").write_text("terms: [{name: x}]\n", encoding="utf-8")
    (tmp_path / "study.yaml").write_text("name: d\nsources: [gepris]\n", encoding="utf-8")
    assert Study.load(tmp_path).suggest_model == "z-ai/glm-5.2"   # built-in default

    (tmp_path / "study.yaml").write_text(
        "name: d\nsources: [gepris]\nsuggest_model: openai/gpt-4o-mini\n", encoding="utf-8")
    assert Study.load(tmp_path).suggest_model == "openai/gpt-4o-mini"
