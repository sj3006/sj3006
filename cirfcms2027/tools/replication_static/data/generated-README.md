# Generated data

Every file here was produced by the code in `../../code/`. None was downloaded.
All are JSON except the conference reproduction report, which is Markdown.
`../../scripts/use_shipped_data.py` copies the current files to where the code
reads them; `../../scripts/compare_outputs.py` compares a regenerated file with
the copy here.

## conference/

| file | produced by | content |
|---|---|---|
| `REPORT.md` | `code/repro/check.py` | the 234 numbers printed in the conference paper: printed value, recomputed value, kind (computed or taken from a source), and what each means |

The conference paper has no other shipped output: `check.py --no-cache`
recomputes everything from the model in about four minutes.

## certificate/

| file | produced by | content |
|---|---|---|
| `results.json` | `code/certificate/results.py` | every number the certificate paper quotes |

Top-level keys: `meta` (draws, cases per cell, alpha, noise convention, signal
levels, fault and sensor names, run time); `geometry` (whitened noise levels and
pairwise angles at one instant and with build context); `floor` (the separation
floor and the signal each pair needs); `channels` (the factorisation J = MC: the
channel matrices, factorisation error, rank, the exact power–gas relation, the
null direction, the weakness of the preheat channel); `probing` and
`probing_best` (worst and second-worst pair angles under operating-point
probing); `linearisation` (departure of the linearised from the exact test);
`certificates` (size and coverage of the certificate, by regime and signal);
`benchmark` (the deterministic diagnostic arms and their scores);
`admissibility` (how often each arm's answer is in the certificate);
`appendix` (the instrument-model derivations).

## fidelity/

Final run, instrument-model grid 961 x 961.

| file | produced by | content |
|---|---|---|
| `_region.json` | `code/fidelity/twins.py` | the validation region: `rows` holds 2048 Sobol samples as [absorptivity, conductivity, heat capacity, profiled keyhole coefficient, sum of squared relative residuals]; also the calibrated model's sum of squares, the minimum, the acceptance threshold, the seed |
| `_study.json` | `code/fidelity/study.py` | `rows`: one record per twin (301), with family, name, the twin's parameters, prediction error against the truth (`pred_rms`, `pred_max`), error against the benchmark data (`amb_*`), directional error per fault (`delta`) and its maximum, pairwise angle changes (`dtheta`), verdict changes at one instant and with build context (`flips_*`, `false_sep_*`), certificate coverage at four signal levels (`cov_inst`, `cov_big`); also the build-context gains and the region summary |
| `_results.json` | `code/fidelity/results.py` | every number the fidelity paper quotes: the family table, statistical tests, controls, the spread among accepted twins, tolerances, depth groups, the precision envelope, theory constants, the grid and floor checks, and the scores of every named twin |
| `_grid.json` | `code/fidelity/grid_convergence.py` | the calibrated model's Jacobian at grids 121, 241, 481 and 961, the directional change and pairwise angles at each, and the operating-point scan at grids 121 and 481 |
| `_floor.json` | `code/fidelity/floor_check.py` | the largest directional error of seven twins at grids 961 and 1921; the difference is the numerical floor |
| `_sloppy.json` | `code/fidelity/sloppy.py` | the local linearised precision analysis; **a recorded negative result, not used in the paper** (see the laboratory notebook, entry 6) |
| `caches/_jacobians.json` | `code/fidelity/study.py` | the 288 Jacobians (3 instruments x 5 faults) computed in the final run, keyed by every quantity the Jacobian depends on |

### fidelity/superseded/

Earlier runs, kept because the laboratory notebook (entries 3 and 4) reports and
explains them. They are not used by the paper.

| file | content |
|---|---|
| `_study_grid121.json`, `_jacobians_grid121.json` | first run, 275 twins, instrument grid 121 x 121 |
| `_study_grid481.json`, `_results_grid481.json`, `_jacobians_grid481.json` | second run, 301 twins, grid 481 x 481 |
