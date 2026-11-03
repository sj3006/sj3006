"""Every number the paper quotes, recomputed from the model.

One function per group of paper claims, each returning a flat dict of named
scalars. `claims.py` maps paper text onto keys in these dicts and `check.py`
compares them. Nothing here reads the paper; nothing in `claims.py` computes
anything. That separation is the point: a claim and its recomputation cannot
quietly become the same number by being written in the same place.

Groups are cached to disk because a few of them take minutes. Delete
`repro/cache/` or pass --no-cache to force a recompute.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

GROUPS: dict[str, callable] = {}


def group(name):
    def wrap(fn):
        GROUPS[name] = fn
        fn.group_name = name
        return fn
    return wrap


def _flat_angles(prefix, angles):
    return {f"{prefix}.{a}_{b}": v for (a, b), v in angles.items()}


# ===========================================================================
@group("calibration")
def calibration() -> dict:
    """Section 3.1: the forward model, its fit, and why the keyhole term stays."""
    from calibrate import WEAVER_POINTS, fit, predict
    from conduction_baseline import (aspect_ratios, conduction_only_fit,
                                     historical_one_parameter_fit)
    from diagnosability import jacobian
    from eagar_tsai import IN718, IN718_ABSORPTIVITY, IN718_KEYHOLE_C

    # Every result in the paper runs on the constants STORED in eagar_tsai.py,
    # not on a fresh least-squares output, so the calibration error is reported
    # against those. They are the fit's answer rounded to the precision they are
    # written at - `fit_agreement` below is how far that rounding moves them -
    # but quoting the fit's unrounded output for the error and the stored
    # constants for everything else would make two numbers in one section come
    # from two different models, which is how 13.0 and +1.7 came to disagree in
    # an earlier draft.
    STORED = (IN718_ABSORPTIVITY, IN718.k, IN718.cp, IN718_KEYHOLE_C)
    theta, rep = fit(WEAVER_POINTS)
    base = WEAVER_POINTS[0]
    pred = predict(base, STORED)
    a = aspect_ratios()
    c = conduction_only_fit()
    h = historical_one_parameter_fit()
    under = [1 for p in WEAVER_POINTS if predict(p, STORED)["width"] < p.width]

    werr, derr = [], []
    for p in WEAVER_POINTS:
        g = predict(p, STORED)
        werr.append(abs(g["width"] - p.width) / p.width)
        derr.append(abs(g["depth_corrected"] - p.depth) / p.depth)

    out = {
        "width_mape_pct": 100 * float(np.mean(werr)),
        "depth_mape_pct": 100 * float(np.mean(derr)),
        "refit_width_mape_pct": rep["width_mape_pct"],
        "refit_depth_mape_pct": rep["depth_mape_pct"],
        "fit_agreement": float(np.max(np.abs(
            (np.array(theta) - np.array(STORED))
            / np.maximum(np.abs(np.array(STORED)), 1e-12)))),
        "n_conditions": float(rep["n_conditions"]),
        "baseline_power_W": base.power,
        "baseline_speed_mm_s": base.speed * 1e3,
        "baseline_spot_um": base.spot_diameter * 1e6,
        "baseline_width_err_pct": 100 * (pred["width"] - base.width) / base.width,
        "baseline_depth_err_pct": 100 * (pred["depth_corrected"] - base.depth)
                                  / base.depth,
        "n_width_underpredicted": float(len(under)),
        "aspect_dw_min": a["depth_over_width_range"][0],
        "aspect_dw_max": a["depth_over_width_range"][1],
        "aspect_dhw_min": a["depth_over_half_width_range"][0],
        "aspect_dhw_max": a["depth_over_half_width_range"][1],
        "keyhole_criterion_dw": a["criterion_depth_over_width"],
        "n_keyholing": float(a["n_keyholing"]),
        "conduction_only_width_mape_pct": c["width_mape_pct"],
        "conduction_only_depth_mape_pct": c["depth_mape_pct"],
        "historical_conduction_depth_mape_pct": h["depth_mape_pct"],
        "historical_conduction_width_mape_pct": h["width_mape_pct"],
        "fitted_absorptivity": STORED[0],
        "fitted_conductivity": STORED[1],
        "fitted_heat_capacity": STORED[2],
        "fitted_keyhole_C": STORED[3],
    }

    # derivative step convergence: max relative change against the previous step
    steps = (0.08, 0.04, 0.02, 0.01, 0.005)
    prev = None
    for s in steps:
        J, _ = jacobian(step=s)
        if prev is not None:
            ch = 100 * float(np.max(np.abs((J - prev) / prev)))
            out[f"step_change_pct_at_{s}"] = ch
        prev = J
    out["derivative_step"] = 0.002
    return out


# ===========================================================================
@group("couplings")
def couplings() -> dict:
    """Section 3.2: the layer fault's three channels."""
    from faults import FaultCouplings
    from layer_couplings import (absorptivity_coupling, channel_decomposition,
                                 enthalpy_coupling)

    a = absorptivity_coupling()
    e = enthalpy_coupling()
    d = FaultCouplings()
    sens = [absorptivity_coupling(ratio=r, d50_um=t)["coupling"]
            for r in (1.5, 2.0, 2.5) for t in (15.0, 30.0, 45.0)]
    out = {
        "absorptivity_coupling": a["coupling"],
        "model_absorptivity_coupling": d.layer_to_absorptivity,
        "powder_enhancement": a["enhancement"],
        "implied_solid_absorptivity": a["implied_solid_absorptivity"],
        "absorptivity_sens_min": float(min(sens)),
        "absorptivity_sens_max": float(max(sens)),
        "enthalpy_coupling": e["coupling"],
        "model_enthalpy_coupling": d.layer_to_powder_enthalpy,
        "phi_pct": 100 * e["phi"],
        "absorbed_J_per_m": e["absorbed_J_per_m"],
        "melting_J_per_m": e["melting_J_per_m"],
        "net_product_coupling": d.layer_to_absorptivity + d.layer_to_powder_enthalpy,
        "geometry_preheat_kelvin": d.geometry_preheat_kelvin,
    }
    for k, v in channel_decomposition().items():
        key = k.replace(" + ", "_plus_").replace(" ", "_")
        out[f"channel_{key}_depth_pct"] = 100 * v["depth"]
        out[f"channel_{key}_width_pct"] = 100 * v["width"]
    return out


