# Record of the work

This document is the complete account of what was done in this directory, what
was found, what was created, and where each item is kept. It is written to be
read without access to the conversations in which the work was carried out. It
indexes the more detailed documents rather than repeating them; every statement
of a result below is backed by a file named next to it.

Repository: `sj3006/sj3006`, branch `claude/lucid-feynman-bqpmqw`, directory
`cirfcms2027/`. Period covered: 11 September to 19 November 2026, 107 commits
(listed in `docs/commit-history.md`).

Authors of the papers: Soham Jain and Tribeni Roy, Department of Mechanical
Engineering, Birla Institute of Technology and Science Pilani. The analysis,
code and drafts were produced with Claude Code, an AI coding assistant, working
under the authors' direction; each paper carries a declaration to that effect.
Decisions that were taken by the assistant without the authors' input are
recorded with their reasons in the documents named in Section 7.

A self-contained package for sharing and replicating the work is in
`replication/` (Section 8).

---

## 1. The subject

Laser powder bed fusion machines carry coaxial instruments (a photodiode, a melt
pool camera, a pyrometer) that observe the melt pool during a build. The
literature maps these signals onto defects. The question taken up here is one
step upstream: which process **causes** the instruments can tell apart in
principle, what a diagnostic system is entitled to claim from them, and how
accurate the model underlying such a system must be. The work is simulation
only. A thermal model (Eagar–Tsai with a keyhole depth correction), calibrated
on seven published single-track measurements of nickel alloy 718, generates the
instrument signals under five faults: laser power deviation, scan speed error,
powder layer thickness deviation, shielding gas degradation and local heat
accumulation from part geometry.

## 2. The three papers

| | conference paper | certificate paper | fidelity paper |
|---|---|---|---|
| title | Which process faults can be told apart? Diagnosability limits of in-situ monitoring in laser powder bed fusion | What a monitoring agent is entitled to conclude: identifiability limits for fault diagnosis in laser powder bed fusion | Validated for prediction, unverified for diagnosis: how accurate a digital twin must be to attribute process faults in laser powder bed fusion |
| venue | Procedia CIRP (submitted) | journal, to be chosen | journal, to be chosen |
| state | submitted | complete draft except the language-model results (Section 4.7), which await the authors' decision on API access | first full draft |
| source | `paper/paper.tex`, `overleaf/` | `certificate/paper/paper.tex` | `fidelity/paper/paper.tex` |
| code | `src/`, `run_all.py` | `certificate/` | `fidelity/` |
| summary of results | `README.md` | `certificate/FINDINGS.md` | `fidelity/FINDINGS.md` |
| number check | `repro/check.py`: 234 of 234 | `certificate/claims.py`: 76 of 76 | `fidelity/claims.py`: 71 of 71 |
| theory check | | `certificate/verify.py`: 32 of 32 | `fidelity/verify.py`: 16 of 16 |

Each "number check" compares every number printed in a paper with a fresh
computation and passes only if the computed value rounds to the printed one.
The counts above were obtained by running the checks on 19 November 2026.

### 2.1 Conference paper: main results

1. Laser power and shielding gas degradation are exactly confounded at a single
   instant: both act only on the absorbed power, so no instrument separates
   them. The structural analysis finds the same pair from equation form alone.
2. The binding limit is the melt pool, not the instrumentation. All faults
   funnel into four physical channels; seven candidate observables reach rank 3
   against that bound of 4.
3. Build context the machine already records (toolpath, layer index, gas-flow
   direction, local geometry) raises the rank from 3 to 5 and the worst fault
   pair from 0.00 to 24.90 degrees.

### 2.2 Certificate paper: main results

1. Diagnosis written as a hypothesis test, with the unknown fault severity
   profiled out, gives for each candidate cause a residual with an exact
   chi-squared distribution; the causes not rejected form a confidence set (the
   certificate) with exact coverage.
2. The ten-degree separation floor of the diagnosability literature is an
   assumption about signal strength: it corresponds to a whitened
   signal-to-noise ratio of 28.1.
3. A three-instrument suite at one instant names a unique cause in 3.5 % of
   builds; a maximum-likelihood estimator from the same data is right 44.0 % of
   the time; with build context the unique-cause rate is 95.3 %.
