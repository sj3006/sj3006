"""Figure 2: a modelled direction against a measured one.

Coverage of the nominally 95 % certificate for the true cause as the fault's
whitened signal strength `rho` grows, three instruments. Grey curves: the
twin's direction is wrong by a fixed angle (Theorem 2). Blue curve: the
direction is measured from four commanded steps as strong as the fault
(Proposition 6). The dotted line is the 90 % target; the vertical line marks
rho = 28, the signal strength the ten degree floor implies.

Writes `paper/figures/fig2_theory.png` and `.pdf`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theory as th                                               # noqa: E402

OUT = HERE / "paper" / "figures"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#b4b3ad", "#ecebe8"
BLUE = "#2a78d6"
GREYS = ("#8a8984", "#5f5e5a", "#2f2e2b")


def draw(ax):
    rho = np.geomspace(5, 200, 120)
    for d, g in zip((0.5, 1.6, 5.0), GREYS):
        c = [float(th.coverage_directional(d, r, 3)) for r in rho]
        ax.plot(rho, c, color=g, lw=1.6)
        i = np.searchsorted(-np.asarray(c), -0.55)
        i = min(max(i, 5), len(rho) - 5)
        ax.text(rho[i] / 1.06, c[i], f"modelled, off by {d:g}\u00b0",
                color=g, fontsize=7.5, va="center", ha="right")
    rr = np.geomspace(5, 200, 30)
    cm = [th.commanded_coverage(r, r * 2.0, 3) for r in rr]
    ax.plot(rr, cm, color=BLUE, lw=2.0)
    ax.text(5.4, 0.86, "measured, four commanded steps", color=BLUE,
            fontsize=7.5, va="top")
    ax.axhline(0.90, color=INK2, lw=0.8, ls=":")
    ax.axhline(0.95, color=MUTED, lw=0.6)
    ax.axvline(28, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.text(28 * 1.04, 0.03, r"$\rho$ = 28", color=INK2, fontsize=7.5)
    ax.set_xscale("log")
    ax.set_ylim(0, 1.0)
    ax.set_xlim(5, 200)
    ax.set_xticks([5, 10, 20, 50, 100, 200])
    ax.set_xticklabels(["5", "10", "20", "50", "100", "200"])
    ax.minorticks_off()
    ax.set_xlabel(r"whitened signal strength of the fault, $\rho$", color=INK2)
    ax.set_ylabel("coverage of the true cause", color=INK2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.2, 3.4), dpi=200)
    draw(ax)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig2_theory.{ext}", bbox_inches="tight")
    print("wrote", OUT / "fig2_theory.png")


if __name__ == "__main__":
    main()
