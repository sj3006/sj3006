"""Route C: which faults would a new sensor separate, and how good must it be?

The accepted abstract promises three classes, one of them being fault pairs that
"require an additional measurement". Route B answered half of it - the four
candidate melt-pool observables add rows without adding rank, because they all
read the same four-channel pool. That is a negative result and it does not
discharge the promise.

The problem with going further is that the sensors which *would* help - plume or
fume sensing for the gas fault, powder-bed or recoater sensing for the layer
fault - cannot be simulated. Eagar-Tsai has no plume and no powder layer, so
their Jacobian rows are not computable and any number would be invented.

The way round it is standard in diagnosability analysis and is hardware
independent: **do not model the instrument, model what it measures.** Ask what
happens if some sensor supplies a direct reading of fault k - a row e_k, unit
sensitivity to that fault and nothing else - with relative noise sigma_new. That
is the idealised best case for any instrument aimed at that cause, and it
brackets every real one.

Two questions follow and both are answerable:

1. **Which pairs does it unlock?** Add e_k, recompute the angles, see which pairs
   cross the practical floor.
2. **How good must it be?** Sweep sigma_new. Below some precision the added row
   is drowned by its own noise and buys nothing; the crossing point is a
   specification a machine builder can procure against.

What this licenses is a statement of the form "a measurement of the gas fault
accurate to X% would separate pairs A, B and C" - conditional, quantified, and
independent of whether the instrument is a light barrier, a plume camera or
something not yet built. What it does not license is any claim about a specific
instrument's performance.
"""

from __future__ import annotations

import numpy as np

from diagnosability import jacobian
from faults import FAULT_NAMES
from locality_routeA import SIGMAS, pair_angles, rank_cond

__all__ = ["add_direct_sensor", "unlock_table", "precision_sweep", "FLOOR"]

# The angle below which practitioners stop believing a separation. Used only to
# report crossings; every table also carries the raw angles.
FLOOR = 10.0

PAIRS = [(a, b) for i, a in enumerate(FAULT_NAMES) for b in FAULT_NAMES[i + 1:]]


def add_direct_sensor(J, sigmas, faults, sigma_new):
    """Append one idealised direct measurement per named fault."""
    rows, sig = [J], [np.asarray(sigmas, float)]
    for f in faults:
        row = np.zeros((1, J.shape[1]))
        row[0, FAULT_NAMES.index(f)] = 1.0
        rows.append(row)
        sig.append(np.array([sigma_new]))
    return np.vstack(rows), np.concatenate(sig)


def unlock_table(J, sigma_new=0.05):
    """For each candidate added measurement, which pairs clear the floor."""
    base_a = pair_angles(J, SIGMAS)
    base_r, _ = rank_cond(J, SIGMAS)
    out = {}
    for f in FAULT_NAMES:
        Jn, sn = add_direct_sensor(J, SIGMAS, [f], sigma_new)
        a = pair_angles(Jn, sn)
        r, c = rank_cond(Jn, sn)
        gained = [p for p in PAIRS if base_a[p] < FLOOR <= a[p]]
        out[f] = {"angles": a, "rank": r, "cond": c, "gained": gained,
                  "worst": min(a.values())}
    return base_a, base_r, out


def precision_sweep(J, fault, sigmas=(0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.002)):
    """How accurate must a direct measurement of `fault` be to be worth fitting?"""
    rows = []
    for s in sigmas:
        Jn, sn = add_direct_sensor(J, SIGMAS, [fault], s)
        a = pair_angles(Jn, sn)
        r, c = rank_cond(Jn, sn)
        rows.append((s, min(a.values()), sum(1 for p in PAIRS if a[p] >= FLOOR), r, c))
    return rows


if __name__ == "__main__":
    J, _ = jacobian()
    base_a, base_r, res = unlock_table(J)

    print("BASELINE, three coaxial sensors")
    print(f"   rank {base_r}   worst pair {min(base_a.values()):.2f} deg   "
          f"pairs above {FLOOR:.0f} deg: {sum(1 for p in PAIRS if base_a[p] >= FLOOR)} of {len(PAIRS)}")

    print(f"\nADD ONE IDEALISED DIRECT MEASUREMENT (relative noise 5%)")
    print(f"   {'measure':10s}{'rank':>6s}{'cond':>8s}{'worst':>8s}{'>=floor':>9s}   pairs newly cleared")
    for f, d in res.items():
        n_ok = sum(1 for p in PAIRS if d["angles"][p] >= FLOOR)
        gained = ", ".join(f"{a}/{b}" for a, b in d["gained"]) or "-"
        print(f"   {f:10s}{d['rank']:>6d}{d['cond']:>8,.0f}{d['worst']:>8.2f}"
              f"{n_ok:>6d}/{len(PAIRS)}   {gained}")

    print("\nFULL ANGLE TABLE (degrees), baseline vs each added measurement")
    print(f"   {'pair':18s}{'base':>8s}" + "".join(f"{'+'+f:>10s}" for f in FAULT_NAMES))
    for p in sorted(PAIRS, key=lambda q: base_a[q]):
        print(f"   {p[0]+' / '+p[1]:18s}{base_a[p]:>8.2f}"
              + "".join(f"{res[f]['angles'][p]:>10.2f}" for f in FAULT_NAMES))

    print("\nHOW GOOD MUST IT BE?  direct measurement of the gas fault")
    print(f"   {'rel. noise':>11s}{'worst pair':>12s}{'pairs>=floor':>14s}{'rank':>6s}{'cond':>8s}")
    for s, w, n, r, c in precision_sweep(J, "gas"):
        print(f"   {s:>11.1%}{w:>12.2f}{n:>11d}/{len(PAIRS)}{r:>6d}{c:>8,.0f}")

    print("\nTWO ADDED MEASUREMENTS, gas and layer together (5% each)")
    Jn, sn = add_direct_sensor(J, SIGMAS, ["gas", "layer"], 0.05)
    a = pair_angles(Jn, sn); r, c = rank_cond(Jn, sn)
    print(f"   rank {r}   condition {c:,.0f}   worst pair {min(a.values()):.2f} deg   "
          f"pairs above floor {sum(1 for p in PAIRS if a[p] >= FLOOR)}/{len(PAIRS)}")
    for p in sorted(PAIRS, key=lambda q: a[q])[:4]:
        print(f"      {p[0]+' / '+p[1]:18s}{base_a[p]:>8.2f} -> {a[p]:>7.2f}")
