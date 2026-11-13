"""Paper figures (vector PDF) from the CSVs in results/final.

fig_scaling: trials to certify half the safe region vs grid size, for the
  synthetic window and the Rosenthal 316L model (fixed budget).
fig_fixed_conf: fixed-confidence cost of the search and of the per-setting
  method next to the lower bounds with and without the ordering.

Run from process_window/:  python3 experiments/paper_figs.py
"""

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FixedLocator, NullLocator  # noqa: E402

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "..", "results", "final")
FIGS = os.path.join(HERE, "..", "paper", "latex", "figs")
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
# Fixed categorical order; colors follow the method across all figures.
COL = {"ours": "#2a78d6", "no ordering": "#1baf7a", "full grid (Bonferroni)": "#e87ba4",
       "full grid (fixed sequence)": "#008300", "search": "#2a78d6", "per-setting": "#1baf7a"}
# Distinct marker shapes give every series a second, color-independent cue.
MARK = {"ours": "o", "no ordering": "s", "full grid (fixed sequence)": "^", "full grid (Bonferroni)": "D"}
NAME = {"ours": "ours", "unstructured": "no ordering", "grid DoE": "full grid (Bonferroni)",
        "grid FST": "full grid (fixed sequence)"}
plt.rcParams.update({"font.size": 8, "font.family": "serif", "figure.facecolor": SURFACE,
                     "pdf.fonttype": 42})


def _read(name):
    with open(os.path.join(RES, name)) as f:
        return list(csv.DictReader(f))


def _style(ax, ns):
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.6, which="major")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=7)
    ax.xaxis.set_major_locator(FixedLocator(ns))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("grid size $n$ ($n\\times n$ settings)", color=INK)


def _guides(ax, ns, n0, c0):
    ns = np.array(ns, float)
    ax.loglog(ns, c0 * ns / n0, ":", color=INK2, lw=0.9)
    ax.loglog(ns, c0 * (ns / n0) ** 2, "--", color=INK2, lw=0.9)
    ax.text(ns[-1], c0 * ns[-1] / n0, " slope 1", color=INK2, fontsize=6, va="center")
    ax.text(ns[-1], c0 * (ns[-1] / n0) ** 2, " slope 2", color=INK2, fontsize=6, va="center")


def fig_scaling():
    grid = _read("scaling_grid_baselines.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.4), constrained_layout=True)
    for ax, (scen, title) in zip(axes, (("toy-good", "Synthetic window"), ("lpbf-good", "Rosenthal 316L"))):
        rows = _read(f"scaling_{scen}.csv") + [r for r in grid if r["scen"] == scen]
        ns = sorted({int(r["n"]) for r in rows if r["method"] == "ours"})
        for m in ("ours", "unstructured", "grid FST", "grid DoE"):
            pts = sorted(((int(r["n"]), float(r["median"])) for r in rows
                          if r["method"] == m and int(r["n"]) in ns and np.isfinite(float(r["median"]))))
            if pts:
                x, y = zip(*pts)
                ax.loglog(x, y, "-", marker=MARK[NAME[m]], color=COL[NAME[m]], lw=1.6, ms=3.5, label=NAME[m])
        o = [r for r in rows if r["method"] == "ours" and int(r["n"]) == ns[0]][0]
        _guides(ax, ns, ns[0], float(o["median"]))
        _style(ax, ns)
        ax.set_title(title, fontsize=8, color=INK)
    axes[0].set_ylabel("trials to certify 50% of $W$", color=INK)
    axes[0].legend(fontsize=6.5, frameon=False, labelcolor=INK, loc="upper left")
    fig.savefig(os.path.join(FIGS, "fig_scaling.pdf"), facecolor=SURFACE)
    plt.close(fig)


def fig_fixed_conf():
    rows = _read("fixed_confidence_good_8-24.csv") + _read("fixed_confidence_good_32-48.csv")
    rows = sorted(rows, key=lambda r: int(r["n"]))
    ns = [int(r["n"]) for r in rows]
    fig, ax = plt.subplots(figsize=(3.25, 2.4), constrained_layout=True)

    def series(key):
        pts = [(int(r["n"]), float(r[key])) for r in rows if r.get(key) not in (None, "", "nan")]
        return zip(*pts)

    x, y = series("search")
    ax.loglog(x, y, "o-", color=COL["search"], lw=1.6, ms=3.5, label="search (ours)")
    x, y = series("LB_ordered")
    ax.loglog(x, y, "o:", color=COL["search"], lw=1.2, ms=3, label="lower bound, ordered")
    x, y = series("per-setting")
    ax.loglog(x, y, "s-", color=COL["per-setting"], lw=1.6, ms=3.5, label="per-setting (no ordering)")
    x, y = series("LB_unordered")
    ax.loglog(x, y, "s:", color=COL["per-setting"], lw=1.2, ms=3, label="lower bound, unordered")
    _style(ax, ns)
    ax.set_ylabel("trials until stop", color=INK)
    ax.legend(fontsize=6, frameon=False, labelcolor=INK, loc="upper left")
    fig.savefig(os.path.join(FIGS, "fig_fixed_conf.pdf"), facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIGS, exist_ok=True)
    fig_scaling()
    fig_fixed_conf()
    print("figures in", FIGS)
