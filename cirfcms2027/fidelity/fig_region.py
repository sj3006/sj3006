"""Figure 3: the validation region in the plane of the identifiable groups.

The thermal model depends on absorptivity, conductivity and heat capacity only
through two groups, absorbed power per unit conductivity (`mu / k`) and
diffusivity (`k / cp`, the density being fixed); scaling all three together
changes nothing (LABNOTEBOOK entry 5). So every twin is a point in this plane.
Small points: the 2048 Sobol samples, accepted by the data (light blue) or
rejected (grey). Large points: the accepted twins scored in the study, shaded by
their largest directional error on a log scale. The star is the truth.

Writes `paper/figures/fig3_region.png` and `.pdf`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm   # noqa: E402
import numpy as np                                                # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

OUT = HERE / "paper" / "figures"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#b4b3ad", "#ecebe8"
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#cfe1f7", "#7fb0ea", "#2a78d6", "#1a4f93", "#0d2b52"])


def groups(mu, k, cp, ref):
    return (np.log10((mu / k) / (ref[0] / ref[1])),
            np.log10((k / cp) / (ref[1] / ref[2])))


def main(path: str | None = None):
    import twins as tw_mod
    R = tw_mod.REFERENCE
    ref = (R.absorptivity, R.k, R.cp)
    reg = json.loads((HERE / "_region.json").read_text())
    X = np.asarray(reg["rows"], float)
    acc = X[:, 4] <= reg["threshold"]
    src = Path(path) if path else HERE / "_study.json"
    rows = [r for r in json.loads(src.read_text())["rows"]
            if r["family"] == "validation-equivalent"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0), dpi=200)
    gx, gy = groups(X[:, 0], X[:, 1], X[:, 2], ref)
    ax.scatter(gx[~acc], gy[~acc], s=4, c="#dddcd7", lw=0, label="rejected by the data")
    ax.scatter(gx[acc], gy[acc], s=5, c="#cfe1f7", lw=0, label="accepted by the data")
    mu = np.array([r["twin"]["absorptivity"] for r in rows])
    k = np.array([r["twin"]["k"] for r in rows])
    cp = np.array([r["twin"]["cp"] for r in rows])
    d = np.array([r["delta_max"] for r in rows])
    sx, sy = groups(mu, k, cp, ref)
    sc = ax.scatter(sx, sy, s=22, c=d, cmap=BLUES, norm=LogNorm(1.0, 90.0),
                    edgecolor="white", lw=0.5, zorder=3)
    ax.scatter([0], [0], marker="*", s=160, c=INK, edgecolor="white", lw=0.8,
               zorder=4, label="truth (calibrated model)")
    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label("largest directional error of an accepted twin (deg)",
                 color=INK2, fontsize=8)
    cb.set_ticks([1, 2, 5, 10, 20, 50])
    cb.set_ticklabels(["1", "2", "5", "10", "20", "50"])
    cb.ax.tick_params(labelsize=7, colors=INK2)
    cb.outline.set_visible(False)
    ax.set_xlabel("absorbed power per conductivity, log$_{10}$ relative to truth",
                  color=INK2, fontsize=8.5)
    ax.set_ylabel("diffusivity, log$_{10}$ relative to truth", color=INK2,
                  fontsize=8.5)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7.5, loc="lower left",
              bbox_to_anchor=(0.0, 1.0), ncol=3, handletextpad=0.3,
              columnspacing=1.0, markerscale=1.5)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig3_region.{ext}", bbox_inches="tight")
    print("wrote", OUT / "fig3_region.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
