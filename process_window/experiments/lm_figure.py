"""Figures for the language-model application.

fig_lm_surface: the two measured failure-rate surfaces (one sequential
blue scale, shared) and the safe region with the part certified by our
method after a given number of generations (pilot included).
fig_lm_budget: certified fraction of the safe region vs generations for
every method in results/lm/lm_fixed_budget.csv.

Run from process_window/ after experiments/exp_lm.py:
    python3 experiments/lm_figure.py [--budget 8000] [--path results/lm/surface_scores.npz]
For the nested 23 x 23 grid (pilot at the 12 x 12 settings):
    python3 experiments/lm_figure.py --path results/lm/surface_scores_23.npz --pilot-stride 2
(outputs get the surface file's suffix, e.g. fig_lm_surface_23.pdf).
"""

import argparse
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, ListedColormap  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.lm_scenario import PATH, make_lm_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE_RAMP = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("seq_blue", BLUE_RAMP)
# Categorical slots in fixed order; each method keeps the color it has in
# the other paper figures (final.py SERIES), new entities take the next slot.
SERIES = {"ours": "#2a78d6", "ours, no simulator": "#eb6834", "no ordering": "#1baf7a",
          "full grid (Bonferroni)": "#e87ba4", "full grid (fixed sequence)": "#008300"}
SAFE_FILL, CERT_FILL = "#e4e3df", "#2a78d6"


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.title.set_color(INK)


def _extent(sc):
    t, p = sc.power, sc.speed
    dt, dp = (t[1] - t[0]) / 2, (p[1] - p[0]) / 2
    return [t[0] - dt, t[-1] + dt, p[0] - dp, p[-1] + dp]


def surface_figure(path, budget, seed=0, pilot_stride=1, suffix=""):
    sc = make_lm_scenario(0.10, "pilot", path=path, pilot_stride=pilot_stride)
    n = sc.truth["degenerate"].shape[0]
    c = ConeCertifier(sc, rule="cone", weights="ensemble", alloc="edge", target_q=0.7, batch=2 * n,
                      coupons0=sc.meta["pilot_coupons"], rng=np.random.default_rng(seed))
    c.run(budget)
    W, C = sc.true_window(), c.window()
    ext = _extent(sc)
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), constrained_layout=True)
    fig.patch.set_facecolor(SURFACE)
    titles = {"degenerate": "Repetition rate", "incoherent": "Incoherence rate"}
    for ax, m in zip(axes[:2], ("degenerate", "incoherent")):
        im = ax.imshow(sc.truth[m].T, origin="lower", extent=ext, aspect="auto", cmap=SEQ, vmin=0, vmax=1)
        ax.contour(sc.power, sc.speed, sc.truth[m].T, levels=[sc.eps[m]], colors=INK, linewidths=1.2)
        ax.set_title(f"{titles[m]} (line: tolerance {sc.eps[m]:.0%})", fontsize=9)
        _style(ax)
    cb = fig.colorbar(im, ax=axes[:2], shrink=0.9, pad=0.02)
    cb.set_label("failure rate", color=INK, fontsize=8)
    cb.ax.tick_params(colors=INK2, labelsize=8)
    cb.outline.set_visible(False)
    # Region panel: unsafe = surface, safe = gray, certified = blue.
    reg = np.where(C, 2, np.where(W, 1, 0)).T
    axes[2].imshow(reg, origin="lower", extent=ext, aspect="auto",
                   cmap=ListedColormap([SURFACE, SAFE_FILL, CERT_FILL]), vmin=0, vmax=2)
    # Surface gaps between cells keep the grid readable (thinner on fine grids).
    t, p = sc.power, sc.speed
    gap = 1.0 if n <= 12 else 0.5
    for x in (t[:-1] + t[1:]) / 2:
        axes[2].axvline(x, color=SURFACE, lw=gap)
    for y in (p[:-1] + p[1:]) / 2:
        axes[2].axhline(y, color=SURFACE, lw=gap)
    axes[2].set_title(f"Certified after {c.coupons / 1000:.1f}k generations", fontsize=9)
    _style(axes[2])
    from matplotlib.patches import Patch
    axes[2].legend(handles=[Patch(color=CERT_FILL, label=f"certified ({int(C.sum())})"),
                            Patch(color=SAFE_FILL, label=f"safe, not certified ({int((W & ~C).sum())})"),
                            Patch(facecolor=SURFACE, edgecolor=INK2, label="unsafe")],
                   fontsize=7, frameon=False, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    for ax in axes:
        ax.set_xlabel("temperature")
    axes[0].set_ylabel("top-p")
    for ext_ in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_lm_surface{suffix}.{ext_}"), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("certified", int(C.sum()), "of", int(W.sum()), "safe; unsafe certified:", int((C & ~W).sum()))


def budget_figure():
    path = os.path.join(OUT, "lm_fixed_budget.csv")
    if not os.path.exists(path):
        print("no", path)
        return
    rows = list(csv.DictReader(open(path)))
    fig, ax = plt.subplots(figsize=(5.0, 3.2), constrained_layout=True)
    fig.patch.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for name, col in SERIES.items():
        r = [x for x in rows if x["method"] == name]
        if not r:
            continue
        x = np.array([float(v["generations"]) for v in r]) / 1000
        y = np.array([float(v["frac"]) for v in r])
        # Full grids dashed: a second cue besides color (CVD, print).
        ax.plot(x, y, color=col, lw=2, label=name, ls="--" if name.startswith("full grid") else "-")
    ax.set_xlabel("generations (thousands; pilot included)")
    ax.set_ylabel("fraction of safe region certified")
    ax.set_ylim(0, 1)
    _style(ax)
    ax.legend(fontsize=7, frameon=False, labelcolor=INK, loc="lower right")
    for ext_ in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_lm_budget.{ext_}"), dpi=200, facecolor=SURFACE)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--path", default=PATH)
    ap.add_argument("--pilot-stride", type=int, default=1)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.path))[0]
    suffix = stem.replace("surface_scores", "")
    surface_figure(args.path, args.budget, pilot_stride=args.pilot_stride, suffix=suffix)
    if not suffix:
        budget_figure()


if __name__ == "__main__":
    main()
