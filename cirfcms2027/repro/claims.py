"""Every number the paper quotes, with what it means and where it comes from.

One `Claim` per number. Nothing here computes anything: `key` names an entry in
the dict returned by one of `compute.GROUPS`, and `check.py` compares the two.

Tolerance
---------
By default a claim passes if and only if the recomputed value *rounds to the
printed one*: the tolerance is half a unit in the last printed decimal place,
read off `quoted`. So "24.90" must recompute to within 0.005 and "11.7" to
within 0.05. That is strict on purpose - it is the test that catches a number
which drifted after it was written down. Where the paper deliberately states a
bound or an approximation ("roughly", "about", "below", "at least"), the claim
carries an explicit `tol` or a `relation` other than equality, and says so.

Kinds
-----
computed    recomputed from the forward model by this repository
source      a measurement or a reported fit taken from a cited work. Not
            recomputable here; what is checked is that the paper and the code
            carry the same number, so a transcription error cannot hide in one
            of them. The `provenance` field says which article and where.
convention  a threshold or unit this work chose (the 10-degree floor, the
            1e-6 rank tolerance, 100 K per unit of geometry fault). Checked
            against the constant the code actually uses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = ["Claim", "CLAIMS", "by_group"]


def _half_ulp(quoted: str) -> float:
    """Half a unit in the last decimal place of a printed number.

    A claim whose `quoted` text is words rather than digits ("seven", "all
    seven conditions", "rank 5 at every magnitude") is a count or a yes/no, so
    half a unit is the right tolerance there too.
    """
    m = re.search(r"-?\d+(?:\.\d+)?", quoted.replace(",", "").replace("$", ""))
    if m is None:
        return 0.5
    text = m.group()
    if "." in text:
        return 0.5 * 10 ** -len(text.split(".")[1])
    return 0.5


@dataclass(frozen=True)
class Claim:
    id: str
    section: str
    quoted: str
    key: str
    value: float
    means: str
    kind: str = "computed"
    tol: float | None = None
    relation: str = "=="          # "==", ">=", "<=", "range_lo", "range_hi"
    provenance: str = ""
    note: str = ""

    @property
    def tolerance(self) -> float:
        return self.tol if self.tol is not None else _half_ulp(self.quoted)


C = Claim

CLAIMS: list[Claim] = [

    # =====================================================================
    # Section 3.1  Forward model and calibration
    # =====================================================================
    C("cal.width-mape", "3.1", "11.7 %", "calibration.width_mape_pct", 11.7,
      "Mean absolute percentage error on melt pool width over the seven "
      "AM-Bench single-track conditions, after fitting four effective "
      "parameters."),
    C("cal.depth-mape", "3.1", "13.1 %", "calibration.depth_mape_pct", 13.1,
      "The same, on depth."),
    C("cal.n-conditions", "3.1", "seven", "calibration.n_conditions", 7,
      "Number of AM-Bench bare-plate single-track conditions fitted."),
    C("cal.baseline-power", "3.1", "285 W", "calibration.baseline_power_W", 285,
      "The benchmark's own baseline laser power, at which all results are "
      "evaluated.", kind="source",
      provenance="Weaver et al. (2024) Table 4, case 0"),
    C("cal.baseline-speed", "3.1", "960 mm/s",
      "calibration.baseline_speed_mm_s", 960,
      "Baseline scan speed.", kind="source",
      provenance="Weaver et al. (2024) Table 4, case 0"),
    C("cal.baseline-spot", "3.1", "67 um", "calibration.baseline_spot_um", 67,
      "Baseline D4-sigma spot diameter.", kind="source",
      provenance="Weaver et al. (2024) Table 4, case 0"),
    C("cal.baseline-width-err", "3.1", "-15.5 %",
      "calibration.baseline_width_err_pct", -15.5,
      "The model's signed width error at the baseline condition: it "
      "under-predicts."),
    C("cal.baseline-depth-err", "3.1", "+1.7 %",
      "calibration.baseline_depth_err_pct", 1.7,
      "The model's signed depth error at the baseline condition. This is why "
      "depth is the channel the profile inversions of Section 3.5 run "
      "through."),
    C("cal.U-width", "3.1", "6.2 um", "sources.weaver_case0_width_U_um", 6.2,
      "Expanded measurement uncertainty (k = 2) on the baseline width, from "
      "the benchmark's own metrology budget.", kind="source",
      provenance="Weaver et al. (2024) Table 4, case 0"),
    C("cal.U-depth", "3.1", "14.1 um", "sources.weaver_case0_depth_U_um", 14.1,
      "The same, on depth.", kind="source",
      provenance="Weaver et al. (2024) Table 4, case 0"),
    C("cal.all-under", "3.1", "all seven conditions",
      "calibration.n_width_underpredicted", 7,
      "Width is under-predicted at every condition, not scattered about zero: "
      "the one-sided bias of a conduction solution with no mechanism that "
      "widens a pool."),
    C("cal.aspect-lo", "3.1", "0.72", "calibration.aspect_dw_min", 0.72,
      "Smallest measured depth-to-width ratio of the seven tracks. Honarmandi's "
      "keyholing criterion is depth >= width / 1.5, i.e. 0.667, so every "
      "condition is keyholing.", relation="range_lo"),
    C("cal.aspect-hi", "3.1", "2.14", "calibration.aspect_dw_max", 2.14,
      "Largest measured depth-to-width ratio.", relation="range_hi"),
    C("cal.n-keyholing", "3.1", "all seven cases keyhole",
      "calibration.n_keyholing", 7,
      "Conditions meeting the keyholing criterion, applied to the measured "
      "dimensions so it does not depend on the model being corrected."),
    C("cal.conduction-depth", "3.1", "23.6 %",
      "calibration.conduction_only_depth_mape_pct", 23.6,
      "Depth error of a pure conduction fit with the same three free "
      "parameters over the same bounds - the like-for-like comparison that "
      "makes the keyhole term necessary rather than cosmetic."),
    C("cal.conduction-width", "3.1", "8.5 %",
      "calibration.conduction_only_width_mape_pct", 8.5,
      "Width error of that same conduction-only fit: essentially unchanged, so "
      "the keyhole term buys depth without costing width."),
    C("cal.keyhole-criterion", "3.1", "the criterion's 0.67",
      "calibration.keyhole_criterion_dw", 0.67,
      "Honarmandi's keyholing criterion restated as a depth-to-width ratio: "
      "depth >= width / 1.5. Applied to the measured dimensions, so it does not "
      "depend on the model being corrected.", kind="convention"),
    C("cal.step", "3.1", "h = 0.002", "calibration.derivative_step", 0.002,
      "The central-difference step at which every Jacobian in the paper is "
      "evaluated.", kind="convention"),
    C("cal.step-change-002", "3.1", "39.3 %",
      "calibration.step_change_pct_at_0.02", 39.3,
      "Largest relative change in any Jacobian entry between h = 0.04 and "
      "h = 0.02: the derivative has not converged at those steps."),
    C("cal.step-change-0005", "3.1", "below 0.3 %",
      "calibration.step_change_pct_at_0.005", 0.3,
      "The same between h = 0.01 and h = 0.005, by which point it has.",
      relation="<="),

    # =====================================================================
    # Section 3.2  Fault definitions
    # =====================================================================
    C("fault.geometry-unit", "3.2", "100 K",
      "couplings.geometry_preheat_kelvin", 100,
      "The geometry fault is a local preheat rise, one unit being 100 K.",
      kind="convention"),
    C("fault.absorptivity-coupling", "3.2", "-0.230",
      "couplings.absorptivity_coupling", -0.230,
      "d(ln A)/d(ln t) for a powder bed whose absorptivity saturates with "
      "depth, negated because the fault is positive for a thinner layer. "
      "Derived, not chosen."),
    C("fault.trapp-ratio", "3.2", "approximately two",
      "sources.trapp_powder_solid_ratio", 2.0,
      "Powder-to-solid absorptivity ratio measured calorimetrically in situ.",
      kind="source", provenance="Trapp et al. (2017), Applied Materials Today 9"),
    C("fault.trapp-wavelength", "3.2", "1070 nm",
      "sources.trapp_wavelength_nm", 1070,
      "Wavelength of that measurement.", kind="source",
      provenance="Trapp et al. (2017)"),
    C("fault.implied-solid-absorptivity", "3.2", "0.258",
      "couplings.implied_solid_absorptivity", 0.258,
      "Bare-solid absorptivity implied by dividing the fitted effective value "
      "by the powder enhancement. It lands inside the 0.25-0.35 published for "
      "nickel alloys near 1 um, which the calibration was not built to do."),
    C("fault.enthalpy-coupling", "3.2", "+0.186",
      "couplings.enthalpy_coupling", 0.186,
      "The effective-power coupling of a layer-thickness change, phi/(1-phi), "
      "from the share of absorbed energy spent melting the powder itself."),
    C("fault.phi", "3.2", "15.7 %", "couplings.phi_pct", 15.7,
      "That share: melting the nominal layer consumes 15.7 % of the absorbed "
      "energy per unit track length."),
    C("fault.net-product", "3.2", "-0.044",
      "couplings.net_product_coupling", -0.044,
      "The two derived channels act on the same product (absorptivity x power) "
      "and nearly cancel there. What is left is the unmeasured conductivity "
      "channel, which is therefore the one thing that distinguishes a thin "
      "layer from a weak laser at an instant."),
    C("fault.power-layer-no-conductivity", "3.2", "0.00 deg",
      "couplings_sweep.power_layer_at_zero_conductivity", 0.00,
      "With the conductivity channel removed, the layer fault acts only through "
      "the absorbed-power product and joins the power/gas degeneracy exactly."),
    C("fault.layer-gas-no-conductivity", "3.2", "0.00 deg",
      "couplings_sweep.layer_gas_at_zero_conductivity", 0.00,
      "The same for the layer/gas pair."),

    # =====================================================================
    # Section 3.4  Diagnosability measures
    # =====================================================================
    C("measure.floor", "3.4", "10 deg", "robustness.floor", 10.0,
      "The practical separation floor adopted as a convention throughout.",
      kind="convention"),
    C("measure.rank-tol", "3.4", "1e-6", "meltpool.rank_tol", 1e-6,
      "A singular value below this fraction of the largest counts as no "
      "direction at all.", kind="convention", tol=1e-12),

    # =====================================================================
    # Section 3.5  Build context and the enlarged observation
    # =====================================================================
    C("ctx.n-segments", "3.5", "N = 84", "context.n_segments", 84,
      "Segments in the default synthetic build plan: six layers of fourteen "
      "scan vectors."),
    C("ctx.n-observables", "3.5", "15 observables",
      "context.n_observables", 15,
      "Three sensors times five regression coefficients each, in place of three "
      "instantaneous readings."),
    C("ctx.root-diag-lo", "3.5", "0.109", "context.root_diag_min", 0.109,
      "Smallest of the five sqrt[(G'G)^-1]_jj factors by which fitting 84 "
      "segments to five regressors reduces each coefficient's noise.",
      relation="range_lo"),
    C("ctx.root-diag-hi", "3.5", "0.136", "context.root_diag_max", 0.136,
      "Largest of those factors.", relation="range_hi"),
    C("ctx.noise-reduction", "3.5", "a seven- to ninefold",
      "context.noise_reduction_max", 9.0,
      "The reciprocal of the smallest factor. The reduction runs from about "
      "sevenfold to about ninefold across the five coefficients.", tol=0.3),
    C("ctx.cross-flow", "3.5", "4.3 m/s", "sources.weaver_cross_flow_m_s", 4.3,
      "Argon cross-flow speed over the benchmark pads.", kind="source",
      provenance="Weaver et al. (2024)"),
    C("ctx.pad-mean", "3.5", "27.2 %", "context.pad_mean_change_pct", -27.2,
      "Mean depth reduction on pad tracks scanned parallel to the gas flow "
      "against anti-parallel ones, over four cross-sections.", kind="source",
      provenance="Weaver et al. (2024) Table 5, Y-pad; computed from the "
                 "twelve depths recorded in weaver_pads.py"),
    C("ctx.pad-sd-lo", "3.5", "4 um", "context.pad_sd_min_um", 4.0,
      "Smallest standard deviation across the twelve Table 5 rows. The effect "
      "is about 50 um against a scatter of about 10 um.", kind="source",
      provenance="Weaver et al. (2024) Table 5", relation="range_lo"),
    C("ctx.pad-sd-hi", "3.5", "11 um", "context.pad_sd_max_um", 11.0,
      "Largest of those standard deviations.", kind="source",
      provenance="Weaver et al. (2024) Table 5", relation="range_hi"),
    C("ctx.control-lo", "3.5", "2.4 %", "context.pad_control_max_pct", -2.4,
      "The perpendicular control pad's smaller depth change, which is what "
      "makes the parallel effect attributable to the gas rather than to scan "
      "reversal.", kind="source", provenance="Weaver et al. (2024) Table 5"),
    C("ctx.control-hi", "3.5", "4.7 %", "context.pad_control_min_pct", -4.7,
      "Its larger one.", kind="source",
      provenance="Weaver et al. (2024) Table 5"),
    C("ctx.f-gas-control", "3.5", "0.046", "context.f_gas_control", 0.046,
      "Gas-fault severity implied by the control pad's depth change, inverted "
      "through the model's depth channel."),
    C("ctx.f-gas-parallel", "3.5", "0.404", "context.f_gas_parallel_mean",
      0.404, "The same for the parallel-track mean."),
    C("ctx.swing", "3.5", "8.8x", "context.measured_swing", 8.8,
      "Ratio of those two: the gas channel's effective severity swings this "
      "much inside a single healthy build, from scan direction alone."),
    C("ctx.asserted-swing", "3.5", "6.05x", "context.asserted_swing", 6.05,
      "The swing of the gas profile this work assumes, exp(2c) at c = 0.90."),
    C("ctx.measured-contrast", "3.5", "1.08", "context.measured_contrast", 1.08,
      "The measured swing in contrast units, ln(swing)/2, which is what makes "
      "it comparable with the asserted profile."),
    C("ctx.asserted-contrast", "3.5", "0.90", "context.asserted_contrast", 0.90,
      "The asserted gas contrast.", kind="convention"),
    C("ctx.understatement", "3.5", "20 %", "context.understatement_pct", 20.0,
      "By how much the one profile that can be checked against measurement is "
      "understated - in the direction that costs this analysis nothing.",
      tol=1.0),

    # =====================================================================
    # Section 3.6  Sensor noise, derived from transduction
    # =====================================================================
    C("noise.weaver-width-pct", "3.6", "2.3 %",
      "sources.weaver_width_uncertainty_pct", 2.3,
      "The only citable in-process-adjacent figure found: a relative width "
      "uncertainty from a cross-sectional metrology budget - which is not "
      "in-process noise, which is why the figures are derived instead.",
      kind="source", provenance="Weaver et al. (2024), 3.1 um on 136.3 um"),
    C("noise.wien", "3.6", "1.333", "noise.ratio_wien_sensitivity", 1.333,
      "|d ln R / d ln T| for a two-colour ratio at 750/950 nm in the Wien "
      "limit: (c2/T)(1/lambda2 - 1/lambda1). The inversion divides by this, so "
      "closely spaced bands amplify noise."),
    C("noise.peak-T", "3.6", "3031 K", "noise.peak_temperature_K", 3031,
      "The model's peak melt pool temperature, at which that sensitivity is "
      "evaluated."),
    C("noise.pyrometer", "3.6", "1.061", "noise.pyrometer", 1.061,
      "The pyrometer's relative noise in units of the photodiode's: sqrt(2) "
      "from two independent channels, divided by the ratio's temperature "
      "sensitivity. A two-colour pyrometer is a noisier relative instrument "
      "than the photodiode it is built from."),
    C("noise.planck", "3.6", "10.52", "noise.planck_log_sensitivity", 10.52,
      "d ln L / d ln T at 850 nm and the liquidus, 1609 K. Planck is steep "
      "there, which is why an intensity threshold localises an edge well."),
    C("noise.isotherm-shift", "3.6", "0.095 %",
      "noise.isotherm_shift_pct_at_1pct", 0.095,
      "How far a 1 % radiance error displaces the apparent liquidus isotherm, "
      "in temperature."),
    C("noise.camera", "3.6", "0.142", "noise.camera", 0.142,
      "The camera's relative noise, from propagating that isotherm shift "
      "through the model's own dimension solver."),
    C("noise.photodiode", "3.6", "1", "noise.photodiode", 1.0,
      "The photodiode reading is a band-integrated radiometric power, so its "
      "relative noise is the shared fractional radiometric noise itself. It "
      "serves as the unit, and only ratios enter the whitening."),
    C("noise.camera-factor", "3.6", "a factor of seven",
      "noise.camera_precision_factor", 7.0,
      "How much more precise the camera is than the photodiode, in relative "
      "terms.", tol=0.5),

    # =====================================================================
    # Section 4.1  Validation
    # =====================================================================
    C("val.guo-depth", "4.1", "2.37x", "validation.guo_depth_span_all", 2.37,
      "Span of melt pool depth across the constant-energy-density sweep. Guo "
      "et al. report orders of magnitude, so this is a partial pass: the "
      "existence, direction and regime transition reproduce, the magnitude "
      "does not."),
    C("val.guo-length", "4.1", "2.53x",
      "validation.guo_length_span_conduction", 2.53,
      "Span of melt pool length over the conduction-regime rows of the same "
      "sweep, so the keyhole jump cannot flatter it. Length carries the "
      "variation that width and depth do not."),
    C("val.guo-width", "4.1", "1.11x",
      "validation.guo_width_span_conduction", 1.11,
      "Span of width over those rows."),
    C("val.n-melted", "4.1", "27 melted conditions", "ved.primary_grid.n", 27,
      "Conditions in the primary energy-density grid that produced a melt "
      "pool."),
    C("val.r-width", "4.1", "+0.20", "ved.primary_grid.width.r", 0.20,
      "Log-log correlation of width with volumetric energy density on that "
      "grid."),
    C("val.r-depth", "4.1", "+0.77", "ved.primary_grid.depth.r", 0.77,
      "The same for depth: depth tracks energy density, width does not, which "
      "is the structure the benchmark reports."),
    C("val.r-width-hi", "4.1", "+0.68", "ved.width.r_max", 0.68,
      "Largest value width's correlation takes across the five grids. It runs "
      "right across zero, so the correlation is a property of the sampled "
      "region rather than of the model - which is why the paper reports "
      "exponents instead.", relation="range_hi"),
    C("val.r-width-lo", "4.1", "-0.22", "ved.width.r_min", -0.22,
      "Its smallest value.", relation="range_lo"),
    C("val.r2-floor", "4.1", "R2 >= 0.94", "ved.depth.r2_min", 0.94,
      "Worst coefficient of determination of a (P, v, d) power-law fit to "
      "width or depth over all five grids. The exponents are stable where the "
      "correlation is not.", relation=">="),
    C("val.cos-depth-lo", "4.1", "0.64", "ved.depth.cos_min", 0.64,
      "Smallest cosine between depth's fitted exponents and the (1, -1, -2) "
      "ray a pure function of energy density must lie along.",
      relation="range_lo"),
    C("val.cos-depth-hi", "4.1", "0.74", "ved.depth.cos_max", 0.74,
      "Its largest.", relation="range_hi"),
    C("val.cos-width-lo", "4.1", "-0.11", "ved.width.cos_min", -0.11,
      "Smallest cosine for width - essentially orthogonal to the ray on every "
      "grid, because width and depth depend on spot size with opposite signs "
      "and spot size is the one variable a volumetric density folds away.",
      relation="range_lo"),
    C("val.cos-width-hi", "4.1", "0.00", "ved.width.cos_max", 0.00,
      "Its largest.", relation="range_hi"),

    # =====================================================================
    # Section 4.2  Laser power and shielding gas are exactly confounded
    # =====================================================================
    C("conf.ratio-pd", "4.2", "-0.99999", "meltpool.ratio_power_gas_pd",
      -0.99999,
      "Ratio of the power and gas Jacobian columns at the photodiode. The two "
      "faults act only on the product (effective absorptivity x power), in "
      "which the temperature rise is linear, so the columns are the same "
      "vector."),
    C("conf.ratio-cam", "4.2", "-1.00000", "meltpool.ratio_power_gas_cam",
      -1.00000, "The same at the camera."),
    C("conf.ratio-pyr", "4.2", "-0.99993", "meltpool.ratio_power_gas_pyr",
      -0.99993, "The same at the pyrometer."),
    C("conf.ratio-spread", "4.2", "7e-5", "meltpool.ratio_spread", 7.0e-5,
      "Spread of those three, which is finite-difference error on an exact "
      "identity rather than physics.", tol=0.5e-5),
    C("conf.identity", "4.2", "eight significant figures",
      "meltpool.identity_max_relative_error", 0.0,
      "Largest relative difference between the nominal readings and those "
      "under a simultaneous power fault f and gas fault ln(1+f), over f from "
      "2 % to 20 %. The two cancel exactly: the readings are bit-identical in "
      "double precision, so the paper's 'eight significant figures' understates "
      "it.", tol=1e-14),
    C("conf.angle", "4.2", "0.00 deg", "meltpool.inst.power_gas", 0.00,
      "The pairwise angle between the whitened power and gas columns. Zero by "
      "algebra, not by noise."),
    C("conf.sweep-max", "4.2", "0.00 deg",
      "couplings_sweep.power_gas_max_over_sweep", 0.00,
      "The largest that angle reaches over every coupling constant swept "
      "across its plausible range: the degeneracy is not an artefact of a "
      "chosen constant."),

    # =====================================================================
    # Section 4.3  The limit is the melt pool, not the sensor count
    # =====================================================================
    C("melt.corr-pd-cam", "4.3", "0.99960", "meltpool.corr_pd_cam", 0.99960,
      "Correlation between the photodiode's and the camera's response patterns "
      "across the five faults, from the normalised sensor Gram matrix. Row "
      "scalings cancel in the normalisation, so this is the one result here "
      "that does not depend on the derived noise figures."),
    C("melt.corr-pd-pyr", "4.3", "0.99508", "meltpool.corr_pd_pyr", 0.99508,
      "The same for photodiode and pyrometer."),
    C("melt.corr-cam-pyr", "4.3", "0.99477", "meltpool.corr_cam_pyr", 0.99477,
      "The same for camera and pyrometer."),
    C("melt.sv1", "4.3", "13.14", "meltpool.sv1", 13.14,
      "Largest singular value of the whitened Jacobian: the suite's response "
      "along its dominant direction, in noise widths."),
    C("melt.sv2", "4.3", "0.0638", "meltpool.sv2", 0.0638,
      "The second."),
    C("melt.sv3", "4.3", "0.00513", "meltpool.sv3", 0.00513,
      "The third."),
    C("melt.energy", "4.3", "99.998 %", "meltpool.leading_energy_pct", 99.998,
      "Share of the suite's squared response lying along that one direction."),
    C("melt.rank", "4.3", "Three of the five fault directions",
      "meltpool.inst_rank", 3,
      "Effective rank of the whitened Jacobian: how many fault directions are "
      "observable at all."),
    C("melt.unobserved", "4.3", "two are not observed at all",
      "meltpool.n_unobserved_directions", 2,
      "The remaining directions, spanning the power-gas combination."),
    C("melt.cond", "4.3", "2562", "meltpool.inst_cond", 2562,
      "Condition number: the weakest observed direction responds this many "
      "times less than the strongest.", tol=0.5),
    C("melt.seven-rank", "4.3", "does not raise the attained rank",
      "meltpool.seven_rank", 3,
      "Rank with all seven candidate observables fitted. Seven instruments "
      "leave power and gas exactly as confounded as one."),
    C("melt.seven-sv1", "4.3", "23.7", "meltpool.seven_sv1", 23.7,
      "First singular value of the seven-row whitened Jacobian."),
    C("melt.seven-sv2", "4.3", "9.74", "meltpool.seven_sv2", 9.74,
      "The second."),
    C("melt.seven-sv3", "4.3", "6.0e-2", "meltpool.seven_sv3", 6.0e-2,
      "The third.", tol=0.05e-2),
    C("melt.seven-sv4", "4.3", "5.0e-6", "meltpool.seven_sv4", 5.0e-6,
      "The fourth, which is below the rank threshold.", tol=0.05e-6),
    C("melt.seven-sv5", "4.3", "1.4e-6", "meltpool.seven_sv5", 1.4e-6,
      "The fifth.", tol=0.05e-6),
    C("melt.seven-sv4-ratio", "4.3", "2e-7",
      "meltpool.seven_sv4_over_sv1", 2e-7,
      "The fourth singular value as a fraction of the leading one: two orders "
      "below the threshold adopted here, so four directions are formally "
      "present but only three are measurements.", tol=0.5e-7),
    C("melt.channel-bound", "4.3", "rank 4", "meltpool.channel_bound", 4,
      "The structural bound. Everything the model knows funnels into four "
      "physical channels - absorbed power, scan speed, effective conductivity "
      "and preheat - so no instrument reading only the melt pool can exceed "
      "it, however many are fitted.", kind="convention"),

    # =====================================================================
    # Section 4.4  Build context dissolves the limit
    # =====================================================================
    C("ctx.rank", "4.4", "rank rises from 3 to 5", "meltpool.acc_rank", 5,
      "Rank of the enlarged observation: all five fault directions become "
      "observable."),
    C("ctx.worst", "4.4", "24.90 deg", "meltpool.acc_worst", 24.90,
      "The worst pair over a build, against 0.00 per segment. This is the "
      "paper's headline number and the pair is power/speed."),
    C("ctx.power-gas", "4.4", "29.34 deg", "meltpool.acc.power_gas", 29.34,
      "Power against gas over a build: the pair that is exactly confounded "
      "instantaneously."),
    C("ctx.cond", "4.4", "falls from 2562 to 50", "meltpool.acc_cond", 50,
      "Condition number of the enlarged observation.", tol=0.5),
    C("ctx.cleared", "4.4", "all ten pairs clearing",
      "meltpool.acc_cleared", 10,
      "Pairs clearing the 10-degree floor over a build."),
    C("ctx.inst-cleared", "4.4", "against none per segment",
      "meltpool.inst_cleared", 0,
      "Pairs clearing it per segment."),
    C("ctl.shared-rank", "4.4", "rank 3", "meltpool.shared_profile_rank", 3,
      "Rank when all five faults are given one identical profile. The enlarged "
      "matrix still has 15 rows, so the gain is not dimensionality: "
      "proportional columns of B make it inherit the instantaneous column "
      "directions."),
    C("ctl.shared-cond", "4.4", "condition number 2562",
      "meltpool.shared_profile_cond", 2562,
      "Its condition number - the instantaneous value exactly.", tol=0.5),
    C("ctl.shared-worst", "4.4", "0.00 deg",
      "meltpool.shared_profile_worst", 0.00,
      "Its worst pair: the instantaneous result returns exactly."),
    C("sec.rank5", "4.4", "rank 5 at every magnitude", "secants.all_rank_5", 1,
      "Whether replacing every derivative by a secant through the full "
      "nonlinear chain still gives rank 5, at every magnitude tested in both "
      "signs."),
    C("sec.mag-lo", "4.4", "0.2 %", "secants.mag_min_pct", 0.2,
      "Smallest fault magnitude at which the secant check is run."),
    C("sec.mag-hi", "4.4", "20 %", "secants.mag_max_pct", 20,
      "Largest."),
    C("sec.binding-lo", "4.4", "12.82 deg", "secants.binding_pair_min", 12.82,
      "Smallest value the baseline binding pair (power/speed) takes across "
      "those magnitudes, at +20 %. So the derivative limit is not strictly "
      "conservative.", relation="range_lo"),
    C("sec.binding-hi", "4.4", "37.95 deg", "secants.binding_pair_max", 37.95,
      "Its largest, at -20 %.", relation="range_hi"),
    C("sec.cond-lo", "4.4", "47", "secants.cond_min", 47,
      "Smallest condition number over those magnitudes.", relation="range_lo",
      tol=0.5),
    C("sec.cond-hi", "4.4", "62", "secants.cond_max", 62,
      "Largest.", relation="range_hi", tol=0.5),
    C("sec.margin", "4.4", "1.3x", "secants.floor_margin_at_plus20", 1.3,
      "How far the +20 % case clears the floor.", tol=0.05),
    C("sec.exact", "4.4", "0.04 deg",
      "secants.exact_vs_interpolated_max_deg", 0.04,
      "Largest angle disagreement between the interpolated response curves and "
      "recomputing the full model at every one of the 84 segments."),

    # =====================================================================
    # Section 4.5  Robustness
    # =====================================================================
    C("rob.n-at-25", "4.5", "five of ten pairs",
      "robustness.n_clearing_at_25pct", 5,
      "Pairs clearing the floor at or below a quarter of the asserted profile "
      "strength."),
    C("rob.hardest", "4.5", "45 %", "robustness.hardest_pair_contrast", 0.45,
      "The strength the hardest pair, power/speed, needs. A machine whose "
      "patterns are half as strong still resolves every pair.", tol=0.005),
    C("rob.n-perm", "4.5", "all 120 permutations",
      "robustness.n_permutations", 120,
      "Ways of reassigning which fault follows which build variable."),
    C("rob.perm-rank5", "4.5", "survives every one",
      "robustness.perm_rank5", 120,
      "Assignments that still give rank 5."),
    C("rob.perm-cleared", "4.5", "survives every one",
      "robustness.perm_all_cleared", 120,
      "Assignments in which all ten pairs still clear the floor."),
    C("rob.perm-lo", "4.5", "16.2 deg", "robustness.perm_worst_min", 16.2,
      "Smallest the worst pair becomes over those 120 assignments. It does not "
      "matter which fault follows which variable, only that they differ - but "
      "the headline does move, by up to about nine degrees.",
      relation="range_lo"),
    C("rob.perm-hi", "4.5", "30.1 deg", "robustness.perm_worst_max", 30.1,
      "Its largest.", relation="range_hi"),
    C("rob.noise-sets", "4.5", "all four noise sets",
      "noise_sets.n_noise_sets", 4,
      "Noise assumptions swept: the derived set, a gain-dominated pyrometer, a "
      "perimeter-averaged camera, and equal noise on every channel."),
    C("rob.noise-spread", "4.5", "under half a degree",
      "noise_sets.spread_deg", 0.5,
      "How far the headline moves across those four sets.", relation="<=",
      tol=0.5),
    C("rob.coupling-spread", "4.5", "the full range of the unmeasured "
      "conductivity coupling", "couplings_sweep.acc_worst_spread", 0.0,
      "How far the headline moves across every coupling constant swept over "
      "its plausible range.", relation="<=", tol=0.5),
    C("rob.N12", "4.5", "11.23 deg", "robustness.worst_at_N12", 11.23,
      "The worst pair with only twelve segments: the regression has barely "
      "enough to fit five regressors."),
    C("rob.N30", "4.5", "22.90 deg", "robustness.worst_at_N30", 22.90,
      "With thirty."),
    C("rob.N84", "4.5", "flat thereafter", "robustness.worst_at_N84", 24.90,
      "With the default 84."),
    C("rob.N288", "4.5", "flat thereafter", "robustness.worst_at_N288", 24.9,
      "With 288: flat, so segment count stops binding well before the default "
      "plan.", tol=0.5),
    C("rob.collapse", "4.5", "collapses that pair to its instantaneous angle",
      "robustness.collapse_max_disagreement_deg", 0.0,
      "Largest disagreement between a forced-equal pair's angle and its "
      "instantaneous angle, over all ten pairs. Forcing two profiles equal "
      "returns that pair exactly to where it was per segment.", tol=1e-3),
    C("rob.mildest", "4.5", "4.63 deg", "robustness.mildest_instantaneous",
      4.63, "The mildest instantaneous angle, which is still below the floor - "
      "so no pair of faults may share a spatial signature."),
    C("rob.support-tolerance", "4.5", "roughly 84 %",
      "robustness.support_mix_tolerance", 0.84,
      "How much of the layer profile may be driven by part support, rather "
      "than by the recoater cycle assumed here, before layer/geometry falls "
      "below the floor. Liu et al. measure layer-thickness variation following "
      "support, so this is the relevant failure.", tol=0.01),
    C("rob.support-at-80", "4.5", "12.07 deg",
      "robustness.support_mix_at_80pct", 12.07,
      "The layer/geometry angle at 80 % support-driven."),
    C("rob.drift-never", "4.5", "never brings power/layer below it",
      "robustness.drift_mix_crosses_floor", 0,
      "Whether mixing the power fault's build-drift driver into the layer "
      "profile ever takes power/layer below the floor. It does not: every "
      "profile is normalised to unit mean, so two faults sharing a driver give "
      "(1, a) and (1, b), which are non-proportional wherever the contrasts "
      "differ."),

    # =====================================================================
    # Table 1  The diagnosability matrix
    # =====================================================================
    *[C(f"tab.inst.{a}_{b}", "Table 1", f"{v:.2f}", f"meltpool.inst.{a}_{b}", v,
        f"Per-segment angle between {a} and {b} for the baseline suite.")
      for a, b, v in [
          ("power", "gas", 0.00), ("layer", "gas", 0.32),
          ("power", "layer", 0.32), ("power", "speed", 0.70),
          ("speed", "gas", 0.70), ("speed", "layer", 1.03),
          ("speed", "geometry", 3.62), ("power", "geometry", 4.31),
          ("gas", "geometry", 4.31), ("layer", "geometry", 4.63)]],
    *[C(f"tab.split.{a}_{b}", "Table 1", f"{v:.2f}", f"added.split.inst.{a}_{b}",
        v, f"Per-segment angle between {a} and {b} with the camera's two axes "
           f"reported separately instead of as an area.")
      for a, b, v in [
          ("power", "gas", 0.00), ("layer", "gas", 64.53),
          ("power", "layer", 64.53), ("power", "speed", 43.43),
          ("speed", "gas", 43.43), ("speed", "layer", 72.04),
          ("speed", "geometry", 43.28), ("power", "geometry", 3.08),
          ("gas", "geometry", 3.08), ("layer", "geometry", 64.81)]],
    *[C(f"tab.acc.{a}_{b}", "Table 1", f"{v:.2f}", f"meltpool.acc.{a}_{b}", v,
        f"Angle between {a} and {b} accumulated over an 84-segment build.")
      for a, b, v in [
          ("power", "gas", 29.34), ("layer", "gas", 44.48),
          ("power", "layer", 36.26), ("power", "speed", 24.90),
          ("speed", "gas", 35.87), ("speed", "layer", 46.16),
          ("speed", "geometry", 31.95), ("power", "geometry", 25.42),
          ("gas", "geometry", 31.39), ("layer", "geometry", 40.54)]],
    C("tab.inst-count", "Table 1", "0/10", "meltpool.inst_cleared", 0,
      "Pairs clearing the floor per segment, baseline suite."),
    C("tab.split-count", "Table 1", "7/10", "added.split.inst_cleared", 7,
      "Pairs clearing it per segment with the camera split."),
    C("tab.acc-count", "Table 1", "10/10", "meltpool.acc_cleared", 10,
      "Pairs clearing it over a build."),

    # =====================================================================
    # Section 4.6  Configuration classes
    # =====================================================================
    C("cfg.A-rank", "4.6", "rank 1", "configs.A.rank", 1,
      "Rank of a single coaxial photodiode."),
    C("cfg.B-rank", "4.6", "rank 2", "configs.B.rank", 2,
      "Rank of photodiode plus pool imaging."),
    C("cfg.C-rank", "4.6", "rank 2", "configs.C.rank", 2,
      "Rank of two photodiodes in separate bands."),
    C("cfg.D-rank", "4.6", "rank 3", "configs.D.rank", 3,
      "Rank of the research reference, which adds pyrometry."),
    C("cfg.E-rank", "4.6", "rank 3", "configs.E.rank", 3,
      "Rank of two photodiodes plus upstream power monitoring."),
    C("cfg.A-power-gas", "4.6", "0.00 deg", "configs.A.power_gas", 0.00,
      "Power against gas for configuration A."),
    C("cfg.B-power-gas", "4.6", "0.00 deg", "configs.B.power_gas", 0.00,
      "The same for B."),
    C("cfg.C-power-gas", "4.6", "0.00 deg", "configs.C.power_gas", 0.00,
      "For C."),
    C("cfg.D-power-gas", "4.6", "0.00 deg", "configs.D.power_gas", 0.00,
      "For D. No configuration built solely from melt-pool observables "
      "separates the pair, whatever its sensor count."),
    C("cfg.E-power-gas", "4.6", "84.02 deg", "configs.E.power_gas", 84.02,
      "For E, which samples delivered laser power upstream of the process zone "
      "and so sees the laser output without the plume attenuation."),
    C("cfg.E-cleared", "4.6", "resolves four of ten",
      "configs.E.inst_cleared", 4,
      "Pairs E resolves per segment - the only class that resolves any."),
    C("cfg.corr-two-bands", "4.6", "0.99996", "configs.corr_two_bands",
      0.99996,
      "Correlation between two photodiode bands of the same emitted light. "
      "B and C are separated not by class count, both empty, but by this."),
    C("cfg.corr-geometric", "4.6", "0.99960", "configs.corr_geometric",
      0.99960,
      "The same for a geometric measurement against a radiometric one."),
    C("cfg.class3-inst", "4.6", "class 3 empty in both",
      "configs.baseline.instantaneous.class3", 0,
      "Structurally irreducible pairs per segment for the baseline suite."),
    C("cfg.class3-acc", "4.6", "class 3 empty in both",
      "configs.baseline.accumulated.class3", 0,
      "The same over a build."),
    C("cfg.class1-acc", "4.6", "all ten pairs in class 1",
      "configs.baseline.accumulated.class1", 10,
      "Pairs resolvable from existing signals over a build."),

    # =====================================================================
    # Section 4.7  What an added measurement would buy
    # =====================================================================
    C("add.direct-rank", "4.7", "raises the rank to 4",
      "added.direct.power.rank", 4,
      "Rank after adding one idealised direct measurement of a cause."),
    C("add.direct-cleared", "4.7", "clears exactly the four pairs",
      "added.direct.power.cleared", 4,
      "Pairs it clears: the four involving that cause, no more."),
    C("add.geometry-rank", "4.7", "raising the rank not at all",
      "added.direct.geometry.rank", 3,
      "Rank after adding a direct measurement of geometry - unchanged, because "
      "a unit row on geometry already lies inside the existing row space."),
    C("add.projection-geometry", "4.7", "1.0000",
      "added.projection.geometry", 1.0000,
      "Projection of a unit row on geometry onto the row space of the three "
      "existing sensors. The suite observes preheat already and simply cannot "
      "separate the rest."),
    C("add.projection-lo", "4.7", "0.53", "added.projection_others_min", 0.53,
      "Smallest such projection for the other four causes.",
      relation="range_lo"),
    C("add.projection-hi", "4.7", "0.91", "added.projection_others_max", 0.91,
      "Largest.", relation="range_hi"),
    C("add.precision-worst", "4.7", "0.32 deg",
      "added.precision_sweep_worst_min", 0.32,
      "The worst pair with an added gas sensor, unchanged across the whole "
      "precision sweep. Adding a row in a new direction changes the rank; "
      "making an existing row quieter does not."),
    C("add.precision-worst-hi", "4.7", "0.32 deg",
      "added.precision_sweep_worst_max", 0.32,
      "The same at the other end of the sweep - it does not move."),
    C("add.precision-noise-hi", "4.7", "50 %",
      "added.precision_sweep_noise_max_pct", 50,
      "Coarsest added-sensor noise swept."),
    C("add.precision-noise-lo", "4.7", "0.2 %",
      "added.precision_sweep_noise_min_pct", 0.2,
      "Finest."),
    C("add.precision-cleared", "4.7", "four of ten cleared throughout",
      "added.precision_sweep_cleared_min", 4,
      "Pairs cleared, constant across that sweep."),
    C("add.two-rank", "4.7", "rank 5", "added.two_direct.rank", 5,
      "Rank with idealised direct gas and layer sensors together."),
    C("add.two-worst", "4.7", "0.70 deg", "added.two_direct.worst", 0.70,
      "Their worst pair - neither says anything about power against speed, so "
      "build context outperforms two perfect direct measurements of the causes "
      "themselves."),
    C("add.two-cleared", "4.7", "seven of ten", "added.two_direct.cleared", 7,
      "Pairs they clear."),
    C("add.split-gain", "4.7", "+23.89 deg",
      "added.split.gain_on_binding_pair", 23.89,
      "What reporting the camera's two axes separately is worth on the pair "
      "that binds the baseline accumulated result, power/speed."),
    C("add.split-power-speed", "4.7", "48.79 deg",
      "added.split.acc_power_speed", 48.79,
      "That pair's angle after the split, against 24.90 before."),
    C("add.split-worst", "4.7", "25.26 deg", "added.split.acc_worst", 25.26,
      "The suite's worst accumulated pair after the split. Power/speed stops "
      "binding and power/geometry takes over, so the suite's worst improves by "
      "only 0.35 degrees even though the old binding pair nearly doubles.",
      note="not in the paper as drafted; the paper should say it"),
    C("add.split-inst-cleared", "4.7", "seven of ten",
      "added.split.inst_cleared", 7,
      "Pairs the split clears per segment, from none of ten - the only change "
      "that resolves anything instantaneously."),
    C("add.swir-gain", "4.7", "+0.01 deg", "added.swir.gain_on_binding_pair",
      0.01, "What a short-wave infrared photodiode is worth on the same pair."),
    C("add.wide-gain", "4.7", "0.00 deg", "added.wide.gain_on_binding_pair",
      0.00, "What a wide-band pyrometer is worth."),
    C("add.corr-width", "4.7", "0.779", "added.corr_pd_width", 0.779,
      "Correlation of melt pool width with the coaxial photodiode: the least "
      "correlated of the candidates, which is why splitting the camera helps."),
    C("add.corr-length", "4.7", "0.979", "added.corr_pd_length", 0.979,
      "The same for length, which is both more responsive and less "
      "independent. An area averages the informative axis against the "
      "uninformative one and buries it."),

    # =====================================================================
    # Section 5.1  Relation to reported monitoring performance
    # =====================================================================
    C("lit.n-works", "5.1", "19 works", "discussion.n_works", 19,
      "Rows in the literature extraction table."),
    C("lit.year-lo", "5.1", "2019", "discussion.year_min", 2019,
      "Earliest publication year among them.", relation="range_lo"),
    C("lit.year-hi", "5.1", "2025", "discussion.year_max", 2025,
      "Latest.", relation="range_hi"),
    C("lit.n-outcome", "5.1", "seven", "discussion.n_outcome", 7,
      "Works that map signals onto a defect, a property or a surface state."),
    C("lit.n-inputs", "5.1", "three", "discussion.n_input_estimators", 3,
      "Works that estimate a process input from an in-situ signal."),
    C("lit.n-lumped", "5.1", "one of those a lumped energy-density class",
      "discussion.n_lumped", 1,
      "Of those three, how many predict the lumped group rather than its "
      "components."),
    C("rej.reported-b", "5.1", "b = 0.337", "sources.reijonen_b", 0.337,
      "The speed-response exponent reported for a commercial coaxial "
      "photodiode at 400 W.", kind="source",
      provenance="Reijonen (2024), Addit. Manuf. Lett. 11, 100244, Table 2"),
    C("rej.power", "5.1", "400 W", "sources.reijonen_power_W", 400,
      "The power at which it is quoted.", kind="source",
      provenance="Reijonen (2024)"),
    C("rej.speed-lo", "5.1", "400 mm/s", "sources.reijonen_speed_min_mm_s",
      400, "Lower end of the speed range it was fitted over.", kind="source",
      provenance="Reijonen (2024)", relation="range_lo"),
    C("rej.speed-hi", "5.1", "1200 mm/s", "sources.reijonen_speed_max_mm_s",
      1200, "Upper end.", kind="source", provenance="Reijonen (2024)",
      relation="range_hi"),
    C("rej.jacobian-entry", "5.1", "-0.483",
      "discussion.jacobian_speed_photodiode", -0.483,
      "This model's photodiode sensitivity to scan speed as a Jacobian entry - "
      "a derivative at a point, which is not the comparable quantity."),
    C("rej.fit-400", "5.1", "0.468", "discussion.fitted_b_at_400W", 0.468,
      "The comparable quantity: the same power law fitted to this model over "
      "their speed range at their power."),
    C("rej.excess", "5.1", "39 %", "discussion.b_excess_pct", 39.0,
      "By how much that is too steep.", tol=0.5),
    C("rej.fit-100", "5.1", "0.51", "discussion.fitted_b_at_100W", 0.51,
      "The same fit at 100 W, where they report the trend as almost "
      "non-existent."),
    C("rej.fit-285", "5.1", "0.44", "discussion.fitted_b_at_285W", 0.44,
      "At 285 W."),
    C("rej.flat", "5.1", "flat", "discussion.b_range", 0.0,
      "Total spread of the fitted exponent over 100-400 W. Theirs grows "
      "strongly with power; this model's does not, because a plume of fixed "
      "optical depth has no mechanism by which it could.",
      relation="<=", tol=0.15),
    C("rej.relative-power", "5.1", "+1.52",
      "discussion.jacobian_power_photodiode", 1.52,
      "This model's relative photodiode sensitivity to laser power. Reijonen "
      "report a linear fit without quoting its intercept, and relative "
      "sensitivity is aP/(aP+b), equal to one only through the origin, so this "
      "cannot be called a conflict until the intercept is known."),

    # =====================================================================
    # Section 5.2  Limitations
    # =====================================================================
    C("lim.honarmandi-lo", "5.2", "0.93", "sources.honarmandi_corr_min", 0.93,
      "Smallest pair correlation reported between fitted absorptivity, "
      "conductivity and heat capacity during Bayesian calibration of this "
      "model family - the pathology this paper studies, appearing in its own "
      "calibration.", kind="source",
      provenance="Honarmandi et al. (2021), Addit. Manuf. 47, 102300",
      relation="range_lo"),
    C("lim.honarmandi-hi", "5.2", "0.96", "sources.honarmandi_corr_max", 0.96,
      "Largest.", kind="source", provenance="Honarmandi et al. (2021)",
      relation="range_hi"),
    C("lim.gas-width", "5.2", "-10 %",
      "discussion.gas_width_change_pct_at_k0", -10.0,
      "The width change this model gives at a gas severity of 0.4. Reijonen "
      "et al. (2020) report reduced gas flow giving loss of penetration with "
      "*increased* width, so the sign is wrong - attenuation alone shrinks "
      "everything.", tol=0.5),
    C("lim.scatter-lo", "5.2", "2 deg", "discussion.scatter_power_gas_at_k075",
      2.0, "Power against gas once the gas fault is given a second channel - "
      "a spot size broadening with plume optical depth, which power does not "
      "possess - at the broadening that reverses the width sign. The paper "
      "quotes the pair as 2-3 degrees, to one figure.",
      relation="range_lo", tol=0.5),
    C("lim.scatter-hi", "5.2", "3 deg", "discussion.scatter_power_gas_at_k1",
      3.0, "The same at a stronger broadening. Still far below the floor: the "
      "exactness is a property of the model, the inseparability is not.",
      relation="range_hi", tol=0.5),
    C("lim.scatter-worst", "5.2", "0.32 deg", "discussion.scatter_worst_at_k075",
      0.32, "The suite's worst pair with that channel added - unmoved, on a "
      "different pair. No class changes and no count changes."),
    C("lim.geometry-inversion", "5.2", "+687 K",
      "discussion.geometry_inversion_K", 687,
      "Preheat implied by inverting the pads' depth excess over single tracks "
      "through the geometry channel. Not credible as a measurement: a pad "
      "differs from a single track by remelting adjacent tracks as well as by "
      "preheat, so this is an upper bound with a second mechanism folded in.",
      tol=1.0),
    # =====================================================================
    # Provenance: the document of measured inputs against the code
    # =====================================================================
    C("prov.agreement", "inputs", "0", "provenance.worst_relative_disagreement",
      0.0, "Largest relative disagreement between the measurements tabulated in "
      "docs/measured-inputs.md and the values the code actually holds. Zero "
      "means the document describing where every external number came from has "
      "not drifted from the numbers themselves. It does not mean either matches "
      "the article - that still needs a person and a copy of the paper.",
      tol=1e-9),
    C("prov.n-tracks", "inputs", "seven", "provenance.n_single_tracks", 7,
      "Single-track conditions cross-checked between the document and "
      "calibrate.py."),
    C("prov.n-pads", "inputs", "four", "provenance.n_pad_sections", 4,
      "Pad cross-sections cross-checked between the document and "
      "weaver_pads.py."),
    C("prov.n-uncertainties", "inputs", "seven",
      "provenance.n_uncertainties_checked", 7,
      "Expanded-uncertainty pairs cross-checked."),

    C("lim.preheat-response", "5.2", "+2.23 % depth per 100 K",
      "discussion.preheat_depth_pct_per_100K", 2.23,
      "What the model's preheat channel buys, which is why the geometry unit "
      "is probably understated.",
      note="not quoted in the paper; supports the sentence that the unit may "
           "be small"),
]


def by_group() -> dict[str, list[Claim]]:
    out: dict[str, list[Claim]] = {}
    for c in CLAIMS:
        out.setdefault(c.key.split(".")[0], []).append(c)
    return out
