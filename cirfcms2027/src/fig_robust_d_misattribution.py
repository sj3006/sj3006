"""Section 4.5, panel (d): A pattern attributed to the wrong build variable.

Standalone version of one panel of `fig_robust_all.py`, drawn by the same
function so the two cannot disagree. Useful on its own for a slide or for
checking one sweep without recomputing the other three.

    python3 src/fig_robust_d_misattribution.py
"""

from __future__ import annotations

import fig_robust_common as common


def main() -> int:
    result = common.standalone(common.panel_misattribution, "fig9d_misattribution.png")
    common.summarise("misattribution", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
