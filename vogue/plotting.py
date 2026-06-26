from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
from vogue.analysis import Overlay


def plot_overlay(overlay: Overlay, path: Path) -> Path:
    """Plot each series normalized to its own peak, so shapes/lead are comparable
    across very different magnitudes. Writes a PNG; returns the path."""
    path = Path(path)
    years = overlay.years()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if years:
        xs = list(range(min(years), max(years) + 1))
        for name, ser in overlay.series.items():
            ys = [ser.get(y, 0) for y in xs]
            peak = max(ys) or 1
            ax.plot(xs, [y / peak for y in ys], marker=".", label=name)
        ax.set_xlabel("year")
        ax.set_ylabel("share of series peak")
        ax.legend(fontsize="small")
    else:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    ax.set_title(f"{overlay.term}: normalized curves")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
