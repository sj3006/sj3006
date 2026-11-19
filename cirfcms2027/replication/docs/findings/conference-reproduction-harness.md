# Reproducing the paper's numbers

Every number the paper prints is listed here, with what it means, how it is
computed, and a check that the computation still agrees with the text.

```
pip install -r ../requirements.txt
python3 check.py                 # uses the cache, a few seconds
python3 check.py --no-cache      # recomputes everything, about four minutes
```

`check.py` exits non-zero if any claim fails and writes `REPORT.md`, a table of
every claim with its paper value, its recomputed value and a plain-language
statement of what the number means.

## How it is organised

Three files, deliberately separated so that a claim and its recomputation
cannot quietly become the same number by being written in the same place:

| file | holds | holds no |
|---|---|---|
| `claims.py` | what the paper says, what it means, where it came from | computation |
| `compute.py` | the recomputation, grouped by paper section | knowledge of the paper |
| `check.py` | the comparison and the report | either |

`compute.py` imports the model from `../src`. It adds no physics of its own: a
number that this repository cannot compute is not in `compute.py`, it is a
`source` claim in `claims.py` with the article it came from.

## The tolerance rule

A claim passes if and only if the recomputed value **rounds to the number the
paper prints**. The tolerance is half a unit in the last printed decimal place,
read off the quoted text, so `24.90` must recompute to within 0.005 and `11.7`
to within 0.05.

That is strict on purpose. The defect this harness exists to catch is a number
that was computed once, written into prose, and then drifted when something
upstream changed - which happened repeatedly in this project's history, and in
every case the drift was in the second decimal place or beyond.

Where the paper states a bound or an approximation rather than a value
("roughly", "below", "at least"), the claim carries an explicit tolerance or an
inequality, and says which in its `relation` field.

## The three kinds of claim

**`computed`** - derived from the forward model by this repository. These are
the ones the harness actually verifies.

**`source`** - a measurement or a reported fit from a cited work. Not
recomputable here; what is checked is that the paper and the code carry the
same figure, so a transcription error cannot sit in one and not the other. Each
carries a `provenance` field naming the article and the table. *These still
need checking against the articles themselves* - the harness checks internal
consistency, not the literature.

**`convention`** - a threshold or unit this work chose: the 10-degree
separation floor, the 1e-6 rank tolerance, 100 K per unit of geometry fault.
Checked against the constant the code actually uses, so a convention cannot be
described one way in the paper and implemented another.

## What the harness does not do

It does not validate the physics. The forward model is a conduction solution
with an analytic keyhole correction, calibrated against seven benchmark
single-track measurements, and the paper's Section 5.2 says at some length where
it is wrong. The harness checks that the paper reports what the code computes,
which is a different and smaller claim than the code being right.

It also does not check prose. A sentence can be misleading with every number in
it correct - and two of the fixes that came out of building this harness were
exactly that, a figure quoted on one basis and read as though it were on
another.

## Where each group of numbers comes from

| group | paper section | module |
|---|---|---|
| `calibration` | 3.1 | `src/calibrate.py`, `src/conduction_baseline.py` |
| `couplings` | 3.2 | `src/layer_couplings.py` |
| `context` | 3.5 | `src/observables.py`, `src/weaver_pads.py` |
| `noise` | 3.6 | `src/noise.py` |
| `validation`, `ved` | 4.1 | `src/validation.py`, `src/sanity_checks.py` |
| `meltpool` | 4.2, 4.3, 4.4 | `src/diagnosability.py`, `src/observables.py` |
| `secants` | 4.4 | `src/locality_routeA.py` |
| `robustness`, `noise_sets`, `couplings_sweep` | 4.5 | `src/profile_robustness.py`, `src/route_b.py`, `src/coupling_sweep.py` |
| `configs` | 4.6 | `src/commercial.py`, `src/matrix.py` |
| `added` | 4.7 | `src/route_c_added_sensor.py`, `src/route_b.py` |
| `discussion` | 5.1, 5.2 | `src/reijonen_check.py`, `src/scattering_channel.py`, `src/literature_census.py` |
| `sources` | all | constants recorded alongside their citation |

## Adding a claim

Add an entry to `CLAIMS` in `claims.py` with the paper's exact printed text in
`quoted`, the value in `value`, a one-sentence `means`, and a `key` naming an
entry of one of the `compute.GROUPS` dicts. If the number is not yet computed
anywhere, add it to the relevant group in `compute.py` first - and if it is not
computable from the model, make it a `source` claim with its provenance rather
than quietly asserting it.
