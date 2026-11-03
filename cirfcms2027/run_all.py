#!/usr/bin/env python3
"""Run everything, in the order the paper's argument is built.

    python3 run_all.py              # the whole thing, roughly fifteen minutes
    python3 run_all.py --check      # just the claim check against the paper
    python3 run_all.py --list       # what each stage does, without running it
    python3 run_all.py --only noise --only confound

Each stage is one module in `src/` that prints a self-contained report, plus the
claim check in `repro/`. Output goes to the terminal and, with --save, to
`output/<stage>.txt` so a run can be diffed against an earlier one.

Nothing here is required to reproduce the paper: every stage can be run on its
own as `python3 src/<module>.py`. This exists so that a reader who wants to see
the whole argument once, in order, can.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# (stage name, module or command, paper section, one-line description)
STAGES: list[tuple[str, str, str, str]] = [
    ("calibrate", "src/calibrate.py", "3.1",
     "Fit four effective parameters to the seven AM-Bench single tracks and "
     "report the error."),
    ("conduction", "src/conduction_baseline.py", "3.1",
     "Why the keyhole correction is necessary: the regime, and a conduction-only "
     "fit at the same freedom."),
    ("sanity", "src/sanity_checks.py", "4.1",
     "Does the model behave? Directional sweeps, the peak-temperature artefact, "
     "and the energy-density structure across five grids."),
    ("validation", "src/validation.py", "4.1",
     "The Guo constant-energy-density check, and which dimension carries the "
     "information."),
    ("couplings", "src/layer_couplings.py", "3.2",
     "Where the layer fault's two derived coupling constants come from, and what "
     "each channel does to the pool."),
    ("noise", "src/noise.py", "3.6",
     "Each sensor's relative noise, derived from its transduction chain rather "
     "than assumed."),
    ("pads", "src/weaver_pads.py", "3.5",
     "The one modulation profile that can be calibrated from published data - "
     "and the one that cannot."),
    ("structural", "src/structural.py", "3.4",
     "Tier 1: structural detectability and isolability from equation form alone, "
     "via MSO sets."),
    ("diagnosability", "src/diagnosability.py", "4.2",
     "The relative-sensitivity Jacobian, its whitening, and the pairwise angles "
     "per segment."),
    ("couplingsweep", "src/coupling_sweep.py", "4.2",
     "Every coupling constant swept across its plausible range, including the "
     "exact power/gas identity."),
    ("locality", "src/locality_routeA.py", "4.4",
     "The enlarged observation over a build, and the finite-magnitude secant "
     "check against the derivative limit."),
    ("profiles", "src/profile_robustness.py", "4.5",
     "How wrong the modulation profiles may be: strength, assignment, collapse, "
     "wrong driver, segment count."),
    ("profilesweep", "src/profile_sweep.py", "4.5",
     "Profile shape and contrast swept together, with the shared-profile "
     "control."),
    ("subsets", "src/route_b.py", "4.7",
     "Every sensor subset at four noise assumptions, and what each candidate "
     "observable is worth."),
    ("addedsensor", "src/route_c_added_sensor.py", "4.7",
     "What an idealised direct measurement of a cause would buy, and how good "
     "it would have to be."),
    ("matrix", "src/matrix.py", "4.6",
     "The diagnosability matrix for the baseline suite in both regimes, with "
     "class assignments."),
    ("commercial", "src/commercial.py", "4.6",
     "The same for the configuration classes found on current commercial "
     "machines."),
    ("enlarged", "src/structural_enlarged.py", "4.6",
     "Tier 1 again, on the enlarged observation, as an independent check on the "
     "quantitative result."),
    ("reijonen", "src/reijonen_check.py", "5.1",
     "The one external check on this model's sensor response, which it partly "
     "fails."),
    ("scattering", "src/scattering_channel.py", "5.2",
     "How exact the power/gas confound really is, once the gas fault is given a "
     "second channel."),
    ("literature", "src/literature_census.py", "5.1",
     "The counts behind the claim that the field classifies outcomes rather "
     "than causes."),
    ("provenance", "src/provenance_check.py", "inputs",
     "Does the document of measured inputs still match the data in the code?"),
    ("check", "repro/check.py --no-cache", "all",
     "Every number the paper prints, checked against a fresh recomputation. "
     "Exits non-zero on any disagreement."),
]


def run_stage(name: str, cmd: str, save: Path | None) -> tuple[int, float]:
    parts = cmd.split()
    t = time.time()
    proc = subprocess.run([sys.executable, *[str(ROOT / parts[0])], *parts[1:]],
                          cwd=str(SRC if parts[0].startswith("src/") else ROOT),
                          capture_output=True, text=True)
    took = time.time() - t
    body = proc.stdout + (("\n--- stderr ---\n" + proc.stderr)
                          if proc.stderr.strip() else "")
    print(body, end="" if body.endswith("\n") else "\n")
    if save is not None:
        save.parent.mkdir(parents=True, exist_ok=True)
        save.write_text(body)
    return proc.returncode, took


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=None,
                    help="run just these stages, by name; repeatable")
    ap.add_argument("--check", action="store_true",
                    help="shorthand for --only check")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--save", action="store_true",
                    help="also write each stage's output to output/<stage>.txt")
    a = ap.parse_args()

    if a.list:
        print(f"{'stage':16s}{'section':9s}what it does")
        for name, cmd, sec, desc in STAGES:
            print(f"{name:16s}{sec:9s}{desc}")
            print(f"{'':25s}{cmd}")
        return 0

    wanted = ["check"] if a.check else a.only
    stages = [s for s in STAGES if wanted is None or s[0] in wanted]
    if wanted:
        unknown = set(wanted) - {s[0] for s in STAGES}
        if unknown:
            print(f"unknown stage(s): {sorted(unknown)}", file=sys.stderr)
            return 2

    failures, timings = [], []
    for name, cmd, sec, desc in stages:
        print("\n" + "=" * 74)
        print(f"{name.upper()}   (paper Section {sec})")
        print(desc)
        print("=" * 74)
        code, took = run_stage(name, cmd,
                               ROOT / "output" / f"{name}.txt" if a.save else None)
        timings.append((name, took, code))
        if code != 0:
            failures.append(name)

    print("\n" + "=" * 74)
    print(f"{'stage':16s}{'seconds':>9s}  exit")
    for name, took, code in timings:
        print(f"{name:16s}{took:>9.1f}  {code}")
    total = sum(t for _, t, _ in timings)
    print(f"{'total':16s}{total:>9.1f}")
    if failures:
        print(f"\n{len(failures)} stage(s) exited non-zero: "
              f"{', '.join(failures)}")
        return 1
    print("\nall stages exited cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
