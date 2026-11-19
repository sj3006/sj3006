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

Status key: [x] done, [~] in progress, [ ] not started, [-] dropped.

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

- [x] Validity of the certified region: now the cone rule's Theorem 1 in
      the paper, full proof in Appendix A (the chain version in notes/02
      is superseded).
- [x] Cone-rule validity and the closed-testing characterization
      (Theorem 1 and Proposition 1 in the paper).
- [-] Theorem 2 (spreading to the continuous region): dropped; the paper
      stays on grids.
- [x] Error-budget passing between chains: no longer needed. The cone rule
      is closed testing, which reuses the weight of logically certified
      hypotheses automatically (notes/06, section 3).
- [x] Batched build plates: covered (Appendix A setup: a batch is chosen
      before any of its outcomes is seen).
- [x] Monotonicity check: audit (`pwcert/audit.py`, `experiments/violation.py`)
      and a test of the raw LM rates (`exp_lm.py --parts check`).

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
      full grid with fixed-sequence testing (Learn-then-Test) [x]; GP
      level-set estimation, plain and with the monotone closure [x];
      safe expansion (M-SafeUCB-style) and BEAM-style active search
      [implemented; full runs pending].

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
- [x] Lower bounds with and without the ordering (Theorem 2 in the paper,
      proof in Appendix A).
- [x] Oracle upper bound via Wald's identity (Theorem 3). The learned-
      allocation conjecture is superseded by the search and its bound
      (Theorem 4).
- [x] No-simulator mode: pilot plate + monotone fit (`pwcert/pilot.py`) and
      optimistic allocation.
- [x] **Week 6 go/no-go.** The bounds held; staying on ICML.

### Phase 4: extensions and real data (week 7)

- [ ] Your experimental data as the real-world case study.
- [ ] Optional: prediction-powered CT budget (in-situ signal on every coupon,
      CT on a random subset).

### Phase 5: full experiments (week 8)

- [x] `experiments/final.py`: validity, area-vs-budget curves on five
      scenarios, scaling to 48x48, bounds, ablations. Figures in
      `results/final/`.
- [x] GP level-set baseline: 7.5-100% false-certification rates unless
      nearly useless (`pwcert/gp_baseline.py`, `final.py gp`).
- [~] Safe-BO (M-SafeUCB-style) and BEAM-style baselines: implemented as
      sampling rules of the GP baseline; full runs pending.
- [x] Robustness when monotonicity is violated, plus an audit that detects
      gross violations (`pwcert/audit.py`, `experiments/violation.py`).

### Phase 6: writing (weeks 9-10)

- [x] Draft v0 (`paper/draft.md`), v1 (`paper/draft_v1.md`), LaTeX
      (`paper/latex/main.tex`).
- [x] Theory appendix (A), experiment-details appendix (B), Impact
      Statement, internal adversarial review with a number audit, anonymous
      code archive (`scripts/make_supplement.py`).

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
- 2026-11-13 (evening): References checked against publisher, proceedings
  or indexing records (volumes, pages, DOIs); BEAM author list found
  (Fadhel et al., AAAI 2026). Only the volume and pages of Waudby-Smith and
  Ramdas (JRSS B 2024) are unchecked. New baseline: GP level set with the
  monotone closure (as in monotone safe exploration). It certifies more of
  the region than the plain GP, but at confidence parameter 4 still
  certifies an unsafe setting in 2.5-27.5% of runs where it covers 23-87%,
  across all four problems; the tuning that works on one problem fails on
  another. Paper updated. The nested 23 x 23 LM grid is measuring
  (about 350 of 529 settings); its Table 1 row comes next.
