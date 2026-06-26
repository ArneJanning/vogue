from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402
from vogue.analysis import Overlay  # noqa: E402

# colour by source, line-style by metric — so a glance separates "who" from "what"
_SOURCE_COLOR = {"gepris": "#c1432e", "openalex": "#2e6fc1", "crossref": "#3a9e57"}
_METRIC_STYLE = {  # metric -> (linestyle, linewidth, marker, alpha)
    "coded_trope": ("-", 2.4, "o", 0.95),
    "discipline": ("--", 1.4, None, 0.55),
    "raw": (":", 1.3, None, 0.5),
}
_FALLBACK = ["#7b5cb8", "#d18f1e", "#159b8a", "#b8366f"]


def _label(name: str) -> str:
    src, _, metric = name.partition(":")
    return f"{src.upper()} · {metric.replace('_', ' ')}" if metric else name


def plot_overlay(overlay: Overlay, path: Path, series: list[str] | None = None,
                 normalize: str = "peak", title: str | None = None,
                 mark_year: int | None = None) -> Path:
    """Plot year-series, by default normalized to each series' own peak so shapes (and any
    lead) are comparable across very different magnitudes. `series` selects/orders which to
    draw; `mark_year` adds a labelled vertical line (e.g. a shared crest). Writes a PNG."""
    path = Path(path)
    names = [n for n in (series or overlay.series) if overlay.series.get(n)]
    plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(figsize=(9.5, 5.2), constrained_layout=True)

    drawn_years: set[int] = set()
    for i, name in enumerate(names):
        ser = overlay.series[name]
        drawn_years.update(ser)
    if names and drawn_years:
        xs = list(range(min(drawn_years), max(drawn_years) + 1))
        for i, name in enumerate(names):
            ser = overlay.series[name]
            ys = [ser.get(y, 0) for y in xs]
            if normalize == "peak":
                peak = max(ys) or 1
                ys = [y / peak for y in ys]
            metric = name.partition(":")[2]
            ls, lw, marker, alpha = _METRIC_STYLE.get(metric, ("-", 2.0, "o", 0.9))
            color = _SOURCE_COLOR.get(name.partition(":")[0], _FALLBACK[i % len(_FALLBACK)])
            ax.plot(xs, ys, ls=ls, lw=lw, marker=marker, markersize=5.5,
                    color=color, alpha=alpha, label=_label(name))
        if mark_year is not None:
            ax.axvline(mark_year, color="0.4", ls=(0, (2, 3)), lw=1)
            ax.text(mark_year, 0.94, str(mark_year), color="0.35", fontsize=9,
                    ha="center", va="top", transform=ax.get_xaxis_transform(),
                    bbox=dict(facecolor="white", edgecolor="none", pad=1))
        ax.set_xlabel("year")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel("share of series peak" if normalize == "peak" else "count")
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color="0.9", lw=0.8)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.legend(frameon=False, fontsize=10, loc="upper left")
    else:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
        ax.set_axis_off()
    ax.set_title(title or f"{overlay.term}: normalized curves")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path