# ===========================================================================
@group("noise")
def noise_group() -> dict:
    """Section 3.6: each sensor's relative noise, derived from transduction."""
    import noise as N
    from diagnosability import jacobian
    from noise import C2, derive, planck_log_sensitivity

    N.verify()                      # stored constants against their derivation
    d = derive()
    _, meta = jacobian()
    T_peak = float(meta[2])
    pyro = (C2 / T_peak) * (1 / 750e-9 - 1 / 950e-9)
    planck = planck_log_sensitivity(850e-9, 1609.0)
    return {
        "photodiode": d["photodiode"],
        "camera": d["camera"],
        "pyrometer": d["pyrometer"],
        "camera_width": d["camera_width"],
        "camera_length": d["camera_length"],
        "photodiode_swir": d["photodiode_swir"],
        "pyrometer_wide": d["pyrometer_wide"],
        "peak_temperature_K": T_peak,
        "ratio_wien_sensitivity": abs(pyro),
        "planck_log_sensitivity": planck,
        "isotherm_shift_pct_at_1pct": 100 * 0.01 / planck,
        "camera_precision_factor": d["photodiode"] / d["camera"],
        "liquidus_K": 1609.0,
        "camera_band_centre_nm": 850.0,
    }


# ===========================================================================
@group("context")
def context() -> dict:
    """Section 3.5: the enlarged observation and the one calibrated profile."""
    from noise import SIGMAS
    from observables import (REGRESSOR_NAMES, coefficient_sigmas, regressors,
                             scan_plan)
    from weaver_pads import (Y_PAD_SD_RANGE_UM, gas_inversion,
                             pad_depth_changes)  # noqa: E501

    plan = scan_plan()
    G = regressors(plan)
    root = np.sqrt(np.diag(np.linalg.inv(G.T @ G)))
    sig = coefficient_sigmas(SIGMAS, plan)
    ch = pad_depth_changes()
    g = gas_inversion()
    return {
        "n_segments": float(len(plan["layer"])),
        "n_regressors": float(len(REGRESSOR_NAMES)),
        "n_observables": float(len(SIGMAS) * len(REGRESSOR_NAMES)),
        "root_diag_min": float(root.min()),
        "root_diag_max": float(root.max()),
        "noise_reduction_min": float(1 / root.max()),
        "noise_reduction_max": float(1 / root.min()),
        "coefficient_sigma_min": float(sig.min()),
        "coefficient_sigma_max": float(sig.max()),
        "pad_mean_change_pct": 100 * ch["mean"],
        "pad_strongest_change_pct": 100 * ch["strongest"],
        "pad_weakest_change_pct": 100 * ch["weakest"],
        "pad_control_min_pct": 100 * min(ch["control_range"]),
        "pad_control_max_pct": 100 * max(ch["control_range"]),
        "pad_sd_min_um": Y_PAD_SD_RANGE_UM[0],
        "pad_sd_max_um": Y_PAD_SD_RANGE_UM[1],
        "f_gas_control": g["f_control"],
        "f_gas_parallel_mean": g["f_mean"],
        "measured_swing": g["swing"],
        "measured_contrast": g["measured_contrast"],
        "asserted_contrast": g["asserted_contrast"],
        "asserted_swing": g["asserted_swing"],
        "understatement_pct": 100 * g["understatement"],
    }


