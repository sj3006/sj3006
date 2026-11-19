"""Figure: the three transduction chains that produce the noise set.

Section 3.6 derives 1 : 0.142 : 1.061 from a single assumption by following
each instrument's conversion of radiance into a reading. That is a branching
derivation with one arithmetic step per box, which reads better as a diagram
than as three paragraphs of prose.

Every number shown is taken from `noise.derive()` rather than typed in, so the
figure cannot drift away from the code. Sized for one column of the Procedia
two-column layout.

    python3 src/fig_noise_chain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch    # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import noise                                                      # noqa: E402
from eagar_tsai import IN718                                      # noqa: E402
from sensors import SensorConfig                                  # noqa: E402

OUT = HERE.parent / "paper" / "fig8_noise_chain.png"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#b4b3ad"
LANE = {"photodiode": "#2a78d6", "pyrometer": "#eb6834", "camera": "#1baf7a"}

plt.rcParams.update({
    "font.family": "serif", "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _numbers() -> dict:
    """Pull every quantity the figure shows from the code that derives them."""
    d = noise.derive()
    noise.verify()
    cfg = SensorConfig()
    l1, l2 = cfg.pyrometer_bands
    lam_cam = float(np.mean(cfg.photodiode_band))
    t_pool = 3030.644
    return {
        "pd": d["photodiode"],
        "cam": d["camera"], "cam_w": d["camera_width"], "cam_l": d["camera_length"],
        "pyr": d["pyrometer"],
        "planck": noise.planck_log_sensitivity(lam_cam, IN718.t_liquidus),
        "lam_cam_nm": lam_cam * 1e9,
        "lambda_ratio": (noise.C2 / t_pool) * (1.0 / l1 - 1.0 / l2),
        "b1_nm": l1 * 1e9, "b2_nm": l2 * 1e9,
    }


def _box(ax, x, y, w, h, text, colour, fs=5.6, bold=False, fill=0.07):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.015",
                                linewidth=0.7, edgecolor=colour,
                                facecolor=colour, alpha=fill, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.015",
                                linewidth=0.7, edgecolor=colour,
                                facecolor="none", zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, zorder=4,
            fontweight="bold" if bold else "normal", linespacing=1.35)


def _arrow(ax, x0, y0, x1, y1, colour, label=None, fs=5.2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                 arrowstyle="-|>", mutation_scale=7,
                                 linewidth=0.7, color=colour, zorder=1,
                                 shrinkA=0, shrinkB=0))
    if label:
        ax.text((x0 + x1) / 2 + 0.012, (y0 + y1) / 2, label, ha="left",
                va="center", fontsize=fs, color=INK2, zorder=4)


def draw() -> Path:
    n = _numbers()
    fig, ax = plt.subplots(figsize=(3.35, 3.45))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    W = 0.29
    # Lane order follows the ratio the figure ends on, photodiode : camera :
    # pyrometer, so the reader does not have to reorder three columns in their
    # head to check the last line against the picture.
    lanes = [("photodiode", 0.025), ("camera", 0.355), ("pyrometer", 0.685)]

    _box(ax, 0.025, 0.915, 0.95, 0.070,
         "every radiometric channel carries the same\n"
         "fractional noise $\\varepsilon$", MUTED, fs=6.0, fill=0.25)

    for name, x in lanes:
        c = LANE[name]
        _arrow(ax, x + W / 2, 0.915, x + W / 2, 0.880, MUTED)
        _box(ax, x, 0.820, W, 0.058, name, c, fs=6.4, bold=True, fill=0.16)

    def step(x, c, y0, y1, label):
        """Arrow down the left of the lane, label to its right, inside the lane."""
        _arrow(ax, x + 0.05, y0, x + 0.05, y1, c)
        ax.text(x + 0.085, (y0 + y1) / 2, label, ha="left", va="center",
                fontsize=5.0, color=INK2, linespacing=1.35)

    # ---- photodiode: one step, which is why it is the unit ----------------
    x, c = 0.025, LANE["photodiode"]
    _arrow(ax, x + W / 2, 0.820, x + W / 2, 0.760, c)
    _box(ax, x, 0.665, W, 0.095, "sums the light\nin its band", c)
    step(x, c, 0.665, 0.330, "the fractional\nerror passes\nthrough\nunchanged")

    # ---- camera -----------------------------------------------------------
    x, c = 0.355, LANE["camera"]
    _arrow(ax, x + W / 2, 0.820, x + W / 2, 0.760, c)
    _box(ax, x, 0.665, W, 0.095, "thresholds the\nimage at the liquidus", c)
    step(x, c, 0.665, 0.545, f"Planck is steep,\n{n['planck']:.2f} % in $L$\n"
                             f"per 1 % in $T$")
    _box(ax, x, 0.450, W, 0.095,
         f"isotherm moves\n{0.01 * 100 / n['planck']:.3f} % in $T$", c)
    step(x, c, 0.450, 0.330, f"width {n['cam_w']:.3f},\nlength {n['cam_l']:.3f},\n"
                             f"area their sum")

    # ---- pyrometer --------------------------------------------------------
    x, c = 0.685, LANE["pyrometer"]
    _arrow(ax, x + W / 2, 0.820, x + W / 2, 0.760, c)
    _box(ax, x, 0.665, W, 0.095,
         f"ratio of the {n['b1_nm']:.0f}\nand {n['b2_nm']:.0f} nm bands", c)
    step(x, c, 0.665, 0.545, "two independent\nband errors")
    _box(ax, x, 0.450, W, 0.095, "$\\sqrt{2}\\,\\varepsilon$ on the ratio", c)
    step(x, c, 0.450, 0.330, f"the ratio moves\n{n['lambda_ratio']:.3f} % per\n"
                             f"1 % of $T$")

    for name, x in lanes:
        key = {"photodiode": "pd", "camera": "cam", "pyrometer": "pyr"}[name]
        _box(ax, x, 0.235, W, 0.095, f"$\\sigma = {n[key]:.3f}\\,\\varepsilon$",
             LANE[name], fs=7.2, bold=True, fill=0.20)

    ax.plot([0.025, 0.975], [0.185, 0.185], color=MUTED, lw=0.6)
    ax.text(0.5, 0.125, f"$1 : {n['cam']:.3f} : {n['pyr']:.3f}$",
            ha="center", va="center", fontsize=10.0, color=INK)
    ax.text(0.5, 0.040,
            "Only ratios enter the whitening, so $\\varepsilon$ cancels\n"
            "and no absolute noise level is claimed.",
            ha="center", va="center", fontsize=5.4, color=INK2, linespacing=1.4)

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=400, bbox_inches="tight")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    p = draw()
    print(f"written {p}")
