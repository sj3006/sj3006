# Verification report

The package was tested on 19 November 2026 as a recipient would use it: the zip
file `cirfcms2027-replication.zip` was unpacked into an empty directory outside
the source repository, and every script was run from there. Machine: Linux
x86-64, four cores, 16 GB memory, Python 3.13.18, numpy 2.5.3, scipy 1.18.1,
matplotlib 3.11.2.

## 1. Quick verification: `scripts/check_all.sh`

| step | result |
|---|---|
| manifest | 185 files listed, 0 discrepancies |
| conference paper, printed numbers recomputed from the model | 234 checked, 234 reproduced |
| certificate paper, theory checks | 32 of 32 passed |
| certificate paper, printed numbers against shipped results | 76 checked, 0 mismatches |
| fidelity paper, theory checks | 16 of 16 passed |
| fidelity paper, printed numbers against shipped results | 71 checked, 0 mismatches |

## 2. Reproduction from scratch

**Certificate paper, `scripts/reproduce_certificate.sh`.** All caches and the
results file were deleted and regenerated. Theory checks 32 of 32; printed
numbers 76 of 76 against the regenerated results; the regenerated
`results.json` agrees with the shipped file at relative tolerance 1e-6.

**Fidelity paper, `scripts/reproduce_fidelity.sh`.** All caches and outputs were
deleted and regenerated: the validation region (2048 samples), the study of 301
twins (2706 s on four cores), the grid convergence and numerical floor checks,
the results file, the paper's tables and the three figures. Theory checks 16 of
16; printed numbers 71 of 71 against the regenerated results. Each regenerated
file agrees with the shipped copy at relative tolerance 1e-6: `_region.json`,
`_study.json`, `_grid.json`, `_floor.json`, `_results.json`. The local
linearised analysis (`sloppy.py`), a recorded negative result not used in the
paper, was not rerun; its shipped output was used.

**Conference paper.** Step 3 of the quick verification is itself a full
recomputation of every printed number from the model, without any cache.

## 3. After the reproductions

`scripts/verify_manifest.py` was run again on the test directory after all
three reproductions: 185 files listed, 0 discrepancies. In particular the
fidelity paper's source, whose data tables are rewritten from the regenerated
results by `fill_tables.py`, came out byte-for-byte identical to the shipped
copy.

## 4. Not tested

* The conference paper's full stage-by-stage run (`reproduce_conference.sh
  --full`, which calls `run_all.py`); its numbers are covered by the
  recomputation above.
* Rebuilding the PDFs with LaTeX from inside the package. The shipped PDFs were
  built from the same sources in the source repository.
* Other operating systems, processors or library versions.
* The certificate paper's language-model arms, which are not part of the
  package.