# ===========================================================================
@group("meltpool")
def meltpool() -> dict:
    """Sections 4.2-4.4: the instantaneous suite and the enlarged observation."""
    import math

    from diagnosability import jacobian, whiten
    from faults import FaultState
    from diagnosability import _readings
    from locality_routeA import _rank_cond, pair_angles
    from noise import SIGMAS, sigmas_for
    from observables import (coefficient_sigmas, enlarged_jacobian, drivers,
                             regressors, scan_plan, PROFILE_CONTRAST)
    from route_b import full_jacobian
    from sensors import ALL_SENSOR_NAMES

    J, _ = jacobian()
    Jw = whiten(J, SIGMAS)
    Gm = Jw @ Jw.T
    dg = np.sqrt(np.diag(Gm))
    corr = Gm / np.outer(dg, dg)
    sv = np.linalg.svd(Jw, compute_uv=False)
    r_i, c_i = _rank_cond(J, SIGMAS)
    inst = pair_angles(J, SIGMAS)

    plan = scan_plan()
    bsig = coefficient_sigmas(SIGMAS, plan)
    Jb = enlarged_jacobian(J, plan)
    r_e, c_e = _rank_cond(Jb, bsig)
    acc = pair_angles(Jb, bsig)

    # seven observables
    J7, _ = full_jacobian()
    s7 = sigmas_for(ALL_SENSOR_NAMES)
    sv7 = np.linalg.svd(whiten(J7, s7), compute_uv=False)
    r7, _ = _rank_cond(J7, s7)

    # the exact confound
    ratio = J[:, 0] / J[:, 3]
    nom = _readings(FaultState())
    worst_identity = 0.0
    for f in (0.02, 0.05, 0.10, 0.20):
        both = _readings(FaultState(power=f, gas=math.log(1 + f)))
        worst_identity = max(worst_identity,
                             float(np.max(np.abs(both - nom) / np.abs(nom))))

    # shared-profile control
    Z, C = drivers(plan), np.asarray(PROFILE_CONTRAST, float)
    Zs = np.repeat((Z[:, [0]] * C[0]), len(C), axis=1)
    M = np.exp(Zs); M = M / M.mean(axis=0, keepdims=True)
    B = np.linalg.lstsq(regressors(plan), M, rcond=None)[0]
    Ds = np.vstack([J[s, :] * B[j, :] for s in range(J.shape[0])
                    for j in range(B.shape[0])])
    r_s, c_s = _rank_cond(Ds, bsig)
    shared = pair_angles(Ds, bsig)

    out = {
        "corr_pd_cam": corr[0, 1], "corr_pd_pyr": corr[0, 2],
        "corr_cam_pyr": corr[1, 2],
        "sv1": sv[0], "sv2": sv[1], "sv3": sv[2],
        "leading_energy_pct": 100 * sv[0] ** 2 / float(np.sum(sv ** 2)),
        "inst_rank": float(r_i), "inst_cond": c_i,
        "n_unobserved_directions": float(5 - r_i),
        "acc_rank": float(r_e), "acc_cond": c_e,
        "channel_bound": 4.0,
        "seven_rank": float(r7),
        "seven_sv1": sv7[0], "seven_sv2": sv7[1], "seven_sv3": sv7[2],
        "seven_sv4": sv7[3], "seven_sv5": sv7[4],
        "seven_sv4_over_sv1": sv7[3] / sv7[0],
        "rank_tol": 1e-6,
        "ratio_power_gas_pd": ratio[0], "ratio_power_gas_cam": ratio[1],
        "ratio_power_gas_pyr": ratio[2],
        "ratio_spread": float(ratio.max() - ratio.min()),
        "identity_max_relative_error": worst_identity,
        "shared_profile_rank": float(r_s), "shared_profile_cond": c_s,
        "shared_profile_worst": min(shared.values()),
        "inst_worst": min(inst.values()), "acc_worst": min(acc.values()),
        "inst_cleared": float(sum(v >= 10 for v in inst.values())),
        "acc_cleared": float(sum(v >= 10 for v in acc.values())),
    }
    out.update(_flat_angles("inst", inst))
    out.update(_flat_angles("acc", acc))
    return out