4. The power–gas confound is a theorem of the channel factorisation, and
   deliberate probing cannot remove it.

### 2.3 Fidelity paper: main results

1. The certificate depends on the twin only through the directions in which
   faults move the instruments. A directional error reduces coverage by an exact
   amount, and the admissible error shrinks in inverse proportion to the signal:
   1.62 degrees at the signal the ten-degree floor implies, and 0.24 to 0.29
   degrees with build context.
2. Validation against melt-pool geometry does not secure this. The models the
   benchmark data accept as equally good disagree with the calibrated model by a
   median of 22.5 degrees and with one another by 30.1 degrees.
3. Quantities used only by diagnosis (the noise model, an omitted scattering
   channel, the numerical resolution of the instrument model) change no
   prediction yet move the directions by amounts comparable to the budget.
4. Directions can be measured rather than modelled: four commanded steps as
   strong as the fault keep the certificate within its coverage target at every
   signal strength.

## 3. Chronology

| period | work | where recorded |
|---|---|---|
| 11 Sep to 11 Oct | planning, novelty check, choice of alloy and calibration data | `00`–`06` numbered documents, `05-risks-and-decisions.md` |
| 11 Oct to 12 Oct | forward model, calibration (passes at 11.7 % width and 13.0 % depth error), faults, sensors, quantitative diagnosability, build-context route | `src/`, `explainers/01`–`04`, `05-risks-and-decisions.md` |
| 12 Oct to 22 Oct | literature extraction, corrections to the model's domain and noise model, physical fault definitions, diagnosability matrices, added-sensor route, first figures | `07-literature-extraction.md`, `explainers/`, commit history |
| 22 Oct to 3 Nov | conference draft, robustness tests, removal of vendor names, errata and their application, noise derived from transduction physics, reproduction harness | `08-paper-draft.md`, `10-errata-and-draft-2-changes.md`, `repro/` |
| 5 Nov to 17 Nov | manuscript re-verification; final figures and text edits for the conference paper | `paper/`, `overleaf/`, commit history |
| 15 Nov to 18 Nov | certificate paper: statistical core, exact profile test, case generator, agent backends and scoring, channel factorisation, draft with seven appendices | `certificate/ROADMAP.md`, `certificate/FINDINGS.md` |
| 18 Nov to 19 Nov | fidelity paper: theory, twin families, three study runs, findings, draft | `fidelity/LABNOTEBOOK.md` (dated entries 1–6) |

## 4. What was created

### 4.1 Code

| directory | content | entry points |
|---|---|---|
| `src/` | forward model, calibration, faults, sensors, noise derivation, diagnosability analysis, structural analysis, robustness and validation studies, figure scripts for the conference paper | `run_all.py --list` describes every stage |
| `repro/` | claim registry and recomputation for the conference paper (234 claims) | `repro/check.py` |
| `certificate/` | inference, case generation, equivalence classes, agent backends, benchmark, probe analysis, results pipeline, figures, claim registry, verification | `certificate/results.py`, `verify.py`, `claims.py` |
| `fidelity/` | twin parameterisation, twin families, the study, convergence and floor checks, results pipeline, figures, claim registry, verification | `fidelity/README.md` lists every module |
| `tools/` | maintenance scripts for this record and for the replication package | `tools/commit_history.py`, `tools/build_replication.py` |

### 4.2 Data generated

No data was downloaded into the repository. All generated data comes from the
code above and can be regenerated by it.

| file | produced by | content |
|---|---|---|
| `certificate/results.json` | `certificate/results.py` | every number the certificate paper quotes |
| `fidelity/_region.json` | `fidelity/twins.py` | 2048 sampled parameter sets with their fit to the benchmark data |
| `fidelity/_study.json` | `fidelity/study.py` | 301 twins scored on prediction and diagnosis (final run, 961 grid) |
| `fidelity/_results.json` | `fidelity/results.py` | every number the fidelity paper quotes |
| `fidelity/_grid.json`, `_floor.json`, `_sloppy.json` | the corresponding scripts | grid convergence, numerical floor, the failed local analysis |
| `fidelity/_study_grid121.json`, `_study_grid481.json`, `_results_grid481.json` | earlier runs | superseded study runs, kept as the record of entries 3 and 4 |
| `fidelity/_jacobians*.json` | `fidelity/study.py` | Jacobian caches for the three runs |

