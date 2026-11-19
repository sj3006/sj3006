"""Shared pieces for Section 4.5's four robustness panels.

Each of the four sweeps lives in its own script so it can be regenerated,
inspected or dropped into a talk on its own, and `fig_robust_all.py` assembles
the same four functions into the 2x2 composite the paper carries. Writing the
drawing once and calling it from both places is what keeps the standalone
versions and the composite from drifting apart.

All four share one vertical axis, the worst pairwise angle in degrees, and one
floor line. That is the point of the figure: the panels are only comparable
because the quantity and the threshold are the same in each.

Values come from `profile_robustness`, the module the prose quotes, so a figure
cannot disagree with the text unless the text is stale.
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

OUTDIR = HERE.parent / "paper"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#b4b3ad"
ACCENT = "#2a78d6"
WARN = "#eb6834"

FLOOR = pr.FLOOR
YMAX = 55.0

#: Font sizes for the composite. `use_scale` enlarges them for a standalone
#: panel, which occupies several times the area and would otherwise be set in
#: type far smaller than the body text.
_BASE = {"tick": 5.6, "label": 6.4, "title": 6.6, "note": 5.2}
_S = dict(_BASE)


def use_scale(factor: float = 1.0) -> None:
    """Set the type scale, 1.0 for the composite and about 1.5 standalone."""
    global _S
    _S = {k: v * factor for k, v in _BASE.items()}
    plt.rcParams.update({
        "font.family": "serif", "font.size": _S["label"],
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.edgecolor": MUTED, "axes.linewidth": 0.5,
        "axes.labelcolor": INK, "axes.labelsize": _S["label"],
        "axes.titlesize": _S["title"],
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.labelsize": _S["tick"], "ytick.labelsize": _S["tick"],
        "axes.grid": True, "grid.color": "#ececea", "grid.linewidth": 0.4,
        "legend.frameon": False, "legend.fontsize": _S["note"],
        "lines.linewidth": 1.1 * min(factor, 1.3),
    })


use_scale(1.0)


def floor_line(ax) -> None:
    ax.axhline(FLOOR, color=INK, lw=0.7, ls=(0, (4, 2)), zorder=4)


def finish(fig, name: str) -> Path:
    OUTDIR.mkdir(exist_ok=True)
    path = OUTDIR / name
    fig.savefig(path, dpi=400, bbox_inches="tight")
    plt.close(fig)
    print(f"written {path}")
    return path


def standalone(panel, name: str, figsize=(3.3, 2.5), scale: float = 1.5):
    """Draw one panel on its own axes and save it."""
    use_scale(scale)
    fig, ax = plt.subplots(figsize=figsize)
    out = panel(ax)
    ax.set_ylabel("worst pair, degrees")
    if panel is not panel_permutation:
        ax.set_ylim(0, YMAX)
    finish(fig, name)
    use_scale(1.0)
    return out


# ---------------------------------------------------------------------------
# (a) how strong a machine's spatial patterns must be
# ---------------------------------------------------------------------------
def panel_contrast(ax) -> dict:
    """Every pair's angle against a common multiplier on the profile contrasts.

    The grey curves are the ten pairs, the blue one the worst of them, which is
    the quantity the floor has to clear.
    """
    J, plan, G, bsig, _, _ = pr._setup()
    xs = np.linspace(0.05, 1.5, 60)
    worst, curves = [], {p: [] for p in pr.PAIRS}
    for c in xs:
        a, _ = pr._angles_from_profile(J, G, bsig, modulations(plan, contrast=c))
        worst.append(min(a.values()))
        for p in pr.PAIRS:
            curves[p].append(a[p])
    for p in pr.PAIRS:
        ax.plot(xs, curves[p], color=MUTED, lw=0.5, zorder=2)
    ax.plot(xs, worst, color=ACCENT, zorder=3)
    floor_line(ax)
    thresholds = pr.contrast_thresholds()
    hardest = max(v for v in thresholds.values() if v is not None)
    cheap = sum(1 for v in thresholds.values() if v is not None and v <= 0.25)
    ax.axvline(hardest, color=WARN, lw=0.7, ls=":", zorder=4)
    ax.annotate(f"all ten clear\nat {hardest:.2f}", (hardest, YMAX * 0.93),
                xytext=(3, 0), textcoords="offset points",
                fontsize=_S["note"], color=WARN, va="top")
    ax.axvline(1.0, color=MUTED, lw=0.6, zorder=1)
    ax.set_xlabel("contrast multiplier")
    ax.set_title("(a) weaker machine patterns", loc="left", color=INK)
    ax.set_xlim(0, 1.5)
    return {"hardest": hardest, "cleared_at_quarter": cheap,
            "thresholds": thresholds}


# ---------------------------------------------------------------------------
# (b) which fault follows which build variable
# ---------------------------------------------------------------------------
def panel_permutation(ax) -> dict:
    """The worst pair over all 120 assignments of profiles to faults."""
    res = pr.permutation_sweep()
    worst = np.asarray(res["worst_values"], float)
    ax.hist(worst, bins=18, color=ACCENT, alpha=0.75, zorder=3)
    ax.axvline(FLOOR, color=INK, lw=0.7, ls=(0, (4, 2)), zorder=4)
    ax.annotate(f"{worst.min():.1f}$^\\circ$ to {worst.max():.1f}$^\\circ$,\n"
                f"all {len(worst)} above the floor",
                (0.97, 0.93), xycoords="axes fraction", fontsize=_S["note"],
                color=INK2, ha="right", va="top")
    ax.set_xlabel("worst pair, degrees")
    ax.set_ylabel("assignments")
    ax.set_title("(b) which fault owns which pattern", loc="left", color=INK)
    ax.set_xlim(0, YMAX)
    return res


# ---------------------------------------------------------------------------
# (c) how much of a build the regression needs
# ---------------------------------------------------------------------------
def panel_segments(ax) -> list[dict]:
    """The worst pair against the number of segments regressed over."""
    rows = pr.segment_sweep()
    n = [r["N"] for r in rows]
    w = [r["worst"] for r in rows]
    ax.plot(n, w, "o-", color=ACCENT, markersize=2.6, zorder=3)
    floor_line(ax)
    for target in (12, 30):
        k = min(range(len(n)), key=lambda i: abs(n[i] - target))
        ax.annotate(f"$N={n[k]}$: {w[k]:.1f}$^\\circ$", (n[k], w[k]),
                    xytext=(4, 5), textcoords="offset points",
                    fontsize=_S["note"], color=INK2)
    ax.set_xlabel("segments, $N$")
    ax.set_title("(c) how much build is needed", loc="left", color=INK)
    ax.set_xscale("log")
    ax.set_xticks([12, 30, 84, 240])
    ax.set_xticklabels(["12", "30", "84", "240"])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    return rows


# ---------------------------------------------------------------------------
# (d) a pattern attributed to the wrong build variable
# ---------------------------------------------------------------------------
def panel_misattribution(ax) -> dict:
    """The layer-geometry angle as the layer profile is replaced by support."""
    fractions = tuple(np.linspace(0.0, 1.0, 21))
    res = pr.misattribution_sweep(fractions=fractions)
    alpha = [r["alpha"] for r in res["rows"]]
    angle = [r["pair_angle"] for r in res["rows"]]
    ax.plot(alpha, angle, color=ACCENT, zorder=3)
    floor_line(ax)
    tol = res["tolerance"]
    if tol is not None:
        ax.axvline(tol, color=WARN, lw=0.7, ls=":", zorder=4)
        ax.annotate(f"holds to {tol:.0%}", (tol, YMAX * 0.93), xytext=(-3, 0),
                    textcoords="offset points", fontsize=_S["note"],
                    color=WARN, ha="right", va="top")
    ax.set_xlabel("layer profile driven by support")
    ax.set_title("(d) pattern on the wrong variable", loc="left", color=INK)
    ax.set_xlim(0, 1)
    return res


def summarise(name, r) -> None:
    """One line of what the panel shows, instead of a raw dump."""
    if name == "contrast":
        print(f"  all ten pairs clear at a contrast multiplier of {r['hardest']:.3f}; "
              f"{r['cleared_at_quarter']} of ten clear at 0.25 or below")
    elif name == "permutation":
        print(f"  {r['n']} assignments: worst pair {r['worst_min']:.2f} to "
              f"{r['worst_max']:.2f} deg, median {r['worst_median']:.2f}, "
              f"rank 5 in {r['all_rank_5']}, all ten pairs clear in {r['all_cleared']}")
    elif name == "segments":
        print(f"  N = {r[0]['N']} gives {r[0]['worst']:.2f} deg, "
              f"N = {r[1]['N']} gives {r[1]['worst']:.2f} deg, "
              f"flat to {r[-1]['worst']:.2f} deg at N = {r[-1]['N']}")
    else:
        rows = {round(x['alpha'], 2): x['pair_angle'] for x in r['rows']}
        print(f"  {r['pair'][0]}/{r['pair'][1]} clears the floor until "
              f"{r['tolerance']:.1%} support-driven ({rows[0.8]:.2f} deg at 80 %)")


PANELS = {"a": panel_contrast, "b": panel_permutation,
          "c": panel_segments, "d": panel_misattribution}