# ===========================================================================
@group("secants")
def secants() -> dict:
    """Section 4.4: replacing every derivative by a finite-magnitude secant."""
    from locality_routeA import (_rank_cond, big_sigmas, exact_secant_directions,
                                 pair_angles, response_curves, secant_directions)
    from observables import scan_plan

    plan = scan_plan()
    bsig = big_sigmas(plan)
    curves, nominal = response_curves()
    mags = (0.002, 0.01, 0.02, 0.05, 0.10, 0.20, -0.002, -0.02, -0.05, -0.20)
    worst, ranks, conds, binding = [], [], [], []
    rows = {}
    for f in mags:
        D = secant_directions(f, plan, curves, nominal)
        a = pair_angles(D, bsig)
        rows[f] = a
        r, c = _rank_cond(D, bsig)
        worst.append(min(a.values())); ranks.append(r); conds.append(c)
        binding.append(a[("power", "speed")])
    out = {
        "mag_min_pct": 100 * min(abs(m) for m in mags),
        "mag_max_pct": 100 * max(abs(m) for m in mags),
        "all_rank_5": float(all(r == 5 for r in ranks)),
        "worst_over_magnitudes_min": float(min(worst)),
        "binding_pair_min": float(min(binding)),
        "binding_pair_max": float(max(binding)),
        "cond_min": float(min(conds)), "cond_max": float(max(conds)),
        "floor_margin_at_plus20": float(rows[0.20][("power", "speed")] / 10.0),
    }
    # no-interpolation cross-check
    diffs = []
    for f in (0.05, 0.20):
        De = exact_secant_directions(f, plan, nominal)
        ae = pair_angles(De, bsig)
        diffs.append(max(abs(ae[p] - rows[f][p]) for p in ae))
    out["exact_vs_interpolated_max_deg"] = float(max(diffs))
    return out


# ===========================================================================
@group("robustness")
def robustness() -> dict:
    """Section 4.5: how wrong the modulation profiles may be."""
    from profile_robustness import (collapse_test, contrast_thresholds,
                                    misattribution_sweep, permutation_sweep,
                                    segment_sweep)

    ct = contrast_thresholds()
    ps = permutation_sweep()
    cl = collapse_test()
    mg = misattribution_sweep(contaminant="geometry")
    mp_ = misattribution_sweep(contaminant="power")
    seg = {r["N"]: r for r in segment_sweep()}

    vals = [v for v in ct.values() if v is not None]
    out = {
        "floor": 10.0,
        "n_clearing_at_25pct": float(sum(v <= 0.25 for v in vals)),
        "hardest_pair_contrast": float(max(vals)),
        "n_permutations": float(ps["n"]),
        "perm_rank5": float(ps["all_rank_5"]),
        "perm_all_cleared": float(ps["all_cleared"]),
        "perm_worst_min": ps["worst_min"], "perm_worst_max": ps["worst_max"],
        "perm_worst_median": ps["worst_median"],
        "collapse_max_disagreement_deg": float(max(
            abs(r["forced"] - r["instantaneous"]) for r in cl.values())),
        "mildest_instantaneous": float(max(r["instantaneous"]
                                           for r in cl.values())),
        "support_mix_tolerance": mg["tolerance"],
        "support_mix_at_80pct": [r["pair_angle"] for r in mg["rows"]
                                 if abs(r["alpha"] - 0.8) < 1e-9][0],
        "drift_mix_crosses_floor": 0.0 if mp_["tolerance"] is None else 1.0,
        "drift_mix_min": float(min(r["pair_angle"] for r in mp_["rows"])),
        "worst_at_N12": seg[12]["worst"], "worst_at_N30": seg[30]["worst"],
        "worst_at_N84": seg[84]["worst"],
        "worst_at_N128": seg[128]["worst"], "worst_at_N288": seg[288]["worst"],
    }
    for p, v in ct.items():
        out[f"contrast.{p[0]}_{p[1]}"] = -1.0 if v is None else v
    return out