The fidelity files begin with an underscore because the working directory treats
them as caches; the committed copies are in `replication/data/generated/`, with
a description of each file's structure.

### 4.3 Documents

The numbered documents `00` to `10` are the conference paper's planning and
working record; `explainers/` holds eleven first-principles explanations of the
method; `docs/measured-inputs.md` lists every outside measurement;
`docs/sources-consulted.md` lists the web searches made; `docs/commit-history.md`
lists every commit. Each paper has its own roadmap and findings document, and
the fidelity paper has a dated laboratory notebook.

## 5. Data from outside the project, and sources consulted

Every number the code takes from a published article is listed in
`docs/measured-inputs.md` with the article, the table and the module that holds
it: melt-pool widths and depths of seven single tracks and the pad depths under
gas cross-flow from the 2022 Additive Manufacturing Benchmark (Weaver et al.,
2024), powder absorptivity measurements, and the other cited constants. These
are the numbers a reader checking the work should check first, since the
reproduction harnesses verify that the papers and the code agree but cannot
verify that either agrees with the article.

Web searches were used to locate and check references. Those made from 15
November onward are listed individually, with every link returned, in
`docs/sources-consulted.md`; earlier searches are described in
`06-literature-landscape.md`, `07-literature-extraction.md` and
`09-data-wanted.md`. Publisher sites and doi.org were not reachable from the
working environment, so no full text was opened; references were checked against
publisher landing pages and catalogue records found by search, and those that
could not be confirmed are marked in the bibliographies.

## 6. Findings that affect earlier work, and corrections

The conference paper's errata, with the original text, the defect and the
correction for each, are in `10-errata-and-draft-2-changes.md`; the reproduction
harness found nine numbers in the draft that no longer reproduced, all corrected
before submission (`repro/README.md`).

The fidelity work found three things that bear on the two earlier papers. They
are recorded in `fidelity/FINDINGS.md` and have not been applied to those papers:

1. The instrument model's default 121 x 121 quadrature grid places fault
   directions up to 0.97 degrees from their converged values, and the quoted
   pairwise angles shift by up to 0.60 degrees. No separability verdict changes.
   The certificate paper's build-context results require directions accurate to
   about 0.25 degrees, so its model should use a grid of at least 961 x 961.
2. Absorptivity, conductivity and heat capacity are not separately identifiable
   from melt-pool geometry: the model is exactly invariant under a common scaling
   of the three, which is why the calibrated conductivity and heat capacity sit
   on their bounds.
3. Both earlier papers generated and interpreted observations with the same
   model; the certificate's exact coverage holds only under that condition.

Corrections made within the fidelity work itself are listed in
`fidelity/LABNOTEBOOK.md`, entry 6.

## 7. Decisions taken without the authors

The fidelity paper was carried out on the instruction to proceed on best
judgement without input. Every decision so taken (the choice of truth model, the
validation region, the grid, the families added and dropped) is in
`fidelity/LABNOTEBOOK.md` with its reason and how to reverse it. The certificate
paper's open decision, on access to language-model services for Section 4.7, is
in `certificate/ROADMAP.md`.

## 8. The replication package

`replication/` is a formal, self-contained copy of everything needed to
reproduce the three papers: the code, the published inputs, the generated data,
the papers' sources, a pinned environment, scripts that run each pipeline and
compare the results with the shipped data, and a manifest with a SHA-256
checksum for every file. It can be copied out of the repository and shared on
its own. It is rebuilt from the working directories by
`tools/build_replication.py`, so it does not drift from them. Its
`README.md` is the starting point.

The package was tested on 19 November 2026 from a fresh unpacked copy outside
the repository: every check passed, and the certificate and fidelity results,
regenerated from scratch, agreed with the shipped data. The details are in
`replication/VERIFICATION.md`.

## 9. Open items

* Fidelity paper: choice of journal; abstract to be shortened to the journal's
  limit; two references to verify (`fidelity/paper/refs.bib`).
* Certificate paper: Section 4.7, pending the decision on language-model access;
  rerun on the converged instrument grid.
* Conference paper: whether to issue a correction for the grid finding (no
  verdict changes; quoted angles move by up to 0.60 degrees).
* No licence has been chosen for the code and documents. One must be added
  before the replication package is shared publicly.