- 2026-11-13 (night): The nested 23 x 23 LM grid is measured (529
  settings, 160 generations each; the 12 x 12 settings are reused). To
  certify half the safe region, ours needs 5.8k generations (pilot
  counted), no ordering 25.0k, full-grid fixed-sequence 47.1k, full-grid
  Bonferroni 75.1k. From 12 x 12 to 23 x 23 our cost grows 1.5x and the
  unordered cost 3.1x (edge 1.9x, area 3.7x), so the gap grows from 2.1x
  to 4.3x, as the theory predicts. At 70%: 8.4k / 41.3k / 75.1k / 132k.
  Without the pilot ours needs 12.4k (50%) and 14.7k (70%), so on the fine
  grid the pilot roughly halves the cost. Fixed confidence: the search
  stops at 51.8k (8 of 8 complete, none unsafe) against 129.7k per-setting
  (2.5x, up from 1.6x); the ratio to the ordered bound grows from 9.4 to
  14.8. Table 1, Table 2, Figure 2 (new LM panel) and the abstract are
  updated. Waudby-Smith volume 86 issue 1 confirmed; only its page range
  is unchecked.
- 2026-11-14: Submission pieces: Impact Statement, Appendix B (experiment
  details), and an anonymous supplement builder (scripts/make_supplement.py;
  refuses to write the zip if a name, path, e-mail or tool name is left).
  Number audit against the result files; fixes: fixed-sequence testing
  helps full grids by 17-37%; GP sentence; ablation signs; the LM
  monotonicity check is now an exact binomial test (no setting outside 99%
  on either grid). Table 2 did not reproduce because the search's start
  rule had changed after the runs; the old rule (start at the edge the side
  information predicts) is 6-14% cheaper, so it is the default again and
  the 23 x 23 LM search figure is 52.1k (not 51.8k). New baselines at
  16 x 16 (40 runs per tuning): BEAM-style active search errs in 70-100% of
  runs at beta 2; at beta 4, lengthscale 0.1, it erred in 1 of 40 runs on
  each problem and certified 66-79% (ours 54-84%), but at lengthscale 0.3
  it errs in 42.5% on the drug screen. Safe expansion (SafeOpt/M-SafeUCB
  style) stalls at its seed or overshoots. 316L sensitivity: moving the
  absorptivity and each threshold by 10-20% leaves ours 1.4-2.5x cheaper
  than no ordering and 14-62x cheaper than full-grid FST, no false
  certificate. Search tightening: no gain found (weight mix within 2%; the
  bracket probe rule makes no difference at 16 x 16; at 32 x 32 the
  midpoint rule has the cheaper median, 165.6k vs 175.0k, but it is the
  one with the probe time-out). Qwen2.5-0.5B surface measuring.
- 2026-11-14 (later): Second language model measured: Qwen2.5-0.5B on the
  12 x 12 grid (86 of 144 settings safe; no setting off the monotone fit at
  the 1% level, 1 of 264 pairs reversed). To certify half the safe region:
  ours 4.6k generations (pilot counted), no ordering 9.2k (2.0x), full-grid
  fixed-sequence 17.0k, full-grid Bonferroni 24.8k; fixed confidence: search
  22.9k (8 of 8 complete) vs 39.0k per-setting, 10.5x the ordered bound.
  Added to Tables 1-2, the abstract and the text (Qwen2.5 report cited,
  arXiv 2412.15115). Figure 1 now uses the 23 x 23 grid: at 10k
  generations ours certifies 75% of the safe region on average (213 of
  292 in the pictured run, none unsafe), no ordering 16%, full grids 0%.
  GP baselines on the language model: BEAM-style at beta 4, lengthscale
  0.1-0.2 erred in 1 of 20 runs and certified 94-95% (ours 90%), but 35%
  errors at lengthscale 0.3; safe expansion stalls or overshoots. GP
  certificates in the all-at-tolerance worst case: 0-1.25% errors
  (BEAM-style), up to 12.5% (with the closure), so their failures come
  from the surface's shape. Abstract GP sentence rewritten to cover all
  three GP baselines. Supplement: full test suite passes from the unpacked
  archive (57 tests).