# ===========================================================================
@group("noise_sets")
def noise_sets() -> dict:
    """Section 4.5: the headline under all four noise assumptions."""
    from locality_routeA import pair_angles
    from noise import DERIVED
    from observables import coefficient_sigmas, enlarged_jacobian, scan_plan
    from route_b import RATIO_SETS, full_jacobian
    from sensors import SENSOR_NAMES, ALL_SENSOR_NAMES

    plan = scan_plan()
    J7, _ = full_jacobian()
    idx = [list(ALL_SENSOR_NAMES).index(n) for n in SENSOR_NAMES]
    J = J7[idx, :]
    out = {}
    worsts = []
    for label, ratios in RATIO_SETS.items():
        sig = np.array([ratios[n] for n in SENSOR_NAMES], float)
        a = pair_angles(enlarged_jacobian(J, plan),
                        coefficient_sigmas(sig, plan))
        w = min(a.values())
        worsts.append(w)
        out[f"worst.{label.replace(' ', '_')}"] = w
    out["n_noise_sets"] = float(len(RATIO_SETS))
    out["spread_deg"] = float(max(worsts) - min(worsts))
    return out


# ===========================================================================
@group("couplings_sweep")
def couplings_sweep() -> dict:
    """Section 4.2 and 4.5: the degeneracy and the headline against the couplings."""
    from dataclasses import replace

    from coupling_sweep import DEFAULTS, RANGES
    from diagnosability import jacobian
    from locality_routeA import pair_angles
    from noise import SIGMAS
    from observables import coefficient_sigmas, enlarged_jacobian, scan_plan

    plan = scan_plan()
    bsig = coefficient_sigmas(SIGMAS, plan)
    pg, worsts, pl = [], [], {}
    for name, values in RANGES.items():
        for v in values:
            J, _ = jacobian(couplings=replace(DEFAULTS, **{name: v}))
            inst = pair_angles(J, SIGMAS)
            acc = pair_angles(enlarged_jacobian(J, plan), bsig)
            pg.append(inst[("power", "gas")])
            worsts.append(min(acc.values()))
            if name == "layer_to_conductivity":
                pl[v] = (inst[("power", "layer")], inst[("layer", "gas")])
    return {
        "n_coupling_values": float(len(pg)),
        "power_gas_max_over_sweep": float(max(pg)),
        "acc_worst_min": float(min(worsts)),
        "acc_worst_max": float(max(worsts)),
        "acc_worst_spread": float(max(worsts) - min(worsts)),
        "power_layer_at_zero_conductivity": pl[0.0][0],
        "layer_gas_at_zero_conductivity": pl[0.0][1],
    }


