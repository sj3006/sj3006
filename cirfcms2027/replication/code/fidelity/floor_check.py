"""Numerical floor of the directional error on the study grid.

Recomputes a handful of the study's small directional errors on a grid about
twice as fine as the study's, truth and twin both, and reports the difference.
Small errors in the results are quoted only where they exceed this floor.
Writes `_floor.json`.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import theory as th                                               # noqa: E402
import twins as tw_mod                                            # noqa: E402

R = tw_mod.REFERENCE
CASES = [("power x0.95", dict(power=R.power * 0.95)),
         ("power x1.05", dict(power=R.power * 1.05)),
         ("power x1.10", dict(power=R.power * 1.10)),
         ("speed x1.10", dict(speed=R.speed * 1.10)),
         ("absorptivity x0.98", dict(absorptivity=R.absorptivity * 0.98)),
         ("heat capacity x1.05", dict(cp=R.cp * 1.05)),
         ("scattering k=0.75", dict(scattering_k=0.75))]


FINE = 2 * tw_mod.STUDY_GRID - 1


def jac(args):
    n, changes = args
    return R.but("x", n_grid=n, **changes).jacobian()


def main():
    G = (tw_mod.STUDY_GRID, FINE)
    jobs = [(n, {}) for n in G] + [(n, c) for _, c in CASES for n in G]
    with ProcessPoolExecutor(4) as ex:
        Js = list(ex.map(jac, jobs))
    sig = np.asarray(R.sigmas, float)
    T = {G[0]: Js[0], G[1]: Js[1]}
    out = {}
    print(f"{'case':22s}{'grid ' + str(G[0]):>11s}{'grid ' + str(G[1]):>11s}{'diff':>8s}"
          "   (largest over faults, deg)")
    for i, (name, _) in enumerate(CASES):
        J481, J961 = Js[2 + 2 * i], Js[3 + 2 * i]
        d = {n: max(th.folded_angle(T[n][:, k] / sig, J[:, k] / sig) for k in range(5))
             for n, J in ((G[0], J481), (G[1], J961))}
        out[name] = {str(k): v for k, v in d.items()}
        print(f"{name:22s}{d[G[0]]:11.3f}{d[G[1]]:11.3f}{d[G[0]] - d[G[1]]:8.3f}")
    (HERE / "_floor.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
