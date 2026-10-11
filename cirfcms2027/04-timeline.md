# Three-week sprint plan

**Revised from a twelve-week part-time plan.** Nothing has been removed from the
methodology. The calendar compressed; the work did not.

## The arithmetic, read this first

Twelve weeks at 12-15 h/week was roughly 150-180 hours. Three weeks to the same
total means **9-10 hours a day, six days a week**. If that is not available, the
plan does not close, and knowing that today is worth more than discovering it in
week two.

Two things make three weeks feasible rather than merely harder:

**Parallel tracks.** Tier 1 (structural analysis) needs only the model's
*structure* — which equations involve which variables and faults. It does not need
the thermal model to run. Build it alongside, not behind. Same for the AM-Bench
calibration extraction and the literature table: neither needs code.

**Named buffer.** Three items are not promised in the accepted abstract and are
therefore where depth gets reduced if you fall behind: active excitation (route
C), the Latin hypercube robustness sweep, and the LDA confirmation step. Decide
that under pressure from this list, not from the methodology.

## What the abstract actually commits you to

Irreducible — all of this ships:

- reduced-order process model
- five fault modes (power, speed, thin layer, gas flow, geometric heat accumulation)
- sensor suite response models
- noise levels from published sensor characterisations
- **structural** diagnosability (Tier 1) and **quantitative** diagnosability (Tier 2)
- three-way matrix: resolvable by structure / needs a sensor / structurally irreducible
- matrices for configurations on current commercial machines
- comparison against defect classes and accuracies in the monitoring literature

## Week 1 — build the whole forward chain

Everything exists and runs by Saturday. Gate 3 moves from week 7 to day 6.

**Day 1 (three parallel tracks, do them in this order within the day)**
- Scaffold: `src/`, venv, pinned numpy/scipy/matplotlib. Thirty minutes, no cleverness.
- Eagar-Tsai forward model. Gauss-Legendre quadrature, vectorised. Plot one field
  and eyeball it: comet-shaped isotherms trailing the beam, not symmetric.
- Sweep power and speed independently. Width and depth must move the right way —
  wider/deeper with power, shallower/longer with speed. Wrong direction means a
  sign or units bug and you want it on day 1.
- Pull 4-6 single-track points (power, speed, spot size, width, depth) from
  Weaver et al. 2024. These are the Gate 1 targets.
- Sketch the structural matrix on paper: equations x (unknowns + faults).

**Day 2**
- Absorptivity fit by least squares against the Weaver points. **Gate 1: within
  ~15% on width and depth.** No recovery room if this slips — if it fails, switch
  to a simpler analytical form and widen the stated error bars the same day.
- Tier 1 structural analysis: bipartite graph, Dulmage-Mendelsohn, MSO sets,
  binary detectability and isolability matrix. Independent of Gate 1, so it
  proceeds even if the morning goes badly.

**Day 3** — Five fault modes as model perturbations. Verify each changes the
field in the physically expected direction.

**Day 4** — Three observation models: photodiode (Planck radiance over band and
melt pool area), camera (area above T_melt), two-colour pyrometer (band ratio).

**Day 5** — Noise figures from published sensor characterisations; build Sigma;
whitening. **Gate 2: simulated photodiode magnitudes and trends plausible against
published traces.** Fallback if radiometry fights you: melt pool area as the
photodiode proxy, stated in the paper.

**Day 6** — Complex-step Jacobian, whitened. First pairwise angles.
**Gate 3: a diagnosability matrix exists.** This is the minimum publishable
result and it now lands on day 6.

## Week 2 — analysis, results, validation

**Day 7** — Collinearity index over fault subsets (not just pairs — catches a
fault mimicked by a *combination* of two others). SVD rank and condition number.

**Day 8** — Detectability thresholds from a chi-squared false-alarm criterion.
Minimum detectable magnitude per fault.

**Day 9** — Route A: enlarge the observation vector with temporal and spatial
statistics (drift rate, layer periodicity, gradient along gas direction,
correlation with known build geometry). Recompute. Which confusions dissolve?

**Day 10** — Route B: sensor subset sweep, greedy selection, matrices for
commercial configurations. Assemble the three-way classification.

**Day 11 — validation day, both checks**
- *Depth versus width (central claim).* Weaver et al. report depth tracking
  volumetric energy density while width did not. The analysis should show power
  and speed strongly confounded in depth-sensitive observables, less so in
  width-sensitive ones. Run this one first — it tests the central claim against an
  independent published observation.
- *Recoater fault (method sanity).* Should come out poorly isolable from melt-pool
  sensors alone and well isolable once layer imaging is added, reproducing what
  industry already does.

**Day 12** — Literature extraction. 15-20 monitoring papers, recording per paper:
outcome classes or cause classes, binary detection or multi-class isolation, and
the magnitude separation between tested levels. No code — good work for a tired
evening, and it can be started earlier in spare hours.

## Week 3 — write

**Day 13** — Figures 1-4 (method schematic, model verification, signature
directions, angle heatmap).

**Day 14** — Figures 5-7 (three-way classification, validation checks).
**Decision point: if behind, trim from the buffer list now, not later.**

**Days 15-17** — Write. Introduction carries leg 2 of the novelty argument (the
field works this problem data-driven) and the causes-versus-outcomes distinction.

**Day 18** — Internal read-through against the abstract, clause by clause. Every
promise must map to a section.

**Days 19-21** — Buffer, supervisor review, submit.

## Daily discipline that makes this work

Every decision is pre-made — see `05-risks-and-decisions.md`. No exploratory
coding. If you hit a fork not covered there, take the simpler branch and write the
choice down rather than investigating.

Commit at the end of every day, even broken. The record matters more than the
tidiness in a sprint.

One hour each evening on the literature table or the manuscript skeleton. It is
low-energy work that otherwise piles up into week 3.

## If a gate fails

**Gate 1 (day 2)** — simpler analytical form, wider error bars, same day. Do not
spend day 3 on it.

**Gate 2 (day 5)** — melt pool area as photodiode proxy. Say so in the paper. Do
not spend day 6 on radiometry.

**Gate 3 (day 6)** — if there is no matrix by end of day 6, the three-week
timeline has failed and the honest move is to tell the conference, not to write
up something unfinished.
