"""Figures, drawn from `results.json` so nothing is recomputed here.

Every number a figure shows is one the claim registry has checked, which is the
point of routing both through one file. A figure that disagrees with the text is
the failure mode this arrangement exists to prevent.

Choices that are not taste. Each panel does one job: a line where the job is a
magnitude against a continuous axis, a heat map where it is a matrix, a
horizontal bar where it is a comparison across named categories. No panel
carries two y-scales. Identity is never colour alone: every series is in the
legend and the few-series panels are directly labelled as well. The five hues
are a fixed order over the five faults, assigned once and never cycled, so a
fault keeps its colour across figures.

    python3 figures.py            # all six, into figures/
    python3 figures.py --only 2   # one of them
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402
from matplotlib.ticker import NullFormatter, NullLocator      # noqa: E402
from matplotlib.patches import Wedge                         # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results.json"
OUTDIR = HERE / "figures"

# Validated against the data-visualisation palette checks: all five inside the
# lightness band, chroma above the floor, worst adjacent pair dE 9.1 under
# protanopia and 22.9 under normal vision. Fixed order over the five faults.
FAULT_COLOUR = {
    "power":    "#2a78d6",
    "speed":    "#eb6834",
    "layer":    "#1baf7a",
    "gas":      "#eda100",
    "geometry": "#6250d6",
}
REGIME_COLOUR = {"instantaneous": "#eb6834", "build_context": "#2a78d6"}
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#a9a8a2"
SURFACE = "#ffffff"
FLOOR_DEG = 10.0

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "serif", "font.size": 8.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 9,
    "axes.linewidth": 0.6, "axes.grid": True, "grid.color": "#e8e7e3",
    "grid.linewidth": 0.5, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.frameon": False, "legend.fontsize": 7.5,
    "lines.linewidth": 1.6, "lines.markersize": 4.5,
})


def load() -> dict:
    if not RESULTS.exists():
        raise SystemExit(f"{RESULTS} not found; run `python3 results.py` first")
    return json.loads(RESULTS.read_text())


def _logticks(ax, values) -> None:
    """Hand-set ticks on a log axis, with the default decade ticks removed.

    Matplotlib keeps drawing its own minor labels (2x10^1 and so on) underneath
    hand-set major ticks, which on these ranges lands them on top of the labels
    that were set deliberately.
    """
    ax.set_xscale("log")
    ax.set_xticks(values)
    ax.set_xticklabels([f"{v:.0f}" for v in values])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())


def _finish(fig, name: str) -> Path:
    OUTDIR.mkdir(exist_ok=True)
    path = OUTDIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   {path.name}")
    return path


# --------------------------------------------------------------------------
# 1. the admissible cone
# --------------------------------------------------------------------------

def fig1_geometry(R: dict) -> None:
    """Why a certificate holds several causes.

    The left panel draws the cone for the instantaneous suite. Laying the five
    signature directions out in a plane at their true angle from the power
    direction is exact enough to draw here only because every one of those
    angles is below five degrees; the same layout for the enlarged observation
    would be a misrepresentation, since those angles run to 49 degrees and are
    genuinely not coplanar. So the right panel drops the picture and plots the
    quantity the test actually uses, which is a scalar and therefore honest in
    any number of dimensions: each pair's angle against the width of the cone.
    """
    fig = plt.figure(figsize=(7.2, 3.1))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25], wspace=0.28)
    rho = 28.0

    # --- left: the cone, instantaneous only
    ax = fig.add_subplot(gs[0, 0])
    ang = R["geometry"]["instantaneous"]["angles"]
    faults = R["meta"]["faults"]
    placed = {"power": 0.0}
    for f in faults[1:]:
        k = f"power|{f}" if f"power|{f}" in ang else f"{f}|power"
        placed[f] = ang[k]
    q = R["floor"]["instantaneous"]["q"]
    psi = np.degrees(np.arcsin(min(1.0, np.sqrt(q) / rho)))
    obs_angle = float(np.mean(list(placed.values())))
    # spread the labels vertically so they do not stack on each other
    order = sorted(placed, key=lambda f: placed[f])
    label_y = np.linspace(-0.055, 0.075, len(order))
    ax.add_patch(Wedge((0, 0), 1.0, obs_angle - psi, obs_angle + psi,
                       facecolor="#2a78d6", alpha=0.13, edgecolor="none",
                       zorder=0))
    for i, f in enumerate(order):
        r = np.radians(placed[f])
        ax.plot([0, np.cos(r)], [0, np.sin(r)], color=FAULT_COLOUR[f],
                lw=1.7, solid_capstyle="round", zorder=3)
        ax.plot([np.cos(r), 1.10], [np.sin(r), label_y[i]],
                color=FAULT_COLOUR[f], lw=0.5, alpha=0.65, zorder=2)
        ax.annotate(f, (1.12, label_y[i]), color=FAULT_COLOUR[f], fontsize=7.5,
                    ha="left", va="center", zorder=4)
    r = np.radians(obs_angle)
    ax.plot([0, np.cos(r) * 0.8], [0, np.sin(r) * 0.8], color=INK, lw=1.1,
            ls=(0, (3, 2)), zorder=5)
    ax.annotate("observation", (0.42, -0.028), color=INK2, fontsize=7,
                ha="center", va="top")
    ax.set_title(f"one instant: cone half-angle {psi:.1f}$^\\circ$,\n"
                 f"all five directions inside it", color=INK)
    ax.set_xlim(-0.05, 1.52); ax.set_ylim(-0.11, 0.16)
    ax.axis("off")

    # --- right: every pair against the cone width, both regimes
    ax = fig.add_subplot(gs[0, 1])
    inst = R["geometry"]["instantaneous"]["angles"]
    ctx = R["geometry"]["build_context_full"]["angles"]
    pairs = sorted(inst, key=lambda p: inst[p])
    y = np.arange(len(pairs))
    width_i = 2 * psi
    q2 = R["floor"]["build_context"]["q"]
    width_c = 2 * np.degrees(np.arcsin(min(1.0, np.sqrt(q2) / rho)))
    for w, key, tag in ((width_i, "instantaneous", "one instant"),
                        (width_c, "build_context", "across a build")):
        ax.axvline(w, color=REGIME_COLOUR[key], lw=1.0, ls=(0, (4, 2)),
                   zorder=1)
        ax.annotate(f"cone width,\n{tag}: {w:.0f}$^\\circ$", (w, -0.75),
                    xytext=(3, 0), textcoords="offset points", fontsize=6.5,
                    color=REGIME_COLOUR[key], va="center", ha="left",
                    annotation_clip=False)
    ax.scatter([max(inst[p], 1.5e-3) for p in pairs], y, s=26, zorder=3,
               color=REGIME_COLOUR["instantaneous"], label="one instant")
    ax.scatter([ctx[p] for p in pairs], y, s=26, zorder=3,
               color=REGIME_COLOUR["build_context"], label="across a build")
    ax.set_yticks(y)
    ax.set_yticklabels([p.replace("|", " / ") for p in pairs], fontsize=7)
    ax.invert_yaxis()
    ax.set_xscale("log"); ax.set_xlim(1.2e-3, 300)
    ax.set_xlabel("angle between the pair, degrees")
    ax.set_title("a pair is confusable while it sits\ninside the cone", color=INK)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2, fontsize=7)
    _finish(fig, "fig1_cone.png")


# --------------------------------------------------------------------------
# 2. certificate size against signal
# --------------------------------------------------------------------------

def fig2_certificate(R: dict) -> None:
    """The headline: how often the data licenses naming one cause."""
    snrs = [float(s) for s in R["meta"]["snrs"]]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for key, label in (("instantaneous", "one instant"),
                       ("build_context", "across a build")):
        per = R["certificates"][key]
        uniq = [per[f"{s:.0f}"]["unique"] for s in snrs]
        size = [per[f"{s:.0f}"]["mean_size"] for s in snrs]
        c = REGIME_COLOUR[key]
        axes[0].plot(snrs, uniq, "o-", color=c, label=label, zorder=3)
        axes[1].plot(snrs, size, "o-", color=c, label=label, zorder=3)
    axes[0].set_ylabel("certificate names exactly one cause")
    axes[0].set_ylim(0, 1.03)
    axes[1].set_ylabel("causes in the certificate")
    axes[1].set_ylim(0, 5.2)
    axes[1].axhline(5, color=MUTED, lw=0.6, ls=":")
    for ax in axes:
        _logticks(ax, snrs)
        ax.set_xlabel("whitened signal-to-noise ratio  $\\rho$")
        ax.set_xlim(snrs[0] * 0.88, snrs[-1] * 1.14)
        ax.legend(loc="center left")
    fig.suptitle("What a monitoring suite licenses, with and without build "
                 "context", fontsize=9.5, color=INK, y=1.04)
    _finish(fig, "fig2_certificate.png")


# --------------------------------------------------------------------------
# 3. admissibility matrices
# --------------------------------------------------------------------------

def fig3_admissibility(R: dict) -> None:
    """A[k,l]: how often cause l survives a build whose cause was k."""
    faults = R["meta"]["faults"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.1))
    fig.subplots_adjust(wspace=0.55)
    for ax, key, title in (
            (axes[0], "instantaneous", "one instant"),
            (axes[1], "build_context", "across a build")):
        A = np.array(R["admissibility"][key]["28"]["matrix"])
        im = ax.imshow(A, cmap="Blues", vmin=0.0, vmax=1.0, aspect="equal")
        ax.set_xticks(range(5)); ax.set_yticks(range(5))
        ax.set_xticklabels(faults, rotation=35, ha="right")
        ax.set_yticklabels(faults)
        ax.set_title(title, color=INK)
        ax.grid(False)
        for i in range(5):
            for j in range(5):
                ax.text(j, i, f"{A[i, j]:.2f}", ha="center", va="center",
                        fontsize=6.5,
                        color=SURFACE if A[i, j] > 0.55 else INK)
        if ax is axes[0]:
            ax.set_ylabel("the cause that was actually present")
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02,
                 label="probability the column's cause survives")
    fig.suptitle("Which causes travel together, at $\\rho = 28$",
                 fontsize=9.5, color=INK, y=1.02)
    _finish(fig, "fig3_admissibility.png")


# --------------------------------------------------------------------------
# 4. the signal each pair would need
# --------------------------------------------------------------------------

def fig4_required(R: dict) -> None:
    """Required signal-to-noise per pair, and the pair that needs infinity."""
    inst = R["floor"]["instantaneous"]["required_snr"]
    ctx = R["floor"]["build_context"]["required_snr"]
    pairs = sorted(inst, key=lambda p: (inst[p] is None, inst[p] or 0))
    y = np.arange(len(pairs))
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    cap = 3000.0
    for off, (d, label, colour) in enumerate((
            (ctx, "across a build", REGIME_COLOUR["build_context"]),
            (inst, "one instant", REGIME_COLOUR["instantaneous"]))):
        vals = [d[p] for p in pairs]
        yy = y + (off - 0.5) * 0.36
        finite = [(a, b) for a, b in zip(yy, vals) if b is not None]
        ax.barh([a for a, _ in finite], [b for _, b in finite], height=0.32,
                color=colour, label=label, zorder=3)
        for a, b in zip(yy, vals):
            if b is None:
                ax.barh([a], [cap], height=0.32, color=colour, alpha=0.22,
                        zorder=2, hatch="////", edgecolor=colour, lw=0)
                ax.text(7.0, a, "no signal suffices", ha="left",
                        va="center", fontsize=6.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([p.replace("|", " / ") for p in pairs])
    ax.set_xscale("log")
    ax.set_xlim(5, cap)
    ax.set_xlabel("whitened signal-to-noise ratio needed to tell the pair apart")
    ax.invert_yaxis()
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)
    ax.set_title("What each pair would cost, as signal", color=INK)
    _finish(fig, "fig4_required.png")


# --------------------------------------------------------------------------
# 5. probing against build context
# --------------------------------------------------------------------------

def fig5_probing(R: dict) -> None:
    """Deliberate probes against structure the machine already records."""
    rows = [(k, v) for k, v in R["probing"].items()]
    labels = [k for k, _ in rows]
    second = [v["second"] for _, v in rows]
    worst = [v["worst"] for _, v in rows]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    colours = [REGIME_COLOUR["build_context"] if "build context" in l
               else REGIME_COLOUR["instantaneous"] for l in labels]
    ax.barh(y, second, height=0.5, color=colours, zorder=3)
    ax.scatter(worst, y, marker="D", s=14, color=INK, zorder=4,
               label="worst pair, power / gas, which no probe moves")
    ax.axvline(FLOOR_DEG, color=INK, lw=0.9, ls=(0, (4, 2)), zorder=5)
    ax.annotate("ten degree floor", (FLOOR_DEG, -0.62), xytext=(4, 0),
                textcoords="offset points", fontsize=7, color=INK,
                va="center", ha="left", annotation_clip=False)
    for a, b in zip(y, second):
        ax.text(b + 0.6, a, f"{b:.1f}°", va="center", fontsize=7, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("second-worst pairwise angle, degrees")
    ax.set_xlim(-0.6, 34)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22))
    ax.set_title("Probing the operating point against reading the build",
                 color=INK)
    _finish(fig, "fig5_probing.png")


# --------------------------------------------------------------------------
# 6. why the test is built on the exact model
# --------------------------------------------------------------------------

def fig6_coverage(R: dict) -> None:
    """Coverage of the exact profile test against the linearised one."""
    snrs = [float(s) for s in R["meta"]["snrs"]]
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    per = R["certificates"]["instantaneous"]
    exact = [per[f"{s:.0f}"]["coverage"] for s in snrs]
    linear = [per[f"{s:.0f}"]["linear_coverage"] for s in snrs]
    ax.axhline(0.95, color=MUTED, lw=0.8, ls=":", zorder=1)
    ax.annotate("nominal 0.95", (snrs[0], 0.952), fontsize=7, color=INK2)
    ax.plot(snrs, exact, "o-", color=REGIME_COLOUR["build_context"],
            label="profiled through the exact model", zorder=3)
    ax.plot(snrs, linear, "s--", color=REGIME_COLOUR["instantaneous"],
            label="profiled through the tangent", zorder=3)
    _logticks(ax, snrs)
    ax.set_xlabel("whitened signal-to-noise ratio  $\\rho$")
    ax.set_ylabel("coverage of the 95 % certificate")
    ax.set_ylim(0.6, 1.0)
    ax.legend(loc="lower left")
    ax.set_title("A linearised certificate rules out the true cause",
                 color=INK)
    _finish(fig, "fig6_coverage.png")


FIGURES = {1: fig1_geometry, 2: fig2_certificate, 3: fig3_admissibility,
           4: fig4_required, 5: fig5_probing, 6: fig6_coverage}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, action="append")
    args = ap.parse_args()
    R = load()
    print("Drawing figures from results.json")
    for n, fn in FIGURES.items():
        if args.only and n not in args.only:
            continue
        fn(R)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
