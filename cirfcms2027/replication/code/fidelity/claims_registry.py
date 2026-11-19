"""The registered claims of the fidelity paper. Used by `claims.py`.

Each entry: an identifier, the section, the string as printed, the value it
must round to, where the value comes from, and what it means.
"""

from __future__ import annotations


def claims(R: dict, Claim, fam) -> list:
    T = R["theory"]
    ve = fam(R, "validation-equivalent")
    rej = fam(R, "region-rejected")
    t = R["tests"]
    sp = R["spread"]
    dg = {round(g["ssr_ratio"], 2): g for g in R["depth_groups"]}
    N = R["named"]
    env = R["envelope"]
    curve = {c["s"]: c for c in env["curve"]}
    gr = R["grid"]
    gain = R["gain"]

    import theory as th
    bb = [th.matched_severity_budget(28.0, g)[1] for g in gain]
    pair_shift = max(abs(gr["rows"]["121"]["pairs"][p] - gr["rows"]["961"]["pairs"][p])
                     for p in gr["rows"]["961"]["pairs"])
    loc = [r for r in N.values() if r["family"] in ("one parameter", "operating point")]

    C = []
    add = lambda *a, **k: C.append(Claim(*a, **k))

    # theory
    add("budget14", "3", "3.23", T["budget"]["14"], "theory.delta_max(14,3)", "budget at rho 14")
    add("budget28", "3", "1.62", T["budget"]["28"], "theory.delta_max(28,3)", "budget at rho 28")
    add("budget56", "3", "0.81", T["budget"]["56"], "theory.delta_max(56,3)", "budget at rho 56")
    add("budget120", "3", "0.38", T["budget"]["120"], "theory.delta_max(120,3)", "budget at rho 120")
    add("lambda_star", "3", "0.624", T["lambda_star_S3"], "noncentrality_for_coverage", "noncentrality at 90 %")
    add("kappa_star", "3", "0.549", T["kappa_star_S3"], "kappa_star(3)", "commanded-step constant")
    add("repeats", "3", "4", T["repeats_S3"]["28"], "commanded_repeats", "four repeats", skip_text=True)
    add("noise10", "3", "91.6", 100 * T["noise_level_coverage"]["1.1"], "chi2", "true noise 10 % higher")
    add("noise25", "3", "85.3", 100 * T["noise_level_coverage"]["1.25"], "chi2", "true noise 25 % higher")
    add("noise50", "3", "73.6", 100 * T["noise_level_coverage"]["1.5"], "chi2", "true noise 50 % higher")
    add("gain_lo", "3", "9.3", min(gain), "Scorer.gain", "smallest build-context gain")
    add("gain_hi", "3", "11.5", max(gain), "Scorer.gain", "largest build-context gain")
    add("step_power", "6", "3.2", 100 * T["step_for_rho28_eps1pct"]["power"], "J at 961", "power step for rho 28")
    add("step_speed", "6", "9.4", 100 * T["step_for_rho28_eps1pct"]["speed"], "J at 961", "speed step for rho 28")
    add("step_geom", "6", "0.43", T["step_for_rho28_eps1pct"]["geometry"], "J at 961", "preheat index for rho 28")

    # design
    add("n_twins", "4", "301", R["n_twins"], "study rows", "twins scored")
    add("n_region", "4", "2048", R["n_region"], "_region.json", "Sobol samples")
    add("n_accepted", "4", "328", R["n_region_accepted"], "_region.json", "accepted samples")
    add("frac_accepted", "4", "16.0", 100 * R["n_region_accepted"] / R["n_region"], "_region.json", "share accepted")
    add("truth_amb", "2", "12.4", R["truth_amb_mape"], "twin.amb_errors", "truth's error against AM-Bench")

    # validation-equivalent
    add("ve_pred_med", "5.1", "8.5", ve["pred_rms_median"], "table", "median prediction error")
    add("ve_pred_max", "5.1", "11.7", ve["pred_rms_max"], "table", "largest prediction error")
    add("ve_delta_med", "5.1", "22.5", ve["delta_max_median"], "table", "median directional error")
    add("ve_over_n", "5.1", "119", round(ve["frac_over_budget"] * ve["n"]), "table", "twins over budget")
    add("ve_over_pct", "abs", "99", 100 * ve["frac_over_budget"], "table", "share over budget")
    add("ve_flips", "5.1", "89", 100 * ve["flips_inst_any"], "table", "share changing a verdict")
    add("ve_speed", "5.1", "13.4", t["delta_by_fault_accepted_median"]["speed"], "tests", "speed median")
    add("ve_layer", "5.1", "3.3", t["delta_by_fault_accepted_median"]["layer"], "tests", "layer median")
    add("ve_gas", "5.1", "18.1", t["delta_by_fault_accepted_median"]["gas"], "tests", "gas median")
    add("ve_power", "5.1", "18.1", t["delta_by_fault_accepted_median"]["power"], "tests", "power median")
    add("spread_pairs", "5.1", "7140", sp["n_pairs"], "spread", "pairs")
    add("spread_med", "5.1", "30.1", sp["pair_delta_max_median"], "spread", "median pairwise error")
    add("spread_over", "5.1", "98", 100 * sp["pair_frac_over_budget"], "spread", "share of pairs over")
    add("rej_med", "5.1", "71.5", rej["delta_max_median"], "table", "rejected median")
    add("tight_n", "5.1", "28", dg[1.5]["n"], "depth_groups", "twins within 1.5x")
    add("tight125_med", "5.1", "8.7", dg[1.25]["median"], "depth_groups", "median within 1.25x")
    add("tight125_over", "5.1", "5", round(dg[1.25]["frac_over"] * dg[1.25]["n"]), "depth_groups",
        "over budget within 1.25x", skip_text=True)
    add("tight15_med", "5.1", "11.2", dg[1.5]["median"], "depth_groups", "median within 1.5x")

    # indicator
    add("rs_acc", "5.2", "0.18", t["spearman_pred_vs_delta_accepted"]["rho"], "tests", "rank corr, accepted")
    add("rs_acc_p", "5.2", "0.046", t["spearman_pred_vs_delta_accepted"]["p"], "tests", "its p value")
    add("rs_amb", "5.2", "0.32", t["spearman_amb_vs_delta_accepted"]["rho"], "tests", "rank corr with AM-Bench error")
    add("rs_all", "5.2", "0.36", t["spearman_pred_vs_delta_sampled"]["rho"], "tests", "rank corr, all sampled")
    add("keyhole_pred", "5.2", "18.1", N["keyhole coefficient x1.5"]["pred_rms"], "named", "keyhole x1.5 prediction error")

    # accuracy
    add("local_max", "5.3", "1.32", max(r["delta_max"] for r in loc), "named", "largest local error")
    add("local_cov", "5.3", "91.8", 100 * min(r["cov_inst_min28"] for r in loc), "named", "smallest local coverage")
    add("env_first_pred", "5.3", "2.09", env["first_over_pred"], "envelope", "first over-budget prediction error")
    add("env_first_delta", "5.3", "2.54", env["first_over_delta"], "envelope", "its directional error")
    add("env3_pred", "5.3", "2.56", curve[3.0]["worst_pred"], "envelope", "prediction error of 16 deg twin")
    add("env3_delta", "5.3", "16.4", curve[3.0]["worst"], "envelope", "16 deg twin")
    add("env4_pred", "5.3", "3.34", curve[4.0]["worst_pred"], "envelope", "prediction error of 45 deg twin")
    add("env4_delta", "5.3", "45.1", curve[4.0]["worst"], "envelope", "45 deg twin")
    add("env_n2", "5.3", "21", env["n_below_2pct"], "envelope", "twins below 2 %")

    # diagnosis-only
    ctrl = max(r["delta_max"] for r in N.values() if r["family"] == "couplings control")
    add("ctrl", "5.4", "0.001", ctrl, "named", "geometry control upper bound", places=3)
    add("layer_c", "5.4", "0.37",
        max(r["delta_max"] for r in N.values() if r["family"] == "couplings"), "named", "layer couplings")
    add("gain_dom", "5.4", "5.0", 100 * N["noise: gain dominated"]["cov_inst_min28"], "named", "gain-dominated coverage")
    add("equal_noise", "5.4", "96.0", 100 * N["noise: equal noise"]["cov_inst_min28"], "named", "equal-noise coverage")
    add("equal_flips", "5.4", "4", N["noise: equal noise"]["flips_inst"], "named", "verdicts changed", skip_text=True)
    add("scat1", "5.4", "0.44", N["twin omits scattering k=0.25"]["delta_max"], "named", "scattering 0.25")
    add("scat2", "5.4", "1.55", N["twin omits scattering k=0.75"]["delta_max"], "named", "scattering 0.75")
    add("scat3", "5.4", "2.27", N["twin omits scattering k=1"]["delta_max"], "named", "scattering 1.0")

    # build context
    add("bb_min", "5.5", "0.24", min(bb), "matched_severity_budget", "smallest build budget")
    add("bb_max", "5.5", "0.29", max(bb), "matched_severity_budget", "largest build budget")
    add("bc_power5", "5.5", "0.05", 100 * N["power x1.05"]["cov_big_min28"], "named", "build coverage, power +5 %")
    add("bc_abs2", "5.5", "59.8", 100 * N["absorptivity x1.02"]["cov_big_min28"], "named", "build coverage, absorptivity +2 %")
    add("abs2_delta", "5.5", "0.55", N["absorptivity x1.02"]["delta_max"], "named", "absorptivity +2 % error")

    # grid
    add("grid121", "5.6", "0.97", max(gr["rows"]["121"]["delta"]), "_grid.json", "121 vs 961, truth")
    add("grid_pair", "5.6", "0.60", pair_shift, "_grid.json", "largest pairwise shift")
    add("grid_twin", "5.6", "0.97", N["sensor grid 121"]["delta_max"], "named", "121 grid as a twin")
    add("grid_pct", "5.6", "60", 100 * N["sensor grid 121"]["delta_max"] / T["budget"]["28"], "named", "share of budget")
    add("grid_bc", "5.6", "3.1", 100 * N["sensor grid 121"]["cov_big_min28"], "named", "build coverage, 121 grid")
    fl = R.get("floor")
    if fl:
        worst = max(abs(v[k1] - v[k2]) for v in fl.values() for k1, k2 in [tuple(v)])
        add("floor", "5.6", "0.17", worst, "_floor.json", "961 vs 1921 floor", places=2)
    return C
