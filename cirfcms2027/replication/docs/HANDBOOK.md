# Handbook: finishing and implementing the three papers

This handbook is written so that the authors can finish all three papers, and
take the work towards a real machine, without access to Claude or any other
assistant. It says where everything is, how to run and change it without
breaking the papers, exactly what remains to be done on each paper and how to
do it, and how each result would be implemented and tested on real equipment.

It complements, and does not repeat, three other documents:

* `RECORD.md`: what was done, found and created, and where it is kept.
* `conversations/`: the full written record of the conversation in which most
  of this was produced, with every request and every reply verbatim.
* `replication/`: the formal, self-contained package for sharing the work.

Status at the time of writing (19 November 2026): the conference paper is
submitted; the certificate paper is a complete draft except its Section 4.7;
the fidelity paper is a first full draft.

---

## Contents

1. Getting set up
2. Where everything is
3. Rules that keep the papers correct
4. The conference paper: status and remaining work
5. The certificate paper: status and remaining work
6. The fidelity paper: status and remaining work
7. Taking the work to a real machine
8. Directions for further papers
9. Open decisions, in one list
10. Known inconsistencies to fix
11. Glossary
12. Troubleshooting

---

## 1. Getting set up

**Repository.** All work is in the GitHub repository `sj3006/cirpcms2027`, a
copy of the directory `cirfcms2027/` of `sj3006/sj3006` (branch
`claude/lucid-feynman-bqpmqw`) with its full history. Either may be used; the
dedicated repository is the simpler one to share and continue.

    git clone https://github.com/sj3006/cirpcms2027.git
    cd cirpcms2027

**Python.** Python 3.10 or later, with numpy 2.0 or later, scipy and
matplotlib. The versions used for every result are pinned in
`replication/environment/requirements.txt`.

    python3 -m venv .venv
    . .venv/bin/activate                    # Windows: .venv\Scripts\activate
    pip install -r replication/environment/requirements.txt

**LaTeX.** A TeX distribution with the Elsevier `elsarticle` class (TeX Live,
MiKTeX or Overleaf). Each journal paper builds with

    pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper

and the conference paper, whose bibliography is inline, with three runs of
`pdflatex`.

**First check.** Before changing anything, confirm that the copy works:

    bash replication/scripts/check_all.sh

This takes about ten minutes and must end with "All checks passed".

---

## 2. Where everything is

| what | where |
|---|---|
| conference paper, repository copy | `paper/paper.tex` (single column), `overleaf/paper.tex` (two-column Procedia layout) |
| conference paper, submitted version | **your Overleaf project** (see Section 4.1) |
| conference code | `src/` (model and analyses), `run_all.py` (every stage in order) |
| conference number check | `repro/check.py` (234 printed numbers) |
| certificate paper | `certificate/paper/paper.tex`, `refs.bib` |
| certificate code | `certificate/` (`results.py` computes, `verify.py` checks the theory, `claims.py` checks the text) |
| fidelity paper | `fidelity/paper/paper.tex`, `refs.bib` |
| fidelity code | `fidelity/` (its `README.md` lists every module) |
| results summaries | `README.md` (conference), `certificate/FINDINGS.md`, `fidelity/FINDINGS.md` |
| laboratory notebook of the fidelity work | `fidelity/LABNOTEBOOK.md` |
| every outside measurement used | `docs/measured-inputs.md` |
| every web search made | `docs/sources-consulted.md` |
| first-principles explanations of the method | `explainers/` |
| conference errata and their reasons | `10-errata-and-draft-2-changes.md` |
| conversation record | `conversations/` |

---

## 3. Rules that keep the papers correct

The single most important practice in this project is that **no number is
typed into a paper by hand**. Each paper has a chain:

    code  ->  results file  ->  claim registry  ->  paper text