# ===========================================================================
@group("configs")
def configs() -> dict:
    """Section 4.6: the five commercial configuration classes."""
    from commercial import CONFIGS
    from locality_routeA import _rank_cond, pair_angles
    from matrix import classify
    from noise import sigmas_for
    from observables import coefficient_sigmas, enlarged_jacobian, scan_plan
    from route_b import full_jacobian
    from route_c_added_sensor import add_direct_sensor
    from sensors import ALL_SENSOR_NAMES

    plan = scan_plan()
    J7, _ = full_jacobian()
    out = {}
    for key, cfg in CONFIGS.items():
        tag = key.split()[0]
        obs = cfg["obs"]
        idx = [list(ALL_SENSOR_NAMES).index(n) for n in obs]
        J = J7[idx, :]
        sig = sigmas_for(obs)
        if cfg["direct"]:
            J, sig = add_direct_sensor(J, sig, list(cfg["direct"]), 0.05)
        inst = pair_angles(J, sig)
        r, _ = _rank_cond(J, sig)
        out[f"{tag}.rank"] = float(r)
        out[f"{tag}.power_gas"] = inst[("power", "gas")]
        out[f"{tag}.inst_cleared"] = float(sum(v >= 10 for v in inst.values()))
    # correlations that separate B from C
    Gm = J7 @ J7.T
    dg = np.sqrt(np.diag(Gm))
    corr = Gm / np.outer(dg, dg)
    i = list(ALL_SENSOR_NAMES).index
    out["corr_two_bands"] = corr[i("photodiode"), i("photodiode_swir")]
    out["corr_geometric"] = corr[i("photodiode"), i("camera")]
    # class counts for the baseline suite in both regimes
    for regime in ("instantaneous", "accumulated"):
        rows, _ = classify(("photodiode", "camera", "pyrometer"), regime=regime)
        for c in (1, 2, 3):
            out[f"baseline.{regime}.class{c}"] = float(
                sum(1 for v in rows.values() if v["class"] == c))
    return out


# ===========================================================================
@group("added")
def added() -> dict:
    """Section 4.7: what an added measurement would buy."""
    from diagnosability import jacobian, whiten
    from faults import FAULT_NAMES
    from locality_routeA import _rank_cond, pair_angles
    from noise import SIGMAS, sigmas_for
    from observables import coefficient_sigmas, enlarged_jacobian, scan_plan
    from route_b import SUBSETS, full_jacobian
    from route_c_added_sensor import add_direct_sensor, precision_sweep
    from sensors import ALL_SENSOR_NAMES

    plan = scan_plan()
    J, _ = jacobian()
    out: dict[str, float] = {}

    # row-space projection of a unit row on each fault
    U, s, Vt = np.linalg.svd(whiten(J, SIGMAS))
    k = int(np.sum(s > s.max() * 1e-6))
    V = Vt[:k].T
    projections = {}
    for i, n in enumerate(FAULT_NAMES):
        e = np.zeros(len(FAULT_NAMES)); e[i] = 1.0
        projections[n] = float(np.linalg.norm(V.T @ e))
        out[f"projection.{n}"] = projections[n]
    others = [v for n, v in projections.items() if n != "geometry"]
    out["projection_others_min"] = float(min(others))
    out["projection_others_max"] = float(max(others))

    # one idealised direct measurement of each cause
    for n in FAULT_NAMES:
        Jn, sn = add_direct_sensor(J, SIGMAS, [n], 0.05)
        a = pair_angles(Jn, sn)
        r, _ = _rank_cond(Jn, sn)
        out[f"direct.{n}.rank"] = float(r)
        out[f"direct.{n}.cleared"] = float(sum(v >= 10 for v in a.values()))

    # precision sweep on the gas sensor
    # precision_sweep returns (sigma, worst, n_above_floor, rank, cond) tuples
    sw = precision_sweep(J, "gas")
    out["precision_sweep_worst_min"] = float(min(r[1] for r in sw))
    out["precision_sweep_worst_max"] = float(max(r[1] for r in sw))
    out["precision_sweep_cleared_min"] = float(min(r[2] for r in sw))
    out["precision_sweep_cleared_max"] = float(max(r[2] for r in sw))
    out["precision_sweep_noise_max_pct"] = 100 * max(r[0] for r in sw)
    out["precision_sweep_noise_min_pct"] = 100 * min(r[0] for r in sw)

    # gas and layer sensors together
    Jn, sn = add_direct_sensor(J, SIGMAS, ["gas", "layer"], 0.05)
    a = pair_angles(Jn, sn)
    r, _ = _rank_cond(Jn, sn)
    out["two_direct.rank"] = float(r)
    out["two_direct.worst"] = min(a.values())
    out["two_direct.cleared"] = float(sum(v >= 10 for v in a.values()))

    # candidate melt-pool observables
    J7, _ = full_jacobian()
    base_names = SUBSETS["all three (baseline)"]

    def summary(names):
        idx = [list(ALL_SENSOR_NAMES).index(n) for n in names]
        Js = J7[idx, :]
        sig = sigmas_for(names)
        inst = pair_angles(Js, sig)
        Jb = enlarged_jacobian(Js, plan)
        acc = pair_angles(Jb, coefficient_sigmas(sig, plan))
        return inst, acc

    base_i, base_a = summary(base_names)
    out["baseline.acc_power_speed"] = base_a[("power", "speed")]
    out["baseline.acc_worst"] = min(base_a.values())
    out["baseline.inst_cleared"] = float(sum(v >= 10 for v in base_i.values()))
    for label, key in (("+ split the camera (free)", "split"),
                       ("+ SWIR photodiode", "swir"),
                       ("+ wide-band pyrometer", "wide")):
        inst, acc = summary(SUBSETS[label])
        out[f"{key}.gain_on_binding_pair"] = (acc[("power", "speed")]
                                              - base_a[("power", "speed")])
        out[f"{key}.acc_power_speed"] = acc[("power", "speed")]
        out[f"{key}.acc_worst"] = min(acc.values())
        out[f"{key}.inst_cleared"] = float(sum(v >= 10 for v in inst.values()))
        for (a_, b_), v in inst.items():
            out[f"{key}.inst.{a_}_{b_}"] = v

    # candidate correlations with the coaxial photodiode
    Gm = J7 @ J7.T
    dg = np.sqrt(np.diag(Gm))
    corr = Gm / np.outer(dg, dg)
    i = list(ALL_SENSOR_NAMES).index
    out["corr_pd_width"] = corr[i("photodiode"), i("camera_width")]
    out["corr_pd_length"] = corr[i("photodiode"), i("camera_length")]
    return out


