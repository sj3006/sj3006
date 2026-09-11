# Diagnosability limits of in-situ monitoring in LPBF

Working folder for a CIRP conference submission.

**One line:** before anyone trains another defect classifier, work out from physics
which faults a given sensor package could possibly tell apart, and show that some
pairs are hopeless regardless of the algorithm.

| File | Contents |
|---|---|
| `01-vision.md` | Project vision, problem statement, what the paper claims |
| `02-abstract.md` | Submission abstract, title options, keywords |
| `03-technical-stack.md` | Chronological method stack: algorithms and their objectives |
| `04-timeline.md` | Twelve-week plan, go/no-go gates, cut order |
| `05-risks-and-decisions.md` | Risks, decisions already made, open questions |
| `06-literature-landscape.md` | Novelty check results: what is occupied, what is not |

## Status

Planning complete. Nothing implemented yet.

**Before submitting the abstract**, do the one outstanding check in
`05-risks-and-decisions.md` (novelty search on "structural analysis fault
isolation" terminology).

## Constraints this plan was built under

- No physical experiments of any kind. Everything is computational.
- No dependency on any external dataset. This was a deliberate choice after
  two candidate datasets failed on access or novelty grounds — see
  `06-literature-landscape.md`.
- Runs on a laptop. No GPU, no licensed solver, no cluster.
- Target: roughly twelve weeks from start to submission.