| paper | compute | results file | check the text |
|---|---|---|---|
| conference | (computed inside the check) | `repro/` | `python3 repro/check.py --no-cache` |
| certificate | `python3 certificate/results.py` | `certificate/results.json` | `python3 certificate/claims.py` |
| fidelity | `fidelity/study.py`, then `results.py` | `fidelity/_results.json` | `python3 fidelity/claims.py` |

A claim passes only if the computed value rounds to the printed one at the
precision printed. So:

* **To change a number in a paper**, change the code or the input, rerun the
  compute step, then edit the text to the new value, then run the claim check.
* **To add a new number to a paper**, add it to the results script, then add a
  claim for it: in `repro/claims.py` (conference), `certificate/claims.py`, or
  `fidelity/claims_registry.py`. Copy an existing entry; each records the
  string as printed, the value, where it comes from and what it means.
* **Before committing**, run the theory check and the claim check for the paper
  you touched. Every past error that reached a draft in this project was a
  number that drifted between code and text.

Other standing conventions, from the authors' instructions during the work:

* Formal, conservative, plain academic register; no conversational phrasing.
* No em-dashes in paper text.
* No company or product names in the papers; describe configurations by their
  content.
* Explanations from first principles with real numbers (see `CLAUDE.md`, which
  records the standard).
* Sentence-case headings.

---

## 4. The conference paper

*Which process faults can be told apart? Diagnosability limits of in-situ
monitoring in laser powder bed fusion.* Procedia CIRP, submitted.

### 4.1 Important: the submitted text is in Overleaf, not in this repository

The repository's `paper/paper.tex` and `overleaf/paper.tex` were last changed
on 3 November 2026. All later text changes were made by the authors in their
Overleaf project, using replacement text supplied in the conversation. The
repository therefore does **not** contain the submitted wording. The figures
added later (`paper/fig8_noise_chain.png` and the `fig9` set) are in the
repository.

**Action:** download the submitted version from Overleaf (Menu, Download,
Source) and commit it to `paper/` (or to a new directory such as
`paper/submitted/`), so that the repository holds the version under review.
Then run `python3 repro/check.py --no-cache`; if a printed number was changed in
Overleaf, the check will name it.

Every replacement text supplied in the conversation is preserved verbatim in
`conversations/`:

| date | request | file |
|---|---|---|
| 10 Nov | reduce space between headings and text | `conversations/2026-11-10.md` |
| 10 Nov | remove bold text at the source | `conversations/2026-11-10.md` |
| 16 Nov | LaTeX to make all italic text upright | `conversations/2026-11-16.md` |
| 17 Nov | reference for "previous studies classified defects"; as BibTeX | `conversations/2026-11-17.md` |
| 17 Nov | reference for the monitoring-sensors sentence | `conversations/2026-11-17.md` |
| 17 Nov | whether the power–speed sentence is needed | `conversations/2026-11-17.md` |
| 17 Nov | structural analysis section simplified, then rewritten formally | `conversations/2026-11-17.md` |
| 17 Nov | meaning of slopes, curvatures, entries; of s, k and l in the equations | `conversations/2026-11-17.md` |
| 17 Nov | replacement for the word "whitened"; condition-number explanation | `conversations/2026-11-17.md` |
| 17 Nov | compressing Section 3.6 and the results into figures; new Section 4.5 text and figure scripts | `conversations/2026-11-17.md` |
| 17 Nov | formal rewrite of a section; where to trim a quarter page | `conversations/2026-11-17.md` |
| 17 Nov | Section 5.2 with a paragraph cut; whether Section 2.2 is needed; Section 2.1 with a sentence added | `conversations/2026-11-17.md` |

### 4.2 If reviewers respond

Most likely questions, and where the answer already is:

| likely question | where the answer is |
|---|---|
| Is the thermal model adequate? | paper's limitations section; `explainers/06-the-base-case.md`; `src/conduction_baseline.py` |
| Where do the noise ratios come from? | `explainers/11-deriving-sensor-noise.md`; `src/noise.py`; Appendix A of the certificate paper |
| The modulation profiles are assumed | `src/profile_robustness.py` (half strength, 120 reassignments, wrong driver up to 84 %) |
| Is power–gas confounding an artefact? | it is exact (both act on absorbed power); certificate paper, Appendix E (the channel factorisation), proves it |
| Comparison with published accuracies | `src/commercial.py`, `07-literature-extraction.md` |
| Numerical accuracy | the grid finding below |

