from vogue.analysis import Overlay
from vogue.plotting import plot_overlay


def test_plot_overlay_writes_png(tmp_path):
    ov = Overlay(term="repair", series={
        "gepris:coded_trope": {2019: 1, 2021: 3},
        "openalex:raw": {2016: 100, 2019: 400, 2021: 900},
    })
    out = tmp_path / "repair.png"
    returned = plot_overlay(ov, out)
    assert returned == out
    assert out.exists() and out.stat().st_size > 0


def test_plot_overlay_handles_empty(tmp_path):
    out = tmp_path / "empty.png"
    plot_overlay(Overlay(term="x", series={}), out)
    assert out.exists()  # writes an empty-state figure rather than crashing
