# Risks, decisions and open questions

## Novelty check — CLOSED

Run and resolved. The claim survives, and on stronger footing than "searches
returned nothing". The evidence has three legs, two of them positive.

**Leg 1 — the method is mature elsewhere, with a named toolkit.** Structural
analysis is the standard FDI route to determining observability, fault
detectability and diagnosability from model structure alone. Established
machinery: bipartite graph of the model equations, Dulmage-Mendelsohn
decomposition, Minimal Structurally Overdetermined (MSO) sets for residual
generation, Binary Diagnostic Matrix, and a formal weak/strong isolability
distinction. Published algorithms compute which sensors to add to meet a stated
isolability requirement.

Applied domains to cite:
- Anti-lock braking systems — pmc.ncbi.nlm.nih.gov/articles/PMC6308433
- Automatic transmission clutch faults — structural-analysis sensor placement
- Hydraulic torque converters — pmc.ncbi.nlm.nih.gov/articles/PMC6308526
- Permanent magnet traction drives — pmc.ncbi.nlm.nih.gov/articles/PMC11086266
- Wind turbine hydraulic pitch systems — arxiv.org/pdf/2312.09018
- Sensor placement for FDI — orbilu.uni.lu/bitstream/10993/4479/1/0161.pdf

**Leg 2 — AM fault diagnosis is active but exclusively data-driven.** This is the
strongest leg: the field is working the same problem with a different toolset, so
the question is demonstrably live rather than uninteresting.
- MAFN multi-view adaptive fusion network for AM fault diagnosis,
  sciencedirect.com/science/article/pii/S0888327025013810
- Multimodal sensor fusion for AI-based fault detection in 3D printing (Feb 2026),
  arxiv.org/pdf/2602.16108
- Online fault detection for metal AM with data-driven time series models,
  link.springer.com/chapter/10.1007/978-3-031-94895-4_2
- Survey of image-based fault monitoring in AM,
  pmc.ncbi.nlm.nih.gov/articles/PMC10422627
- Review of fault diagnosis: traditional ML to LLM fusion,
  pmc.ncbi.nlm.nih.gov/articles/PMC12846000

None is model-based. None asks what the sensors can resolve in principle.

**Leg 3 — the intersection is empty.** Diagnosability, isolability and structural
analysis searched together with additive manufacturing return LPBF defect-
detection papers and unrelated mechanical-structure work. No formal diagnosability
analysis for this process.

**Claim this licenses:** a mature FDI method, with an established toolkit and a
decade of automotive and aerospace application, has never been applied to a
process where fault diagnosis is otherwise an active data-driven research area.
Keep the wording "not previously used in additive manufacturing" in the abstract.

**Framing note.** Leg 2 should appear in the introduction. It converts the
contribution from "nobody did this" (weak, unprovable) into "the field works this
problem with a toolset that cannot answer the in-principle question" (strong,
citable).

## The three real risks

**Thermal model does not match published melt pool dimensions.**
Discovered at Gate 1, week 3 — early enough to recover. Mitigation: switch to a
simpler analytical form and accept wider error bars.

**Photodiode radiometry harder than expected.**
Discovered at Gate 2, week 6. Mitigation: use melt pool area as the photodiode
proxy, which is what the literature says photodiodes actually correlate with.

**No citable sensor noise figures.**
Mitigate by gathering these in week 1, not week 6. If they genuinely do not exist,
run the analysis parametrically across a range of noise levels and report the
threshold at which each confusion appears. That is arguably a better result than a
single matrix.

## Review risks

**Overclaiming novelty.** The method is mature elsewhere. Claim a first
application, not a new method. Reviewers punish overclaiming much harder than
modest scope.

**"Why do I need this when fusion models already hit 99%?"** The answer, which
should appear in the introduction: those accuracies are per-study on
self-selected class sets, and a 99% number on a chosen set says nothing about what
a configuration resolves in general.

**"Your fault modes are not what people monitor for."** Partly true and it is the
motivation, not a weakness. The field classifies outcomes; operators need causes,
because an outcome says something went wrong while a cause says what to change.
Put this in the introduction rather than waiting for review.

**"Classifiers already report 99%, so faults are clearly separable."** The most
likely objection. Full answer in `01-vision.md` under "Causes, not outcomes" —
different question, mostly outcome classes, often binary detection, usually large
magnitude separations, and confusions do appear where confusable classes are
included.

**Fault normalisation is arbitrary.** It partly is. Justify the fractional-
deviation choice explicitly and show the main conclusions survive a different
normalisation.

**Gas flow fault is thinly supported.** No published work identifies gas flow
faults from melt pool signals, so there is no corroboration available for this one
and it is the hardest of the five to model credibly. Keep it but state the
uncertainty, and do not put it in a headline claim. If a reviewer pushes hard, it
is the fault to drop.

## Decisions already made

| Decision | Rationale |
|---|---|
| No external dataset | Two candidates failed — see `06-literature-landscape.md`. Removing the dependency removes the only failure mode outside our control. |
| Analytical thermal model, not FE | Need speed and smooth derivatives, not fidelity. Also avoids any solver licence. |
| One calibrated parameter (absorptivity) | Defensible. Multi-parameter tuning invites the curve-fitting objection. |
| Complex-step derivatives | Exact to machine precision, trivial to implement, model is analytic. |
| Angles, not distances, for isolability | Magnitude-independent. A distance threshold depends on how big you made each fault. |
| LDA only for the ML step | Optimal under linear-Gaussian assumptions, so its errors are determined by the geometry. A neural net would let reviewers blame architecture instead of physics. |
| Noise from published specs, not a dataset | Keeps the abstract true regardless of data access. |

## Open questions for the supervisor

1. Which alloy — 316L has more published melt pool data, IN718 has AM-Bench.
2. Target venue and word limit, which decides whether the abstract is trimmed.
3. Whether active excitation (route C) should be in this paper or held back.
4. Author list and affiliations.

## Things deliberately not in scope

Multi-material. Part-scale thermal history. Microstructure. Closed-loop control
design. Any experimental validation. Acoustic sensing (modelling acoustic emission
from a thermal model is not credible — say so if asked rather than faking it).
