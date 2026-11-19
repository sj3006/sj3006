# Repository overview

This repository holds two separate projects.

## 1. Certifying safe operating regions (ICML 2027 submission)

**Moved (2026-11-19):** this project now lives in its own private repository,
[sj3006/safe-operating-regions](https://github.com/sj3006/safe-operating-regions),
with its full history. The folder below is a frozen copy.

Folder: [`process_window/`](process_window/)

A method for certifying which settings of a system (laser power and speed
in metal 3D printing, sampling settings of a language model, two drug
doses) keep every failure mode rare, with a 95% guarantee and far fewer
trials than testing each setting separately.

- **Start here:** [`process_window/PROJECT_RECORD.md`](process_window/PROJECT_RECORD.md).
  It is the full record: the idea, every result, the decisions, the
  history, what is left, and a step-by-step plan to submit.
- The paper: [`process_window/paper/latex/main.pdf`](process_window/paper/latex/main.pdf)
- The code: [`process_window/README.md`](process_window/README.md)

## 2. LIME stability study (earlier, independent work)

Files at the top level of this repository (`WA_LIME_study.ipynb`, `paper/`,
`scripts/`, `limePaper/` and the Markdown reports). See
[`PAPER_PIPELINE.md`](PAPER_PIPELINE.md) and
[`RUNNING_LOCALLY.md`](RUNNING_LOCALLY.md). The `process_window/` project
does not use any of it.
