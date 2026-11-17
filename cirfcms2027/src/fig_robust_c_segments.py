"""Section 4.5, panel (c): How many segments the regression needs.

Standalone version of one panel of `fig_robust_all.py`, drawn by the same
function so the two cannot disagree. Useful on its own for a slide or for
checking one sweep without recomputing the other three.

    python3 src/fig_robust_c_segments.py
"""

from __future__ import annotations

import fig_robust_common as common


def main() -> int:
    result = common.standalone(common.panel_segments, "fig9c_segments.png")
    common.summarise("segments", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
