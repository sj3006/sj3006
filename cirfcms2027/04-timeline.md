# Twelve-week plan

Weeks are nominal. The gates matter more than the dates — each one is placed so a
failure is discovered early enough to recover.

## Week 1 — Freeze scope

- Pick one alloy (316L or IN718). Do not revisit this decision.
- Fix the fault list and the sensor list.
- Run the outstanding novelty check (see `05-risks-and-decisions.md`).
- Collect published melt pool dimension data for the validation target.
- Collect published sensor noise figures. **Do this now, not in week 6** — if they
  do not exist, the analysis goes parametric and you need to know early.

## Weeks 2–3 — Thermal model

Build Eagar–Tsai in Python. Verify melt pool width and depth against published
measurements at three or four parameter sets.

> **Gate 1.** Within roughly 15% on width and depth. If not, fix it now rather
> than building on sand. Fallback: simpler analytical form, wider stated error
> bars.

## Week 4 — Fault injection

Implement the five fault modes as perturbations. Check each produces a physically
sensible change in the temperature field.

## Week 5 — Sensor models

Photodiode radiometry first — it is the one every machine has. Camera area and
pyrometer ratio follow quickly once the field is in hand.

## Week 6 — Noise and sanity check

Whitening covariance from the specs gathered in week 1. Check simulated photodiode
magnitudes and trends against published traces.

> **Gate 2.** Right order of magnitude, right direction of trend. If the
> radiometry is fighting you, fall back to melt pool area as a photodiode proxy
> and say so in the paper — the literature already treats photodiode signal as
> correlating with melt pool area.

## Week 7 — First matrix

Sensitivity Jacobian, whitening, pairwise angles, SVD rank.

> **Gate 3. This is the minimum publishable result.** Everything after this
> enriches it. If you reach here on time, the paper exists.

## Week 8 — Richer observables

Enlarge the observation vector with temporal and spatial statistics. Recompute.
Identify which confusions dissolve without new hardware.

## Week 9 — Sensor configurations and literature comparison

Subset sweep over sensor configurations. In parallel, extract defect class sets
and reported confusions from 15–20 monitoring papers.

## Week 10 — Robustness and figures

Latin hypercube sampling over uncertain properties and noise. Build the figure
set: angle heatmap, detectability thresholds, subset comparison.

## Weeks 11–12 — Write

---

## If you fall behind

Cut in this order:

1. Active excitation (route C) — drop first, it was always optional
2. Robustness sweep
3. Two-colour pyrometer
4. Literature comparison
5. Sensor subset sweep

**Never cut weeks 2–7.** That chain is the paper. A submission with one alloy,
two sensors, five faults and one matrix is complete and defensible.

## Figure set to aim for

| Figure | Content |
|---|---|
| 1 | Method schematic: physics model to sensor models to Jacobian to matrix |
| 2 | Model verification against published melt pool dimensions |
| 3 | Fault signature directions in whitened sensor space |
| 4 | Diagnosability matrix (angle heatmap), main result |
| 5 | Three-way classification per sensor configuration |
| 6 | LDA confusion matrix on simulated data versus predicted angles |

Six figures is about right for a Procedia CIRP paper. If space is tight, merge 2
into a table and drop 3.
