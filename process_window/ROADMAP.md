# Certified process windows: project trajectory

Working title: *Certifying process windows with ordered physics: anytime-valid,
simulator-guided discovery of feasible manufacturing settings.*

Target: ICML 2027 main track (deadline expected late January 2027; confirm when
the call for papers is posted). Fallback: the same paper retargeted to an
applied venue (Additive Manufacturing, JMS) or an ICML workshop if the
sample-complexity theory does not land by the week 6 checkpoint.

This directory is independent of the LIME/RUL work elsewhere in the repo.

## The claim we are building toward

Given a grid of process settings (laser power x scan speed, later more axes)
and several failure modes (lack of fusion, keyholing, balling), return a
region of settings such that, with probability at least 1 - alpha, every
setting in it has each failure-mode rate below its threshold.

The guarantee must hold

- at any stopping time (check after every build, stop whenever),
- under any adaptive choice of which settings to build next,
- for any simulator, including a badly wrong one,

assuming only that each failure mode is monotone in known directions
(the physics ordering). The novelty claims are:

1. Problem: certifying a region when every configuration needs its own
   costly experiments (unlike Learn-then-Test / Pareto Testing, which assume
   one shared calibration set).
2. Structure: multi-dimensional partial orders with opposing failure modes
   (prior monotone thresholding work is one-dimensional; monotone safe BO is
   single-variable and GP-based).
3. Theory: sample complexity scales with the window boundary, not the grid
   size, with a matching lower bound.
4. Simulator: sets fixed weights and steers sampling, never validity.

**Current method (since 2026-11-12):** the cone rule in `pwcert/cone.py`.
Certify a setting for a mode when the weighted betting wealth in its riskier
cone reaches 1/alpha (closed testing with e-values; notes/06). Ensemble
weights from the simulator, frontier allocation with optimism, pilot plate
when there is no simulator. The chain-based certifier in `pwcert/certify.py`
is kept for the earlier experiments. Paper draft: `paper/draft.md`.

## Phases and milestones

Status key: [x] done, [~] in progress, [ ] not started.

### Phase 0: foundations (week 1)

- [ ] Day 1: read Shafer 2021 (testing by betting). Companion note:
      `notes/01_betting_and_ville.md`.
- [ ] Day 2: read Ramdas et al. 2023 (SAVI survey).
- [x] Day 2: single-setting betting test in code, error rate checked by
      simulation. Code: `pwcert/eprocess.py`, `experiments/exp01_single_setting.py`.
- [ ] Day 3: read Waudby-Smith & Ramdas 2024.
- [x] Day 3: simulator-seeded betting, checked against good and bad
      simulators (same files). Finding: bet seeding helps little (note 4).
- [ ] Day 4: read Bretz et al. 2009 (graphical multiple testing).
- [x] Day 4: 2D grid with monotone spreading and chain-wise testing.
      Code: `pwcert/certify.py`, `experiments/exp02_grid.py`. Companion
      note: `notes/03_multiple_testing.md`.
- [ ] Day 5: read Garivier, Menard & Rossi 2017; proof walkthrough.
- [ ] Day 6: skim positioning papers; rewrite the problem statement in your
      own words (`notes/02_problem_statement.md` is the v0 to edit).

Exit criterion: code reproduces the guarantee empirically (error rate at or
below alpha in every configuration, including adversarial simulators).
**Met** (exp01, exp02 part A).

### Phase 1: validity theory and method v1 (weeks 2-3)

- [~] Theorem 1 (validity of the certified window). Draft proof in
      `notes/02_problem_statement.md`; needs independent checking.
- [~] Cone-rule validity (Theorem 5, notes/06): three-line proof via Ville
      on the true-null set; needs checking.
- [ ] Theorem 2 (spreading to the continuous region under monotonicity).
- [x] Error-budget passing between chains: no longer needed. The cone rule
      is closed testing, which reuses the weight of logically certified
      hypotheses automatically (notes/06, section 3).
