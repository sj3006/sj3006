"""Figure: Section 4.5's four sweeps on one shared axis.

Section 4.5 carries 52 numbers in 578 words, which is the densest prose in the
paper. Four of its results are one-dimensional sweeps of an assumption against
the worst pairwise angle, so they share an axis and belong in one figure: the
reader then sees in a glance that the conclusion survives every assumption,
which is the claim the section is making and which no amount of prose shows as
directly.

The fifth result, the collapse of the enlarged angles onto the instantaneous
ones when two faults share a profile, is a theorem rather than a sweep and
stays in the text.

Every panel shares the same vertical axis and the same floor line so that the
four are directly comparable. Values come from `profile_robustness`, the same
module the prose quotes.

    python3 src/fig_robustness_panels.py
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

import profile_robustness as pr                                   # noqa: E402
from observables import modulations                               # noqa: E402

OUT = HERE.parent / "paper" / "fig9_robustness_panels.png"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#b4b3ad"
ACCENT = "#2a78d6"
WARN = "#eb6834"
FLOOR = pr.FLOOR

plt.rcParams.update({
    "font.family": "serif", "font.size": 6.4,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "axes.edgecolor": MUTED, "axes.linewidth": 0.5,
    "axes.labelcolor": INK, "axes.titlesize": 6.6,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 5.6, "ytick.labelsize": 5.6,
    "axes.grid": True, "grid.color": "#ececea", "grid.linewidth": 0.4,
    "legend.frameon": False, "legend.fontsize": 5.4,
    "lines.linewidth": 1.1,
})

YMAX = 55.0


def _floor_line(ax, label=False):
    ax.axhline(FLOOR, color=INK, lw=0.7, ls=(0, (4, 2)), zorder=4)
    if label:
        ax.annotate("floor", (ax.get_xlim()[1], FLOOR), xytext=(-2, 2),
                    textcoords="offset points", fontsize=5.2, color=INK,
                    ha="right", va="bottom")


def panel_contrast(ax):
    """Worst pair against a common multiplier on every profile contrast."""
    J, plan, G, bsig, _, _ = pr._setup()
    xs = np.linspace(0.05, 1.5, 60)
    worst, pair_curves = [], {p: [] for p in pr.PAIRS}
    for c in xs:
        a, _ = pr._angles_from_profile(J, G, bsig, modulations(plan, contrast=c))
        worst.append(min(a.values()))
        for p in pr.PAIRS:
            pair_curves[p].append(a[p])
    for p in pr.PAIRS:
        ax.plot(xs, pair_curves[p], color=MUTED, lw=0.5, zorder=2)
    ax.plot(xs, worst, color=ACCENT, zorder=3)
    _floor_line(ax)
    thr = pr.contrast_thresholds()
    hardest = max(v for v in thr.values() if v is not None)
    ax.axvline(hardest, color=WARN, lw=0.7, ls=":", zorder=4)
    ax.annotate(f"all ten clear\nat {hardest:.2f}", (hardest, YMAX * 0.93),
                xytext=(3, 0), textcoords="offset points", fontsize=5.2,
                color=WARN, va="top")
    ax.axvline(1.0, color=MUTED, lw=0.6, zorder=1)
    ax.set_xlabel("contrast multiplier")
    ax.set_title("(a) weaker machine patterns", loc="left", color=INK)
    ax.set_xlim(0, 1.5)
    return hardest


def panel_permutation(ax):
    """All 120 ways of assigning the five profiles to the five faults."""
    res = pr.permutation_sweep()
    worst = np.asarray(res["worst_values"], float)
    ax.hist(worst, bins=18, color=ACCENT, alpha=0.75, zorder=3)
    ax.axvline(FLOOR, color=INK, lw=0.7, ls=(0, (4, 2)), zorder=4)
    ax.annotate(f"{worst.min():.1f}$^\\circ$ to {worst.max():.1f}$^\\circ$,\n"
                f"all {len(worst)} above the floor",
                (0.97, 0.93), xycoords="axes fraction", fontsize=5.2,
                color=INK2, ha="right", va="top")
    ax.set_xlabel("worst pair, degrees")
    ax.set_ylabel("assignments")
    ax.set_title("(b) which fault owns which pattern", loc="left", color=INK)
    ax.set_xlim(0, YMAX)
    return worst


def panel_segments(ax):
    """Worst pair against the number of segments the regression sees."""
    rows = pr.segment_sweep()
    n = [r["N"] for r in rows]
    w = [r["worst"] for r in rows]
    ax.plot(n, w, "o-", color=ACCENT, markersize=2.6, zorder=3)
    _floor_line(ax)
    for target in (12, 30):
        k = min(range(len(n)), key=lambda i: abs(n[i] - target))
        ax.annotate(f"$N={n[k]}$: {w[k]:.1f}$^\\circ$", (n[k], w[k]),
                    xytext=(4, 5), textcoords="offset points", fontsize=5.2,
                    color=INK2)
    ax.set_xlabel("segments, $N$")
    ax.set_title("(c) how much build is needed", loc="left", color=INK)
    ax.set_xscale("log")
    ax.set_xticks([12, 30, 84, 240])
    ax.set_xticklabels(["12", "30", "84", "240"])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    return rows


def panel_misattribution(ax):
    """One fault's profile progressively replaced by another's driver."""
    fr = np.linspace(0.0, 1.0, 21)
    res = pr.misattribution_sweep(fractions=tuple(fr))
    alpha = [r["alpha"] for r in res["rows"]]
    ang = [r["pair_angle"] for r in res["rows"]]
    ax.plot(alpha, ang, color=ACCENT, zorder=3)
    _floor_line(ax)
    tol = res["tolerance"]
    if tol is not None:
        ax.axvline(tol, color=WARN, lw=0.7, ls=":", zorder=4)
        ax.annotate(f"holds to {tol:.0%}", (tol, YMAX * 0.93), xytext=(-3, 0),
                    textcoords="offset points", fontsize=5.2, color=WARN,
                    ha="right", va="top")
    ax.set_xlabel("layer profile driven by support")
    ax.set_title("(d) pattern on the wrong variable", loc="left", color=INK)
    ax.set_xlim(0, 1)
    return res


def draw() -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(3.35, 2.95))
    fig.subplots_adjust(hspace=0.70, wspace=0.42)
    a = panel_contrast(axes[0, 0])
    w = panel_permutation(axes[0, 1])
    s = panel_segments(axes[1, 0])
    m = panel_misattribution(axes[1, 1])

    for ax in (axes[0, 0], axes[1, 0], axes[1, 1]):
        ax.set_ylim(0, YMAX)
    axes[0, 0].set_ylabel("worst pair, degrees")
    axes[1, 0].set_ylabel("worst pair, degrees")

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=400, bbox_inches="tight")
    plt.close(fig)
    print(f"  (a) all ten pairs clear at a contrast multiplier of {a:.3f}")
    print(f"  (b) 120 assignments, worst pair {w.min():.2f} to {w.max():.2f} deg")
    print(f"  (c) N from {s[0]['N']} to {s[-1]['N']}, worst "
          f"{s[0]['worst']:.2f} to {s[-1]['worst']:.2f} deg")
    print(f"  (d) {m['pair']} holds to alpha = {m['tolerance']:.4f}")
    return OUT


if __name__ == "__main__":
    print(f"written {draw()}")
