# Replication package: diagnosability, certified diagnosis and twin fidelity in laser powder bed fusion

This package contains everything required to reproduce the results of three
related papers by Soham Jain and Tribeni Roy (Department of Mechanical
Engineering, Birla Institute of Technology and Science Pilani):

1. **Conference paper.** *Which process faults can be told apart? Diagnosability
   limits of in-situ monitoring in laser powder bed fusion.* Procedia CIRP,
   submitted.
2. **Certificate paper.** *What a monitoring agent is entitled to conclude:
   identifiability limits for fault diagnosis in laser powder bed fusion.*
   Journal manuscript in preparation.
3. **Fidelity paper.** *Validated for prediction, unverified for diagnosis: how
   accurate a digital twin must be to attribute process faults in laser powder
   bed fusion.* Journal manuscript in preparation.

The work is computational. A thermal model of the melt pool, calibrated on
published measurements, generates the signals of three coaxial monitoring
instruments under five process faults. The papers analyse which faults those
signals can distinguish, construct a statistical test that returns the set of
causes consistent with an observation, and determine how accurate the model
must be for that test to remain valid. No experiments were performed for this
work and no external dataset is required to run it.

Package version: 1.0. Built 2026-11-19 from commit `83396ae` of the
source repository.

---

## 1. Contents

| directory | content |
|---|---|
| `code/` | all source code, laid out as in the source repository so that the relative imports work unchanged |
| `data/input/` | every measured value taken from published work, with its source, in machine-readable form |
| `data/generated/` | every output the code produced for the papers, including superseded runs |
| `papers/` | the three papers: LaTeX source, bibliography, figures and compiled PDF |
| `docs/` | the record of the work, findings, laboratory notebook, literature notes and sources consulted |
| `environment/` | pinned package versions and the computing environment |
| `scripts/` | verification and reproduction scripts |
| `MANIFEST.tsv` | every file in the package with its size and SHA-256 checksum |
| `VERIFICATION.md` | the record of testing this package from a fresh copy |
| `LICENSE-NOTICE.md` | licensing status |
| `CITATION.md` | how to cite the papers and the data |

## 2. Requirements

Python 3.10 or later with numpy (2.0 or later), scipy and matplotlib. The exact
versions used are pinned in `environment/requirements.txt`:

    python3 -m venv .venv && . .venv/bin/activate
    pip install -r environment/requirements.txt

Rebuilding the papers additionally requires a LaTeX installation with the
Elsevier `elsarticle` class. Details and measured run times are in
`environment/ENVIRONMENT.md`.

## 3. Verifying the package (about ten minutes)

    bash scripts/check_all.sh

This script:

1. checks every file against `MANIFEST.tsv`;
2. copies the shipped outputs from `data/generated/` to the locations where the
   code reads them;
3. recomputes the 234 numbers printed in the conference paper from the model and
   compares each with the printed value;
4. runs the 32 simulation checks of the certificate paper's theory;
5. compares the 76 numbers printed in the certificate paper with its shipped
   results file;
6. runs the 16 simulation checks of the fidelity paper's theory and compares the
   71 numbers printed in that paper with its shipped results file.

A printed number passes only if the computed value rounds to it at the precision
printed. The script stops at the first failure.

## 4. Reproducing the results from scratch

Each script regenerates one paper's outputs from the model, checks the printed
numbers against the new outputs, and compares the new outputs with the shipped
ones.

| paper | command | time | regenerates |
|---|---|---|---|
| conference | `bash scripts/reproduce_conference.sh` | 4 min | every printed number; `--full` also runs every analysis stage (15 min) |
| certificate | `bash scripts/reproduce_certificate.sh` | 10 min | `results.json` and the figures |
| fidelity | `bash scripts/reproduce_fidelity.sh` | 70 min | the validation region, the study of 301 twins, the convergence and floor checks, the results file, the tables and the figures |

Outputs are written inside `code/`. The comparison uses a relative tolerance of
1e-6 (see `environment/ENVIRONMENT.md` on determinism).

To rebuild a paper after reproducing it, run LaTeX in the paper's directory
under `code/` (for example `code/fidelity/paper/`), or copy the regenerated
figures into the corresponding directory under `papers/`.

## 5. Code