- [ ] Batched build plates: confirm the proof covers a plate of coupons
      decided before any of them are measured.
- [ ] Monotonicity check: sequential test that flags violations in the data.

Exit criterion: Theorems 1-2 written out in full, checked line by line.

### Phase 2: realistic benchmark (week 4)

- [ ] Replace the toy ground truth with one fitted to process-map data
      (MeltpoolNet-style, check licence) or to your own experiments.
- [x] Analytical melt-pool simulator: Rosenthal pool + Tang lack of fusion,
      King keyhole, length/width balling (`pwcert/physics.py`). Thresholds
      are placeholder calibrations until we have data.
- [x] Second domain for generality: two-drug combination screen with a
      Bliss-independence simulator (`pwcert/dose.py`).
- [~] Baselines: grid DoE + Clopper-Pearson + Bonferroni [x]; adaptive
      betting tests without the ordering, same allocation and re-check [x];
      GP level-set estimation [ ]; M-SafeUCB [ ]; BEAM-style BO search [ ].

### Phase 3: adaptive sampling and sample-complexity theory (weeks 5-6)

- [x] Frontier sampling rule v1: most new predicted-window area per
      expected coupon (`alloc="frontier"`).
- [x] Scaling experiment (`experiments/exp03_scaling.py`): 8x8 -> 32x32,
      cost to certify 70% of the window grows ~n^1.34 (ours, good sim) vs
      ~n^2.25 (unstructured) and ~n^2.2 (grid DoE). No-simulator variant
      still scales like area: needs a better no-sim chain start.
- [x] Oracle comparison (`experiments/exp04_oracle.py`): on the area goal,
      learned frontier allocation matches the oracle.
- [x] Edge allocation rule (the lower bound's binding constraints used as
      an algorithm) with optimistic re-check. Tracks the oracle upper bound
      when rates are known; learned overhead grows slowly (1.1x-2.2x of UB
      from 8x8 to 24x24). Shrinking it is the open learning term.
- [x] Bounds next to practice (`experiments/exp05_bounds.py`).
- [~] Theorem 4a/4b lower bounds drafted (`notes/05_lower_bound.md`); need
      checking.
- [x] Theorem 3a: rigorous oracle upper bound via Wald's identity
      (notes/07); 3b (learned allocation, with slack) still a conjecture.
- [~] Theorem 4: lower bounds drafted (notes/05); computed next to practice
      in `experiments/final.py bounds`.
- [x] No-simulator mode: pilot plate + monotone fit (`pwcert/pilot.py`) and
      optimistic allocation.
- [ ] **Week 6 go/no-go.** If the 2D bounds hold, stay on ICML. Otherwise
      retarget to an applied venue.

### Phase 4: extensions and real data (week 7)

- [ ] Your experimental data as the real-world case study.
- [ ] Optional: prediction-powered CT budget (in-situ signal on every coupon,
      CT on a random subset).

### Phase 5: full experiments (week 8)

- [~] `experiments/final.py`: validity, area-vs-budget curves on five
      scenarios, scaling to 48x48, bounds, ablations. Figures in
      `results/final/`.
- [x] GP level-set baseline: 7.5-100% false-certification rates unless
      nearly useless (`pwcert/gp_baseline.py`, `final.py gp`).
- [ ] Safe-BO (M-SafeUCB) and BEAM-style baselines.
- [x] Robustness when monotonicity is violated, plus an audit that detects
      gross violations (`pwcert/audit.py`, `experiments/violation.py`).

### Phase 6: writing (weeks 9-10)

- [~] Draft v0 (`paper/draft.md`).
- [ ] Theory appendix, internal adversarial review, code release.

## Open questions for Amit

These change the method, so they need your answer before Phase 2:

1. Process and materials, and whether you have replicate coupons per setting.
2. Outcome type: pass/fail per defect type, relative density, porosity
   fraction? Measured how (CT, metallography, Archimedes)?
3. In-situ monitoring on every coupon?
4. What "coupon" means in your setup (single track, cube, tensile bar) and
   roughly how many fit on one build plate.
