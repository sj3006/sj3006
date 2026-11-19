"""Section 4.5's four sweeps as the 2x2 composite the paper carries.

Each panel is drawn by the same function its standalone script uses, from
`fig_robust_common`, so the composite and the individual files cannot drift
apart. The four share one vertical axis and one floor line, which is what makes
them comparable and is the whole argument of the section: the conclusion
survives every assumption swept here.

    python3 src/fig_robust_all.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

import fig_robust_common as common


def main() -> int:
    common.use_scale(1.0)
    fig, axes = plt.subplots(2, 2, figsize=(3.35, 2.95))
    fig.subplots_adjust(hspace=0.70, wspace=0.42)

    a = common.panel_contrast(axes[0, 0])
    b = common.panel_permutation(axes[0, 1])
    c = common.panel_segments(axes[1, 0])
    d = common.panel_misattribution(axes[1, 1])

    for ax in (axes[0, 0], axes[1, 0], axes[1, 1]):
        ax.set_ylim(0, common.YMAX)
    axes[0, 0].set_ylabel("worst pair, degrees")
    axes[1, 0].set_ylabel("worst pair, degrees")

    common.finish(fig, "fig9_robustness_panels.png")
    print(f"  (a) all ten pairs clear at a multiplier of {a['hardest']:.3f}; "
          f"{a['cleared_at_quarter']} of ten clear at 0.25 or below")
    print(f"  (b) {b['n']} assignments, worst pair {b['worst_min']:.2f} to "
          f"{b['worst_max']:.2f} deg, all rank 5: {b['all_rank_5'] == b['n']}")
    print(f"  (c) N from {c[0]['N']} to {c[-1]['N']}, worst "
          f"{c[0]['worst']:.2f} to {c[-1]['worst']:.2f} deg")
    print(f"  (d) {d['pair'][0]}/{d['pair'][1]} holds to {d['tolerance']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