**The grid finding.** The fidelity work found that the instrument model's
default 121 x 121 grid places fault directions up to 0.97 degrees from their
converged values; the pairwise angles quoted in this paper move by up to 0.60
degrees (for example 4.31 to 3.80, 4.63 to 4.03). No separability verdict
changes, because every pair is far from the ten-degree floor. If a reviewer
asks about numerical convergence, or if a revision is invited, the honest course
is to report the converged values. To produce them, change the default
`n_grid` in `src/sensors.py` (`SensorConfig`) from 121 to 961, rerun
`repro/check.py --no-cache`, and update every number it reports as changed.
Expect the run to take several times longer.

---

## 5. The certificate paper

*What a monitoring agent is entitled to conclude: identifiability limits for
fault diagnosis in laser powder bed fusion.* Complete draft, 32 pages, seven
appendices; `verify.py` 32 of 32, `claims.py` 76 of 76.

Target journals considered in the conversation (15 November): Journal of
Manufacturing Systems (strongest fit), Advanced Engineering Informatics,
Robotics and Computer-Integrated Manufacturing, Journal of Intelligent
Manufacturing, or the AI-Empowered Manufacturing Processes special issue. The
International Journal of Machine Tools and Manufacture was judged a poor fit
without experiments.

### 5.1 Remaining work, in order

**(a) Section 4.7, the language-model arms.** The only missing result. The
harness, prompts, parser and scoring are built and tested; what is needed is a
language-model service account. `certificate/run_llm_arms.py` runs it:

    export ANTHROPIC_API_KEY=...            # your own key; never commit it
    cd certificate
    python3 run_llm_arms.py --dry-run --n-per-cell 3      # checks the pipeline, no cost
    python3 run_llm_arms.py --model MODEL_NAME --n-per-cell 10

`MODEL_NAME` is the provider's identifier for the model to test. There are
`n_per_cell x 20` cases and three calls per case (unconstrained with a neutral
prompt, unconstrained with an operator-style prompt, and certified). Start with
`--n-per-cell 10` (600 calls) and check the cost with the provider. Every reply
is saved in `llm_replies.json`, so a run can be rescored later without new calls
(`--rescore`). Scores go to `llm_results.json` and print as a table beside the
deterministic arms (oracle, maximum likelihood, certificate, everything,
chance), which bracket them.

For several providers, add a `Backend` subclass to `agents.py` following
`AnthropicBackend` (a `complete(prompt) -> text` method) and register it in
`BACKENDS` in `run_llm_arms.py`.

Then write Section 4.7: replace the red "[Pending.]" paragraph in
`paper/paper.tex` (line about 656) with the results, report over-attribution
(how often a model names fewer causes than the certificate allows),
admissibility and coverage for each arm and prompt, and add the new numbers as
claims in `certificate/claims.py`. The paper's introduction already states what
the agent is and is not for; keep the results consistent with it.

**(b) Two design decisions** recorded in `certificate/ROADMAP.md`: whether to
add a "no fault" option (it changes the test to a composite null and is a
second test, not a sixth column), and whether the build-context regime needs its
own prompt (its coefficient matrix does not read naturally as prose; the driver
offers only the instantaneous regime for this reason).

**(c) Rerun on the converged grid.** The fidelity work showed that build-context
results require directions accurate to about 0.25 degrees, while the 121-cell
grid used here is up to 0.97 degrees off. Before submission, rerun with
`n_grid = 961` (see Section 4.2 for where to change it), rerun `results.py`
(longer than the current four minutes), run `claims.py`, and update the numbers
it flags. The headline unique-attribution rates may move; the theorems will
not.

