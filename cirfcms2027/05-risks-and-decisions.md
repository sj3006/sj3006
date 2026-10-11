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

## Day-1 implementation findings

Three things came out of getting the Eagar-Tsai module running. All verified by
running the code, not predicted.

**Weaver reproduction PASSES, on day 1.** Varying power, speed and spot size over
27 melted conditions, log-log correlation with volumetric energy density came out
depth r = +0.727, width r = +0.032. That is Weaver et al.'s reported finding
(depth tracks VED, width does not) reproduced from an analytical model. The
central claim's physics basis is confirmed against an independent published
benchmark before any diagnosability machinery exists. Keep `src/sanity_checks.py`
in the paper's reproducibility materials.

**Peak temperature is unphysical and this has a consequence.** The model gives
~12,000 K peak at 250 W / 0.8 m/s against a 3190 K vaporisation point. Expected
for constant-property Eagar-Tsai (no latent heat, no vaporisation, no melt pool
convection) and harmless for melt pool *geometry*, which came out realistic
(123 um wide, 54 um deep). But a photodiode model integrating radiance ~ T^4
would be dominated entirely by the artefact. **The Gate 2 fallback (melt pool area
as photodiode proxy) should now be treated as the baseline, not the fallback.**
Decide this before day 4, not during it.

**IN718 properties are provisional.** The values in `src/eagar_tsai.py` are
literature-typical effective near-melt figures, good enough for directional
checks. Each needs a citable source before the Gate 1 fit. Flagged in the module
docstring.

## Tier 1 structural analysis - COMPLETE, with a result

Built and run on day 2, in parallel with calibration and needing none of it.
`src/structural.py`. 11 equations, 8 unknowns, 5 faults, overall structural
redundancy 3. Exhaustive MSO enumeration (2^11 subsets, exact and instant)
finds 32 MSO sets. All five faults are structurally detectable.

**Baseline isolability.** Two directed pairs fail:
`f_P` is not isolable from `f_layer`, and `f_P` is not isolable from `f_gas`.
The asymmetry is real: `f_layer` and `f_gas` *are* isolable from `f_P`.

**Why.** A fault can be isolated from another only if it reaches the
measurements by a route the other does not share. `f_P` acts solely through
absorbed power. `f_layer` additionally changes the conduction path beneath the
track; `f_gas` additionally changes surface convection. Those second routes are
their private fingerprints. A power deviation has none.

**Sensitivity to the modelling choices (the most attackable part of Tier 1).**
Four variants run, each weakening one arguable coupling:

| Variant | Non-isolable directed pairs |
|---|---|
| Baseline | f_P -/-> f_layer, f_P -/-> f_gas |
| V1: gas has no convection route | + f_gas -/-> f_P, f_gas -/-> f_layer |
| V2: thin layer has no absorptivity route | only f_P -/-> f_gas |
| V3: both second routes removed | f_P -/-> f_gas, f_gas -/-> f_P |

**The robust result: `f_P` is never isolable from `f_gas`, under every variant.**
Physically obvious in hindsight and all the better for it - a power deviation and
a degraded gas flow both reduce the energy reaching the melt pool, one at the
source and one in transit, and the melt pool cannot distinguish "less was
emitted" from "less arrived". This is the structurally irreducible pair, and it
is the one conclusion that rests on no debatable assumption.

**Feeds the three-way classification directly:**
- structurally irreducible: f_P vs f_gas
- modelling-dependent: f_P vs f_layer (hinges on whether thin layers change absorptivity)
- everything else: structure permits it, so Tier 2 and the noise floor decide

Note a counter-intuitive detail worth keeping: in V2, *removing* a fault coupling
*improves* isolability, because f_layer sharing e1 with f_P was what blocked
f_P's isolation. The analysis is not monotone in model richness.

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
| Alloy: IN718 | Weaver et al. 2024 (DOI 10.1007/s40192-024-00355-5) gives AM-Bench 2022 single-track melt pool width and depth on bare IN718 with power, speed and spot size varied, plus uncertainty budgets stated for model validation. One authoritative benchmark with known uncertainties beats scattered 316L literature values with heterogeneous measurement methods, despite 316L having more papers overall. |

### Gate 1 calibration source

**Weaver et al. (2024)**, *Integrating Materials and Manufacturing Innovation*,
DOI 10.1007/s40192-024-00355-5 — "Cross-Sectional Melt Pool Geometry of Laser
Scanned Tracks and Pads on Nickel Alloy 718 for the 2022 Additive Manufacturing
Benchmark Challenges". PMC copy at PMC11187816; NIST also hosts a download.
Related AM-Bench material: AMB2022-03 challenge descriptions on nist.gov, and the
data.gov catalogue entry for the cross-sectional microstructure dataset.

Pull 4-6 single-track points (power, speed, spot size, width, depth) from this for
the absorptivity fit. This replaces any dataset dependency — the project needs a
handful of numbers from one paper, not a corpus.

### Two findings in that paper that support the thesis

**Melt pool depth tracked volumetric energy density; width did not.** Published,
independent evidence that power and speed are confounded *in depth* while width
carries information they do not share. The framework should reproduce this. If it
does, it is a second known-practice validation (alongside the recoater check) and
this one lands on the central claim rather than a side one. Add it to week 8b.

**Pad melt pool depth was smaller when scan direction ran parallel to gas flow.**
Gas flow was flagged as the fault mode with no corroboration anywhere. It now has
some, from a NIST benchmark. Worth citing when defending that fault's inclusion.



## Open questions for the supervisor

1. ~~Which alloy~~ — **DECIDED: IN718.** Rationale below.
2. Target venue and word limit, which decides whether the abstract is trimmed.
3. Whether active excitation (route C) should be in this paper or held back.
4. Author list and affiliations.

## Things deliberately not in scope

Multi-material. Part-scale thermal history. Microstructure. Closed-loop control
design. Any experimental validation. Acoustic sensing (modelling acoustic emission
from a thermal model is not credible — say so if asked rather than faking it).