# ===========================================================================
@group("validation")
def validation_group() -> dict:
    """Section 4.1: the Guo check and the energy-density structure."""
    from validation import constant_ved_sweep

    _, rows = constant_ved_sweep()
    cond = [r for r in rows if not r["keyholing"]]
    allr = [r for r in rows if r["corrected_depth"] > 0]

    def span(key, subset):
        v = np.array([r[key] for r in subset], float)
        return float(v.max() / v.min())

    out = {
        "guo_depth_span_all": span("corrected_depth", allr),
        "guo_length_span_conduction": span("length", cond),
        "guo_width_span_conduction": span("width", cond),
        "guo_depth_span_conduction": span("corrected_depth", cond),
        "guo_n_regimes": float(len({r["keyholing"] for r in rows})),
    }
    return out


@group("ved")
def ved() -> dict:
    """Section 4.1: VED correlations and exponents across five grids."""
    from sanity_checks import grid_statistics

    out = {}
    stats = grid_statistics()
    for name, s in stats.items():
        key = name.replace(" ", "_")
        for dim in ("width", "depth", "length"):
            out[f"{key}.{dim}.r"] = s[dim]["r"]
            out[f"{key}.{dim}.r2"] = s[dim]["r2"]
            out[f"{key}.{dim}.cos"] = s[dim]["cos"]
        out[f"{key}.n"] = float(s["n"])
    out["primary_grid.width.r"] = stats["sanity_checks 3x3x3"]["width"]["r"]
    out["primary_grid.depth.r"] = stats["sanity_checks 3x3x3"]["depth"]["r"]
    out["primary_grid.n"] = float(stats["sanity_checks 3x3x3"]["n"])
    for dim in ("width", "depth", "length"):
        rs = [s[dim]["r"] for s in stats.values()]
        cs = [s[dim]["cos"] for s in stats.values()]
        r2 = [s[dim]["r2"] for s in stats.values()]
        out[f"{dim}.r_min"] = float(min(rs)); out[f"{dim}.r_max"] = float(max(rs))
        out[f"{dim}.cos_min"] = float(min(cs)); out[f"{dim}.cos_max"] = float(max(cs))
        out[f"{dim}.r2_min"] = float(min(r2))
    out["n_grids"] = float(len(stats))
    return out