**(d) References.** `Chen2025` (flagged in `refs.bib`: its DOI could not be
resolved during the work) must be checked against the publisher's page, and
`Grasso2021` needs its volume and article number filled in, before submission.

**(e) Format for the chosen journal**, check length and abstract limits, and
add the cover letter.

---

## 6. The fidelity paper

*Validated for prediction, unverified for diagnosis: how accurate a digital twin
must be to attribute process faults in laser powder bed fusion.* First full
draft, 23 pages; `verify.py` 16 of 16, `claims.py` 71 of 71. Written without the
authors' input on their instruction to proceed on best judgement; every
decision so taken is in `fidelity/LABNOTEBOOK.md` with its reason.

### 6.1 Remaining work

1. **Read the draft and the notebook**, and reverse any decision you disagree
   with. The notebook says how to reverse each.
2. **Choose the journal.** The draft is written for Journal of Manufacturing
   Systems or Advanced Engineering Informatics; the theory would also suit
   Mechanical Systems and Signal Processing.
3. **Shorten the abstract** from about 330 words to the journal's limit
   (usually 250). Every number in it is checked by `claims.py`; keep them.
4. **Verify two references** in `fidelity/paper/refs.bib`: the National
   Academies report's DOI (10.17226/26894, written from memory) and the ASME
   V&V 40 entry (checked only from secondary descriptions).
5. **Decide whether to strengthen three points** that the limitations section
   currently concedes:
   * the validation region is cut off by the calibration's bounds at the truth's
     diffusivity; widening the bounds in `fidelity/twins.py` (`BOX_LO`,
     `BOX_HI`) and rerunning would show the full region;
   * observations are linear in the truth; generating them from the full
     model would combine twin error with model curvature;
   * few sampled twins have prediction errors below 2 %, so whether 2 % is
     sufficient precision is open; sampling more densely near the best fit
     (for example along the band in Figure 3) would settle it.
6. **Rerun everything after any change**: `bash replication/scripts/reproduce_fidelity.sh`
   (about 70 minutes on four cores) regenerates every output, the tables and the
   figures, checks the text and compares with the previous outputs.

### 6.2 How the paper's argument is built, for revising it

Theorem 1 (only directions matter) and Theorem 2 (exact coverage under a
directional error) give the requirement; the Corollary turns it into a budget
that shrinks as 1/rho; Propositions 3 to 5 cover verdicts, noise-model errors
and build context; Proposition 6 gives the constructive alternative. The study
then shows validation does not meet the requirement (Section 5.1), that
prediction error is a weak indicator (5.2), how accurate a twin must be (5.3),
what diagnosis-only quantities do (5.4), the build-context case (5.5) and the
grid (5.6). Proofs are in `fidelity/theory.py` docstrings and the appendix; each
result has a simulation check in `fidelity/verify.py`.

---

## 7. Taking the work to a real machine

None of the three papers involved experiments. This section sets out how the
results would be implemented and tested on a laser powder bed fusion machine
with coaxial monitoring, in the order the steps depend on each other. Numbers
are those of the calibrated model and the papers' conventions, and are starting
values to be replaced by measurement.

### 7.1 What is needed

* A machine with a coaxial photodiode, a melt-pool camera reporting area (or
  width and length), and a two-colour pyrometer, all logged synchronously with
  the scan position.
* The build context the controller already records: layer index, position in
  the toolpath, scan direction relative to the gas flow, and local geometry
  (overhang, wall thickness). The certificate paper's build-context result
  depends on these.
* Control over laser power, scan speed, layer thickness and, if available,
  build-plate preheat, for the commanded steps of Section 7.3.
* Cross-sections of single tracks for calibration, as in the benchmark data
  (`replication/data/input/weaver2024_table4_single_tracks.csv`).

### 7.2 Step 1: measure each instrument's noise

