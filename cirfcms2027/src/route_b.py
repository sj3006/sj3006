"""Route B: which sensors earn their place, and what a fourth would buy.

Tier 2 and Route A both assume the suite a production machine already carries:
one coaxial photodiode, one coaxial camera reporting melt pool area, one
two-colour pyrometer. Two questions follow immediately and neither has been
asked yet.

**Is each of the three pulling its weight?** If a two-sensor subset reaches the
same diagnosability, the third is redundant for diagnosis, whatever else it is
good for. That is a finding a machine builder can act on.

**What would a fourth buy?** This is the question the accepted abstract promised
an answer to - the class of fault pairs "requiring an additional measurement" -
so it cannot be left as an aside. Four candidates, chosen because each is
something a real shop could actually do and each costs something different:

    camera_width + camera_length   free. The camera already forms an image;
        reporting area collapses two independent axes into one number. Splitting
        them is image processing. If it helps, it is the cheapest possible
        recommendation.
    photodiode_swir                new hardware. A second photodiode in a
        short-wave infrared band. Longer wavelengths weight the cooler parts of
        the pool more, so it is not a duplicate of the visible one.
    pyrometer_wide                 filter change. Same instrument, widely
        separated band pair, higher temperature sensitivity.

A caution that belongs in the paper
-----------------------------------
Ranking subsets requires per-sensor noise, and the noise ratios here are
assumptions, not measurements - that decision and its reasons are recorded under
"Noise figures: deliberately not used". A subset ranking is therefore only as
trustworthy as the ratios, so every ranking below is recomputed under three
different ratio assumptions and only conclusions that survive all three are
reported as conclusions.
"""

from __future__ import annotations

import itertools

import numpy as np

from faults import FAULT_NAMES, FaultState, apply_faults
from locality_routeA import pair_angles, rank_cond
from observables import (PROFILE_CONTRAST, coefficient_sigmas, drivers,
                         enlarged_jacobian, regressors, scan_plan)
from sensors import ALL_SENSOR_NAMES, SENSOR_NAMES, sensor_readings

__all__ = ["RATIO_SETS", "full_jacobian", "subset_summary",
           "misspecification_error", "report"]

# Relative noise per sensor. The first set is the one used throughout the study.
# The others are deliberate stress cases: an excellent pyrometer, and all
# sensors equal. Geometric sensors (width, length) inherit the camera's figure.
RATIO_SETS = {
    "study default": {"photodiode": 1.0, "camera": 1.0, "pyrometer": 0.03,
                      "camera_width": 1.0, "camera_length": 1.0,
                      "photodiode_swir": 1.0, "pyrometer_wide": 0.03},
    "equal noise": {n: 1.0 for n in ALL_SENSOR_NAMES},
    "fine pyrometer": {"photodiode": 1.0, "camera": 1.0, "pyrometer": 0.003,
                       "camera_width": 1.0, "camera_length": 1.0,
                       "photodiode_swir": 1.0, "pyrometer_wide": 0.003},
}

# Subsets worth reporting. The full power set of seven observables is 127 rows,
# most of them physically meaningless (a camera width without a camera), so the
# sets below are the ones a machine builder could actually specify.
SUBSETS = {
    "all three (baseline)": ("photodiode", "camera", "pyrometer"),
    "photodiode only": ("photodiode",),
    "camera only": ("camera",),
    "pyrometer only": ("pyrometer",),
    "photodiode + camera": ("photodiode", "camera"),
    "photodiode + pyrometer": ("photodiode", "pyrometer"),
    "camera + pyrometer": ("camera", "pyrometer"),
    "+ split the camera (free)": ("photodiode", "camera_width", "camera_length",
                                  "pyrometer"),
    "+ SWIR photodiode": ("photodiode", "camera", "pyrometer", "photodiode_swir"),
    "+ wide-band pyrometer": ("photodiode", "camera", "pyrometer", "pyrometer_wide"),
    "split camera + SWIR": ("photodiode", "camera_width", "camera_length",
                            "pyrometer", "photodiode_swir"),
    "everything": ALL_SENSOR_NAMES,
}