| directory | paper | content | main entry points |
|---|---|---|---|
| `code/src/` | all | forward model (`eagar_tsai.py`), calibration (`calibrate.py`), faults (`faults.py`), instruments (`sensors.py`), noise derivation (`noise.py`), diagnosability analysis (`diagnosability.py`, `structural.py`), build context (`observables.py`), robustness and validation studies, conference figures | `code/run_all.py --list` |
| `code/repro/` | conference | registry of the 234 printed numbers and their recomputation | `repro/check.py` |
| `code/certificate/` | certificate | statistical test (`inference.py`), cases, equivalence classes, agent backends, benchmark, probe analysis, results, figures, claim registry, theory checks | `results.py`, `verify.py`, `claims.py` |
| `code/fidelity/` | fidelity | twin parameterisation (`twin.py`), twin families (`twins.py`), study (`study.py`), theory (`theory.py`), convergence and floor checks, results, figures, claim registry, theory checks | `README.md` in that directory |

Each directory has its own README describing every module. The paper sources
inside `code/` (`code/certificate/paper/paper.tex`, `code/fidelity/paper/paper.tex`)
are present because the claim checks read them; they are identical to the copies
in `papers/`, as the manifest checksums show. Likewise
`code/07-literature-extraction.md` and `code/docs/measured-inputs.md` are read by
`src/literature_census.py` and `src/provenance_check.py`.

The language-model arms of the certificate paper (its Section 4.7) require
access to a commercial language-model service and have not been run; the driver
that runs them, `code/certificate/run_llm_arms.py`, is included, with a dry-run
mode that needs no network. The deterministic arms and all other results are
in the package.

## 6. Data

### 6.1 Published measurements (`data/input/`)

The model is calibrated on seven single-track melt-pool cross-sections of nickel
alloy 718 from the 2022 Additive Manufacturing Benchmark (Weaver et al., 2024,
Table 4) and uses the pad depths under gas cross-flow from the same article
(Table 5) as an external check. These values are provided as CSV files,
exported from the constants in the code by the package build, so that the two
cannot differ. `measured-inputs.md` lists every other value taken from published
work, with the article, the table and the module that holds it. The measurements
remain subject to the terms of their source articles.

### 6.2 Generated data (`data/generated/`)

Every file the code produced for the papers. `data/generated/README.md`
describes the structure of each file. The fidelity paper's study was run three
times as numerical problems were found and corrected; the two superseded runs
are kept in `data/generated/fidelity/superseded/` because the laboratory notebook
refers to them.

## 7. Documentation (`docs/`)

| file | content |
|---|---|
| `RECORD.md` | the complete record of the work: what was done, found and created, and where it is |
| `HANDBOOK.md` | how to finish the three papers and implement the work on a real machine |
| `conversations/` | the record of the conversation in which most of the work was done |
| `findings/` | the findings documents of the three papers |
| `fidelity-labnotebook.md` | dated record of the fidelity work, including errors found and corrected |
| `roadmaps/` | the plans of the certificate and fidelity papers |
| `literature/` | literature notes and the outcome-versus-cause census |
| `sources-consulted.md`, `web-lookups-2026-11.json` | every web search made during the later work, with the links returned |
| `measured-inputs.md` | every outside measurement and its source |
| `errata-conference.md` | every correction made to the conference paper's draft, with reasons |
| `explainers/` | first-principles explanations of the method |
| `project-notes/` | the conference paper's planning documents |
| `commit-history.md` | every change to the source repository |

## 8. Known limitations

The thermal model is a constant-property conduction solution with an analytic
keyhole correction fitted to seven measurements; each paper states its
limitations. Two numerical points affect reuse of the code:

* The photodiode and pyrometer models integrate over a square grid
  (`SensorConfig.n_grid`). The default of 121 cells, used by the conference and
  certificate papers, places fault directions up to 0.97 degrees from their
  converged values. No conclusion of those papers changes, but quoted angles
  carry that error. The fidelity paper uses 961 cells, within 0.17 degrees of a
  1921-cell grid. See `docs/findings/fidelity-FINDINGS.md`.
* Absorptivity, conductivity and heat capacity are not separately identifiable
  from melt-pool geometry; only absorbed power per unit conductivity and the
  diffusivity are.

## 9. Licence and citation

See `LICENSE-NOTICE.md` and `CITATION.md`.

## 10. Contact

Soham Jain (corresponding author), Department of Mechanical Engineering, Birla
Institute of Technology and Science Pilani, f20240343@pilani.bits-pilani.ac.in.