The papers derive the relative noise of the three instruments from their
transduction physics, as 1 : 0.142 : 1.061 (photodiode : camera area :
pyrometer), under one assumption: every radiometric channel has the same
fractional noise. On a real machine this is measured directly. Record each
instrument over many nominally identical segments of a healthy build, compute
the standard deviation of the relative signal, and use those values in place of
the derived set. The fidelity paper's Proposition 4 shows why this matters:
underestimating the noise by 25 % reduces the 95 % certificate's coverage to
85 %, whatever the signal; overestimating it is safe.

### 7.3 Step 2: measure the fault directions with commanded steps

The fidelity paper's main constructive result (Proposition 6): the test needs
only the direction in which each fault moves the readings, and that direction
can be measured. For each fault that can be commanded, change the input by a
fixed step, record the change in the three readings relative to the healthy
baseline, divide each by its noise (Step 1), and average over repeats. Four
repeats at a step as strong as the faults to be diagnosed keep the certificate
at 90 % coverage or better at any signal strength.

Steps that give the paper's reference signal strength (rho = 28) at a 1 %
fractional noise, from the calibrated model:

| fault | commanded step | notes |
|---|---|---|
| laser power | 3.2 % | directly commanded |
| scan speed | 9.4 % | directly commanded |
| powder layer thickness | about 9 % thicker layer | the layer couplings are defined per unit change in log layer thickness (`src/faults.py`, `src/layer_couplings.py`) |
| shielding gas | not commanded: same direction as power in the model | a power step measures it, unless plume scattering is present (fidelity paper, Section 5.4) |
| part geometry (heat accumulation) | 43 K local preheat | a heated build plate can impose it |

Compare the measured directions with the model's: the angle between them is the
model's directional error, and the fidelity paper's budget (1.6 degrees at rho
= 28, about 0.25 degrees with build context) says whether the model is good
enough. If it is not, use the measured directions in the test directly.

### 7.4 Step 3: run the certificate during a build

For each monitored segment:

1. Compute the relative change of each reading from its healthy baseline,
   `dy_s / y_s`, and divide by that instrument's noise to get `z_w`
   (three numbers).
2. For each candidate fault `k`, with unit direction `u_k` from Step 2 (or the
   model), compute the residual `R_k = |z_w|^2 - (z_w . u_k)^2`.
3. Report every fault with `R_k <= 5.991` (the 95 % point of chi-squared with
   two degrees of freedom, for three instruments). That set contains the true
   cause 95 % of the time.
4. If the set has more than one member, report all of them; naming one is not
   supported by the data. If it is empty, the observation is not explained by
   any single listed fault.

With build context, the readings of a group of segments are first regressed on
the known context, and the test is applied to the coefficients (fourteen
degrees of freedom; threshold from chi-squared with fourteen degrees of
freedom). `certificate/inference.py` implements both regimes.

### 7.5 Step 4: validate against deliberately induced faults

The test of the whole chain, and the experiment proposed on 15 November as the
route to a machine-tools journal: build plates with known induced faults
(commanded power and speed offsets, a deliberately mis-set recoater, throttled
shielding gas, geometry with overhangs) and check that the certificate covers
the induced cause at its stated rate, and how often it names a unique cause.
This also measures the modulation profiles that the conference paper assumes
(`src/profile_robustness.py` describes the assumptions).

### 7.6 Data that would improve the papers without new experiments

`09-data-wanted.md` lists, in order of value, published datasets and full texts
that could not be reached from the working environment and that the authors can
obtain through a library or by email.

---

## 8. Directions for further papers

On 15 November ten directions for extending the conference paper were set out;
the full text is in `conversations/2026-11-15.md`. In brief: (1) the certificate
and agent benchmark, which became the certificate paper; (2) the fidelity a
digital twin needs, which became the fidelity paper; (3) probe planning and its
ceiling, included in the certificate paper; (4) identifiability of the twin's
own parameters, partly answered by the fidelity paper's symmetry finding;
then experimental validation with induced faults, measured noise, a
suite-design procedure (minimum instrumentation for a required fault set),
consequences for closed-loop control, achievability (Fisher information and a
Cramér–Rao bound), and a structured literature review. The experimental
programme of Section 7 is the natural next paper, and the one that would suit
the International Journal of Machine Tools and Manufacture.

