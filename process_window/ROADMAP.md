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
4. Simulator: steers bets, chain starting points and sampling, never
   validity.

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
- [ ] Theorem 2 (spreading to the continuous region under monotonicity).
- [ ] Error-budget passing between chains (graphical procedure with
      e-processes); prove it keeps Theorem 1.
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
- [ ] Second domain for generality: two-drug dose-combination scenarios.
- [ ] Baselines: grid + Clopper-Pearson + Bonferroni; bandit e-BH without
      structure (Xu, Wang & Ramdas); GP level-set estimation; M-SafeUCB;
      BO feasibility search (BEAM-style).

### Phase 3: adaptive sampling and sample-complexity theory (weeks 5-6)

- [x] Frontier sampling rule v1: most new predicted-window area per
      expected coupon (`alloc="frontier"`).
- [~] Scaling experiment (`experiments/exp03_scaling.py`).
- [x] Oracle comparison (`experiments/exp04_oracle.py`): on the area goal,
      learned frontier allocation matches the oracle.
- [x] Edge allocation rule (the lower bound's binding constraints used as
      an algorithm) with optimistic re-check. Tracks the oracle upper bound
      when rates are known; learned overhead grows slowly (1.1x-2.2x of UB
      from 8x8 to 24x24). Shrinking it is the open learning term.
- [~] Bounds next to practice (`experiments/exp05_bounds.py`).
- [~] Theorem 4a/4b lower bounds drafted (`notes/05_lower_bound.md`); need
      checking.
- [ ] Theorem 3: upper bound in terms of the weighted cover C*(T)
      (note 4, section 4).
- [ ] Theorem 4: matching lower bound by change of measure.
- [ ] **Week 6 go/no-go.** If the 2D bounds hold, stay on ICML. Otherwise
      retarget to an applied venue.

### Phase 4: extensions and real data (week 7)

- [ ] Your experimental data as the real-world case study.
- [ ] Optional: prediction-powered CT budget (in-situ signal on every coupon,
      CT on a random subset).

### Phase 5: full experiments (week 8)

- [ ] All baselines, simulator-bias sweeps, ablations, error-rate tables.

### Phase 6: writing (weeks 9-10)

- [ ] Full draft, theory appendix, internal adversarial review, code release.

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
