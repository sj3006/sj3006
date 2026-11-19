# Project record

**Certifying Safe Operating Regions under Monotone Failure Modes**
(target: ICML 2027, main track)

This file is the complete record of the project: what the idea is, what was
built, every result and where it lives, the decisions taken and why, the
mistakes found and fixed, and exactly what is left to do and how to do it.
It is written so that you can finish and submit the paper, answer
reviewers, and pick the work up again later, with no AI assistant and no
memory of the conversations that produced it.

Last updated: 2026-11-19. The running log of dated changes is at the
bottom of [`ROADMAP.md`](ROADMAP.md); this file is the overview.

---

## Contents

1. [Where everything is](#1-where-everything-is)
2. [The project in plain words](#2-the-project-in-plain-words)
3. [The paper as it stands](#3-the-paper-as-it-stands)
4. [What was done, in order](#4-what-was-done-in-order)
5. [Decisions and the reasons for them](#5-decisions-and-the-reasons-for-them)
6. [Mistakes found and fixed](#6-mistakes-found-and-fixed)
7. [Repository map](#7-repository-map)
8. [Results index: which file backs which claim](#8-results-index-which-file-backs-which-claim)
9. [How to run everything](#9-how-to-run-everything)
10. [What is left](#10-what-is-left)
11. [Submitting without help: a step-by-step plan](#11-submitting-without-help-a-step-by-step-plan)
12. [Ideas for later work](#12-ideas-for-later-work)
13. [Glossary](#13-glossary)

---

## 1. Where everything is

**On GitHub.** Everything is in the repository `sj3006/sj3006`, folder
`process_window/`, on the branch **`claude/exciting-turing-fm5s3y`**. As of
2026-11-18 the repository's default branch (the one GitHub shows first) does
**not** contain this folder: all of this work lives only on that branch.
Merge it into the default branch (or into a branch you control) so it cannot
be lost if the branch is cleaned up. The branch only adds commits on top of
the default branch, so the merge is a fast-forward with no conflicts.

The rest of the repository (the LIME / remaining-useful-life notebooks and
papers at the top level) is a separate, earlier project. Nothing in
`process_window/` uses it.

| What | File |
|---|---|
| The paper (source) | [`paper/latex/main.tex`](paper/latex/main.tex), bibliography [`paper/latex/references.bib`](paper/latex/references.bib) |
| The paper (compiled PDF) | [`paper/latex/main.pdf`](paper/latex/main.pdf) |
| How to build the PDF; style files | [`paper/latex/README.md`](paper/latex/README.md) |
| Proofs in plain text (same as Appendix A) | [`paper/appendix_theory.md`](paper/appendix_theory.md) |
| Readable Markdown version of the paper | [`paper/draft_v1.md`](paper/draft_v1.md) (kept in sync with main.tex) |
| Code overview and reproduction table | [`README.md`](README.md) |
| Dated log of everything done | [`ROADMAP.md`](ROADMAP.md) (bottom section "Log") |
| What extra compute would buy, and how to run it | [`COMPUTE_PLAN.md`](COMPUTE_PLAN.md), [`scripts/gpu_runs.sh`](scripts/gpu_runs.sh) |
| Answers to likely reviewer questions | [`paper/reviewer_faq.md`](paper/reviewer_faq.md) |
| Submission form fields and checklist | [`paper/submission_metadata.md`](paper/submission_metadata.md) |
| Study notes (betting, multiple testing, bounds, search) | [`notes/`](notes/) (nine notes, see section 7) |
| Anonymous code archive for reviewers | `python3 scripts/make_supplement.py` writes `dist/supplement.zip` (not committed; rebuild it) |

---

## 2. The project in plain words

### The problem

Many systems are set by a couple of knobs, and each setting can fail in more
than one way.

- **Laser powder bed fusion (316L).** Knobs: laser power and scan speed. Too
  little energy leaves unmelted powder (lack of fusion); too much drills
  keyhole pores; some combinations break the track into beads (balling).
- **A language model.** Knobs: sampling temperature and top-p. Too cold and
  it repeats itself; too hot and it produces incoherent text.
- **Two drugs given together.** Knobs: the two doses. Too high is toxic; too
  low does nothing.

You want the **safe operating region**: the settings where every failure
rate is below its tolerance (say 10%). The catch is that the failure rate
at a setting can only be learned by running trials *at that setting*. A
full grid of settings, each tested on its own, costs in proportion to the
grid's area, which gets expensive fast.

We want a region that comes with a **guarantee**: with probability at least
95%, *nothing* unsafe is in it (this is called family-wise error control).
And we want it with as few trials as possible.

### The one structural fact we use

Each failure mode gets worse in a known direction. Lack of fusion gets worse
as power goes down or speed goes up; keyholing the other way. Repetition in
a language model gets worse as temperature goes down; incoherence as it goes
up. This is **Assumption A (monotone failure modes)**. If a setting is safe
from keyholing, every setting with less power and more speed is too.

That one fact means you never have to test the inside of the safe region:
testing along its edge is enough. This is where all the savings come from.

### What we built (four pieces)

1. **Betting e-processes (the evidence at one setting).** Think of a gambler
   who bets, trial by trial, that the setting is safe. Each trial without a
   failure pays a little; each failure costs a little. If the setting were
   actually unsafe, the gambler could not expect to make money, so the
   chance that their wealth ever reaches 20 times the stake is at most
   1/20 = 5% (Ville's inequality). So "wealth reached 20" is a valid
   certificate, you may look at it after every trial, and you may choose
   which setting to test next however you like. That freedom is what lets
   the method be adaptive without losing the guarantee. Code:
   `pwcert/eprocess.py` (a mix of a plug-in bet and a fixed menu of bets).
2. **The cone rule (combining settings).** A setting is certified for a
   failure mode when the weighted wealth of all settings that are *riskier*
   than it for that mode (its "cone") adds up to 20. This is a known
   multiple-testing construction (closed testing), and under monotonicity
   it boils down to two cumulative sums over the grid, so it is fast. It
   keeps the 95% guarantee for the whole region at once. Code:
   `pwcert/cone.py`.
3. **Choosing where to test.**
   - *Fixed budget:* the **edge rule** puts trials at the riskiest settings
     of the region we expect to certify (slightly shrunk, to 0.7 times the
     tolerance). These are the settings a lower bound says must be tested.
   - *Fixed confidence:* a **search** along each row of the grid, galloping
     then bisecting, that stops on its own when the whole target region is
     certified. Code: `pwcert/search.py`.
4. **Theory.**
   - *Lower bounds:* any valid method needs a certain number of trials.
     With the ordering, that number depends only on the settings along the
     region's edge (about n of them on an n-by-n grid); without it, on
     every setting (n²).
   - *Upper bound:* the search costs at most the lower bound times a
     log(n) factor and a multiple-testing factor.
   - Code for the bounds: `pwcert/bounds.py`.

**Side information** (a physics simulator, a cheaper model, or a small pilot
study) is used only to decide where to test and how to weight settings. It
can make the method cheaper or more expensive, but it can never break the
guarantee. Even a deliberately wrong simulator keeps the error rate below
5% (checked; section 3).

### How it differs from what exists

- **Learn-then-Test** (Angelopoulos et al.) controls risk for a fixed grid
  of settings with one shared calibration set. Here every setting needs its
  own trials, and we pick them adaptively. We include Learn-then-Test with
  fixed-sequence testing as a baseline; it pays for the whole area.
- **Gaussian-process methods** (level-set estimation, SafeOpt, BEAM-style
  active search) fit a smooth model and certify where the model is
  confident. They have no guarantee unless the kernel is right; we show
  tunings that work on one problem and fail badly on another.
- **Closed testing with e-values** is known. What is new is the problem
  (per-setting trials, several opposing failure modes, partial orders),
  that it reduces to cumulative sums under monotonicity, the edge-vs-area
  lower bounds, and a search that is near-optimal up to stated factors.

### The two-minute pitch

"If you know which way each failure mode gets worse, you only need to test
the edge of the safe region, not its inside. We turn that into a procedure
with a 95% guarantee that nothing unsafe is certified, valid however
adaptively you choose your trials, and prove it is close to the best
possible. On real language-model generations it needs 2 to 4 times fewer
generations than testing without the ordering and 3 to 8 times fewer than
standard full-grid testing; the gap grows with the grid's resolution."

---

## 3. The paper as it stands

**Title:** Certifying Safe Operating Regions under Monotone Failure Modes.
**Format:** ICML style (2026 files until the 2027 ones are released). The
main text ends near the top of page 8 (8 pages allowed). Then come the
Impact Statement, references, Appendix A (proofs) and Appendix B
(experiment details): 15 pages in total.
**Anonymous:** author block and PDF metadata say "Anonymous Authors".

### Sections

1. Introduction (problem, why existing tools fall short, contributions)
2. Problem (Assumption A, protocol, fixed budget, fixed confidence, the
   "between grid points" remark)
3. Testing: the cone rule (Theorem 1 validity, Proposition 1 closed testing)
4. Allocation (edge rule; the search, Algorithm 1)
5. Theory (Theorem 2 lower bound, Theorem 3 oracle upper bound, Theorem 4
   search, Corollary edge vs. area, condition (T))
6. Experiments (applications, baselines, Tables 1-2, Figures 1-3, validity,
   GP baselines, ablations, violations of monotonicity)
7. Related work, 8. Limitations, Impact Statement
8. Appendix A: proofs. Appendix B: experiment details, the published
   melt-pool check, compute.

### Headline numbers

**Table 1: trials to certify half of the safe region (fixed budget).**
LM: generations, pilot study counted. "grid FST" = full grid with
fixed-sequence testing (Learn-then-Test); "grid Bonf." = full grid with a
Bonferroni correction.

| Problem | grid | ours | no ordering | grid FST | grid Bonf. |
|---|---|---|---|---|---|
| synthetic window | 16² | 7.6k | 24.6k | 58.1k | 77.1k |
| | 32² | 16.6k | 116k | 256k | 339k |
| | 48² | 29.6k | 270k | 576k | 763k |
| Rosenthal 316L | 16² | 5.3k | 7.7k | 112k | 135k |
| | 32² | 19.5k | 38.0k | 493k | 653k |
| | 48² | 42.5k | 93.5k | 1.11M | 1.77M |
| SmolLM2-135M | 12² | 3.8k | 8.0k | 11.7k | 18.6k |
| | 23² | 5.8k | 25.0k | 47.1k | 75.1k |
| Qwen2.5-0.5B | 12² | 4.6k | 9.2k | 17.0k | 24.8k |
| Qwen2.5-1.5B | 12² | 6.5k | 10.6k | 17.0k | 27.2k |

**Table 2: fixed confidence (the search stops by itself).**
LB = the lower bound of Theorem 2.

| Problem | search | LB (ordered) | ratio | per-setting test | LB (unordered) |
|---|---|---|---|---|---|
| synthetic 8² | 14.2k | 3.4k | 4.2 | 21.9k | 4.5k |
| synthetic 16² | 50.3k | 8.8k | 5.7 | 100.0k | 18.7k |
| synthetic 32² | 165.6k | 19.4k | 8.5 | 457.7k | 77.0k |
| synthetic 48² | 334.6k | 24.8k | 13.5 | (too slow) | 174.4k |
| SmolLM2 12² | 19.7k | 2.1k | 9.4 | 31.8k | 6.9k |
| SmolLM2 23² | 52.1k | 3.5k | 14.8 | 129.7k | 24.4k |
| Qwen2.5-0.5B 12² | 22.9k | 2.2k | 10.5 | 39.0k | 8.6k |
| Qwen2.5-1.5B 12² | 24.4k | 2.2k | 11.0 | 51.5k | 10.3k |

**Other results in the paper**

- **Validity.** With every setting exactly at the tolerance (the hardest
  case), the false-certification rate is 0-2.75% at a 5% target (400 runs
  per configuration). Across all efficiency runs, no unsafe setting was
  ever certified.
- **The gap grows with resolution**, as the theory says: synthetic 3.2x at
  16² to 9.1x at 48²; language model 2.1x at 12² to 4.3x at 23².
- **Figure 1** (the language-model surface, 23 x 23 grid, 10k
  generations): ours certifies 75% of the safe region on average (213 of
  292 settings in the pictured run, none unsafe); without the ordering
  16%; full grids nothing yet.
- **Robust to the failure definitions** (LM): seven alternative thresholds
  and tolerances, 70 runs: still 1.6-2.2x fewer generations than no
  ordering, no false certificate.
- **Robust to the 316L calibration**: absorptivity and each threshold moved
  by 10-20%: still 1.4-2.5x fewer trials than no ordering, 14-62x fewer
  than full-grid FST, no false certificate.
- **Correlated trials on one build plate** (added 2026-11-18). If coupons
  on a plate share a plate effect, feeding them to the method one by one
  breaks the guarantee: in the worst case it errs in 0.75% of runs at an
  intra-plate correlation of 0.05, but 23% at 0.2.

  Two fixes keep it valid for any correlation:
  - one outcome per setting per plate, which costs 19x more trials
    because the edge rule stacks trials of a setting on one plate;
  - a plate-aware edge rule (one coupon per setting per plate), which
    costs 2.4x more trials and plates.

  Section 6 "Correlated trials" and Appendix B.
- **GP baselines** (level set, with the monotone closure, BEAM-style active
  search, safe expansion): no tuning is both useful and reliable across
  problems. The best case (BEAM-style, confidence 4, lengthscale 0.1)
  erred in 1 of 40 runs and certified 66-94%. The same method at
  lengthscale 0.3 erred in 35-42.5% of runs. The data do not tell you
  which tuning to trust.
- **When monotonicity fails** (an unsafe pocket inside the region): it is
  certified by spreading in 75-92% of runs; an audit catches gross
  violations (96-100%) but rarely mild ones (4-9%). The paper says so.
- **Is Assumption A true?**
  - *LM:* on all three models, no setting deviates from the monotone fit
    at the 1% level; 0-1 of 264 neighbouring pairs is reversed by more
    than 2 standard errors.
  - *316L:* in published melt-pool measurements from 11 single-track
    studies (MeltpoolNet), depth and width grow with power and fall with
    speed in every study; 5 of 942 neighbouring pairs reverse by more than
    2 standard errors.
- **Live runs:** the certifier queried SmolLM2 directly in five runs.
  Each used 8.0k generations and certified 59-65 of the 78 safe settings
  (62.8 on average) and no unsafe one. Twenty runs on the measured surface
  at the same budget certify 59-69 (64.3 on average). The benchmark's
  shortcut (drawing outcomes from the measured surface) therefore matches
  querying the model.

### The five pointers you set, and where each stands

| Pointer | Status |
|---|---|
| 1. Near-optimal algorithm | Done. The search is within O(log n) and a multiple-testing factor of a matching-shape lower bound (Theorems 2-4). Measured gap 4.2-14.8x. Whether the log N part of the gap is necessary is stated as open. |
| 2. ML-native application | Done. Sampling settings of three language models, failure rates measured from real generations: SmolLM2-135M on 12² and 23² grids, Qwen2.5-0.5B and Qwen2.5-1.5B on 12². Live runs (the certifier querying the model directly) agree with the surface runs. 7B models need a GPU (section 10). |
| 3. Airtight proofs | Done to the level we can check ourselves. Appendix A has full proofs, no open "[check]" items; the growth condition (T) needed for termination is explicit and checked numerically. Recommended: one independent read by a statistician (section 10). |
| 4. Real data and stronger baselines | Language model: real data. Manufacturing: no public data with repeated builds exists, so the AM problems are simulated; we test the monotonicity assumption on published data and show the gains survive calibration changes. Baselines: Learn-then-Test (fixed sequence), Bonferroni grid, GP level set (plain and with the ordering), BEAM-style active search, SafeOpt-style safe expansion. |
| 5. Final paper | Written, compiled, within the page limit, anonymized, with supplement. What remains needs your input (section 10). |

---

## 4. What was done, in order

Condensed; the dated detail is in [`ROADMAP.md`](ROADMAP.md).

- **2026-10-24: start.**
  - First version: single-setting betting test (`exp01`), a grid
    certifier using chains of settings (`pwcert/certify.py`, `exp02`), and
    a scaling experiment (`exp03`).
  - Oracle and bounds experiments (`exp04`, `exp05`).
  - A Rosenthal melt-pool simulator for 316L (`pwcert/physics.py`).
  - First drafts of the lower bounds (notes 4-5).
- **2026-11-12: the method takes its final form.**
  - The cone rule replaced the chains: closed testing with e-processes,
    validity in three lines, spreading and pooling built in.
  - Ensemble weights from perturbed simulators.
  - Optimistic allocation, which fixed a stall where one near-threshold
    setting absorbed 40k trials.
  - Pilot-study side information for the "no simulator" case.
  - A two-drug dose scenario (`pwcert/dose.py`).
  - An oracle upper bound via Wald's identity.
  - Edge allocation became the default (1.3-2.5x better than greedy).
  - GP baseline; monotonicity audit; paper draft v0.
- **2026-11-13: reframed for ICML** as "safe operating regions" with the
  language-model application first.
  - The fixed-confidence search (note 9) and the theory appendix.
  - Found and fixed an error in the fixed-confidence lower bound (see
    section 6).
  - Learn-then-Test baseline. LaTeX paper with a verified bibliography.
  - Measured the SmolLM2-135M surface: 12 x 12 settings, 160 generations
    each, 78 of 144 settings safe. Ran the LM benchmark.
  - Proofs completed, with the growth condition (T) made explicit.
  - GP with the monotone closure. The nested 23 x 23 grid (529 settings).
- **2026-11-14: submission pieces.**
  - Impact Statement, Appendix B, and the anonymous supplement builder.
  - Number audit against the result files (fixes in section 6).
  - BEAM-style and safe-expansion baselines.
  - The 316L sensitivity sweep, which replaced the calibration we could
    not do.
  - Tried to tighten the search toward the lower bound: no gain.
  - Second model, Qwen2.5-0.5B. Figure 1 redone on the 23 x 23 grid. GP
    worst-case validity.
- **2026-11-15: you told us there is no LPBF data and no compute budget.**
  - Checked the literature: MeltpoolNet cannot give failure rates, but can
    test the monotonicity assumption, which it supports.
  - Compute plan with GPU scripts; noted that surfaces were measured in
    the checkpoints' bfloat16 precision.
  - Reviewer FAQ, submission metadata, the "between grid points" remark.
  - Started measuring Qwen2.5-1.5B on CPU.
- **2026-11-15 to 2026-11-19.**
  - The 1.5B measurement was interrupted three times. Twice the cloud
    session was idle and its machine was reclaimed; once a 2-hour limit
    on background jobs stopped it. It is resumable, was resumed each
    time, and finished on 2026-11-19.
  - Added a helper that prints the table rows for any measured model
    (`scripts/lm_table_rows.py`).
  - This record.
  - A new experiment on correlated trials within a build plate
    (`experiments/plate_effects.py`). Result: the paper's analysis
    breaks under plate correlation; two valid fixes, now in Section 6
    and Appendix B.
  - Qwen2.5-1.5B finished. It is the third model in Tables 1-2:
    - 88 of 144 settings safe;
    - 1.6x fewer generations than no ordering at half the safe region,
      3.0x at 70%;
    - the search stops at 2.1x fewer generations than the per-setting
      test.
  - More live runs on SmolLM2 (seeds 1-4) and a script that sets them
    next to surface runs (`experiments/lm_live_summary.py`).

---

## 5. Decisions and the reasons for them

- **A fresh start, independent of the LIME/RUL work.** You asked for it;
  nothing in `process_window/` reuses that code or those results.
- **Reframed from "AM process windows" to "safe operating regions", with the
  language model first.** ICML reviewers need an ML-native application. The
  method is the same; AM and drug screening become the second and third
  applications.
- **Family-wise error (FWER), not false discovery rate (FDR).** A
  certificate is a safety claim: one unsafe setting in it is a failure. FDR
  would allow a fraction of unsafe settings, which an engineer qualifying a
  process cannot use.
- **Grids, not continuous knobs.** The continuous version (old "Theorem 2")
  was dropped. The "between grid points" remark covers continuous knobs
  for free: a grid cell is covered once each mode's riskiest corner is
  certified.
- **Edge rule aims at 0.7 times the tolerance.** It was 1.3-2.5x better
  than greedy area-per-trial allocation, and close to the oracle.
- **The search starts at the edge the side information predicts.** It is
  6-14% cheaper than the alternative. Table 2 was re-run with this rule
  after the audit caught a mismatch.
- **Probe time-outs in the search.** They keep validity, make the search
  stop surely, and cost completeness only when a target probe times out
  (1 of 24 synthetic runs).
- **Manufacturing stays simulated.** No public dataset repeats builds at
  each setting, so failure *rates* cannot come from the literature.
  Instead:
  - a 316L sensitivity sweep shows the gains do not hinge on the
    placeholder calibration;
  - published melt-pool data test the monotonicity assumption itself.
- **MeltpoolNet is not redistributed.** Its repository has no licence
  file. The script downloads it, checks the file's hash and runs.
- **LM failure judges:**
  - repetition: the fraction of repeated 4-grams > 0.2;
  - incoherence: the model's own mean token NLL > 3.5 nats;
  - tolerance 10%.

  These are standard automatic proxies. The gains hold over seven
  alternative definitions. A task-level judge is future work (tier C in
  the compute plan).
- **Language models run in their checkpoint precision (bfloat16)**, with
  scores computed in float32. Stated in Appendix B.
- **Supplement:**
  - Leaves out logs, notes, drafts and the early `exp0*` scripts.
  - Uses an MIT licence as a placeholder.
  - The build refuses to finish if any name, local path, e-mail address
    or tool name remains.

---

## 6. Mistakes found and fixed

Kept here so that the history is honest and nobody re-introduces them.

- **Fixed-confidence lower bound (2026-11-13).**
  - Two terms were added that can share the same trials, which overstated
    the bound.
  - Now one joint convex program (`pwcert/bounds.py`). Search-to-bound
    ratios became 4.2-13.5 instead of 4-8.
- **Table 2 did not reproduce (2026-11-14).**
  - The search's start rule had changed after the runs.
  - The original rule (start at the predicted edge) is cheaper, so it is
    the default again. The 23² LM figure is 52.1k, not 51.8k.
- **Number audit (2026-11-14):**
  - Fixed-sequence testing helps full grids by 17-37%, not more.
  - The GP sentence was corrected.
  - Ablation signs were corrected.
  - The LM monotonicity check now uses an exact binomial test.
- **Abstract overclaim (2026-11-14).** "GPs err in 2.5-27.5% even at their
  most cautious" was no longer true once BEAM-style search showed a tuning
  near 5%. Rewritten to the accurate statement: a tuning that works on one
  problem fails on another.
- **Bibliography.** The `beam2026` entry had both volume and number
  (bibtex warning). The number was removed.
- **Precision statement (2026-11-15).** Loading a model with no precision
  argument keeps the checkpoint's bfloat16, not float32. The code comments
  and Appendix B now say so.
- **A 32 x 32 search median (2026-11-14).** The cheaper "midpoint probe"
  median included the one run with a probe time-out, so it is not reported
  as a gain.

---

## 7. Repository map

All paths are relative to `process_window/`.

```
PROJECT_RECORD.md   this file
README.md           code overview; the table of commands that reproduce
                    every table and figure
ROADMAP.md          phases, open questions, and the dated log
COMPUTE_PLAN.md     GPU tiers A-C, costs, how to run
requirements.txt    numpy, scipy, matplotlib, pytest, pandas
requirements-lm.txt torch, transformers, datasets (only to measure LMs)

pwcert/             the library
  eprocess.py       betting e-processes ("failure rate < eps"), hedge of a
                    plug-in bet and a fixed menu of bets
  cone.py           ConeCertifier: cone rule, weights, edge allocation,
                    re-checks, futility; cone_sum (the cumulative sums)
  search.py         SearchCertifier: the fixed-confidence search
  bounds.py         lower bounds (ordered: joint convex program; unordered)
  baselines.py      full grid + Bonferroni; full grid + fixed-sequence (LTT)
  gp_baseline.py    GP level set; options: monotone closure, BEAM-style
                    active search, SafeOpt-style safe expansion
  synthetic.py      Scenario class; synthetic window with controllable
                    simulator error
  physics.py        Rosenthal melt-pool model of 316L (lack of fusion,
                    keyhole, balling)
  dose.py           two-drug toxicity / non-response, Bliss prior
  lm.py             load a causal LM; generate and score (rep-4, NLL)
  lm_scenario.py    LM benchmark built from a measured surface
  pilot.py          pilot-study side information
  certify.py        the earlier chain certifier (kept for exp01-exp05)
  audit.py          the monotonicity audit

experiments/        one script per table or figure (commands in README.md)
  final.py          validity, curves, scaling, bounds, ablations, GP runs,
                    figure plotting (sub-commands)
  exp_search.py     fixed-confidence runs (Table 2, Figure 3)
  exp_lm.py         all language-model benchmark parts
  lm_surface.py     measure an LM surface (resumable)
  lm_live.py        live run: the certifier queries the model directly
  lm_figure.py      Figure 1
  lm_sensitivity.py LM failure-definition sensitivity
  physics_sensitivity.py  316L calibration sensitivity
  violation.py      monotonicity violations and the audit
  am_monotone_check.py    published 316L melt-pool monotonicity check
  plate_effects.py  correlated trials within a build plate (new)
  paper_figs.py     Figures 2-3 from the CSVs
  exp01-exp05       early exploratory experiments (not in the paper)

tests/              63 unit tests (validity checks included); ~1 minute
scripts/
  make_supplement.py  builds the anonymous archive dist/supplement.zip
  gpu_runs.sh         all GPU language-model runs in one command
  lm_table_rows.py    prints Tables 1-2 rows for any measured model
paper/
  latex/            main.tex, references.bib, figs/, ICML 2026 style files
  draft_v1.md       Markdown mirror of the paper
  appendix_theory.md  proofs in plain text
  draft.md          older v0 draft (superseded)
  reviewer_faq.md, submission_metadata.md
notes/              study notes, in reading order:
  01 betting and Ville's inequality   02 problem statement (v0)
  03 multiple testing                 04 findings of week 1
  05 lower bound                      06 the cone rule
  07 upper bound                      08 overnight research log
  09 the search theorem
results/
  final/            CSVs and logs for the simulated problems
  lm/               measured surfaces (surface_scores*.npz), LM CSVs, logs
  exp0*             early experiments
```

---

## 8. Results index: which file backs which claim

| Paper item | Result files (in `results/`) |
|---|---|
| Table 1, synthetic and 316L rows; Figure 2 | `final/scaling_toy-good.csv`, `final/scaling_lpbf-good.csv`, `final/scaling_grid_baselines.csv` |
| Table 1, LM rows | `lm/lm_cost_50.csv` (12²), `lm/lm_cost_50_23.csv` (23²), `lm/lm_cost_50_qwen05b.csv`, `lm/lm_cost_50_qwen15b.csv`; 70% versions `lm_cost_70*` |
| Table 2, synthetic; Figure 3 | `final/fixed_confidence*.csv`, `final/bounds.csv` |
| Table 2, LM rows | `lm/lm_fixed_confidence.csv`, `_23`, `_qwen05b`, `_qwen15b` |
| Figure 1 | `lm/surface_scores_23.npz`, `lm/lm_fixed_budget_23.csv` |
| Validity (0-2.75%) | `final/validity.csv`, `final/validity_edge.csv` |
| Area-vs-budget curves (24²) | `final/curves_*_24.csv` |
| GP baselines | `final/gp_baseline*.csv`, `final/gp_validity.csv`, `lm/lm_gp*.csv` |
| Ablations | `final/ablation_*_16.csv` |
| Monotonicity violations | `final/violation.csv` |
| LM monotonicity check | `lm/lm_monotone_check*.csv` |
| LM failure-definition sensitivity | `lm/lm_sensitivity.csv` |
| 316L sensitivity | `final/physics_sensitivity_24.csv` |
| Published 316L melt-pool check | `final/am_monotone_check.csv` |
| Live LM runs | `lm/lm_live_seed0.json` ... `seed4.json`, summary `lm/lm_live_summary.csv` |
| Measured LM surfaces | `lm/surface_scores.npz` (SmolLM2 12²), `_23.npz` (23²), `_qwen05b.npz`, `_qwen15b.npz` |
| Correlated trials on a plate (Section 6, Appendix B) | `final/plate_effects_{single,cost,grid}.csv` |

Each `log_*.txt` next to a CSV is the console output of the run that made it.

---

## 9. How to run everything

### Set-up

- Python 3.10 or newer (tested with 3.13). From `process_window/`:
  ```bash
  pip install -r requirements.txt          # core
  pip install -r requirements-lm.txt       # only to measure language models
  python3 -m pytest -q tests               # 63 tests, about a minute
  ```
- LaTeX: TeX Live with `latex-extra`. On Ubuntu:
  `apt-get install texlive-latex-extra`. Without it the paper falls back
  to a plain two-column layout.

### Build the paper

```bash
cd paper/latex
pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Check the main text still ends by page 8. Look for where "Impact Statement"
starts in the PDF.

### Build the anonymous supplement

```bash
python3 scripts/make_supplement.py      # writes dist/supplement.zip
```
It stops with an error if anything identifying is left in a text file. To
check the archive works: unzip it somewhere, `pip install -r
requirements.txt`, run `python3 -m pytest -q tests`.

### Re-run an experiment

The table "Reproducing the paper" in [`README.md`](README.md) gives the
exact command, output file and run time for every table and figure. Two
practical rules:

- **Thread settings.** Put `OMP_NUM_THREADS=1` in front of the benchmark
  scripts. They are single-threaded numpy and run slower with thread
  contention. Run several at once instead.
- **Measuring a language model:**
  - Set `HF_HOME` to a cache folder with a few GB free.
  - The surface script saves after every setting and resumes where it
    stopped: if it dies, run the same command again.
  - On a GPU, add `--device cuda --dtype bfloat16 --batch 160`.

### Add a new language model to the paper

1. Measure it (one line per grid in `scripts/gpu_runs.sh`, or on CPU):
   ```bash
   HF_HOME=<cache> python3 experiments/lm_surface.py --model <hf-name> --tag <tag> --threads 4
   ```
2. Run the analyses, four in parallel with `OMP_NUM_THREADS=1`:
   ```bash
   python3 experiments/exp_lm.py --parts cost         --surface results/lm/surface_scores_<tag>.npz
   python3 experiments/exp_lm.py --parts confidence   --surface results/lm/surface_scores_<tag>.npz
   python3 experiments/exp_lm.py --parts check,budget --surface results/lm/surface_scores_<tag>.npz
   python3 experiments/exp_lm.py --parts gp           --surface results/lm/surface_scores_<tag>.npz
   ```
3. Print the rows to paste into Tables 1-2, plus the safe-region size and
   the monotone check:
   ```bash
   python3 scripts/lm_table_rows.py --suffix _<tag> --label "<Name>"
   ```
4. Update in `main.tex`:
   - the table rows and captions;
   - the Setup paragraph (model list, safe-region size, monotone check);
   - the fixed-budget and fixed-confidence sentences;
   - Limitations ("two small models");
   - Appendix B (model, measurement time).

   Mirror the changes in `paper/draft_v1.md`, then rebuild the PDF and
   the supplement.

### Things that bit us

- **Cloud sessions.** A long run started in a cloud AI session can be
  killed when the session goes idle or hits a background time limit. On a
  machine you control (laptop, lab server, cloud VM), use `nohup` or
  `tmux`; it then runs until done. All long scripts can be resumed.
- **Style files.** The ICML style needs `forloop.sty` from `latex-extra`.
- **Downloads.** Hugging Face downloads are anonymous. Set `HF_TOKEN` only
  if you hit rate limits.

---

## 10. What is left

### A. Needs you (no one else can do these)

| Item | Why | Where |
|---|---|---|
| Deadline | ICML 2027 call for papers, expected around late January 2027. Confirm abstract and full-paper dates. | icml.cc |
| Co-authors | Every author needs an OpenReview profile before the deadline. A statistician co-author would also give the proofs an independent read. | openreview.net |
| Licence for the code | MIT is a placeholder in the supplement. | `scripts/make_supplement.py` (the `LICENSE` string) |
| Page range of Waudby-Smith & Ramdas (2024) | The only unchecked reference detail (JRSS B 86(1); pages unknown because the publisher page could not be reached). | `paper/latex/references.bib`, key `waudbysmith2024betting` |
| ICML 2027 style files | Drop `icml2027.sty` and `icml2027.bst` into `paper/latex/` when released; `main.tex` picks them up. Re-check the page count. | `paper/latex/` |
| Reviewer duty | Recent ICMLs asked authors to review. Check the call. | call for papers |
| Compute (optional) | Tier A (three 7B models) is about 10 GPU-hours, roughly $15-40. | `COMPUTE_PLAN.md` |
| Merge the branch | Keep this work safe on the default branch (section 1). | GitHub |

### B. Mechanical steps before submitting

Listed in [`paper/submission_metadata.md`](paper/submission_metadata.md)
(checklist at the bottom):

- Switch to the 2027 style.
- Re-run the anonymity checks on the PDF and the archive.
- Check the page count.
- Upload the PDF and `dist/supplement.zip`.

### C. In progress or ready to run

- **GPU tier A**: `bash scripts/gpu_runs.sh` on one 80 GB GPU. It adds 7B
  rows on both grids and live runs on a 7B model. Details in
  `COMPUTE_PLAN.md`.
- **Live runs on a larger model.** For example Qwen2.5-0.5B on CPU:
  ```bash
  HF_HOME=<cache> python3 experiments/lm_live.py --model Qwen/Qwen2.5-0.5B --surface results/lm/surface_scores_qwen05b.npz --seed 0
  ```
  This takes about 2x longer than SmolLM2. On a GPU it is part of tier A.

### D. Status of the newest items

See the bottom of this file ("Latest status"); it is updated at the end of
each working session.

---

## 11. Submitting without help: a step-by-step plan

1. **Now:** merge the branch (section 1). Read `paper/latex/main.pdf` end
   to end once, and `paper/reviewer_faq.md`.
2. **Decide** co-authors and the code licence. Create the OpenReview
   profiles.
3. **Fix** the one reference detail (Waudby-Smith page range: search the
   journal site or Google Scholar for "Estimating means of bounded random
   variables by betting", JRSS B 2024).
4. **Optional:** get GPU time and run tier A (`scripts/gpu_runs.sh`), then
   add the rows ("Add a new language model", section 9). Without it, the
   paper stands as is.
5. **When the ICML 2027 style is out:** drop it in, rebuild, and make sure
   the main text is at most 8 pages. If it overflows, the easiest cuts are
   the ablation paragraph and the long GP paragraph (shorten; the numbers
   are in Appendix B and the CSVs).
6. **Anonymity:**
   - `pdfinfo main.pdf` (author must say Anonymous Authors).
   - `pdftotext main.pdf - | grep -i <your name>` must find nothing.
   - `python3 scripts/make_supplement.py` must finish without error.
7. **On OpenReview:** title, abstract, TL;DR, keywords and primary area
   are in `paper/submission_metadata.md`. Upload the PDF and
   `dist/supplement.zip`.
8. **After reviews:** start from `paper/reviewer_faq.md`. Every answer
   points to the file with the evidence. Extra runs reviewers often ask
   for are cheap on CPU (more seeds, more live runs, other thresholds).

If ICML does not work out:

- `ROADMAP.md` names two fallbacks:
  - an applied venue (Additive Manufacturing, Journal of Manufacturing
    Systems), with the AM part expanded and the LM part shortened;
  - an ICML workshop.
- The same paper also fits NeurIPS, AISTATS or UAI with little change.

---

## 12. Ideas for later work

- **Real LPBF failure rates.** The method needs replicate coupons per
  setting (say 4-8 per setting, CT or metallography per coupon). With a
  real plate study, the AM part becomes a real-data case study. ROADMAP.md
  lists the questions that would shape it (outcome type, coupon type,
  coupons per plate, balling direction).
- **Correlated trials on a plate.** The paper now shows the problem and
  two valid fixes (Section 6, Appendix B). Two next steps:
  - With a known upper bound on the plate correlation, a deflated
    per-trial e-value could recover most of the per-trial efficiency.
  - A smarter plate-aware allocation could cut the 2.4x price, because
    the current rule fills spare plate slots with re-checks.
- **Task-level LM failures.** For example, format violations or an LLM
  judge on chat prompts (tier C in `COMPUTE_PLAN.md`).
- **Theory:**
  - Is the log N multiple-testing factor necessary for a family-wise
    guarantee?
  - Can the search close the remaining gap to the lower bound (now
    4-15x)?
- **More than two knobs.** The code assumes a 2-D grid; the theory does
  not.

---

## 13. Glossary

- **Tolerance (ε, eps).** The highest acceptable failure rate for a mode
  (10% in the LM study).
- **Safe region (W).** The settings where every mode's rate is below its
  tolerance.
- **Certified region (C).** What the method returns. The guarantee:
  P(C contains an unsafe setting) ≤ α = 5%.
- **Family-wise error (FWER).** The chance of *any* false certificate in
  the whole region.
- **E-process / betting wealth.** A running score that, if the setting were
  unsafe, would reach 1/α only with probability at most α, however long you
  watch it. Valid at any stopping time.
- **Ville's inequality.** The fact behind the line above.
- **Closed testing.** A classic way to test many hypotheses with family-wise
  control. The cone rule is closed testing restricted to the combinations
  monotonicity allows.
- **Cone (of a setting, for a mode).** All settings at least as risky for
  that mode.
- **Edge rule.** The fixed-budget allocation: test the riskiest settings of
  the region you expect to certify.
- **Search / probe.** The fixed-confidence algorithm: along each row, test
  one setting at a time (a probe) until it is certified or rejected, and
  move by galloping and bisection.
- **Lower bound (ordered / unordered).** The fewest trials any valid method
  could need, with and without using monotonicity.
- **Side information / simulator / pilot.** Anything known in advance about
  the rates. It steers the trials and never affects validity.
- **Learn-then-Test (LTT), fixed-sequence testing (FST).** The standard way
  to control risk over a fixed grid of settings. Our full-grid baseline.
- **GP level set, BEAM, SafeOpt.** Model-based baselines. They fit a
  Gaussian process and certify where it is confident; they have no
  guarantee if the model is wrong.
- **seq-rep-4.** The fraction of repeated 4-grams in a generation (the
  repetition judge).
- **NLL.** Mean negative log-likelihood per token under the model itself
  (the incoherence judge).
- **Condition (T).** A checkable property of the bet menus that makes every
  search probe end. It holds at every tolerance used (5-50%).

---

## Latest status

(Updated at the end of each working session.)

- Qwen2.5-1.5B: done 2026-11-19, in Tables 1-2 and the text.
- Plate-correlation experiment: done 2026-11-18, in the paper.
- Live runs: five (seeds 0-4), done 2026-11-19, in the paper.
- Nothing is running. Everything is committed and pushed.