---

## 9. Open decisions, in one list

| paper | decision |
|---|---|
| conference | whether to report converged-grid angles if a revision is invited |
| certificate | whose account runs the language-model arms, and how many providers |
| certificate | whether to add a "no fault" option |
| certificate | whether the build-context regime gets its own prompt |
| certificate | journal |
| fidelity | journal; abstract length; whether to strengthen the three conceded points of Section 6.1 |
| all | licence for the code and documents before public sharing (`replication/LICENSE-NOTICE.md`) |

---

## 10. Known inconsistencies to fix

* `src/faults.py`, the `FaultState` docstring, gives values at `f = 1` (for
  example "local preheat +600 K") that do not match the current coupling
  constants in `FaultCouplings` (100 K per unit for geometry). The code uses the
  constants; the docstring is out of date. Correct it, then run
  `repro/check.py` to confirm nothing else changed.
* The conference paper's repository copy lags the submitted Overleaf version
  (Section 4.1).
* `fidelity/LABNOTEBOOK.md` entry 2 gives the budget at rho = 14 as 3.24
  degrees and words one noise example the wrong way round; entry 6 records both
  corrections, and the paper has the correct values.

---

## 11. Glossary

| term | meaning |
|---|---|
| fault direction, signature | the change in the three instrument readings, each divided by its noise, that a small fault produces; a column of the whitened Jacobian |
| whitened | divided by the noise, so that every reading is in units of its own noise and a distance of 1 means one standard deviation |
| Jacobian | the matrix of relative sensitivities: rows are instruments, columns are faults, entry = (1/y) dy/df |
| folded angle | the angle between two lines (ignoring sign), from 0 to 90 degrees; two faults with a small angle are hard to tell apart |
| rho | the length of the whitened signal: how strong a fault looks in units of noise |
| separation floor | the ten-degree angle below which the diagnosability literature treats two faults as indistinguishable; the certificate paper shows it corresponds to rho = 28.1 |
| certificate | the set of faults whose residual is below the threshold; contains the true cause with the stated probability |
| coverage | how often the certificate contains the true cause; 95 % by design if the model is right |
| build context | what the machine already records about each segment (layer, toolpath, geometry), used as regressors |
| twin, truth | in a twin experiment, the model that interprets the data and the model that generates it |
| validation-equivalent twin | a parameter set the benchmark data cannot reject, by the nonlinear-regression F-test |
| budget | the largest directional error that keeps coverage at 90 %: 1.62 degrees at rho = 28 |
| prediction-only, diagnosis-only, shared | the fidelity paper's classes of model quantity (Table 1 of that paper) |
| claim registry | the list of every printed number with the value it must round to |

---

## 12. Troubleshooting

| problem | cause and remedy |
|---|---|
| `AttributeError: module 'numpy' has no attribute 'trapezoid'` | numpy older than 2.0; install the pinned versions |
| a claim check fails after a code change | a printed number moved; read the failure, decide whether the change is intended, update the text or revert the code |
| `claims.py` reports a number "not found in paper.tex" | the text was edited; restore the number or update the registry entry's printed string |
| the fidelity study is slow | it is about 45 minutes on four cores at the 961 grid; set `OMP_NUM_THREADS=1` so the four workers do not compete |
| results differ in the last digits on another computer | floating-point summation order; `replication/scripts/compare_outputs.py` uses a 1e-6 relative tolerance for this reason |
| directional errors below 0.17 degrees jump around | below the instrument model's numerical floor on the 961 grid; see `fidelity/LABNOTEBOOK.md`, entries 3, 4 and 6 |
| LaTeX cannot find `elsarticle` | install it (TeX Live package `elsarticle`) or build on Overleaf |
