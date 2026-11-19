"""Figure 1: prediction error against directional error, every twin.

One point per twin. Horizontal: how far the twin's healthy-build predictions
are from the truth's (root-mean-square relative difference, %), which is what
validation can see. Vertical: the twin's largest directional error over the
five faults (degrees, log scale), which is what the certificate pays for.
The dashed line is the directional budget at rho = 28 from the Corollary: a
twin above it holds the nominal 95 % certificate below 90 % coverage for at
least one fault.

Three groups only, so the colours stay distinguishable for every reader:
twins the data accept, twins the data reject, and the named alternatives. The
diagnosis-only families sit exactly at zero prediction error, by construction.

Run `study.py` first. Writes `fig1_fidelity.png` and `.pdf` into `paper/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theory as th                                               # noqa: E402

OUTDIR = HERE / "paper" / "figures"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b4b3ad"
BLUE, ORANGE = "#2a78d6", "#eb6834"
FLOOR_DEG = 1e-3      # zero directional error drawn here on the log axis

NAMED = {"structural": "s", "prediction only": ">", "one parameter": "d",
         "operating point": "D", "numerical resolution": "*", "couplings": "^",
         "couplings control": "v", "noise model": "o", "noise level": "o",
         "missing channel": "P", "spurious channel": "X"}


XMAX = 25.0          # rejected twins beyond this are counted, not drawn
NUM_FLOOR = 0.17     # numerical floor of the direction on the study grid, deg


def draw(ax, rows, rho=28.0):
    b = float(th.delta_max(rho, 3))
    acc = [r for r in rows if r["family"] == "validation-equivalent"]
    rej = [r for r in rows if r["family"] == "region-rejected"]
    beyond = sum(r["pred_rms"] > XMAX for r in rej)
    rej = [r for r in rej if r["pred_rms"] <= XMAX]
    y = lambda R: np.maximum([r["delta_max"] for r in R], FLOOR_DEG)
    x = lambda R: [r["pred_rms"] for r in R]
    ax.axhspan(FLOOR_DEG / 2, NUM_FLOOR, color="#f4f3f0", lw=0, zorder=0)
    ax.text(XMAX * 0.99, NUM_FLOOR / 1.2, "below the numerical floor",
            ha="right", va="top", fontsize=7, color=INK2)
    ax.scatter(x(rej), y(rej), s=14, c=MUTED, lw=0, label="rejected by the data")
    ax.scatter(x(acc), y(acc), s=16, c=BLUE, lw=0, label="accepted by the data")
    first = True
    for fam, m in NAMED.items():
        R = [r for r in rows if r["family"] == fam]
        if not R:
            continue
        ax.scatter(x(R), y(R), s=30, marker=m, facecolor=ORANGE,
                   edgecolor="white", lw=0.6, zorder=3,
                   label="named twins" if first else None)
        first = False
    ax.axhline(b, color=INK, lw=1.0, ls=(0, (4, 3)))
    ax.text(XMAX * 0.99, b * 1.15, f"budget at \u03c1 = {rho:.0f}: {b:.1f}\u00b0",
            ha="right", va="bottom", color=INK, fontsize=8)
    # direct labels for the named groups
    kh = sorted(r["pred_rms"] for r in rows if r["family"] == "prediction only")
    if kh:
        tx, ty = (kh[0] + kh[-1]) / 2, 0.006
        ax.text(tx, ty, "keyhole coefficient (prediction only)", fontsize=7,
                color=INK2, ha="center", va="bottom")
        for xv in (kh[0], kh[-1]):
            ax.annotate("", xy=(xv, FLOOR_DEG * 1.25), xytext=(tx, ty),
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.annotate("diagnosis-only quantities", xy=(0.15, 0.6), xytext=(3.2, 0.03),
                fontsize=7, color=INK2, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.annotate("operating point and\none parameter, \u00b110 % / \u00b15 %",
                xy=(2.0, 0.9), xytext=(4.5, 0.25), fontsize=7, color=INK2,
                ha="left", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    st = [r for r in rows if r["family"] == "structural"]
    if st:
        ax.annotate("structural\nalternatives", xy=(st[0]["pred_rms"], st[0]["delta_max"]),
                    xytext=(18.5, 9), fontsize=7, color=INK2, ha="left",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    if beyond:
        ax.text(XMAX * 0.99, 150, f"{beyond} rejected twins beyond {XMAX:.0f} % not shown",
                ha="right", va="bottom", fontsize=7, color=INK2)
    ax.set_yscale("log")
    ax.set_ylim(FLOOR_DEG / 2, 250)
    ax.set_xlim(-0.8, XMAX)
    yt = [FLOOR_DEG, 0.01, 0.1, 1, 10, 100]
    ax.set_yticks(yt)
    ax.set_yticklabels(["0", "0.01", "0.1", "1", "10", "100"])
    ax.minorticks_off()
    ax.set_xlabel("prediction error on healthy builds, RMS (%)", color=INK2)
    ax.set_ylabel("largest directional error (deg)", color=INK2)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, which="major", color="#ecebe8", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7.5, loc="lower left",
              bbox_to_anchor=(0.0, 1.0), ncol=3, handletextpad=0.3,
              columnspacing=1.2)


def main(path: str | None = None):
    src = Path(path) if path else HERE / "_study.json"
    rows = json.loads(src.read_text())["rows"]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.0, 4.0), dpi=200)
    draw(ax, rows)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"fig1_fidelity.{ext}", bbox_inches="tight")
    print("wrote", OUTDIR / "fig1_fidelity.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
