"""Generate the paper's figures. One function per figure, all writing to ../figures.

Figure list, in the order the argument runs:

  fig1  the two tiers side by side: every fault pair instantaneously and after
        the enlarged observation. This is the headline.
  fig2  worst-pair angle against profile contrast, which is the honest form of
        the headline - a threshold, not a point value.
  fig3  angle against fault magnitude, instantaneous versus enlarged. Shows that
        the enlarged result is stable in magnitude where the instantaneous one
        swings non-monotonically. This is the locality limitation, answered.
  fig4  Route B: robustness to profile misspecification by sensor subset. The
        answer to "what does another sensor buy" once rank stops being the
        constraint.
  fig5  the constant-energy-density sweep, showing length carrying the
        information that width and depth do not - the mechanism behind fig4's
        recommendation.
  fig6  the diagnosability matrix: every pair in both regimes, classified. The
        abstract's headline deliverable.
  fig7  Route C: what each idealised added measurement unlocks, against the
        free alternative.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from diagnosability import jacobian
from faults import FAULT_NAMES
from locality_routeA import (SIGMAS, big_sigmas, instantaneous_secants,
                             pair_angles, response_curves, secant_directions)
from observables import enlarged_jacobian, scan_plan
from profile_sweep import CONTRASTS, MAX_REACH
from route_b import RATIO_SETS, SUBSETS, full_jacobian, misspecification_error
from sensors import ALL_SENSOR_NAMES
from validation import constant_ved_sweep

OUT = os.path.join(os.path.dirname(__file__), "..", "figures")
PAIRS = [(a, b) for i, a in enumerate(FAULT_NAMES)
         for b in FAULT_NAMES[i + 1:]]

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 9,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})
C_INST, C_BIG = "#B4453C", "#2E5E7E"


def _save(fig, name):
    path = os.path.abspath(os.path.join(OUT, name))
    fig.savefig(path)
    plt.close(fig)
    print(f"   wrote {path}")
    return path


def fig1(J, plan):
    """Pairwise angles, instantaneous vs enlarged, every pair."""
    ai = pair_angles(J, SIGMAS)
    ab = pair_angles(enlarged_jacobian(J, plan), big_sigmas(plan))
    order = sorted(PAIRS, key=lambda p: ab[p])
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(4.4, 2.8))
    ax.barh(y - 0.2, [ai[p] for p in order], 0.38, color=C_INST,
            label="instantaneous (3 observables)")
    ax.barh(y + 0.2, [ab[p] for p in order], 0.38, color=C_BIG,
            label="enlarged (15 observables)")
    ax.axvline(10, ls=":", lw=0.8, color="0.4")
    ax.text(10.6, len(order) - 0.6, "10$\\degree$", fontsize=6, color="0.3")
    for k, p_ in enumerate(order):
        if ai[p_] < 0.05:
            ax.annotate("0.00$\\degree$ - exactly parallel", (0.6, k - 0.2),
                        va="center", fontsize=6, color=C_INST)
    ax.set_yticks(y, [f"{a} / {b}" for a, b in order])
    ax.set_xlabel("angle between whitened fault signatures (degrees)")
    ax.set_xlim(0, 90)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title("Every fault pair becomes separable without new hardware")
    return _save(fig, "fig1_two_tiers.png")


def fig2(curves, nominal, plan):
    """Worst-pair angle against profile contrast."""
    from observables import modulations
    xs, worst, cond = [], [], []
    for c in CONTRASTS:
        cc = 1e-9 if c == 0.0 else c
        if float(np.max(np.abs(0.002 * modulations(plan, contrast=cc)))) > MAX_REACH:
            continue
        D = secant_directions(0.002, plan, curves, nominal, contrast=cc)
        a = pair_angles(D, big_sigmas(plan))
        s = np.linalg.svd(D / big_sigmas(plan)[:, None], compute_uv=False)
        xs.append(c)
        worst.append(min(a.values()))
        cond.append(s[0] / s[s > s.max() * 1e-6][-1])
    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    ax.plot(xs, worst, "o-", color=C_BIG, ms=3.5, lw=1.2)
    ax.axhline(10, ls=":", lw=0.8, color="0.4")
    ax.annotate("conventional 10$\\degree$ floor", (0.05, 11), fontsize=6, color="0.3")
    ax.axvline(1.0, ls="--", lw=0.8, color="0.6")
    ax.annotate("asserted\nprofile strength", (1.03, 3), fontsize=6, color="0.4")
    ax.set_xlabel("profile contrast  (severity spans $e^{2c}$ across the build)")
    ax.set_ylabel("worst pair angle (degrees)")
    ax.set_title("The claim is a threshold, not a number")
    return _save(fig, "fig2_contrast_threshold.png")


def fig3(curves, nominal, plan):
    """Angle against fault magnitude, instantaneous vs enlarged."""
    mags = np.array([0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20])
    bs = big_sigmas(plan)
    wi, wb = [], []
    for f in mags:
        wi.append(min(pair_angles(instantaneous_secants(f, curves, nominal),
                                  SIGMAS).values()))
        wb.append(min(pair_angles(secant_directions(f, plan, curves, nominal),
                                  bs).values()))
    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    ax.semilogx(mags * 100, wi, "s-", color=C_INST, ms=3.5, lw=1.2,
                label="instantaneous")
    ax.semilogx(mags * 100, wb, "o-", color=C_BIG, ms=3.5, lw=1.2,
                label="enlarged")
    ax.axhline(10, ls=":", lw=0.8, color="0.4")
    ax.set_xlabel("fault index $f$ (% — a common scale only for power and speed)")
    ax.set_ylabel("worst pair angle (degrees)")
    ax.set_ylim(0, 50)
    ax.set_xticks(mags * 100, [f"{m*100:g}" for m in mags])
    ax.minorticks_off()
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.02, 0.78))
    ax.set_title("Diagnosability is local - unless context is used")
    return _save(fig, "fig3_magnitude.png")


def fig4(plan):
    """Robustness to profile misspecification, by sensor subset."""
    J_all, _ = full_jacobian()
    names = list(ALL_SENSOR_NAMES)
    ratios = RATIO_SETS["study default"]
    labels = ["photodiode\nonly", "camera\nonly", "photodiode\n+ pyrometer",
              "all three\n(baseline)", "+ split the\ncamera (free)", "everything"]
    keys = ["photodiode only", "camera only", "photodiode + pyrometer",
            "all three (baseline)", "+ split the camera (free)", "everything"]
    deltas = (0.1, 0.3, 0.5)
    fig, ax = plt.subplots(figsize=(4.6, 2.6))
    x = np.arange(len(keys))
    for i, d in enumerate(deltas):
        vals = [misspecification_error(J_all, names, SUBSETS[k], ratios, plan,
                                       delta=d)[1] for k in keys]
        ax.bar(x + (i - 1) * 0.27, vals, 0.25,
               color=plt.cm.Blues(0.4 + 0.25 * i), label=f"{d:.0%} profile error")
    ax.set_xticks(x, labels)
    ax.set_ylabel("worst-case error in\nrecovered fault vector")
    ax.legend(frameon=False, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, 1.14))
    ax.set_title("What extra sensors buy is robustness, not rank", pad=28)
    ax.set_ylim(0, 1.25)
    return _save(fig, "fig4_robustness.png")


def fig5():
    """Constant energy density: length carries what width and depth do not."""
    _, rows = constant_ved_sweep()
    p = np.array([r["power"] for r in rows])
    fig, ax = plt.subplots(figsize=(3.8, 2.5))
    for key, label, c, m in (("width", "width", "#B4453C", "s"),
                             ("corrected_depth", "depth (keyhole-corrected)",
                              "#7A6A3A", "^"),
                             ("length", "length", "#2E5E7E", "o")):
        v = np.array([r[key] for r in rows]) * 1e6
        ax.plot(p, v / v[0], m + "-", color=c, ms=3.5, lw=1.2, label=label)
    kh = [r["power"] for r in rows if r["keyholing"]]
    if kh:
        ax.axvspan(min(kh) - 10, p.max() + 15, color="0.9", zorder=0)
        ax.text(min(kh) - 5, 2.3, "keyhole", fontsize=6, color="0.4")
    ax.set_xlabel("laser power (W), speed compensating to hold $P/(v\\sigma^2)$ fixed")
    ax.set_ylabel("dimension, relative to 150 W")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("At fixed energy density, length is the discriminator")
    return _save(fig, "fig5_constant_ved.png")


def fig6(J, plan):
    """The diagnosability matrix, both regimes."""
    from matrix import FLOOR, classify
    ri, _ = classify(("photodiode", "camera", "pyrometer"), regime="instantaneous")
    ra, _ = classify(("photodiode", "camera", "pyrometer"), regime="accumulated")
    order = sorted(PAIRS, key=lambda p: ri[p]["instant"])
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(4.8, 2.9))
    ax.barh(y - 0.2, [ri[p]["instant"] for p in order], 0.38, color=C_INST,
            label="instantaneous (per segment)")
    ax.barh(y + 0.2, [ra[p]["enlarged"] for p in order], 0.38, color=C_BIG,
            label="accumulated (build context)")
    ax.axvline(FLOOR, ls=":", lw=0.9, color="0.35")
    ax.text(FLOOR + 0.8, len(order) - 0.4, "separation floor", fontsize=6, color="0.3")
    for k, p in enumerate(order):
        if ri[p]["class"] == 2:
            ax.text(max(ri[p]["instant"], ra[p]["enlarged"]) + 1.5, k, "class 2",
                    fontsize=6, color=C_INST, ha="left", va="center", style="italic")
        if ri[p]["instant"] < 0.05:
            ax.text(0.8, k - 0.2, "0.00$\\degree$ - identical", fontsize=6,
                    color=C_INST, va="center")
    ax.set_yticks(y, [f"{a} / {b}" for a, b in order])
    ax.set_xlabel("separation angle (degrees)")
    ax.set_xlim(0, 80)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title("Five pairs need a measurement per segment, none over a build",
                 fontsize=8.5)
    return _save(fig, "fig6_matrix.png")


def fig7(J, plan):
    """What an added measurement unlocks, versus the free alternative."""
    from matrix import FLOOR
    from route_c_added_sensor import add_direct_sensor
    from locality_routeA import big_sigmas
    from observables import enlarged_jacobian
    base = pair_angles(J, SIGMAS)
    Jn, sn = add_direct_sensor(J, SIGMAS, ["gas", "layer"], 0.05)
    added = pair_angles(Jn, sn)
    routeA = pair_angles(enlarged_jacobian(J, plan), big_sigmas(plan))
    order = sorted(PAIRS, key=lambda p: base[p])[:6]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    for i, (vals, lab, c) in enumerate((
            ([base[p] for p in order], "existing suite, per segment", C_INST),
            ([added[p] for p in order], "+ 2 idealised cause sensors", "#8C8C8C"),
            ([routeA[p] for p in order], "build context (free)", C_BIG))):
        ax.bar(x + (i - 1) * 0.27, vals, 0.25, color=c, label=lab)
    ax.axhline(FLOOR, ls=":", lw=0.9, color="0.35")
    ax.set_xticks(x, [f"{a}\n{b}" for a, b in order], fontsize=6.5)
    ax.set_ylabel("separation angle (degrees)")
    ax.legend(frameon=False, ncol=1, loc="upper left", fontsize=6.5)
    ax.set_title("The free method beats two perfect added sensors")
    ax.annotate("added sensors do nothing here - neither says\nanything about power versus speed",
                xy=(4.0, 9), xytext=(3.4, 50), fontsize=6, color="0.3",
                ha="center", va="bottom",
                arrowprops=dict(arrowstyle="->", lw=0.7, color="0.5"))
    ax.set_ylim(0, 98)
    return _save(fig, "fig7_added_sensor.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    plan = scan_plan()
    J, _ = jacobian()
    print("generating figures")
    fig1(J, plan)
    fig5()
    fig4(plan)
    fig6(J, plan)
    fig7(J, plan)
    curves, nominal = response_curves()
    fig2(curves, nominal, plan)
    fig3(curves, nominal, plan)
    print("done")
