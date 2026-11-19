"""How far the sensor model's quadrature grid moves the fault directions.

The photodiode and pyrometer integrate a surface temperature field, capped at
the boiling point, over a fixed square grid (`sensors.SensorConfig.n_grid`,
default 121 cells a side). The cap makes the integrand non-smooth: as power or
a fault changes, the edge of the capped region crosses grid nodes, so the
readings are piecewise smooth with small kinks at the grid scale. A central
difference with a 0.2 % step straddles some of those kinks.

The camera reading does not have this problem; its docstring records that the
area was moved off the grid for exactly this reason. The other two sensors were
left on it.

This script computes the truth's Jacobian at four grids and reports, against
the finest, each fault's directional change and each pairwise angle. It also
scans the operating point in 1 % steps at two grids, which is where the effect
was first seen: the directional error of an operating-point twin jumped by
about 1 degree between neighbouring offsets.

Takes about a minute. Writes `_grid.json`.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import theory as th                                               # noqa: E402
from faults import FAULT_NAMES                                    # noqa: E402
from twin import TRUTH                                            # noqa: E402

GRIDS = (121, 241, 481, 961)
PAIRS = [(i, j) for i in range(5) for j in range(i + 1, 5)]


def main() -> dict:
    st = np.asarray(TRUTH.sigmas, float)
    J, secs = {}, {}
    for n in GRIDS:
        t0 = time.time()
        J[n] = TRUTH.but(f"grid {n}", n_grid=n).jacobian()
        secs[n] = time.time() - t0
    ref = J[GRIDS[-1]]
    out = {"grids": list(GRIDS), "seconds": secs, "rows": {}}
    print(f"{'grid':>6s}  directional change against {GRIDS[-1]} (deg), "
          f"per fault {list(FAULT_NAMES)}")
    for n in GRIDS:
        U = J[n] / st[:, None]
        d = [th.folded_angle(ref[:, k] / st, J[n][:, k] / st) for k in range(5)]
        pa = {f"{FAULT_NAMES[i]}|{FAULT_NAMES[j]}": th.folded_angle(U[:, i], U[:, j])
              for i, j in PAIRS}
        out["rows"][n] = {"delta": d, "pairs": pa, "jacobian": J[n].tolist()}
        print(f"{n:6d}  {np.round(d, 3).tolist()}   ({secs[n]:.0f}s)")
    print("\npairwise angles (deg)")
    print(f"{'pair':18s}" + "".join(f"{n:>8d}" for n in GRIDS))
    for i, j in PAIRS:
        p = f"{FAULT_NAMES[i]}|{FAULT_NAMES[j]}"
        print(f"{p:18s}" + "".join(f"{out['rows'][n]['pairs'][p]:8.2f}" for n in GRIDS))

    print("\noperating-point scan, largest directional error (deg)")
    scan = {}
    for n in (121, 481):
        base = TRUTH.but("ref", n_grid=n)
        R = base.jacobian()
        vals = []
        for s in np.round(np.arange(0.90, 1.1001, 0.01), 2):
            Jm = base.but("p", power=base.power * s).jacobian()
            vals.append(max(th.folded_angle(R[:, k] / st, Jm[:, k] / st)
                            for k in range(5)))
        scan[n] = vals
        print(f"{n:6d}  " + " ".join(f"{v:4.2f}" for v in vals))
    out["power_scan"] = {"scales": np.round(np.arange(0.90, 1.1001, 0.01), 2).tolist(),
                         **{str(n): v for n, v in scan.items()}}
    (HERE / "_grid.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
