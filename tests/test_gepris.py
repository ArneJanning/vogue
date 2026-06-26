from pathlib import Path
from vogue.model import Field
from vogue.sources.gepris import parse_results, result_count

FIX = Path(__file__).parent / "fixtures" / "gepris_repair_p0.html"


def test_result_count_parses_fixture():
    html = FIX.read_text(encoding="utf-8")
    n = result_count(html)
    assert isinstance(n, int) and n > 100


def test_result_count_handles_thousands_separator():
    assert result_count('data-result-count="1.234"') == 1234


def test_parse_yields_aligned_records():
    html = FIX.read_text(encoding="utf-8")
    recs = parse_results(html)
    assert len(recs) == 10  # 10 results per page
    r = recs[0]
    assert r.source == "gepris"
    assert r.id and r.title
    assert r.year is None or 1980 <= r.year <= 2030
    assert r.field in set(Field)  # classified, never crashes