# ===========================================================================
@group("discussion")
def discussion() -> dict:
    """Section 5: the external checks and the limitations."""
    from diagnosability import jacobian
    from literature_census import counts
    from reijonen_check import REPORTED_B, fit_speed_exponent
    from scattering_channel import sweep
    from weaver_pads import geometry_inversion

    J, _ = jacobian()
    out = {
        "jacobian_speed_photodiode": J[0, 1],
        "jacobian_power_photodiode": J[0, 0],
        "reported_b": REPORTED_B,
    }
    for p in (100.0, 285.0, 400.0):
        out[f"fitted_b_at_{int(p)}W"] = fit_speed_exponent(p)["b"]
    out["b_excess_pct"] = 100 * (out["fitted_b_at_400W"] / REPORTED_B - 1)
    bs = [out[f"fitted_b_at_{int(p)}W"] for p in (100.0, 285.0, 400.0)]
    out["b_range"] = float(max(bs) - min(bs))

    rows = {r["k"]: r for r in sweep()}
    out["gas_width_change_pct_at_k0"] = 100 * rows[0.0]["width"]
    out["scatter_power_gas_at_k075"] = rows[0.75]["power_gas"]
    out["scatter_power_gas_at_k1"] = rows[1.00]["power_gas"]
    out["scatter_worst_at_k075"] = rows[0.75]["worst"]
    out["scatter_width_sign_at_k075"] = float(np.sign(rows[0.75]["width"]))

    q = geometry_inversion()
    out["geometry_inversion_K"] = q["kelvin"]
    out["preheat_depth_pct_per_100K"] = 100 * q["depth_per_100K"]

    c = counts()
    out["n_works"] = float(c["n_works"])
    out["n_outcome"] = float(c["n_outcome"])
    out["n_input_estimators"] = float(c["n_input_estimators"])
    out["n_lumped"] = float(c["n_lumped"])
    out["year_min"] = float(c["year_range"][0])
    out["year_max"] = float(c["year_range"][1])
    return out


# ===========================================================================
@group("sources")
def sources() -> dict:
    """Values quoted from other people's papers, as recorded in this code.

    These are not recomputed - they are measurements and reported fits from the
    cited works. What is checked is that the paper and the code quote the same
    number, so a transcription error cannot sit in one and not the other. Each
    must still be checked against the article itself before submission; the
    `provenance` column of the report says which.
    """
    from calibrate import WEAVER_POINTS
    from layer_couplings import POWDER_SOLID_RATIO
    from reijonen_check import (REPORTED_AT_POWER, REPORTED_B, SPEED_RANGE_M_S)
    from weaver_pads import CROSS_FLOW_M_S, Y_PAD_SD_RANGE_UM

    base = WEAVER_POINTS[0]
    return {
        # Weaver et al. (2024) Table 4, case 0 expanded uncertainties, k = 2
        "weaver_case0_width_U_um": 6.2,
        "weaver_case0_depth_U_um": 14.1,
        "weaver_case0_width_um": base.width * 1e6,
        "weaver_case0_depth_um": base.depth * 1e6,
        "weaver_cross_flow_m_s": CROSS_FLOW_M_S,
        "weaver_pad_sd_min_um": Y_PAD_SD_RANGE_UM[0],
        "weaver_pad_sd_max_um": Y_PAD_SD_RANGE_UM[1],
        "weaver_width_uncertainty_pct": 100 * 3.1 / 136.3,
        # Trapp et al. (2017): powder absorptivity about twice bare solid
        "trapp_powder_solid_ratio": POWDER_SOLID_RATIO,
        "trapp_wavelength_nm": 1070.0,
        # Reijonen (2024)
        "reijonen_b": REPORTED_B,
        "reijonen_power_W": REPORTED_AT_POWER,
        "reijonen_speed_min_mm_s": SPEED_RANGE_M_S[0] * 1e3,
        "reijonen_speed_max_mm_s": SPEED_RANGE_M_S[1] * 1e3,
        # Honarmandi et al. (2021) report pair correlations between fitted
        # absorptivity, conductivity and heat capacity
        "honarmandi_corr_min": 0.93,
        "honarmandi_corr_max": 0.96,
    }