- 2026-11-15: No self-produced LPBF data and no compute budget for now.
  Literature: the MeltpoolNet tables (Akbari et al. 2022) were checked as
  a source of real LPBF data. They give one measurement per setting (no
  repeated builds), some labels are rule-derived, and two 316L studies
  have formula-like values, so they cannot give failure rates; the one
  clean depth/width grid has no safe window under any standard keyhole
  criterion. What they can do is test Assumption A: in 316L melt-pool
  measurements from 11 single-track studies, depth and width grow with
  power and shrink with speed in every study, and 5 of 942 neighbouring
  pairs (all in width) reverse by more than two standard errors; the
  depth/width ratio (keyhole direction) moves the right way in all 6
  studies that report both (experiments/am_monotone_check.py; paper
  Section 6 and Appendix B). COMPUTE_PLAN.md: tier A (three 7B open
  models, both grids, live runs) is about 10 GPU-hours on one 80 GB GPU,
  roughly $15-40; scripts/gpu_runs.sh runs it in one command and the LM
  code now takes --device/--dtype (tested on CPU). Surfaces so far were
  measured in the checkpoints' bfloat16 (now stated in Appendix B).
  Qwen2.5-1.5B 12 x 12 surface measuring on CPU (about 7 h).
- 2026-11-15 to 2026-11-18: The Qwen2.5-1.5B CPU measurement was stopped
  three times: twice the cloud session's machine was reclaimed while the
  session was idle, once by the 2-hour limit on background jobs. It is
  resumable and was resumed each time. scripts/lm_table_rows.py prints the
  Tables 1-2 rows for any measured model (reproduces the existing rows).
  PROJECT_RECORD.md: the full project record (idea, results, history,
  decisions, mistakes fixed, file map, results index, how to run, what is
  left, step-by-step submission plan); a top-level README.md points to it.
  requirements.txt gains pandas (the melt-pool check and its tests need it).
  New experiment, correlated trials on one build plate
  (experiments/plate_effects.py): with a beta-binomial plate effect,
  feeding trials one by one breaks validity (worst case 0.75% at
  correlation 0.05, 23% at 0.2; one setting with 24 trials per plate 17%
  at 0.05, 57% at 0.2). Two fixes are valid for any correlation and never
  erred: one outcome per setting per plate (19x more trials, because the
  edge rule stacks trials of one setting on a plate) and a plate-aware
  edge rule (2.4x more trials and plates). A plate is worth one to two
  independent trials of a setting however many it holds. Added to Section
  6, Appendix B, Limitations, the Impact Statement and reviewer FAQ 2;
  the main text now ends near the top of page 8. lm_live.py gains
  --threads; a second live run (seed 1) is running.
- 2026-11-19: Qwen2.5-1.5B finished (12 x 12, 160 generations per setting;
  about 7 h on three CPU threads in four pieces). 88 of 144 settings safe;
  no setting off the monotone fit at 1%, 0 of 264 pairs reversed beyond
  2 SE. Half the safe region: ours 6.5k generations (pilot counted), no
  ordering 10.6k (1.6x), full-grid FST 17.0k, Bonferroni 27.2k; at 70%:
  7.7k / 23.4k / 47.7k / 63.1k (3.0x and 6.2x). Fixed confidence: search
  24.4k (8 of 8 complete, none unsafe) vs 51.5k per-setting (2.1x), 11.0x
  the ordered bound. GP: errs in every run at beta 2, 35-90% at 3; at 4
  certifies at most 58% and errs in up to 20% (ours 82%). Added to Tables
  1-2 and the text (abstract: "1.6-2.0x fewer on two larger models";
  Limitations: three small models, 0.1B-1.5B). Five live runs on SmolLM2
  (seeds 0-4, 8.0k generations each): 59-65 of 78 safe settings
  certified (62.8 on average), none unsafe; 20 surface runs at the same
  budget: 59-69 (64.3), none unsafe (experiments/lm_live_summary.py).
  Paper text updated ("five live runs agree"). Main text ends about a
  quarter down page 8.