5. In your process, does balling get worse with *higher* power (melt-pool
   elongation, which the Rosenthal model predicts) or with *lower* power
   (poor wetting)? The monotone direction matters for validity.
6. Are your windows thin bands along constant energy density, or wider?

## Log

- 2026-10-24: Directory created. Roadmap, Day 1 note, problem statement v0,
  e-process and grid certifier code, first two experiments.
- 2026-10-24: Full exp02 (validity holds: worst-case FWER 0-4%). Found that
  mid-window chains scale with area; added boundary-start chains, the
  spread and hybrid structures, and the frontier allocation rule. Added the
  current-practice baseline (grid DoE + Clopper-Pearson + Bonferroni), the
  Rosenthal physics simulator, notes 3-4 with the revised theory target
  (weighted cover C*(T)). Scaling experiment exp03 running.
- 2026-10-24: Drafted Theorem 4a/4b (lower bounds with and without the
  ordering; notes/05). Oracle experiment (exp04). Edge allocation rule +
  optimistic re-check + confidence-based futility after three failure
  modes found by the bounds experiment (exp05). Physics model directions:
  balling worsens with both power and speed in the Rosenthal model.
- 2026-10-24: Full exp03 and exp05 done. Learned overhead diagnosed as a
  target-membership cost; Theorem 3 to be stated with slack (notes/04).
  Next without Amit's input: slack version of Theorem 3, no-sim chain
  starts, give the unstructured baseline the re-check step, budget passing.
- 2026-11-12 (overnight): Cone rule replaces chains (closed testing with
  e-values; validity in three lines; spreading and pooling built in).
  Ensemble weights from perturbed simulators. Optimistic allocation fixes a
  no-simulator stall (one near-threshold setting absorbed 40k coupons).
  Pilot-learned simulator. Two-drug dose scenario. Rigorous oracle upper
  bound (Wald). Consolidated benchmark and paper draft v0.
- 2026-11-12 (overnight, later): edge allocation (aim at 0.7 eps) beats
  greedy frontier by 1.3-2.5x and becomes the default for both methods;
  ours now wins on every scenario including the thin Rosenthal band
  (2.2x at 48x48). GP baseline, monotonicity audit. Full results in
  notes/08 and paper/draft.md; figures in results/final/.
- 2026-11-13: Reframed as "certifying safe operating regions under
  monotone failure modes" with an LLM application first (draft v1).
  Fixed-confidence search (galloping + bisection, two-sided probes,
  notes/09). Theory appendix consolidated (paper/appendix_theory.md).
  Found and fixed an error in the fixed-confidence lower bound (two terms
  were added that can share trials; now one joint convex program,
  pwcert/bounds.py): search/bound ratio is 4.2-13.5, not 4-8. Added the
  Learn-then-Test fixed-sequence full-grid baseline (15-26x more trials
  than ours at 32-48 grids). LaTeX paper (paper/latex/) with verified
  bibliography and figures. LM surface measurement running (SmolLM2-135M,
  12 x 12 settings x 160 generations).
- 2026-11-13 (later): LM surface finished (78 of 144 settings safe; raw
  rates within 1.8 SE of a monotone fit). LM benchmark: to certify half the
  safe region, ours 3.8k generations with the pilot counted, no ordering
  8.0k, full-grid fixed-sequence 11.7k, full-grid Bonferroni 18.6k; the
  fixed-confidence search stops at 19.7k (8 of 8 complete), against 31.8k
  per-setting; the GP certifies unsafe settings in 95-100% of runs at
  beta 2. The LM surface is now Figure 1 of the paper. Proofs: no [check]
  items left. The cone rule is now Proposition 1 (closed testing with
  restricted combinations). Termination needs an explicit growth condition
  (T) on the bet grids, which holds at every tolerance we use and fails
  below about 2%. Time-outs are covered in Theorem 6. Code-release README
  rewritten. Next: live LM run; a nested 23 x 23 LM grid, to show the gap
  growing with resolution on real generations.