def _readings_vec(fault: FaultState, names) -> np.ndarray:
    beam, material = apply_faults(fault)
    r = sensor_readings(beam, material)
    return np.array([r[n] for n in names], float)


def full_jacobian(step: float = 0.002, names=ALL_SENSOR_NAMES):
    """Relative-sensitivity Jacobian over every available observable."""
    nominal = _readings_vec(FaultState(), names)
    cols = []
    for f in FAULT_NAMES:
        plus = _readings_vec(FaultState(**{f: step}), names)
        minus = _readings_vec(FaultState(**{f: -step}), names)
        cols.append((plus - minus) / (2.0 * step) / nominal)
    return np.column_stack(cols), nominal


def subset_summary(J_all, names_all, subset, ratios, plan):
    """Diagnosability of one sensor subset, instantaneous and enlarged."""
    idx = [names_all.index(n) for n in subset]
    J = J_all[idx, :]
    sig = np.array([ratios[n] for n in subset], float)
    ri, ci = rank_cond(J, sig)
    ai = pair_angles(J, sig)
    big = enlarged_jacobian(J, plan)
    bsig = coefficient_sigmas(sig, plan)
    rb, cb = rank_cond(big, bsig)
    ab = pair_angles(big, bsig)
    return {"inst_rank": ri, "inst_cond": ci, "inst_worst": min(ai.values()),
            "big_rank": rb, "big_cond": cb, "big_worst": min(ab.values()),
            "big_angles": ab}


def misspecification_error(J_all, names_all, subset, ratios, plan,
                           delta: float = 0.3, draws: int = 40, seed: int = 0):
    """Worst-case error in the recovered faults when the profiles are wrong.

    Once spatial context is used, rank stops being the constraint - a single
    sensor regressed onto five known regressors already gives five independent
    numbers for five faults. So the question "what does another sensor buy" has
    to be answered on something other than rank, and the honest answer is
    robustness: the inference assumes modulation profiles that are asserted
    rather than measured, so what matters is how badly a wrong assumption
    corrupts the answer.

    Set up as an inverse problem. Diagnosis inverts the *assumed* enlarged
    Jacobian A, while the data is generated by the *true* one T:

        f_hat = pinv(A_w) T_w f

    so the worst-case relative error over all fault directions is the operator
    norm of (pinv(A_w) T_w - I). Zero means the misspecification does not matter
    at all; 1 means the recovered fault vector can be as wrong as the fault
    itself. Extra sensors add rows to an already full-rank system, which is
    exactly the situation where redundancy buys error averaging, so this is the
    metric that should separate the suites if anything does.

    `delta` is the fractional error in each fault's profile contrast, drawn
    independently and uniformly in [-delta, delta].
    """
    idx = [names_all.index(n) for n in subset]
    J = J_all[idx, :]
    sig = np.array([ratios[n] for n in subset], float)
    bsig = coefficient_sigmas(sig, plan)
    A = enlarged_jacobian(J, plan) / bsig[:, None]

    rng = np.random.default_rng(seed)
    base = np.asarray(PROFILE_CONTRAST, float)
    errs = []
    for _ in range(draws):
        scaled = base * (1.0 + rng.uniform(-delta, delta, base.size))
        M = _modulations_with(plan, scaled)
        B = np.linalg.lstsq(regressors(plan), M, rcond=None)[0]
        rows = [J[s, :] * B[j, :] for s in range(J.shape[0])
                for j in range(B.shape[0])]
        T = np.vstack(rows) / bsig[:, None]
        errs.append(float(np.linalg.norm(np.linalg.pinv(A) @ T - np.eye(5), 2)))
    return float(np.mean(errs)), float(np.max(errs))


def _modulations_with(plan, contrasts):
    """Positive-form profiles with a per-fault contrast vector."""
    Z = drivers(plan)
    M = np.exp(Z * np.asarray(contrasts, float))
    return M / M.mean(axis=0)


