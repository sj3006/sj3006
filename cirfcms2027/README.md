# Which process faults can be told apart?

### Diagnosability limits of in-situ monitoring in laser powder bed fusion

In-situ monitoring is standard on metal additive manufacturing machines, and a
large literature maps photodiode and camera signals onto defects with high
reported accuracy. Those results answer a question about **outcomes**: which
defect formed. Specifying hardware requires an answer one step upstream - which
process **causes** a sensor configuration can separate in principle, and which
remain confounded whatever classifier is applied.

Where two causes produce signatures differing by less than the sensor noise, no
volume of training data distinguishes them. The limit is structural, not
algorithmic. This repository works out, from physics, where those limits fall
for a coaxial melt pool monitoring suite in LPBF.

**The three findings, in one paragraph each:**

*Laser power and shielding gas degradation are exactly confounded.* Both act
only on the product (effective absorptivity x laser power), in which the
Eagar-Tsai temperature rise is linear, so a power fault of size *f* and a gas
fault of size ln(1+*f*) produce a bit-identical melt pool. No instrument that
could be built separates them from a single instant, and the structural analysis
finds the same pair from equation form alone.

*The binding limit is the melt pool, not the instrumentation.* Everything the
model knows funnels into four physical channels, with three of the five faults
crowding onto the first. Seven candidate observables - a photodiode, a camera's
width and length separately, a two-colour pyrometer, a wide-band pyrometer, a
short-wave infrared photodiode, pool area - attain rank 3 against that bound of
4. A new wavelength reweights the same Planck curve over the same pool: a row,
not a direction.

*Build structure already present dissolves the limit at no hardware cost.* A
build is thousands of segments whose toolpath, layer index, gas-flow direction
and local geometry the machine already knows, and the five faults do not vary
identically across them. Regressing each sensor's residual onto that known
context raises the rank from 3 to 5 and the worst fault pair from 0.00 to 24.90
degrees - outperforming two idealised, perfect direct measurements of the causes
themselves.

---

## Running it

```
pip install -r requirements.txt

python3 run_all.py --list       # what each stage does
python3 run_all.py              # the whole argument in order, ~15 minutes
python3 run_all.py --check      # just: does the paper match the code?
```

Python 3.11, numpy and scipy. No GPU, no licensed solver, no external dataset:
the forward model generates the sensor signals, and published measurements enter
only as calibration targets and corroboration.

Every stage is also a standalone script. `python3 src/noise.py` prints the noise
derivation and nothing else.

## Is the paper right?

```
python3 repro/check.py --no-cache
```

234 claims - one for every number the paper prints - each checked against a
fresh recomputation, each with a plain-language statement of what the number
means. A claim passes only if the recomputed value **rounds to the printed one**.
It exits non-zero on any disagreement and writes
[`repro/REPORT.md`](repro/REPORT.md), which is the table to read if you want to
know where a particular figure in the paper comes from.

This is not a formality. Running it the first time found nine numbers in the
paper that no longer reproduced, one of them badly wrong, and two sentences that
were accurate but read as something stronger than they were. See
[`repro/README.md`](repro/README.md) for how the harness is built and what it
deliberately does not check.

## Where everything is

| | |
|---|---|
| [`paper/paper.tex`](paper/paper.tex) | the paper, self-contained, no external bibliography |
| [`overleaf/`](overleaf/) | the same paper in a two-column layout, as an Overleaf bundle |
| [`repro/`](repro/) | every quoted number, what it means, and a check that it still holds |
| [`src/`](src/) | the forward model, the sensors, the faults, and the analysis |
| [`docs/measured-inputs.md`](docs/measured-inputs.md) | **every number taken from someone else's article, with its source** |
| [`explainers/`](explainers/) | the method from first principles, one document per idea |
| [`07-literature-extraction.md`](07-literature-extraction.md) | the survey behind the claim that the field classifies outcomes, not causes |
| [`figures/`](figures/) | generated figures |

### The model, in `src/`

| module | what it is |
|---|---|
| `eagar_tsai.py` | Eagar-Tsai moving Gaussian source on a semi-infinite solid, with the Gladush-Smurov keyhole depth correction |
| `calibrate.py` | the four-parameter fit to seven AM-Bench single tracks |
| `conduction_baseline.py` | why the keyhole term is necessary rather than cosmetic |
| `faults.py` | the five fault modes, each defined as a physical quantity acting on a model input |
| `layer_couplings.py` | where the layer fault's coupling constants come from |
| `sensors.py` | photodiode, camera and two-colour pyrometer models from the temperature field |
| `noise.py` | each sensor's relative noise, derived from its transduction chain |
| `diagnosability.py` | the relative-sensitivity Jacobian, whitening, angles, rank |
| `observables.py` | the build plan, the known context regressors, the enlarged observation |
| `weaver_pads.py` | the one modulation profile calibrated from published data, and the one that fails |
| `structural.py`, `structural_enlarged.py` | the structural analysis, over MSO sets |
| `matrix.py`, `commercial.py` | the diagnosability matrices, per configuration class |
| `route_b.py`, `route_c_added_sensor.py` | what more sensors, or better ones, would buy |
| `profile_robustness.py`, `coupling_sweep.py`, `profile_sweep.py` | how wrong the assumptions may be |
| `reijonen_check.py`, `scattering_channel.py` | the external checks, including the one the model partly fails |
| `validation.py`, `sanity_checks.py` | does the model behave, and does it reproduce known structure |
| `literature_census.py`, `provenance_check.py` | the counts and the sources, checked rather than asserted |

## What this work does not claim

The forward model is a constant-property conduction solution with an analytic
keyhole patch, fitted to seven measurements. Its parameters sit at their bounds,
it partly fails the one external check on its sensor response, and the paper's
limitations section says so at length. Three modelling choices make the
instantaneous case **more** confounded than reality, so the reported
0.00 degrees is an upper bound.

The modulation profiles that carry the accumulated-regime result are physical
claims, not measurements. One of the five is calibrated against benchmark data
and comes back 20 % stronger than assumed; the other four are asserted, and
`src/profile_robustness.py` is the whole of the defence - the result survives
the profiles being half as strong, assigned to the wrong faults in any of 120
ways, and following the wrong build variable up to 84 %.

Every result is a **diagnosability** statement: what a suite can distinguish in
principle, at a given relative noise, under a given forward model. Not that any
algorithm achieves it.

## Project notes

The remaining numbered markdown files are working documents - vision, timeline,
risk and decision log, the draft history, and an errata record of every number
that had to be corrected and why. They are kept because the corrections are part
of the work, not because they are meant to be read first.
