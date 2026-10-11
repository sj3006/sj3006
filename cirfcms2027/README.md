# Diagnosability limits of in-situ monitoring in LPBF

Working folder for a CIRP conference submission.

**One line:** before anyone trains another defect classifier, work out from physics
which faults a given sensor package could possibly tell apart, and show that some
pairs are hopeless regardless of the algorithm.

| File | Contents |
|---|---|
| `00-explainer.md` | **Start here.** Plain-language reference for anyone unfamiliar with the work |
| `01-vision.md` | Project vision, problem statement, what the paper claims |
| `02-abstract.md` | Submission abstract, title options, keywords |
| `03-technical-stack.md` | Chronological method stack: algorithms and their objectives |
| `04-timeline.md` | Twelve-week plan, go/no-go gates, cut order |
| `05-risks-and-decisions.md` | Risks, decisions already made, open questions |
| `06-literature-landscape.md` | Novelty check results: what is occupied, what is not |

## Status

Abstract **accepted**. Three-week build sprint, in progress.

Implemented: `src/eagar_tsai.py` (forward thermal model) and
`src/sanity_checks.py` (day-1 verification). Directional sweeps pass, and the
Weaver et al. depth-versus-width observation is reproduced — see day-1 findings in
`05-risks-and-decisions.md`.

Novelty check complete — see `05-risks-and-decisions.md`. The claim holds, with
positive evidence on two of three legs. No blocking items remain before abstract
submission.

## Constraints this plan was built under

- No physical experiments of any kind. Everything is computational.
- **No dependency on any external dataset.** Deliberate, after two candidates
  failed on access or novelty grounds (`06-literature-landscape.md`). The model
  generates the sensor signals; published papers are corroboration, not input.
  What the project needs instead is 4-6 published melt pool measurements for the
  absorptivity fit — see the Gate 1 calibration source in
  `05-risks-and-decisions.md`.
- **Alloy: IN718.** Decided; rationale in `05-risks-and-decisions.md`.
- Runs on a laptop. No GPU, no licensed solver, no cluster.
- **Three-week sprint** (revised from twelve weeks part-time). Nothing removed
  from the methodology; ~9-10 h/day, six days a week. See `04-timeline.md`.
