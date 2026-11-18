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

NAMED = {"structural": "s", "operating point": "D", "couplings": "^",
         "couplings control": "v", "noise model": "o", "noise level": "o",
         "missing channel": "P", "spurious channel": "X"}


def draw(ax, rows, rho=28.0):
    b = float(th.delta_max(rho, 3))
    acc = [r for r in rows if r["family"] == "validation-equivalent"]
    rej = [r for r in rows if r["family"] == "region-rejected"]
    y = lambda R: np.maximum([r["delta_max"] for r in R], FLOOR_DEG)
    x = lambda R: [r["pred_rms"] for r in R]
    ax.scatter(x(rej), y(rej), s=14, c=MUTED, lw=0, label="rejected by the data")
    ax.scatter(x(acc), y(acc), s=16, c=BLUE, lw=0,
               label="accepted by the data")
    first = True
    for fam, m in NAMED.items():
        R = [r for r in rows if r["family"] == fam]
        if not R:
            continue
        ax.scatter(x(R), y(R), s=34, marker=m, facecolor=ORANGE,
                   edgecolor="white", lw=0.6,
                   label="named alternatives" if first else None)
        first = False
    ax.axhline(b, color=INK, lw=1.0, ls=(0, (4, 3)))
    ax.text(ax.get_xlim()[1] if False else 0.99, b * 1.15,
            f"budget at $\\rho$ = {rho:.0f}: {b:.1f}$^\\circ$",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            color=INK, fontsize=8)
    ax.set_yscale("log")
    ax.set_xlabel("prediction error on healthy builds, RMS (%)", color=INK2)
    ax.set_ylabel("largest directional error (deg)", color=INK2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, which="major", color="#ecebe8", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower right")


def main():
    rows = json.loads((HERE / "_study.json").read_text())["rows"]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=200)
    draw(ax, rows)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"fig1_fidelity.{ext}", bbox_inches="tight")
    print("wrote", OUTDIR / "fig1_fidelity.png")


if __name__ == "__main__":
    main()
