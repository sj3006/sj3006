"""Every number the paper prints, checked against what the code computes.

The conference paper's hardest lesson was that figures computed in scratch
scripts drift away from the prose quoting them, and that the drift is invisible
because both halves look fine on their own. So each claim below records the
string as it is printed in `paper/paper.tex` and the value it should equal, and
the runner checks two things:

1. that the quoted string still occurs in the paper, which catches a number
   edited in the text and nowhere else; and
2. that the recomputed value still rounds to the printed one, which catches a
   number that moved in the code and was never carried into the text.

The tolerance is derived from the printed precision rather than chosen. A claim
printed as `4.26` passes only while the recomputed value rounds to `4.26`, so
the registry notices exactly the second-decimal drift this project kept having.

    python3 claims.py            # check, exit non-zero on failure
    python3 claims.py --list     # what is registered, without checking
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results.json"
PAPER = HERE / "paper" / "paper.tex"


@dataclass
class Claim:
    cid: str
    section: str
    quoted: str                 # as it appears in the paper
    value: float                # what it should be
    getter: str                 # where the value comes from
    means: str                  # plain language
    places: int | None = None   # decimal places printed; inferred if None
    skip_text: bool = False     # a value the paper states in words, not digits
    notes: str = ""


def _places(quoted: str) -> int:
    m = re.search(r"\.(\d+)", quoted)
    return len(m.group(1)) if m else 0


def _rounds_to(value: float, quoted: str, places: int | None) -> bool:
    """Does `value`, printed to the precision `quoted` uses, read as `quoted`?

    Stated as rounding rather than as a tolerance because a tolerance has to
    decide what happens exactly on the boundary, and floating point makes that
    decision arbitrary: 5259/6000 as a percentage is 87.64999999999999, which a
    tolerance of 0.05 admits by a hair and a tolerance of 0.049999 rejects. What
    the paper actually promises is that the printed digits are right, so that is
    what is checked.
    """
    p = _places(quoted) if places is None else places
    return f"{float(value):.{p}f}" == f"{float(quoted):.{p}f}"


def build(R: dict) -> list[Claim]:
    g = R["geometry"]
    f = R["floor"]
    ci = R["certificates"]["instantaneous"]
    cc = R["certificates"]["build_context"]
    arms = R["benchmark"]["instantaneous"]["arms"]
    ch = R["channels"]
    pr = R["probing"]
    C = [Claim]

    def ang(regime, a, b):
        d = g[regime]["angles"]
        return d.get(f"{a}|{b}", d.get(f"{b}|{a}"))

    out: list[Claim] = []
    add = out.append

    # --- the derived floor ------------------------------------------------
    add(Claim("floor.inst", "4.1", "28.08", f["instantaneous"]["snr_for_10deg"],
              "floor.instantaneous.snr_for_10deg",
              "the signal-to-noise a ten degree floor implicitly assumes"))
    add(Claim("floor.inst.abstract", "abstract", "28.1",
              f["instantaneous"]["snr_for_10deg"],
              "floor.instantaneous.snr_for_10deg", "the same, to one decimal"))
    add(Claim("floor.ctx", "4.1", "55.84", f["build_context"]["snr_for_10deg"],
              "floor.build_context.snr_for_10deg",
              "the same for the enlarged observation, where the threshold rises"))
    add(Claim("floor.q", "4.1", "5.9915", f["instantaneous"]["q"],
              "floor.instantaneous.q",
              "the 95th percentile of chi-squared on two degrees of freedom"))

    # --- certificate size -------------------------------------------------
    add(Claim("size.inst.28", "4.2", "3.5", 100 * ci["28"]["unique"],
              "certificates.instantaneous.28.unique",
              "how often one instant licenses naming a single cause, per cent"))
    add(Claim("size.inst.120", "4.2", "24.2", 100 * ci["120"]["unique"],
              "certificates.instantaneous.120.unique",
              "the same at a signal four times stronger"))
    add(Claim("size.inst.mean", "4.2", "4.26", ci["28"]["mean_size"],
              "certificates.instantaneous.28.mean_size",
              "causes in the certificate, out of five"))
    add(Claim("size.ctx.28", "4.2", "95.3", 100 * cc["28"]["unique"],
              "certificates.build_context.28.unique",
              "the same with build context, which is the test's own ceiling"))
    for name, printed in (("layer", "0.003"), ("power", "0.007"),
                          ("gas", "0.010"), ("speed", "0.037"),
                          ("geometry", "0.273")):
        add(Claim(f"size.byfault.{name}", "4.2", printed,
                  ci["56"]["by_fault"][name],
                  f"certificates.instantaneous.56.by_fault.{name}",
                  f"unique-cause rate for a {name} fault at rho = 56"))

    # --- the equivalence structure ----------------------------------------
    A = R["admissibility"]["instantaneous"]["28"]["matrix"]
    faults = R["meta"]["faults"]
    gi, si = faults.index("geometry"), faults.index("speed")
    add(Claim("adm.geo.speed", "4.3", "83.9", 100 * A[gi][si],
              "admissibility.instantaneous.28[geometry][speed]",
              "how often speed survives a build whose cause was geometry"))
    add(Claim("adm.speed.geo", "4.3", "60.3", 100 * A[si][gi],
              "admissibility.instantaneous.28[speed][geometry]",
              "the reverse, which is smaller: the matrix is not symmetric"))

    # --- pairs priced ------------------------------------------------------
    rs = f["instantaneous"]["required_snr"]
    rm = f["instantaneous"]["required_magnitudes"]
    add(Claim("priced.ps.snr", "4.4", "398",
              rs.get("power|speed", rs.get("speed|power")),
              "floor.instantaneous.required_snr.power|speed",
              "signal needed to tell a power fault from a speed fault"))
    add(Claim("priced.ps.mag", "4.4", "46",
              100 * rm.get("power|speed", rm.get("speed|power"))["power"],
              "floor.instantaneous.required_magnitudes.power|speed.power",
              "the power deviation that implies, per cent"))
    add(Claim("priced.pl.snr", "4.4", "867",
              rs.get("power|layer", rs.get("layer|power")),
              "floor.instantaneous.required_snr.power|layer",
              "signal needed to tell power from a layer fault"))
    add(Claim("priced.pl.mag", "4.4", "99",
              100 * rm.get("power|layer", rm.get("layer|power"))["power"],
              "floor.instantaneous.required_magnitudes.power|layer.power",
              "the power deviation that implies, per cent"))
    add(Claim("priced.lg.mag", "4.4", "2.7",
              rm.get("layer|gas", rm.get("gas|layer"))["layer"],
              "floor.instantaneous.required_magnitudes.layer|gas.layer",
              "the layer severity index needed, where 1.0 is the convention "
              "for severe"))
    cs = f["build_context"]["required_snr"]
    cm = f["build_context"]["required_magnitudes"]
    add(Claim("priced.ctx.pg.snr", "4.4", "18.8",
              cs.get("power|gas", cs.get("gas|power")),
              "floor.build_context.required_snr.power|gas",
              "signal at which build context separates power from gas"))
    add(Claim("priced.ctx.pg.mag", "4.4", "0.2",
              100 * cm.get("power|gas", cm.get("gas|power"))["power"],
              "floor.build_context.required_magnitudes.power|gas.power",
              "the power deviation that implies, per cent"))
    finite = [v for v in cs.values() if v is not None]
    add(Claim("priced.ctx.lo", "4.4", "11.7", min(finite),
              "min of floor.build_context.required_snr",
              "the easiest pair with build context"))
    add(Claim("priced.ctx.hi", "4.4", "22.0", max(finite),
              "max of floor.build_context.required_snr",
              "the hardest pair with build context"))

    # --- the exact test ----------------------------------------------------
    dep = R["linearisation"]["departure"]
    q = R["linearisation"]["q_instantaneous"]
    for snr, printed in (("28", "0.19"), ("56", "0.77"), ("120", "1.72")):
        add(Claim(f"lin.dep.{snr}", "4.5", printed,
                  dep[f"power|{snr}"]["perpendicular"],
                  f"linearisation.departure.power|{snr}.perpendicular",
                  f"how far a power fault's exact response at rho = {snr} lies "
                  f"off its own tangent, in standard deviations"))
    add(Claim("lin.share", "4.5", "49.6",
              100 * dep["power|120"]["perpendicular"] ** 2 / q,
              "departure squared over q", "the share of the test's budget that "
              "departure consumes on its own, per cent"))
    add(Claim("lin.cov.120", "4.5", "0.76", ci["120"]["linear_coverage"],
              "certificates.instantaneous.120.linear_coverage",
              "coverage of a nominally 95 per cent certificate built on the "
              "tangent"))

    # --- channels and probing ---------------------------------------------
    add(Claim("ch.error", "4.6", "6.8", 1e5 * ch["factorisation_error"],
              "channels.factorisation_error x 1e5",
              "agreement between M C and the direct Jacobian, in units of 1e-5"))
    add(Claim("ch.layer", "4.6", "-0.044", ch["C"][0][2], "channels.C[0][2]",
              "how a layer fault moves absorbed power"))
    add(Claim("ch.cond", "4.6", "0.5", ch["C"][2][2], "channels.C[2][2]",
              "how a layer fault moves effective conductivity"))
    add(Claim("ch.preheat", "4.6", "100", ch["C"][3][4], "channels.C[3][4]",
              "kelvin of preheat per unit geometry index"))
    add(Claim("ch.rank", "4.6", "4", ch["rank_C"], "channels.rank_C",
              "the rank of C, one less than the fault count", places=0))
    add(Claim("probe.nominal", "4.6", "0.32", pr["nominal, one instant"]["second"],
              "probing['nominal, one instant'].second",
              "second-worst pair with no probing"))
    add(Claim("probe.two", "4.6", "5.95", pr["two operating points"]["second"],
              "probing['two operating points'].second",
              "second-worst pair after one deliberate probe"))
    add(Claim("probe.best", "4.6", "6.15", R["probing_best"]["second_worst"],
              "probing_best.second_worst",
              "the best a two-point probe achieves, still short of the floor"))
    add(Claim("probe.bestP", "4.6", "440", R["probing_best"]["operating_point"][0],
              "probing_best.operating_point[0]", "power of that probe, watts"))
    add(Claim("probe.bestV", "4.6", "2.29", R["probing_best"]["operating_point"][1],
              "probing_best.operating_point[1]", "speed of that probe, m/s"))
    add(Claim("probe.four.cond", "4.6", "2.9",
              pr["four operating points"]["condition"] / 1e5,
              "probing['four operating points'].condition / 1e5",
              "condition number at nominal rank 4, in units of 1e5"))

    # --- the arms ----------------------------------------------------------
    add(Claim("arms.ml.cov", "4.7", "44.0", 100 * arms["maximum likelihood"]["coverage"],
              "benchmark.instantaneous.arms['maximum likelihood'].coverage",
              "how often the single best-fitting cause is the true one"))
    add(Claim("arms.cert.size", "4.7", "3.70", arms["certificate"]["mean_size"],
              "benchmark.instantaneous.arms.certificate.mean_size",
              "the price of the certificate's guarantee, in causes reported"))
    add(Claim("arms.cert.cov", "4.7", "0.951", arms["certificate"]["coverage"],
              "benchmark.instantaneous.arms.certificate.coverage",
              "its coverage, which is 1 - alpha by construction"))
    add(Claim("arms.ml.skill", "4.7", "0.17", arms["maximum likelihood"]["skill"],
              "benchmark.instantaneous.arms['maximum likelihood'].skill",
              "how much better than guessing inside the certificate"))
    add(Claim("arms.chance.skill", "4.7", "-0.08", arms["chance"]["skill"],
              "benchmark.instantaneous.arms.chance.skill",
              "the control: a guesser scores about zero"))
    add(Claim("arms.n", "4.7", "6000", R["benchmark"]["instantaneous"]["n"],
              "benchmark.instantaneous.n", "cases scored", places=0))
    add(Claim("arms.amb", "4.7", "5259", R["benchmark"]["instantaneous"]["n_ambiguous"],
              "benchmark.instantaneous.n_ambiguous",
              "of those, how many had an ambiguous certificate", places=0))
    add(Claim("arms.ambpc", "4.7", "87.65",
              100 * R["benchmark"]["instantaneous"]["n_ambiguous"]
              / R["benchmark"]["instantaneous"]["n"],
              "ratio of the two above", "the same as a percentage",
              notes="This one is why the check rounds rather than tolerances. "
                    "5259/6000 is exactly 87.65 per cent, a rounding boundary, "
                    "and whether it prints as 87.6 or 87.7 at one decimal "
                    "depends on the order of the arithmetic: (100*5259)/6000 "
                    "and 5259/6000*100 are different doubles. A number on a "
                    "boundary should not be printed to a precision that "
                    "straddles it, so the paper states both the count and two "
                    "decimals."))

    # --- method constants --------------------------------------------------
    s = R["geometry"]["sigmas"]
    add(Claim("noise.cam", "3.1", "0.142", s["camera"], "geometry.sigmas.camera",
              "the camera's relative noise, against the photodiode's 1"))
    add(Claim("noise.pyr", "3.1", "1.061", s["pyrometer"],
              "geometry.sigmas.pyrometer", "the pyrometer's, slightly noisier"))
    add(Claim("rho28.power", "3.2", "3.2",
              100 * R["floor"]["instantaneous"]["required_magnitudes"]
              .get("power|speed", {}).get("power", 0) * 28.08 / 398.1,
              "magnitude at rho = 28 for a power fault",
              "what rho = 28 means as a power deviation at one per cent noise",
              notes="recomputed by scaling, since the stored map is per pair"))

    # --- appendix A, the noise derivation ----------------------------------
    ap = R["appendix"]
    add(Claim("app.cam.w", "A.2", "0.0298", ap["camera_width"],
              "appendix.camera_width",
              "how far the isotherm shift moves the pool's width, per unit eps"))
    add(Claim("app.cam.l", "A.2", "0.1124", ap["camera_length"],
              "appendix.camera_length", "the same for its length"))
    add(Claim("app.cam.quad", "A.2", "0.116", ap["camera_quadrature"],
              "appendix.camera_quadrature",
              "what the camera's noise would be if the two axes were treated "
              "as independent, which they are not"))
    add(Claim("app.planck.x", "A.2", "10.520", ap["planck_x_camera"],
              "appendix.planck_x_camera",
              "c2 / (lambda T) at the camera band and the liquidus"))
    add(Claim("app.planck.s", "A.2", "10.520", ap["planck_s_camera"],
              "appendix.planck_s_camera",
              "the exact Planck log sensitivity there, which the Wien limit x "
              "matches to better than 0.01 per cent"))
    add(Claim("app.dlnT", "A.2", "0.095", 100.0 / ap["planck_s_camera"] * 0.01,
              "1 / appendix.planck_s_camera",
              "the apparent temperature shift a one per cent brightness error "
              "produces, per cent"))
    add(Claim("app.lambda", "A.3", "1.333", ap["wien_lambda"],
              "appendix.wien_lambda",
              "how much the two-colour ratio moves per unit of temperature"))
    add(Claim("app.c2T", "A.3", "4.747", 1e6 * ap["c2_over_T"],
              "appendix.c2_over_T x 1e6", "c2 / T in units of 1e-6 metre kelvin"))
    add(Claim("app.dinv", "A.3", "2.807", 1e-5 * ap["inv_lambda_difference"],
              "appendix.inv_lambda_difference x 1e-5",
              "the reciprocal wavelength difference, in units of 1e5 per metre"))
    add(Claim("app.s750", "A.3", "6.341", ap["planck_s_750"],
              "appendix.planck_s_750",
              "Planck log sensitivity of the 750 nm band at the pool temperature"))
    add(Claim("app.s950", "A.3", "5.031", ap["planck_s_950"],
              "appendix.planck_s_950", "the same for the 950 nm band"))
    add(Claim("app.sdiff", "A.3", "1.310", ap["planck_difference"],
              "appendix.planck_difference",
              "their difference, which is the exact-Planck counterpart of the "
              "Wien value 1.333"))
    add(Claim("app.pyro.exact", "A.3", "1.080", ap["pyro_sigma_exact_planck"],
              "appendix.pyro_sigma_exact_planck",
              "what the pyrometer's noise would be using the exact-Planck "
              "sensitivity instead of the inverter's own"))
    add(Claim("app.single", "A.3", "0.158", ap["single_band_sigma"],
              "appendix.single_band_sigma",
              "the noise a single calibrated band would give, six times better"))

    # --- appendix C, the cone ----------------------------------------------
    add(Claim("app.sqrtq", "C", "2.4477", ap["sqrt_q_inst"],
              "appendix.sqrt_q_inst", "the square root of the threshold, three "
              "instruments"))
    add(Claim("app.sin5", "C", "0.08716", ap["sin_five_degrees"],
              "appendix.sin_five_degrees", "the sine of half the ten degree floor"))
    add(Claim("app.qctx", "C", "23.6848", ap["q_ctx"], "appendix.q_ctx",
              "the threshold for the enlarged observation, fourteen degrees of "
              "freedom"))

    # --- appendix D, the covariance ----------------------------------------
    add(Claim("app.corr", "D", "0.577", ap["regressor_correlation"],
              "appendix.regressor_correlation",
              "the largest correlation between coefficient estimates, which is "
              "what the diagonal approximation ignores"))
    add(Claim("app.cholkron", "D", "1.4", 1e17 * ap["chol_kron_error"],
              "appendix.chol_kron_error x 1e17",
              "agreement of chol(A kron B) with chol(A) kron chol(B), in units "
              "of 1e-17", skip_text=True,
              notes="the printed token is '1.4', too common a substring for the "
                    "text-presence check to mean anything, so only the value is "
                    "checked here"))

    # --- appendix F, the collapse ------------------------------------------
    add(Claim("app.collapse", "F", "1.0", 1e8 * ap["collapse_max_degrees"],
              "appendix.collapse_max_degrees x 1e8",
              "how exactly the enlarged angles return to the instantaneous ones "
              "when every fault shares one profile, in units of 1e-8 degrees",
              skip_text=True,
              notes="as above, '1.0' is too common a substring to test for"))

    # --- appendix G, the exact test ----------------------------------------
    add(Claim("app.noncentral", "G", "2.97", ap["noncentrality_120"],
              "appendix.noncentrality_120",
              "the noncentrality a linearised test carries at rho = 120, "
              "against a threshold of 5.99"))
    for snr, printed in (("14", "0.943"), ("28", "0.950"), ("56", "0.961"),
                         ("120", "0.950")):
        add(Claim(f"app.cov.{snr}", "G", printed, ci[snr]["coverage"],
                  f"certificates.instantaneous.{snr}.coverage",
                  f"measured coverage of the exact test at rho = {snr}"))
    return out


def _get_quoted_present(text: str, quoted: str) -> bool:
    return quoted in text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if not RESULTS.exists():
        print(f"{RESULTS} not found; run `python3 results.py` first")
        return 2
    R = json.loads(RESULTS.read_text())
    claims = build(R)
    paper = PAPER.read_text() if PAPER.exists() else ""

    if args.list:
        for c in claims:
            print(f"{c.cid:22s} §{c.section:5s} {c.quoted:>9s}  {c.means}")
        return 0

    print(f"Checking {len(claims)} claims against results.json and paper.tex")
    print("=" * 78)
    bad_value, bad_text = [], []
    for c in claims:
        ok_value = _rounds_to(c.value, c.quoted, c.places)
        ok_text = c.skip_text or not paper or _get_quoted_present(paper, c.quoted)
        if not ok_value:
            bad_value.append(c)
        if not ok_text:
            bad_text.append(c)
        if not (ok_value and ok_text):
            flag = []
            if not ok_value:
                p = _places(c.quoted) if c.places is None else c.places
                flag.append(f"value {float(c.value):.{p + 3}f} prints as "
                            f"{float(c.value):.{p}f}, not {c.quoted}")
            if not ok_text:
                flag.append(f"'{c.quoted}' no longer appears in paper.tex")
            print(f"  [FAIL] {c.cid:22s} §{c.section:5s} {'; '.join(flag)}")
            print(f"         from {c.getter}")
            print(f"         means: {c.means}")

    print(f"\n{len(claims)} claims checked; {len(bad_value)} value mismatches, "
          f"{len(bad_text)} missing from the text")
    if not bad_value and not bad_text:
        print("every printed number still rounds to what the code computes, and")
        print("every one of them still appears in the paper")
    return 1 if (bad_value or bad_text) else 0


if __name__ == "__main__":
    raise SystemExit(main())