def report() -> None:
    plan = scan_plan()
    J_all, _ = full_jacobian()
    names = list(ALL_SENSOR_NAMES)

    print("SENSOR SUBSET SWEEP")
    print("instantaneous and enlarged, at three different noise-ratio assumptions\n")
    for label, ratios in RATIO_SETS.items():
        print(f"noise ratios: {label}")
        print(f"   {'subset':28s}{'n':>3s} | {'inst rank':>10s}{'worst':>8s}"
              f"{'cond':>8s} | {'big rank':>9s}{'worst':>8s}{'cond':>8s}")
        for name, subset in SUBSETS.items():
            s = subset_summary(J_all, names, subset, ratios, plan)
            print(f"   {name:28s}{len(subset):>3d} | {s['inst_rank']:>10d}"
                  f"{s['inst_worst']:>8.2f}{s['inst_cond']:>8,.0f} | "
                  f"{s['big_rank']:>9d}{s['big_worst']:>8.2f}{s['big_cond']:>8,.0f}")
        print()

    print("WHICH PAIR IS THE BINDING CONSTRAINT, baseline vs each addition")
    ratios = RATIO_SETS["study default"]
    base = subset_summary(J_all, names, SUBSETS["all three (baseline)"], ratios, plan)
    worst_pair = min(base["big_angles"], key=base["big_angles"].get)
    print(f"   baseline worst pair is {worst_pair[0]}/{worst_pair[1]} at "
          f"{base['big_angles'][worst_pair]:.2f} deg")
    for name in ("+ split the camera (free)", "+ SWIR photodiode",
                 "+ wide-band pyrometer", "split camera + SWIR"):
        s = subset_summary(J_all, names, SUBSETS[name], ratios, plan)
        wp = min(s["big_angles"], key=s["big_angles"].get)
        gain = s["big_angles"][worst_pair] - base["big_angles"][worst_pair]
        print(f"   {name:28s} {worst_pair[0]}/{worst_pair[1]} "
              f"{s['big_angles'][worst_pair]:6.2f} deg ({gain:+5.2f})   "
              f"new worst pair {wp[0]}/{wp[1]} at {s['big_angles'][wp]:.2f} deg")

    print("\nROBUSTNESS TO PROFILE MISSPECIFICATION")
    print("worst-case relative error in the recovered fault vector when each")
    print("profile's contrast is wrong by up to the stated amount\n")
    print(f"   {'subset':28s}{'n':>3s}" + "".join(f"{d:>16.0%}" for d in (0.1, 0.3, 0.5)))
    print(f"   {'':28s}{'':>3s}" + "".join(f"{'mean / worst':>16s}" for _ in range(3)))
    for name in ("photodiode only", "camera only", "pyrometer only",
                 "photodiode + pyrometer", "all three (baseline)",
                 "+ split the camera (free)", "everything"):
        subset = SUBSETS[name]
        cells = ""
        for d in (0.1, 0.3, 0.5):
            m, w = misspecification_error(J_all, names, subset, ratios, plan, delta=d)
            cells += f"{m:>7.3f} /{w:>7.3f}"
        print(f"   {name:28s}{len(subset):>3d}{cells}")

    print("\nIS ANY OF THE THREE REDUNDANT FOR DIAGNOSIS?")
    for drop in SENSOR_NAMES:
        kept = tuple(n for n in SENSOR_NAMES if n != drop)
        for label, ratios in RATIO_SETS.items():
            s = subset_summary(J_all, names, kept, ratios, plan)
            b = subset_summary(J_all, names, SENSOR_NAMES, ratios, plan)
            print(f"   drop {drop:12s} [{label:15s}] enlarged rank "
                  f"{b['big_rank']} -> {s['big_rank']}   worst "
                  f"{b['big_worst']:.2f} -> {s['big_worst']:.2f} deg")
        print()


if __name__ == "__main__":
    report()
