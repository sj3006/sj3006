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

## GATE 1: PASSED, using the Honarmandi keyhole correction

**Result: width 11.7 % MAPE, depth 13.0 % MAPE** over the seven AM-Bench
single-track conditions. Both inside the 15 % threshold. `src/calibrate.py`.

### How we got here

The plain conduction model failed: width 8.4 %, depth 27.8 %, with absorptivity
pegged at its upper bound. Cause was not a bug. Every one of the seven benchmark
conditions is keyholing - aspect ratios 1.45 to 4.28 - and Eagar-Tsai has no
vapour depression and no multiple reflections, so it cannot produce a 227 um
deep pool from a 49 um spot.

### The fix, from Honarmandi et al. (2021)

**Honarmandi, P. et al., "A rigorous test and improvement of the Eagar-Tsai model
for melt pool characteristics in laser powder bed fusion additive manufacturing",
Additive Manufacturing 47 (2021) 102300. DOI 10.1016/j.addma.2021.102300**

They found exactly our failure across four alloys (depth R^2 of 0.12 to 0.42,
RMSE 75 to 161 um) and fixed it with a physics-based depth term rather than a
more complex model. Three things taken from them:

1. **Gladush-Smurov keyhole depth** (their Eq. 5):
   `d_k = mu*P / (2*pi*kappa*T_b) * ln[(sigma + alpha/v)/sigma]`,
   derived from conduction around a cylindrical keyhole held at the boiling
   point. Corrected depth = conduction depth + C * d_k, with C fitted. Their C
   came out 1.32 to 3.10 across four alloys.
2. **Keyholing criterion** `width / 1.5 <= depth`, applied to measured
   dimensions. All seven AM-Bench cases qualify.
3. **Conductivity and heat capacity are calibration parameters, not constants.**
   This resolves the open item about unsourced IN718 properties: the published
   approach is to fit them, because a constant-property model absorbs the
   physics it omits into the properties it has.

Their Eq. 1 is algebraically identical to our implementation, which independently
verifies the module.

### Calibrated values

| Parameter | Value | Honarmandi's range (4 alloys) |
|---|---|---|
| absorption efficiency mu | 0.384 | 0.60 - 0.64 |
| conductivity kappa | 35.0 W/mK | 39 - 62 |
| heat capacity Cp | 450 J/kgK | 849 - 1490 |
| keyhole factor C | 1.00 | 1.32 - 3.10 |

### Two honest caveats, both for the limitations section

**Parameters sit at their bounds.** Conductivity and heat capacity both hit the
edge of the allowed range, and all four values fall below Honarmandi's. The fit
is sliding along a near-degenerate direction until it hits a wall. Unbounded, it
drifts to kappa = 90 W/mK (width 6.2 %, depth 13.4 %) - a better fit and
indefensible for IN718, so conductivity is bounded to 35 W/mK and the slightly
worse error accepted.

**The thermal model's own parameters are confounded.** Honarmandi report pair
correlations of 0.93 to 0.96 between absorptivity, conductivity and heat
capacity. Many combinations fit comparably. **This is the same identifiability
pathology the paper is about, appearing in our own calibration** - worth a
sentence in the discussion, because it shows the phenomenon is not peculiar to
sensor signals.

### Alternatives rejected

| Approach | Width | Depth | Verdict |
|---|---|---|---|
| Conduction only | 8.4 % | 27.8 % | FAIL |
| Ad-hoc one-parameter keyhole scaling | n/a | 14.8 % | borderline, unpublished |
| Honarmandi, unbounded | 6.2 % | 13.4 % | kappa = 90 W/mK, indefensible |
| Honarmandi, nickel-alloy envelope | 16.0 % | 12.8 % | FAIL on width |
| **Honarmandi, physical kappa bound** | **11.7 %** | **13.0 %** | **adopted** |

## GATE 3 REACHED: Tier 2 parametric results

`src/diagnosability.py`, `src/parametric.py`. No in-process noise figures are
used - see the decision below - so everything is swept.

### Noise figures: deliberately not used

NIST AMS 100-35 reports 10 uV resolution on a 35 mV scale for a commercial
coaxial photodiode. That is a bench multimeter reading a static blackbody.
Applying it to a sensor running at tens of kilohertz against a melt pool with
plume and spatter in the field of view would flatter the hardware and bias every
conclusion towards "separable". **Not used.** The paper also characterises only
its broadband detector, never its two wavelength channels, and the system has no
camera, so it would have covered one sensor of three in any case.

Weaver et al. Table 4 gives U(k=2) = 6.2 um on a 136.3 um width, so 2.3 %. That
is metrology uncertainty from cross-sectional microscopy, not in-process camera
noise, so it appears only as a marked reference point on the sweep axis.

### The structural point that shapes the study

Whitening divides each sensor row by its own noise. If all three noise levels
scale together that is a uniform rescaling, and the angles between fault
signatures **do not move at all**. So isolability depends on noise *ratios*
between sensors, while detectability depends on the *absolute* level. Two
separate sweeps, answering different questions.

### Result 1: power and gas are confounded at every noise ratio

Angle 0.00 degrees at every pyrometer quality tested, from 1000x better than the
other sensors to 10x worse. Tier 1 called this the one structurally irreducible
pair under every modelling variant; Tier 2 confirms it exactly and shows that no
sensor improvement touches it. Both faults change the product (absorptivity x
power), and the melt pool cannot distinguish less emitted from less arrived.

### Result 2: the pyrometer has an optimum, and better is not better

| pyrometer / photodiode noise | power/speed | power/layer | speed/geom |
|---|---|---|---|
| 0.001 | 0.70 | 0.25 | 5.98 |
| 0.01 | 5.74 | 1.94 | 54.62 |
| **0.03** | **7.12** | **2.04** | **67.64** |
| 0.1 | 3.62 | 0.95 | 26.38 |
| 1.0 | 2.11 | 0.55 | 14.11 |
| 10 | 2.09 | 0.54 | 13.93 |

Angles peak around a ratio of 0.03 and fall off **in both directions**. An
arbitrarily precise pyrometer makes isolability *worse*: whitening multiplies
its row by 1/sigma, so as its noise goes to zero it dominates the whitened
Jacobian, and since one scalar cannot separate five faults, every signature
collapses onto that single axis.

**There is an optimal balance between sensors, and over-specifying one degrades
the suite.** Counter-intuitive, falsifiable, and directly useful to anyone
specifying monitoring hardware.

### Result 3: the rank limit bites before noise does

Three sensors span at most three directions, so with five faults two are
unresolvable by construction, independent of noise. Singular values at the
optimum ratio are [2.885, 0.678, 0.055], condition number 52 - the third
direction is 52x weaker than the first, so realistically two directions are
usable.

### Result 4: no pair is practically identifiable

Worst finite collinearity index (excluding the exactly-degenerate power/gas
pair) ranges 40 to 321 across the sweep, against a conventional cutoff of 10.
Even at the optimum it is 40, four times the cutoff. Only geometry separates
cleanly from anything, at 6 to 67 degrees.

### Result 5: detection is fine, isolation is not

Minimum detectable fault at 3 sigma, all sensors at equal relative noise:

| noise | power | speed | layer | gas | geometry |
|---|---|---|---|---|---|
| 1.0 % | 1.5 % | 4.7 % | 2.4 % | 7.7 % | 4.4 % |
| 2.3 % | 3.5 % | 10.8 % | 5.6 % | 17.7 % | 10.1 % |

The suite notices faults at plausible magnitudes. It simply cannot say which
one it noticed. That gap between detection and isolation is the paper.

### Derivatives: complex-step abandoned

The plan specified complex-step differentiation. It is invalid here - the model
branches at the liquidus threshold and at the boiling-point cap, and
complex-step through a branch returns nonsense silently. Central differences
with a reported convergence check are used instead. The Jacobian moves 20.6 %
between steps of 0.02 and 0.01, 0.25 % between 0.01 and 0.005, and under 0.03 %
below that; the default is 0.002. **Earlier preview numbers used step 0.10 and
carried substantial curvature error.**

## ROUTE A: richer observables change the headline

> **Numbers in this section are superseded.** They were computed with
> unit-variance profile normalisation, which let a fault reverse sign across the
> plate and, under the exponential form, reach 116% of nominal at one segment.
> See "MODEL DOMAIN DEFECTS" below for the corrections and the current figures.
> The section is kept because the *mechanism* it establishes is unchanged.

`src/observables.py`. Enlarging the observation from three instantaneous sensor
values to the regression of each sensor's residual onto known build context.

### The idea

A build already tells you things the instantaneous reading throws away: the
toolpath, the layer schedule, the gas flow direction, the part geometry. Each
fault leaves a different trace across those.

| fault | how it varies across a build | known regressor |
|---|---|---|
| power | roughly uniform, slow drift | constant / build time |
| speed | worst where the galvo must turn | 1 / vector length |
| layer | constant within a layer, steps between | layer-synchronous indicator |
| gas | gradient along the flow direction | position along gas flow |
| geometry | follows the part's own shape | local solid support depth |

Cheap to compute: to first order the residual at segment i is
`sum_k J[:,k] * f_k * m_k(i)`, so the enlarged Jacobian is
`Jbig[(s,j),k] = J[s,k] * B[j,k]` with `B = (G'G)^-1 G' M`. One small
least-squares solve, no re-running the thermal model.

### Result: everything becomes identifiable

| pair | instantaneous | enlarged |
|---|---|---|
| power / gas | **0.00** | **44.99** |
| layer / gas | 2.04 | 58.31 |
| power / layer | 2.04 | 45.55 |
| power / speed | 7.12 | 33.87 |
| speed / gas | 7.12 | 54.83 |
| speed / layer | 9.16 | 56.97 |

Rank 3 -> 5. Condition number 52 -> 7. Worst finite collinearity index
141,869 -> **2.4**, comfortably inside the conventional cutoff of 10.

**The pair Tier 1 called structurally irreducible is well separated.** That is
not a contradiction: Tier 1 analysed an instantaneous measurement model, and
adding spatial and temporal regressors is a genuinely richer one with new
equations relating each fault to its signature.

### Stress tests, because the result looked too good

**Control - all faults given the same profile.** Min angle 0.00 deg, rank 3,
worst CI 141,869: *identical to instantaneous*. The gain is therefore not from
having more dimensions. It comes entirely from faults varying differently. This
is the test that validates the mechanism.

**Graceful degradation.** Blending the profiles toward a common one:

| blend toward common | min angle | worst CI |
|---|---|---|
| 0 % | 33.87 | 2.4 |
| 25 % | 26.95 | 3.0 |
| 50 % | 19.31 | 4.2 |
| 75 % | 11.61 | 7.0 |
| 100 % | 0.00 | 141,869 |

Stays inside the cutoff until 75 % overlap. Not a knife-edge.

**Imprecise knowledge does not hurt.** Corrupting the assumed profiles by up to
100 % random error leaves min angle unchanged (33.9 -> 36.4 deg). You do not
need to know *how* each fault varies, only that they vary *differently*. This
matters a lot for the practical claim.

**A simpler part still works.** Two layers, uniform vectors, little geometric
variety: regressor conditioning worsens from 2.0 to 5.2, min angle 28.4 deg,
rank still 5.

### What this does to the paper

The three-way classification changes, for the better. Nothing is irreducible
once spatial and temporal context is used; everything is resolvable with no new
hardware. The message shifts from "these sensors cannot tell your faults apart"
to "they cannot instant-by-instant, but the process already hands you the
context that fixes it for free". More surprising, more actionable, and Tier 1
remains the baseline that makes the improvement legible.

### Open

Modulation profiles are physical claims, not measurements. The control test
shows the whole result rests on them being distinct. Each direction is
defensible - recoater faults are layer-synchronous, gas degradation has a flow
gradient, heat accumulation follows the known part shape, galvo error peaks at
turns - but that they dominate real build variation is unproven.

**Tier 1 should be re-run on the enlarged observation set** so the two tiers
describe the same system.

### Where the projection matrix B actually comes from

Raised by Amit, and it is the right question. **No cross-perturbation was ever
run.** Nothing in this project changed `gas_axis` and watched power respond, and
Eagar-Tsai could not do it if asked: it takes power, speed, spot size and
material properties for one straight track in steady state. It has no input for
plate position, no layer index, no gas flow direction and no memory of
previously deposited material.

The thermal model contributes exactly one object to Route A: the 3x5
instantaneous Jacobian `J`. Everything else is bookkeeping on two hand-authored
arrays.

- `G` (84x5), the known context, comes from `scan_plan()` - a synthetic plate of
  6 layers x 14 vectors. In a real deployment every column would come out of the
  sliced build file. Here the plate is invented.
- `M` (84x5), the modulation profiles, are my physical claims about how each
  fault's severity varies across a build, written as hard-coded coefficients
  (0.3 drift, 0.8 turns, 1.0 recoater, 0.9 flow gradient, 1.0 support).
- `B = (G'G)^-1 G' M` is a least-squares solve. No physics enters it.

Three of B's columns are the coefficients typed into `modulations()` read
straight back, because those profiles were written as exact multiples of
regressor columns (gas 0.900, layer 1.000, geometry 1.000, speed 0.800). Only
the power column does non-trivial work, because build time is not a regressor:
regressing it onto G gives [0, -0.0067, 0.132, 0.518, -0.913], and 0.3x that is
the printed power column. Its -0.913 loading on support depth against a plain
correlation of only -0.642 is regressor-regressor collinearity - this paper's own
subject matter appearing inside its construction.

So the 44.99 degrees has two parents: `J` says power and gas are exactly
parallel instantaneously, which is physics and is real; `B` says they have
different spatial signatures, which is an assumption I wrote. The control test
rules out a dimensionality artefact but cannot validate the profiles.

**Consequence for the paper.** 44.99 degrees is not a prediction about any
machine. The modulation coefficients must be swept alongside the fault couplings
and the headline stated as a threshold - the confounded pair separates once
profile contrast exceeds some value - rather than as a point number.


## LIMITATION FOUND: diagnosability is local, not global

Prompted by the question of how fault magnitudes are chosen. The Jacobian is a
derivative, so its perturbation size is a numerical choice and provably
irrelevant (converged below 0.005, default 0.002; angles use normalised
directions so magnitude cancels). But that makes every Tier 2 conclusion a
**linearisation about the healthy operating point**, and the physics here is not
close to linear.

Pairwise angles recomputed at finite fault magnitude rather than as a derivative:

| magnitude | power/gas | power/speed | speed/gas | power/geom |
|---|---|---|---|---|
| +0.2 % (derivative) | 0.99 | 6.03 | 6.92 | 62.12 |
| +1 % | 4.72 | 2.89 | 6.16 | 64.77 |
| +5 % | 17.48 | 42.44 | 24.96 | 37.81 |
| +10 % | 44.94 | 59.47 | 14.63 | 25.58 |
| +20 % | 45.74 | 50.49 | 5.88 | 27.99 |
| -10 % | 11.24 | 26.76 | 37.96 | 41.91 |
| -20 % | 3.51 | 49.49 | 52.99 | 39.43 |

Three things follow.

**There is no single diagnosability matrix.** It depends on fault magnitude, and
on the sign of the deviation. Power/gas is perfectly confounded in the limit,
well separated at +10 %, and confounded again at -20 %.

**Small faults are confounded; large faults mostly separate.** The suite can say
what went badly wrong while being blind to what is starting to go wrong - the
opposite of what monitoring is usually wanted for. That is a genuinely useful
and quotable finding, not just a caveat.

**It is not monotone and not sign-symmetric.** speed/gas runs 6.9 -> 25.0 ->
14.6 -> 5.9 as the fault grows, and a power increase does not mirror a power
decrease. The nonlinearity comes from the keyhole depth term, the T^4 radiance
weighting and the isotherm geometry.

### What this does to the paper

The headline must become **diagnosability as a function of fault magnitude**,
not a single matrix. More work, and the honest presentation. The derivative-limit
matrix stays as the incipient-fault case, which is the hardest and arguably the
most important one.

### Open, and it matters

Does the Route A improvement survive at finite magnitude? The enlarged
observation was computed from the linearised Jacobian via
`Jbig = J[s,k] * B[j,k]`, so it inherits the linearisation wholesale. If the
improvement is a small-fault artefact, the main result weakens considerably.
**Check this before anything else.**

## ROUTE A SURVIVES AT FINITE MAGNITUDE - and the profiles are now swept

`src/locality_routeA.py` and `src/profile_sweep.py`. This was the flagged
check-before-anything-else, because Route A was built as
`Jbig[(s,j),k] = J[s,k] * B[j,k]` and so inherited the linearisation wholesale.
It no longer does: the finite-magnitude version puts each segment's effective
fault `f * m_k(i)` through the full nonlinear chain and regresses the resulting
residuals, with no derivative anywhere.

### It holds

| | derivative limit | +5% fault | +20% fault |
|---|---|---|---|
| worst pair angle, enlarged | 38.5 deg | 39.0 deg | 42.5 deg |
| worst pair angle, instantaneous | 0.00 deg | 4.1 deg | 6.8 deg |
| rank (of 5) | 5 | 5 | 5 |
| condition number | 8 | 7 | 8 |

Rank 5 and single-digit conditioning at every magnitude tested, positive and
negative, from 0.2% to 20%. The instantaneous case stays at rank 3 throughout.
So unlike the instantaneous angles, which swing wildly and non-monotonically
with fault size, the enlarged result is *stable* in magnitude. That is a better
result than hoped for and it is the one to put in the paper.

### Verification, because an interpolant was used

Each fault's response is a function of one scalar, so the study runs off a 57-node
exact response curve per fault rather than re-running the thermal model 84 times
per magnitude. The pointwise interpolation error reaches 7% of the typical
whitened residual, entirely on the pyrometer in a flat region of its response.
That looked alarming, so the end quantity was checked directly: a full
no-interpolation run (84 segments x 5 faults of real model evaluations per
magnitude) agrees with the interpolated angle table to **0.14 deg at +5% and
0.64 deg at +20%**, with identical rank and condition number. The intermediate
metric was the misleading one - it divides by a change that passes through zero.

### Profile form: the linear form was unphysical and is no longer the default

The sweep exposed something that had gone unnoticed. The original profiles
`1 + c*z` go negative wherever `z < -1/c`, so 32 of 420 entries were negative and
a 20% fault acted as **-31%** at some segments: the fault reversed sign across the
plate. Gas starvation does not become gas enrichment at the far wall, and a sign
reversal is an unusually distinctive signature, so it had to be ruled out as the
source of the gain.

`modulations()` now takes a `form`, and the default is **"positive"**
(`exp(c*z)` rescaled to unit mean - strictly positive, same leading order for
small c). The result survives: worst pair 38.6 / 39.0 / 42.5 deg against the
linear form's 33.3 / 46.3 / 47.9 deg at the same three magnitudes. The sign
flips were helping slightly at finite magnitude and hurting slightly at the
limit, so nothing of substance rested on them.

**The headline numbers move.** They moved again afterwards, when the
normalisation was corrected - see "MODEL DOMAIN DEFECTS" below for the figures
that are actually canonical. What this section established and what survived is
the *form*: strictly positive profiles, and a headline stated as a threshold. The projection matrix is also
visibly less diagonal under this form - speed loads 1.385 on turn density but
also 0.220 on the gas axis and 0.211 on support depth - which is honest, because
the near-diagonal linear B was partly an artefact of writing profiles as exact
multiples of regressor columns.

### The control passes exactly

Give all five faults one shared profile: worst angle 0.00 deg, power/gas 0.00 deg,
rank 3, condition 52 - bit-identical to the instantaneous case. So the gain is
the profiles *differing*, not the enlarged observation having 15 rows instead of 3.

### The contrast threshold, which is the honest form of the headline

Angle against profile contrast (1.0 = the coefficients written into the module),
strictly positive profiles, at the derivative limit:

| contrast | 0 | 0.10 | 0.25 | 0.50 | 0.75 | 1.00 | 1.50 | 2.00 |
|---|---|---|---|---|---|---|---|---|
| worst pair, deg | 0.99 | 5.54 | 13.19 | 25.04 | 33.23 | 38.57 | 44.70 | 47.97 |
| condition | 5.7e10 | 68 | 28 | 14 | 10 | 8 | 7 | 7 |

Monotone and smooth, so the paper can state a threshold rather than a point
value: **rank rises from 3 to 5 as soon as contrast is non-zero, and the worst
pair clears 13 deg at contrast 0.25 and 25 deg at 0.50** - a quarter to a half of
the asserted profile strength. That is the defensible claim, and it is a figure.

### A framing this produced for free

At +20% the instantaneous power/gas angle is already 45.7 deg and barely moves
with contrast, while at the derivative limit it is 0.00 deg and moves from 0.99
to 55 deg across the contrast sweep. The two mechanisms cover different regimes:
**nonlinearity separates large faults, spatial context separates incipient
ones.** Complementary, not competing, and it gives the paper a clean reason to
report both.

### Still open

- Fault coupling constants (`FaultCouplings`) are still unswept. Same class of
  assumption as the profiles, and the next thing to do.
- Tier 1 on the enlarged observation set, so both tiers describe one system.
- Rank tolerance is now 1e-6 relative, not 1e-12. At 1e-12 a condition number of
  6.8e9 was being reported as rank 5, which is not a measurement.


## TIER 1 ON THE ENLARGED SET - and a better three-way classification

`src/structural_enlarged.py`. The two tiers were analysing two different
systems, which is the first thing a reviewer would have caught.

### The structural form of Route A

A regression coefficient of sensor s onto regressor j is the component of that
sensor's response along regressor j, and the whole causal chain has such a
component. So each regressor is a *channel* carrying its own copy of the chain:
5 channels x 11 equations = 55 equations, 40 unknowns, redundancy 15. The
structural content is which faults enter which channel - fault k enters channel
j only where `B[j, k]` is non-zero - so the projection matrix's zero pattern is
the entire structural claim, and since B is numerical, a threshold decides it.
The threshold is swept.

### The MSO enumeration had to be replaced, and the replacement is validated

2^11 subsets was exhaustive; 2^55 is not available. But MSO sets were only ever
a means to the two tests, and those need just the structurally overdetermined
part M+:

    f detectable           iff some equation carrying f lies in M+(E)
    f_i isolable from f_j  iff some equation carrying f_i lies in M+(E minus
                               the equations carrying f_j)

and `e in M+(E)` iff `phi(E minus e) = phi(E) - 1`, since phi = |E| - matching
and the matching only shrinks when e was matched in every maximum matching. That
is |E| matching computations instead of 2^|E| subsets. **Checked against Tier 1's
exhaustive answer on the 11-equation model: detectability and isolability both
match exactly.** It is not used until that passes.

### Result, and a non-monotone threshold

| threshold | 0.00 | 0.01 | 0.05 | 0.10 | 0.20 | 0.40 |
|---|---|---|---|---|---|---|
| non-isolable pairs | 2 | 1 | 1 | **0** | **0** | 2 |

At threshold 0 every channel admits every fault, so the enlarged model is five
copies of the instantaneous one and reproduces Tier 1's blocked pairs exactly -
`f_P` from `f_layer` and `f_P` from `f_gas`. A useful consistency check. Full
isolability appears in a *window* - **0.01 to 0.10** under the corrected
profile normalisation, 0.10 to 0.20 as first computed: below it the channels are
not selective enough, above it they admit so little that equations are lost. The
paper must report the window, not a single threshold.

### The scan plan is a diagnosability lever, and this is the most actionable finding yet

Power becomes isolable from gas because the support-depth channel admits power
(B = -0.185) and not gas. But power only loads onto support depth because
in a bottom-up raster, build time and solid support beneath the track both grow
with height - correlation -0.642. **That is a consequence of the operator's chosen
scan order, not a fact about LPBF.** Break it and the structural result changes:

| plan | corr(time, support) | non-isolable pairs | worst angle | power/gas |
|---|---|---|---|---|
| raster, support grows | -0.642 | **0** | 25.83 | 29.34 |
| raster, flat support | -0.000 | 2 | 26.21 | 28.01 |
| random order | +0.078 | 2 | 28.83 | 28.83 |

(Figures under the corrected profile normalisation and the corrected coefficient
noise model.)

### The claim has to be narrowed, and the narrowing is itself the point

The first version of this finding read "diagnosability is partly designed", and
cited both the structural column and the angles, which then moved from 38.5 to
32.3 as the plan changed. **Under the corrected noise model the angles no longer
support that**: 25.83, 26.21, 28.83 deg, and the structurally *worse* plans have
marginally *larger* worst angles. The honest claim is narrower:

> Scan order changes the **structural** classification decisively - zero blocked
> pairs against two - while barely moving the quantitative geometry.

Which is exactly the structural-versus-quantitative distinction again. Scan-plan
design operates on **decoupling**: whether a residual exists that is blind to the
other fault, and therefore whether separability survives the magnitudes being
wrong. It does not operate on signal geometry. A plan with a support-correlated
build order moves power/gas from class 2 (separable only because the calibrated
magnitudes differ) into class 1 (separable from the zero pattern alone), and that
is a real and free upgrade in the *robustness* of the diagnosis, not in its
sharpness.

That is still a useful and publishable lever, and it still reaches the same place
as active excitation without perturbing a production build. But it must be stated
as a structural claim. Citing the angles for it would have been wrong, and nearly
was.

### The apparent contradiction, resolved - and it improves the paper

The flat-support plan reads "structurally non-isolable" while its angle is 39 deg.
That is not a bug. Under that plan, above the threshold:

    constant       power speed layer gas geometry
    gas_axis                         gas
    layer_sync           layer
    turn_density         speed       gas geometry
    support_depth        speed       gas geometry

Power appears **only** in the constant channel, and gas appears there too, so no
residual can be built that is blind to gas. But the power-to-gas ratio across the
five channels is 1.000, 0.001, 34.2, -0.010, 0.005 - wildly different, so the two
signature *directions* are 39 deg apart and a discriminator plainly exists.

The distinction is exact: **structural isolability asks for a residual decoupled
from the other fault; quantitative separability only asks that the signature
directions differ.** Decoupling is the stronger requirement. So the two tiers are
not competing answers to one question, they answer two questions, and the gap
between them has a precise meaning: a structurally isolable pair stays separable
however wrong the magnitudes are, while a merely quantitatively separable pair
relies on the calibration being right.

That sharpens the abstract's three classes into something defensible:

1. **Structurally isolable** - separable from the zero pattern alone, robust to
   calibration error.
2. **Quantitatively separable only** - separable in this calibrated model because
   the magnitudes differ, with no structural guarantee. Honest and useful, but
   conditional.
3. **Neither** - needs another measurement, or a different scan plan.

This is the same three-way split the accepted abstract promised, with the middle
class now given a precise meaning rather than a hand-wave about noise.

### Also recorded

`scan_plan` now takes `order` ("raster", "random", "layer_interleaved") and
`support_with_layer`, and the plan carries an explicit `build_index` so scan
order is a first-class variable rather than an implicit raster. The default
reproduces every previously recorded number exactly - checked.


## MODEL DOMAIN DEFECTS, FOUND AND FIXED - and the canonical numbers

Both were found by the sweeps rather than by inspection, which is the argument
for running them.

### 1. The coupling model left its own domain, silently

The coupling sweep crashed. With `layer_to_conductivity = 1.0`, a -100% layer
fault drives `k_eff = k * (1 + c*f)` to exactly zero, raising a
ZeroDivisionError in the Eagar-Tsai integrand, and negative beyond that - which
makes thermal diffusivity negative and the integrand imaginary. The worse part
was past the zero: NaNs appeared and were then swallowed, so the model returned
finite-looking numbers from a regime where it had no meaning.

**Fix.** Absorptivity and conductivity are now multiplied by exponential factors,
`mu = a*exp(c_layer*f_layer + c_gas*f_gas)` and `k = k0*exp(c_k*f_layer)`. They
agree with the linear form to first order, so the Jacobian is unchanged to two
decimal places - checked - but they are strictly positive everywhere by
construction, which is also the right shape physically: conductivity interpolates
between powder and solid and cannot pass through zero. `apply_faults` now raises
if absorptivity leaves (0, 1], conductivity goes non-positive, or local preheat
reaches the solidus. `form="linear"` is retained for comparison.

### 2. The profile normalisation was the real cause of the sign reversals

The earlier diagnosis blamed the linear profile form. That was wrong.
Standardising the modulation drivers to unit *variance* leaves excursions out
past +/-2, so `1 + c*z` went negative and `exp(c*z)` grew a 5.8x tail - which
means **a +20% fault acted as 116% of nominal at one segment**, so that row of
the locality table was itself outside any physical scope. The guard in
`secant_directions` caught it; nothing else would have.

**Fix.** Modulation drivers are normalised to exactly [-1, 1]. All three profile
forms are then non-negative, the linear one included, which confirms the real
diagnosis. It also gives contrast a physical meaning: with `exp(c*z)` and z in
[-1, 1], a fault's severity spans a factor of `exp(2c)` between its mildest and
most severe segment. At c = 0.3 that is 0.74x to 1.35x; at c = 1.0, 0.37x to
2.72x. Those are numbers that can be defended in a paper. The regressors keep
unit-variance standardisation - they are a basis and their scaling is absorbed
into the regression coefficients.

### The canonical numbers

| | derivative limit | +5% fault | +20% fault |
|---|---|---|---|
| power/gas, enlarged | **30.17** | 38.07 | 48.19 |
| worst pair, enlarged | **29.93** | 37.59 | 30.47 |
| worst pair, instantaneous | 0.00 | - | - |
| rank (of 5) | 5 | 5 | 5 |
| condition number | 12 | 10 | 12 |

No-interpolation cross-check agrees to 0.63 deg at +5% and 0.21 deg at +20%. The
shared-profile control still returns the instantaneous result bit-identically.
Contrast threshold at the derivative limit: 0.99 deg at contrast 0, then 3.57,
8.55, 14.74, 22.04, 29.32, 40.16, 45.70 deg at 0.10 through 2.00 - monotone and
smooth, so the threshold figure survives intact.

The headline has now moved three times: 44.99 (unphysical profiles), 41.44
(positive form, unbounded normalisation), 30.17 (bounded normalisation). Each
move tightened the model rather than chasing a number, and this one is settled
because contrast is now defined and nothing leaves the domain. 30 degrees of
separation on a bounded, interpretable profile is a defensible claim where 45
degrees on a profile that reversed the fault's sign was not.

## COUPLING SWEEP: the conclusions do not depend on the couplings

21 values across the four constants, each re-deriving the response curves, both
tiers, at the derivative limit and at a +5% fault.

| quantity | across all 21 values |
|---|---|
| power/gas angle, instantaneous | **0.00 deg, every value** |
| rank, instantaneous | 3, every value |
| rank, enlarged | 5, every value |
| worst pair, enlarged, derivative limit | **29.93 deg, every value** |
| worst pair, enlarged, +5% | 36.6 to 38.1 deg |
| condition number, enlarged | 7 to 46 |

### Read the invariance precisely

29.93 deg at every single coupling value is not as sweeping as it looks, and the
paper must not oversell it. The worst enlarged pair is **power/speed**, and
neither of those two faults has a coupling constant - power enters through the
power multiplier, speed through the speed multiplier. So that particular number
is coupling-independent by construction. The pairs that *do* depend on the
couplings move in conditioning, from 7 at `gas_to_attenuation = -0.50` to 46 at
-0.05, because a weak coupling makes the gas signature small and the suite badly
conditioned. What is genuinely robust is the structure: rank 3 instantaneous and
rank 5 enlarged at every value, and no pair ever lost.

### Two results that are now analytic rather than numerical

**Power and gas are exactly collinear for any coupling value.** Both faults enter
the model only through the product (absorptivity x power), and the Eagar-Tsai
temperature rise is linear in that product. So the gas column of the Jacobian is
a scalar multiple of the power column, with the scalar being `1/c_gas` -
measured as -5.0001, -5.0001, -5.0028 in the three sensors at the default
-0.20, the last being finite-difference error. Sweeping the coupling rescales
the whole column by exactly 2.5000, 1.7500, 1.0000, 0.5000, 0.2500 with spread
of order 1e-5. **No value of any coupling constant can break this confounding**,
which is why Tier 1 found it from structure alone and why it needs spatial
information rather than better calibration.

**Power and layer collapse to exactly 0.00 deg when `layer_to_conductivity = 0`.**
Predicted before it was run: with no conductivity effect, a layer fault acts
purely through absorptivity, which is the same channel as power. The layer
signature's direction is set by the ratio of its two couplings, so the pair's
angle is a measure of how much of the layer fault is *not* an absorptivity
change. 2.04 deg at the default is small, which is the honest reading: layer is
nearly confounded with power instantaneously, for a reason the sweep makes
explicit.

## ROUTE A HAD THE WRONG NOISE MODEL - found by chasing an absurd Route B result

Route B reported that a **single sensor** reaches enlarged rank 5 with a 29 deg
worst angle. That looked impossible, since Tier 2's whole point was that three
sensors cannot span five faults, so it got chased rather than reported. It turned
out to be two separate things: one genuine error, and one correct-but-startling
result.

### The error

A richer observable is not a raw sensor reading. It is a least-squares
coefficient estimated from every segment of the build, so its noise is

    sigma[s, j] = sigma_s * sqrt( [(G'G)^-1]_jj )

Route A had been whitening every coefficient by `sigma_s` itself. For this plan
the correct factors run 0.109 to 0.136, so averaging over 84 segments buys about
a **9x noise reduction** that was being thrown away, and the *spread* across
regressors is 1.25x because turn density and support depth are correlated at
0.571 - a collinear regressor design should be penalised and now is.

The uniform 9x changes nothing about angles, rank or condition number, all of
which are invariant to scaling every row equally. The 1.25x spread does change
them, and the 9x matters for detectability. `coefficient_sigmas` now computes it,
`pair_angles` and `rank_cond` refuse a noise vector whose length does not match
the number of rows, and every call site passes the right one.

**Corrected canonical numbers:** worst pair **25.83 deg** (was 29.93), power/gas
**29.34 deg** (was 30.17), rank 3 -> 5, condition 12.

### The startling part, which is correct

Rank 5 from one sensor is real, and it is the actual content of Route A. A single
photodiode's residual across the build is

    r(i) = sum_k  J[s,k] * f_k * m_k(i)

one scalar time series - but regressing it onto five known regressors yields five
numbers, and five numbers determine five faults whenever `J[s,k] * B[j,k]` is
invertible, which it generically is. Route A does not add measurements. It
converts a *static* identifiability problem, 3 equations in 5 unknowns, into a
regression problem whose equation count is set by the number of **known
regressors**, not the number of sensors. The rank limit Tier 2 found is therefore
not a hardware limit at all.

That has to be stated carefully rather than trumpeted, because it rests entirely
on knowing the profiles. Which is what makes the next section the one that
matters.

## ROUTE B: what the sensors are actually for

`src/route_b.py`. Four candidate additions, each costing something different: the
camera's two axes reported separately instead of as one area (free - the image
already exists), a short-wave infrared photodiode (new hardware), and a
wide-band filter pair on the existing pyrometer (filter change).

### Instantaneously, sensor count sets the rank. With spatial context it does not.

| subset | inst rank | inst cond | enlarged rank | enlarged worst |
|---|---|---|---|---|
| photodiode only | 1 | 1 | 5 | 24.89 |
| camera only | 1 | 1 | 5 | 24.89 |
| pyrometer only | 1 | 1 | 5 | 24.89 |
| photodiode + pyrometer | 2 | 5 | 5 | 26.12 |
| all three (baseline) | 3 | 52 | 5 | 25.83 |
| + split the camera (free) | 4 | 747,923 | 5 | **29.34** |
| + SWIR photodiode | 3 | 59 | 5 | 25.75 |
| + wide-band pyrometer | 4 | 944,000 | 5 | 25.70 |
| everything | 4 | 676,482 | 5 | 29.34 |

Every subset reaches rank 5 enlarged, with condition 12 to 14, and the angles sit
within 1.3 deg of each other. **Sensor count barely affects the geometry at all**
once spatial context is used. Checked at three different noise-ratio assumptions;
the conclusion holds in all three.

### The best intervention is free, and new hardware buys nothing

Against the baseline worst pair, power/speed:

| addition | power/speed | change | cost |
|---|---|---|---|
| split the camera into width and length | 39.23 deg | **+13.40** | none, image processing |
| SWIR photodiode | 25.75 deg | -0.08 | new hardware |
| wide-band pyrometer | 25.70 deg | -0.13 | filter change |

Reporting the melt pool's two axes separately instead of collapsing them into an
area is the single most valuable change available, and it costs nothing. Neither
new sensor helps at all. For a paper whose promised deliverable includes the class
of pairs "requiring an additional measurement", the honest answer is that the
additional measurement already exists inside an instrument that is throwing it
away.

**And it only shows up in Tier 2.** Instantaneously the split camera has
condition number 747,923 - width and length both scale with pool size, so the
extra row is nearly degenerate and useless. Modulated across the build it is
worth 13 deg. That is the clearest single illustration in the study that the two
tiers answer different questions.

### What extra sensors buy is robustness, and that is measurable

If rank is not the constraint, "what does another sensor buy" has to be answered
on something else. The weakest assumption in the whole study is the modulation
profiles, so the metric is: diagnosis inverts the *assumed* enlarged Jacobian A
while the data comes from the *true* one T, and the worst-case relative error
over all fault directions is the operator norm of `pinv(A_w) T_w - I`.

Contrast wrong by up to:

| subset | n | 10% | 30% | 50% |
|---|---|---|---|---|
| photodiode only | 1 | 0.128 / 0.200 | 0.381 / 0.617 | 0.632 / 1.059 |
| camera only | 1 | 0.107 / 0.168 | 0.320 / 0.519 | 0.530 / 0.887 |
| photodiode + pyrometer | 2 | 0.093 / 0.153 | 0.278 / 0.466 | 0.461 / 0.785 |
| all three (baseline) | 3 | 0.091 / 0.147 | 0.271 / 0.450 | 0.451 / 0.758 |
| + split the camera (free) | 4 | **0.068 / 0.087** | **0.206 / 0.281** | **0.345 / 0.513** |
| everything | 7 | 0.072 / 0.097 | 0.217 / 0.307 | 0.363 / 0.546 |

(mean / worst over 40 random draws.)

Redundancy roughly halves the worst-case error: one sensor at 30% profile error
can get the fault vector 62% wrong, the split-camera suite only 28%. **So the
suite exists to protect the answer against the thing we are least sure of, not
to make the answer possible.** That is a genuinely useful sentence for a paper
whose own weakest point is those profiles, because it turns the weakness into
the reason the hardware matters.

Note also that "everything" is slightly *worse* than the four-observable split
camera set, which is the same over-specification effect Tier 2 found when the
pyrometer was made too good: adding a weak, nearly-redundant row degrades a
suite rather than improving it.

### No sensor is redundant, and none is critical

Dropping any one of the three changes the enlarged worst angle by at most 0.9 deg
at any of the three noise-ratio assumptions, and never changes the rank. There is
no basis for recommending that a builder remove any of them, and no basis for
claiming any one is indispensable. That is a real answer and it should be stated
as one rather than dressed up.

## CANONICAL NUMBERS, after both corrections

Everything below is under exponential couplings, [-1, 1] profile normalisation,
the positive profile form, and coefficient noise `sigma_s * sqrt([(G'G)^-1]_jj)`.
These supersede every earlier figure in this file.

### Route A, instantaneous versus enlarged

| | derivative limit | +5% fault | +20% fault |
|---|---|---|---|
| power/gas, enlarged | **29.34** | 37.42 | 47.73 |
| worst pair, enlarged | **25.83** | 36.61 | 29.40 |
| worst pair, instantaneous | 0.00 | 4.26 | 6.61 |
| rank (of 5) | 5 | 5 | 5 |
| condition number | 12 | 10 | 13 |

Worst enlarged angle over every magnitude and pair tested: **22.19 deg**, at a
-2% fault. Rank 5 throughout; the instantaneous case is rank 3 throughout.

### Contrast threshold, derivative limit

| contrast | 0 | 0.10 | 0.25 | 0.50 | 0.75 | 1.00 | 1.50 | 2.00 |
|---|---|---|---|---|---|---|---|---|
| worst pair, deg | 0.99 | 3.49 | 7.88 | 12.60 | 18.71 | 25.20 | 36.53 | 43.64 |
| condition | 52 | 111 | 45 | 23 | 16 | 12 | 9 | 7 |

Monotone and smooth. The rank rises from 3 to 5 as soon as contrast is non-zero;
the worst pair clears 8 deg at a quarter of the asserted profile strength and
13 deg at half.

### Profile form, worst pair at three magnitudes

| form | limit | +5% | +20% | sign reversals |
|---|---|---|---|---|
| positive (default) | 25.20 | 36.61 | 29.40 | 0 / 420 |
| linear | 30.75 | 38.43 | 40.99 | 0 / 420 |
| clipped | 30.75 | 38.43 | 40.99 | 0 / 420 |

All three forms are admissible now that drivers are range-normalised, and the
positive form is the *conservative* one at every magnitude. Reporting it as the
headline is therefore the cautious choice, not just the defensible one.

### Structural, enlarged

Isolability window unchanged by the noise correction, as it must be - structure
does not depend on noise: **threshold 0.01 to 0.10**, zero blocked pairs, against
two blocked pairs for the instantaneous model and at thresholds outside the
window.

## KNOWN-PRACTICE VALIDATION: partial pass, and it explained Route B

`src/validation.py`. Gate 1 fitted four parameters to seven Weaver points, so
agreement with those points is calibration. Validation means reproducing
something the fit did not target.

### The recoater check was dropped, because it was circular

The plan listed a recoater validation: show that the framework recovers a
recoater fault as layer-synchronous, which is how practitioners actually spot it.
But layer-periodicity is *put in* through the modulation profile, so recovering
it proves nothing about the model. Dropped and replaced, rather than reported as
a pass it would not have earned.

### Check 1, already passing

Over 27 melted conditions spanning power, speed and spot size, depth correlates
with volumetric energy density at r = +0.727 while width gives r = +0.032,
reproducing Weaver et al. This lands on the central claim: width carries
information depth does not.

### Check 2: Guo et al.'s constant-energy-density result

Guo et al., *Additive Manufacturing* 28:600-609 (2019), observed sub-surface melt
pools by X-ray at constant input energy density and found dimension and volume
varying by orders of magnitude, through different melting regimes, attributed to
absorption changing with power and speed separately. It is the published
statement of this paper's own thesis, and it was not fitted.

Holding `P / (v * sigma^2)` at the Weaver case-0 value and sweeping power from
150 to 500 W with speed compensating:

| power, W | speed, m/s | width, um | depth, um | length, um | aspect | regime |
|---|---|---|---|---|---|---|
| 150 | 0.505 | 121.6 | 64.5 | 240.8 | 0.53 | conduction |
| 285 | 0.960 | 115.1 | 69.7 | 415.5 | 0.61 | conduction |
| 420 | 1.415 | 109.9 | 71.6 | 609.3 | 0.65 | conduction |
| 500 | 1.684 | 107.9 | 152.9 | 645.3 | 1.42 | **keyhole** |

**Partial pass, stated as such.** The model reproduces the existence of the
variation, its direction, and a regime transition through the keyholing
criterion. It does not reproduce "orders of magnitude": depth varies 2.37x and
width 1.13x. That is expected and should be said plainly - the mechanism Guo et
al. identify is absorption changing with the vapour-depression geometry, which a
conduction model with an analytic keyhole patch does not contain. The shortfall
is a limitation of the thermal model, not of the diagnosability method built on
it, and the paper is better for saying so than for claiming a match.

### The check produced a better result than the validation

Restricting to conduction-regime rows, so the keyhole jump cannot flatter
anything:

| dimension | span | factor |
|---|---|---|
| width | 109.9 to 121.6 um | 1.11 |
| depth | 64.5 to 71.6 um | 1.11 |
| **length** | **240.8 to 609.3 um** | **2.53** |

At constant energy density, width and depth barely move while **length moves by a
factor of 2.5** - and width moves *downwards* while depth moves up, so the two
are not even redundant with each other.

**This independently explains the Route B result.** The camera reports
`area = pi/4 * width * length`: it multiplies the least informative dimension by
the most informative one and reports the product. That is why splitting the
camera into its two axes was worth 13 deg on the power/speed pair while a SWIR
photodiode and a wide-band pyrometer were worth nothing at all. The information
was already in the image and was being averaged away.

Two independent analyses - a thermal sweep against a published experiment, and a
noise-whitened signature-geometry calculation - arriving at the same conclusion
by different routes is the strongest internal consistency check in the study so
far. It also turns the headline recommendation from an empirical observation into
one with a stated mechanism, which is what makes it publishable rather than
merely true.

## WHAT A FAULT MAGNITUDE MEANS - a scale convention, and where it leaks

Raised by Amit. `power` and `speed` are physical fractions: 0.05 is 5% more
power. `layer`, `gas` and `geometry` are not - they are dimensionless severity
indices whose meaning comes entirely from the coupling constant each multiplies.

| f | layer | gas | geometry |
|---|---|---|---|
| 0.05 | absorptivity -1.5%, conductivity +2.5% | absorptivity -1.0% | preheat +30 K |
| 0.20 | -5.8%, +10.5% | -3.9% | +120 K |
| 1.00 | -25.9%, +64.9% | -18.1% | +600 K |

### How the couplings were actually chosen - corrected

An earlier version of this section said the couplings were "set so f = 1 is the
fault at its physical limit", and showed arithmetic deriving -0.30 from a
bare-solid absorptivity of 0.3 against the fitted 0.384. **That was written
backwards.** The constants were picked first, as round numbers of the right sign
and order; the arithmetic was constructed afterwards to justify them. Amit caught
it on the giveaway - the "derivation" produced 0.25 and the text then "rounded"
it to 0.30, which is a 20% change, not rounding.

What is actually defensible about each constant, and nothing more:

- **The sign.** Fixed by physics and not negotiable. A thinner layer means less
  multiple-reflection trapping, so absorptivity falls. Degraded gas puts plume in
  the beam path, so absorptivity falls. Less insulating powder raises effective
  conductivity. A thin feature raises local preheat.
- **The order of magnitude.** A fractional layer change cannot move absorptivity
  by a factor of ten and cannot leave it unchanged, so it lands somewhere in the
  tens of percent at full severity. -0.30 sits in that band; so do -0.20 and
  -0.45.
- **Nothing else.** No measurement pins any of them, because no benchmark dataset
  with deliberately induced faults exists.

So f = 1 is a *convention* meaning "severe", loosely anchored to the top of the
plausible range. It is not a calibrated physical limit and the paper must not
call it one.

**The defence is the sweep, not the derivation.** `layer_to_absorptivity` from
-0.60 to -0.05 is a twelvefold range, and power/gas stays 0.00 deg, enlarged rank
stays 5, enlarged worst stays 29.93 deg throughout. The honest sentence is: the
constant is a guess, and the conclusions are invariant to the guess across its
whole plausible range. That is a stronger argument than any derivation, and it
does not require the number to be right.

Two figures quoted in passing - bare-metal absorptivity near 0.3 at ~1 um, and
plume attenuation reaching ~20% in severe conditions - are from general knowledge
of the literature, not from sources opened during this work. They are used only
to argue order of magnitude. Each needs a citation before submission, and if
either moves, the sweep already shows nothing breaks.

**A fault index and its coupling are identifiable only as a product.** Double
the coupling and halve f and the model is numerically identical. The scale is a
convention, not a measurement.

### Where that is harmless

Isolability. Scaling a Jacobian column does not change its direction, and angles
see only direction. The coupling sweep demonstrates it exactly: scaling
`gas_to_attenuation` by 2.5 scaled the gas column by 2.5000 in every sensor and
left the angle at 0.00 deg. Every angle, rank and condition number in the study
is immune.

### Where it leaks, and must be said in the paper

**Detectability.** An absolute question, so not well posed under an arbitrary
scale. Already compromised anyway by the deliberately-unused noise figures, so
nothing new is lost - but the two limitations should be stated together rather
than separately, since they bite the same claim.

**The finite-magnitude study.** Every fault is given the same f. At f = 0.05
that is a real 5% for power but a 1.5% absorptivity change for layer and 1.0%
for gas. So those rows do **not** compare equal physical severities, and fig3's
axis is an index rather than a common scale. Relabelled accordingly.

This does not undermine the finite-magnitude conclusion, which is that the
enlarged result stays rank 5 and stays in the 22 to 49 deg band across the whole
sweep while the instantaneous one swings between 0 and 7 deg. That holds
whatever the per-fault scale, because it holds at every point tested. What it
does undermine is any sentence of the form "at a 5% fault, pair X is separable
and pair Y is not" - comparisons *across pairs at fixed f* are not physically
meaningful. The paper must not make one.

## FAULTS REDEFINED AS PHYSICAL QUANTITIES - and a missing term found

Amit rejected "I picked it" as a justification for the coupling constants and
asked for literature. Going and getting it found something worse than a weak
justification, and the fix is structural rather than a better number.

### The root cause: dimensionless indices invent constants

The constants existed only because each fault was defined as a dimensionless
index. Define the fault as a physical quantity and most of them cease to exist.

| fault | was | now | constants |
|---|---|---|---|
| power | fractional deviation | unchanged | none |
| speed | fractional deviation | unchanged | none |
| gas | index x -0.20 | **optical depth of the plume**, Beer-Lambert transmission exp(-f) | **none** |
| geometry | index x 600 K | **preheat rise in units of 100 K** | **none** (a unit) |
| layer | index x two constants | **fractional layer-thickness deviation** | three, derived |

Gas is the clearest: there is no conversion factor to argue about, because
Beer-Lambert *is* the law and f_gas is its optical depth. f_gas = 0.2 is 18.1%
attenuation. Geometry: documented preheat in thin walls and overhangs is tens to
a couple of hundred kelvin, so f = 1 meaning +100 K is realistic rather than the
previous extreme.

### layer_to_absorptivity = -0.230, derived

Anchors: **Trapp et al., Applied Materials Today (2017)** measured in situ at
1070 nm a powder absorptivity about **twice** the bare polished disc for ~100 um
layers; radiative-transfer treatments of metal powder beds put the penetration
depth at a few particle diameters.

    A(t) = A_s + (A_p - A_s)(1 - exp(-t/delta)),  A_p = 2 A_s,
    delta = 2 * d50 = 60 um,  t0 = 40 um

    saturation at t0   1 - exp(-40/60)   = 0.487
    A(t0)/A_s          1 + 1 x 0.487     = 1.487
    d(lnA)/d(ln t)                       = 0.230
    -> coupling = -0.230   (the guessed value was -0.300)

**Self-consistency check, which neither side was built to pass.** That implies a
bare-solid absorptivity of 0.384 / 1.487 = 0.258, and bare nickel alloy at ~1 um
is roughly 0.25-0.35. The Gate 1 *fitted* absorptivity and this *derived*
decomposition agree independently.

Sensitivity across d50 15-45 um and powder/solid ratio 1.5-2.5: -0.12 to -0.30.
That is now the sweep range.

### The missing term, which is the real finding

An IN718 single-track study reports melt pool depth **decreasing with thicker**
powder layers. The model gave the opposite: depth fell from 69.70 to 65.37 um as
f_layer went 0 to +0.3 (thinner).

Not a wrong constant - a **missing physical term**. Eagar-Tsai is a semi-infinite
solid with no powder layer in it, so the layer fault had been shoehorned into the
only two knobs available. Energy spent melting the powder itself was absent.

    absorbed energy        0.384 * 285 / 0.960           = 114.0 J/m
    powder cross-section   40 um x 115 um x 0.55 packing = 2530 um^2
    mass per unit length   8190 x that                   = 20.7 mg/m
    enthalpy to melt       450*(1609-293) + 270e3        = 862 kJ/kg
    energy to melt layer                                 = 17.9 J/m

Melting the powder consumes **15.7%** of the absorbed energy, so a 10% layer
change is worth 1.6% of total energy against 3.0% from the absorptivity term,
**in the opposite direction**. Same order, opposite sign - which left the net
sign of the layer fault unreliable.

    layer_to_powder_enthalpy = phi/(1 - phi) = 0.157/0.843 = +0.186

**And it mattered.** Flipping the relative sign of the layer couplings moves
power/layer from 2.04 to 44.58 deg, a 20x change. The claim that layer is
confounded with power rested entirely on those signs.

### What the fix did

Net layer effect drops from +/-4% to **+/-1.2%** over a +/-20% thickness change,
which moves the model *towards* the review finding of no significant change in
depth or width between 20 and 60 um. Better agreement with literature, not worse.

| pair | instantaneous | enlarged | before |
|---|---|---|---|
| power / gas | **0.00** | 29.34 | 0.00 / 29.34 |
| power / layer | 3.46 | 36.40 | 2.04 / 36.31 |
| power / speed | 7.12 | 25.83 | 7.12 / 25.83 |

Rank 3 -> 5 and enlarged worst 25.83 deg, both unchanged. The power/gas column
ratio is now **exactly -1.0000** in all three sensors rather than -5.0001,
because both faults are now defined as acting directly on the same product.

Every constant became defensible and essentially nothing in the results moved.

### Still not literature-backed, both flagged

**layer_to_conductivity = +0.50 remains an estimate.** Published values bracket
powder conductivity at a tenth to a hundredth of solid, but the conductivity here
is a lumped *fitted* parameter, not the powder's own, so the ratio does not
transfer and nothing constrains its sensitivity to layer thickness. Declared an
estimate and swept. Mitigation: it is much the weakest of the three layer
effects - isolating each at f = 0.2 moves melt depth by 3.4% (absorptivity),
1.6% (enthalpy), 0.35% (conductivity).

**A modelling choice that flatters the paper, recorded deliberately.** Defining
f_gas as pure optical depth drops the convective-cooling channel a real gas-flow
fault would also have. That is exactly Tier 1's variant V1, under which power/gas
is non-isolable in *both* directions - **more** confounded than the baseline.
Since the headline is "confounded before, separable after", adopting the
more-confounded model makes the improvement look bigger. The quantitative
0.00 deg must therefore be reported as an **upper bound** on the confounding,
with the convection-included baseline stated as the conservative case. Restoring
the convection channel quantitatively needs a surface-loss term Eagar-Tsai does
not have, so it is named as a limitation rather than patched.

### Coupling sweep under the new definitions: invariance holds

Both derived constants swept over their *own derivation sensitivity* ranges
(d50 15-45 um and powder/solid ratio 1.5-2.5 for absorptivity; packing 0.45-0.65
and latent heat 250-290 kJ/kg for the enthalpy term), plus the one remaining
estimate over 0 to 1.5.

| swept | power/gas | enlarged worst | enlarged rank | condition |
|---|---|---|---|---|
| layer_to_absorptivity, -0.30 to -0.12 | 0.00 | 25.83 | 5 | 30-31 |
| layer_to_powder_enthalpy, 0.13 to 0.24 | 0.00 | 25.83 | 5 | 30-31 |
| layer_to_conductivity, 0 to 1.5 | 0.00 | 25.83 | 5 | 30-47 |

Every conclusion invariant. Power/gas stays exactly 0.00 deg - the column ratio
is -0.99999, -1.00000, -0.99993, spread 7e-05, which is finite-difference noise
on an exact algebraic identity.

### One result the sweep exposed, and it needs saying plainly

At `layer_to_conductivity = 0`, power/layer is **exactly 0.00 deg**. The reason is
the same algebra as power/gas: with the conductivity channel removed, a layer
fault acts only through absorptivity and through the powder-melting enthalpy, and
*both* of those are pure multipliers on the energy reaching the pool - which is
exactly what a power fault is.

So **the entire instantaneous separation of layer from power lives in the
conductivity channel** - the one coupling that is still an estimate rather than
derived. It buys 3.46 deg at the default and at most 3.76 deg at the top of its
range, all of it below the conventional 10 deg floor.

The honest reading is therefore the conservative one: power and layer are
effectively confounded instantaneously regardless of what that constant is, and
the paper should say so rather than quoting 3.46 deg as a separation. The result
does not depend on the estimate; it survives the estimate going to zero.

### The general lesson for the write-up

Nine or so quantities in this study were hand-set. Three are now eliminated by
physical definition, two derived from published measurement, one remains an
estimate. The ones that remain are defended by **sweeping**, never by a
plausible-sounding physical argument constructed after the fact. If a sentence in
the draft reads like a derivation of one of these constants, it is the same error
Amit caught, and the correct replacement is a sentence about the sweep.

## TWO FLAGS ON THE "BEFORE" PICTURE, BOTH POINTING THE SAME WAY

The paper's contribution is measured as the gap between the instantaneous result
and the enlarged one. Anything that makes the instantaneous case *more*
confounded inflates that gap. Two modelling choices do exactly that, and both
must be declared rather than left to a reviewer.

### Flag 1: the dropped convective channel (recorded earlier)

Defining f_gas as pure optical depth omits the convective cooling a real
gas-flow fault would also cause. That is Tier 1's variant V1, under which
power/gas is non-isolable in both directions - more confounded than the
baseline.

### Flag 2: plume attenuation is modelled as independent of power and speed

Our gas fault is pure Beer-Lambert: `absorptivity x exp(-f_gas)`, a constant
multiplier. That is what makes the power/gas degeneracy *exact*, since both then
act only on the product A*P.

But a coaxial photodiode study reports that **without a vapour plume, gas flow
speed has no effect on the photodiode signal, and once vaporisation is present
the effect depends on laser power, scan speed and focus position.** Physically
that is expected: the plume is produced by vaporisation, which power and speed
drive.

If attenuation genuinely depends on P and v, then f_gas is not a pure multiplier
on A*P, and **the exact 0.00 degree degeneracy would break** - power and gas
would separate by some second-order amount.

### What follows

- The reported 0.00 degrees is an **upper bound** on the instantaneous
  confounding, under both flags. It is not a neutral estimate.
- The structural claim survives either way: power and gas remain *strongly*
  confounded, and the rank limit is untouched, since it comes from counting
  channels rather than from this coupling's form.
- A plume-coupling term of the form `f_gas * g(P, v)` would make the model more
  faithful and the result more conservative. Eagar-Tsai has no plume, so it
  cannot be derived from the present model; it needs either the cited
  measurements or a vaporisation sub-model, and is named as further work.

## ROUTE B's CANDIDATE SENSORS WERE CHOSEN ON THE WRONG CRITERION

Raised by Amit. The four candidates - split camera axes, SWIR photodiode,
wide-band pyrometer - were selected on **cost tiering**: free, filter change,
new hardware. A procurement ladder.

None was selected on the criterion that Piece 6 shows is the only one that
matters: **does it observe something the melt pool's four channels do not
determine?** All four are functions of the same temperature field, so all four
were bound to add rows without adding rank. That outcome was predictable in
advance and was not predicted.

### The criterion, and the sensor classes that meet it

A sensor breaks a confound only by observing *upstream* of A*P - the cause
itself rather than its thermal consequence.

| fault | sensor class | literature |
|---|---|---|
| gas | plume / fume sensing | photodiode light barrier detecting fume crossing an optical path (*Prog. Addit. Manuf.* 2026); off-axis high-speed camera with optical filter separating plume from pool; statistical plume-signature monitoring |
| layer | powder bed / recoater sensing | IR layer-thickness measurement from post-recoat heat-up (Liu et al., *Addit. Manuf.* 2022); recoater-mounted optical scanner (Bugatti & Colosimo, *Addit. Manuf. Letters* 2022) |

The light barrier is the clearest case: it measures fume particles blocking a
beam and does not look at the melt pool at all.

### What can and cannot be claimed about them

**Cannot:** a quantified benefit. Eagar-Tsai has no plume and no powder layer, so
their Jacobian rows cannot be computed. Any number would be invented.

**Can:** the design rule, which is derived rather than asserted - *a sensor added
to break a confound must observe upstream of the shared channel; a sensor reading
the melt pool adds a row, not a direction.* Plus the two named classes that
satisfy it and the citations showing they exist.

That is a weaker claim than a computed angle and a more useful one, because it
generalises past these five faults and this suite. It should be stated as a
design rule in the discussion, not as a result.

## ROUTE C: WHICH FAULTS A NEW SENSOR WOULD SEPARATE - the abstract's third class

`src/route_c_added_sensor.py`. Route B's negative result (four melt-pool
observables add rows, not rank) did not discharge the abstract's promise of a
class "requiring an additional measurement". This does.

### The method, and why it needs no plume model

The sensors that would help - plume or fume sensing for gas, powder-bed or
recoater sensing for layer - cannot be simulated, because Eagar-Tsai has no plume
and no powder layer. Any Jacobian row for them would be invented.

So: **do not model the instrument, model what it measures.** Add a row `e_k` -
unit sensitivity to fault k and nothing else - with relative noise sigma_new.
That is the idealised best case for any instrument aimed at that cause, and it
brackets every real one. Hardware independent, and it answers exactly the
question the abstract asks.

### Result 1: which single measurement unlocks what

| measurement added | rank | worst | pairs >= 10 deg | newly cleared |
|---|---|---|---|---|
| gas | 4 | 3.46 | 8/10 | power/gas, speed/gas, layer/gas |
| power | 4 | 3.46 | 8/10 | power/speed, power/layer, power/gas |
| layer | 4 | 0.00 | 7/10 | power/layer, layer/gas |
| speed | 4 | 0.00 | 7/10 | power/speed, speed/gas |
| **geometry** | **3** | 0.00 | 5/10 | **none** |

Geometry is not worth measuring - it is already separated at 58-68 degrees, so a
direct reading adds nothing. That is a procurement recommendation.

### Result 2: precision is almost irrelevant

Sweeping a direct gas measurement from 50% down to 0.2% relative noise:

    rel. noise   50%    20%    10%     5%     2%     1%   0.2%
    worst pair  3.46   3.46   3.46   3.46   3.46   3.46   3.46
    pairs >=10  8/10   8/10   8/10   8/10   8/10   8/10   8/10

Nothing moves. The pairs a gas measurement unlocks are unlocked at any
precision, and the pair it does not touch (power/layer) is unaffected by its
quality.

**A crude measurement of the right cause beats a perfect measurement of the wrong
one.** That is a useful and slightly counter-intuitive sentence for a
manufacturing audience, and it follows directly from the geometry: adding a row
in a *new direction* changes the rank; making an existing row quieter does not.

### Result 3: the free method beats two idealised cause sensors

| pair | baseline | +2 ideal sensors (gas, layer) | Route A (free) |
|---|---|---|---|
| power / gas | 0.00 | 83.45 | 29.34 |
| power / layer | 3.46 | 87.59 | 36.40 |
| layer / gas | 3.46 | 89.73 | 44.58 |
| speed / gas | 7.12 | 83.51 | 36.47 |
| **power / speed** | 7.12 | **7.12** | **25.83** |
| speed / layer | 10.58 | 87.63 | 47.08 |
| | worst 0.00, rank 3, 5/10 | worst 7.12, rank 5, cond 546, 9/10 | **worst 25.83, rank 5, cond 30, 10/10** |

Route A wins on worst pair, on conditioning and on pairs cleared, against two
*perfect direct measurements of the causes themselves* - and costs nothing.

The reason is specific: **neither a gas sensor nor a layer sensor says anything
about power versus speed.** That pair is untouchable by added hardware of this
kind, and it is precisely what spatial context fixes.

The two approaches are complementary in character rather than competing. Added
sensors give enormous margin (83-90 deg) on the pairs they target; Route A gives
uniform moderate margin (26-47 deg) on all of them.

### The three classes, finally stated properly

The accepted abstract promised: resolvable from existing signals, requiring an
additional measurement, or structurally irreducible. With Route A and Route C
both computed, the honest version is:

1. **Resolvable from the temporal and spatial structure of existing signals** -
   all ten pairs, worst 25.83 deg, rank 5. No new hardware.
2. **Would benefit from an additional measurement** - the gas and layer pairs,
   which reach 83-90 deg with a direct cause measurement instead of 29-47 deg.
   This matters only where spatial context is unavailable: instant-by-instant
   isolation for real-time control, as opposed to diagnosis accumulated over a
   build.
3. **Structurally irreducible** - none, once spatial context is used.

That is a better answer than the abstract promised, and it carries a clean
engineering split: **post-build diagnosis needs no new hardware; real-time
per-segment isolation does, and crude direct sensing of the right cause is
enough.**

### What this does and does not license

**Does:** "a measurement of the gas fault, at any practical precision, separates
power/gas, speed/gas and layer/gas" - conditional, quantified, independent of
whether the instrument is a light barrier, a plume camera, or something not yet
built. Plus the design rule from the previous section, and the two named sensor
classes that satisfy it with citations.

**Does not:** any claim about a specific instrument's achievable performance, or
any assertion that a real plume sensor would attain the idealised row `e_gas`. A
real one would be contaminated - plume intensity depends on vaporisation, which
power and speed drive - so the idealised result is an upper bound on what such a
sensor buys. Stated as such.

## ABSTRACT AUDIT: what is promised, what is delivered, what is not

Amit asked whether the work was complete at the baseline. It is not, and the
audit turned up three commitments beyond the obvious one. Checked against the
accepted text, clause by clause.

| abstract clause | status |
|---|---|
| structural diagnosability analysis applied to LPBF | **done** - Tier 1, 11 equations, MSO enumeration, four sensitivity variants |
| reduced-order model generating sensor response to injected faults | **done** - Eagar-Tsai + keyhole correction, Gate 1 at 11.7% / 13.0% |
| five named fault modes | **done** - power, speed, layer, gas, geometry |
| noise "taken from published sensor characterisations" | **NOT AS STATED** - see below |
| class 1: resolvable from the temporal and spatial structure of existing signals | **Route A, pieces 7-11** - not optional, it is named in the abstract |
| class 2: requiring an additional measurement | **done** - Route C |
| class 3: structurally irreducible | **done** - the answer is *none*, once spatial context is used |
| "matrices reported for configurations found on current commercial machines" | **NOT DONE** |
| "predicted limits compared against defect classes and accuracies reported in the monitoring literature" | **NOT DONE** |

### Stopping at the baseline would empty class 1

"Temporal and spatial structure of existing signals" *is* Route A. Without it,
class 1 is empty, the paper reports that nothing is resolvable from existing
signals and everything needs new hardware - which Route C now shows is **false**
(the free method beats two idealised cause sensors). So the baseline is what
makes the three-way split measurable, not the deliverable.

### Deviation 1: the noise promise

The abstract says distinguishability is evaluated against noise levels **taken
from published sensor characterisations**. It was not. Only the Weaver camera
figure (U(k=2) = 6.2 um on 136.3 um, so sigma = 2.3% relative) was citable; the
NIST report AMS 100-35 is a thermal calibration study, not in-process noise
characterisation, and using its numbers would have looked rigorous and been
wrong. Amit's instruction was not to compromise airtightness for a citable
figure. So noise was treated as a *ratio* and swept across three assumptions.

That is defensible methodology and it does not match the abstract. Three options:

1. find citable in-process characterisations before submission,
2. reword the clause at submission,
3. state plainly in the paper that no suitable characterisations were found,
   and justify the ratio sweep on the grounds that angles, rank and condition
   number are invariant to a common scaling, so only relative noise matters.

**Option 3 is the honest one and probably right**, but it must be a declared
decision rather than a quiet omission. Note the cost: absolute detection
thresholds cannot then be claimed, which is already recorded.

### Deviation 2: named commercial configurations

The abstract promises matrices for "configurations found on current commercial
machines". Route B swept *generic* subsets - photodiode only, camera plus
pyrometer. Real machines from EOS, SLM Solutions, Concept Laser and Renishaw
ship different suites, and the promise is a matrix per real configuration.

A literature task (establish what each vendor actually ships) plus a re-run of
`route_b.py` with those subsets. Not difficult, not started.

### Deviation 3: the comparison against reported accuracies

The closing sentence promises the predicted limits are *compared* against defect
classes and accuracies in the monitoring literature. The 18-row extraction table
exists; the comparison does not.

The interesting case to look for: a paper reporting high accuracy separating two
things this analysis says are confounded. That is either a problem for us or -
far more likely - evidence they are separating **outcomes** rather than causes,
which is the paper's central distinction and would be strong supporting
material. Either way it must be run, not assumed.

### Remaining work, in order

    1. Route A, class 1                    pieces 7-11, the largest item
    2. named commercial configurations     literature + re-run
    3. comparison against published accuracies
    4. decide and declare the noise position
    5. figures, writing

## THE DIAGNOSABILITY MATRIX - the abstract's headline deliverable, assembled

`src/matrix.py`. Every ingredient existed across the other modules; nothing had
assembled them into the artefact the abstract actually names.

### The first attempt was degenerate, and that was informative

Classifying on the enlarged observation alone put **all ten pairs in class 1 for
every configuration, including a single photodiode**. True, and useless: classes
2 and 3 come out empty and the matrix discriminates nothing.

The cause is Route A itself - regressing onto known build context converts a
static problem into a regression whose equation count is set by the regressors,
so one sensor already reaches rank 5.

### The fix: report two regimes

    INSTANTANEOUS   per-segment decisions in real time, no opportunity to
                    accumulate context. Closed-loop control lives here.
    ACCUMULATED     diagnosis over a completed build or a substantial part of
                    one. Post-build qualification and drift monitoring.

This is an engineering distinction a machine builder actually faces, and it is
where the structure is.

### The matrix, baseline coaxial suite

| pair | instant | class | enlarged | class | what changes it |
|---|---|---|---|---|---|
| power / gas | 0.00 | **2** | 29.34 | 1 | measure power, or use build context |
| power / layer | 3.46 | **2** | 36.40 | 1 | measure power, or use build context |
| layer / gas | 3.46 | **2** | 44.58 | 1 | measure layer, or use build context |
| speed / gas | 7.12 | **2** | 36.47 | 1 | measure speed, or use build context |
| power / speed | 7.12 | **2** | 25.83 | 1 | measure power, or use build context |
| speed / layer | 10.58 | 1 | 47.08 | 1 | - |
| layer / geometry | 58.40 | 1 | 66.45 | 1 | - |
| power / geometry | 61.39 | 1 | 64.30 | 1 | - |
| gas / geometry | 61.40 | 1 | 65.80 | 1 | - |
| speed / geometry | 67.64 | 1 | 71.13 | 1 | - |

    instantaneous:  class 1  5/10   class 2  5/10   class 3  0/10
    accumulated:    class 1 10/10   class 2  0/10   class 3  0/10

**Class 3 is empty in both regimes.** Nothing is structurally irreducible for
this suite. That is a stronger answer than the abstract promised and it should
be stated as such rather than hidden by reporting only one regime.

### Per-pair contrast requirement - the honest form of the accumulated result

The accumulated column rests on the modulation profiles, which are asserted.
Reporting one angle hides that. So the matrix also reports, per pair, the
smallest profile contrast at which it clears the floor (1.0 = the asserted
strength):

| pair | contrast needed |
|---|---|
| the four geometry pairs, speed/layer | **0.05** |
| layer / gas | 0.15 |
| power / layer, speed / gas | 0.25 |
| **power / speed, power / gas** | **0.40** |

Even the two hardest pairs need only **40% of the asserted profile strength**.
The accumulated-regime conclusion therefore survives the profiles being 2.5x
weaker than claimed, which is a far stronger statement than quoting 29.34 deg.

This is the number to put in the paper. It lets a reader judge the result
against their own view of how strongly faults vary across a build, rather than
having to accept ours.

### A fourth label carried alongside

Each pair is also flagged **structurally isolable** - separable from the zero
pattern of the equations alone, with no reliance on calibrated magnitudes. A
class 1 pair that is also structurally isolable survives any amount of
calibration error. At the current structural threshold all ten are, so the flag
does not discriminate here; it is retained because it discriminates under other
scan plans (see the plan-dependence section) and because its meaning is what
separates the two tiers.

## COMMERCIAL CONFIGURATIONS - the abstract's "current commercial machines"

> **Policy, decided later: the paper names no commercial products.** Vendor names
> are retained *in this record only*, for traceability of how the configurations
> were derived. In the paper they appear as configurations A to E, described by
> contents. See "VENDOR NAMES REMOVED" below.

`src/commercial.py`. Route B swept generic subsets; the abstract promises real
vendor suites. Mapped from secondary literature onto this study's observables.

### Verification status, which is weak and must improve before submission

Vendor details come from reviews and comparative studies, not datasheets, and
the sources disagree. Detection bands are commonly withheld - one study records
them as "protected under the confidentiality clause by the supplier". SLM's MPM
is described in one source as two photodiodes of different spectral range and in
another as a coaxial pyrometer; modelled as two bands, the more conservative
reading. Concept Laser's QM Meltpool 3D appears only as a table entry. **Every
row needs checking against vendor documentation.** The method does not depend on
these being exactly right; the per-vendor conclusions do.

### The matrices

| configuration | inst rank | inst class 1 | class 2 | class 3 | accum rank | accum class 1 | accum worst |
|---|---|---|---|---|---|---|---|
| EOS, MeltPool only | 1 | 0 | 10 | 0 | 5 | 10 | 24.89 |
| EOS, MeltPool + Exposure OT | 2 | 4 | 6 | 0 | 5 | 10 | 24.97 |
| SLM Solutions MPM | 2 | 0 | 10 | 0 | 5 | 10 | 24.89 |
| Concept Laser QM Meltpool 3D | 2 | 4 | 6 | 0 | 5 | 10 | 24.97 |
| **Renishaw InfiniAM Spectral** | **3** | **4** | 6 | 0 | 5 | 10 | **31.89** |
| research-grade reference | 3 | 5 | 5 | 0 | 5 | 10 | 25.83 |

**Class 3 is empty for every commercial configuration in both regimes.** And
every one of them reaches 10/10 in the accumulated regime - including a single
photodiode. The paper's positive result is not conditional on owning a
well-instrumented machine.

### SUPERSEDED - see "Renishaw unresolved" below. The original finding read:

**Renishaw's InfiniAM Spectral is the only commercial configuration that
separates power from gas instantaneously, at 84.02 degrees.**

| configuration | power/gas, instantaneous |
|---|---|
| EOS MeltPool only | 0.00 confounded |
| EOS MeltPool + Exposure OT | 0.00 confounded |
| SLM Solutions MPM | 0.00 confounded |
| Concept Laser QM Meltpool 3D | 0.00 confounded |
| **Renishaw InfiniAM Spectral** | **84.02 SEPARATED** |
| research-grade reference | 0.00 confounded |

The reason is specific and it is exactly Route C's mechanism. InfiniAM pairs
MeltVIEW (melt pool emissions, NIR and IR) with **LaserVIEW, described as a
photosensitive diode measuring the intensity of the laser energy**. If LaserVIEW
reads laser output *upstream of the plume*, it is a direct measurement of
delivered power that does not see gas attenuation - the sensor Route C predicts
breaks the confound, already fitted to a production machine.

**Conditional on that reading being correct**, and it rests on secondary
literature. It is the single most important line to verify against vendor
documentation, because it turns an abstract design rule into a statement about a
machine people own. If LaserVIEW instead sits after the plume, it is another
melt-pool observable and the row collapses to the others.

### A second, quieter finding

SLM's two-spectral-band suite (0.00 to 7.4 deg across all pairs) performs worse
than EOS's photodiode-plus-camera (0.00 to 16.9 deg), despite both having two
observables. Two spectral bands of the same emitted light are close to
redundant; a *geometric* measurement adds a genuinely different direction.

That is the same lesson as Route B's failed candidates and the split-camera
success, now visible across real products: **adding a different wavelength buys
little, adding a different physical quantity buys more.**

## HOW WRONG CAN THE PATTERNS BE? - permutation and collapse tests

Raised by Amit asking what had actually been assumed. The profile *strengths*
were already swept; the **assignment** - which fault follows which build
variable - was not. That was the gap, and it is now closed.

### Assignment does not matter

All 120 possible reassignments of the five patterns to the five faults:

    rank 5 in 120/120 cases
    worst pair:  min 17.13   median 23.84   max 30.58   (asserted: 25.83)

So it is irrelevant *which* fault follows *which* variable. Only that they
differ. The result does not rest on having guessed the assignments correctly -
a far better position than defending five individual claims.

### What would break it: two faults sharing a pattern

Collapsing one fault's pattern onto another's:

| forced equal | worst pair |
|---|---|
| layer = gas | **3.84** breaks |
| speed = gas | **8.12** breaks |
| speed = layer | 13.02 |
| power = speed | 15.47 |
| power = gas | 15.98 |
| power = layer | 18.34 |
| anything = geometry | 25.83 unchanged |

**The paper's real dependency is a single question:** do the recoater fault and
gas degradation vary differently across a build? Physically they obviously do -
one is layer-periodic, the other spatial along the flow - but that is now the
one assumption carrying weight and it should be named as such rather than buried
among five.

### Consequence for the data hunt

Anything sharing a pattern with geometry leaves the answer at 25.83 deg,
unchanged. **The geometry pattern is the least load-bearing of the five**, so
the NIST overhang dataset - which validates exactly that pattern - is
nice-to-have rather than blocking. It was dropped on this basis.

The pattern worth chasing is **layer periodicity from recoating**. Gas already
has support (Raj et al.).

### For the paper

This belongs in the robustness subsection and strengthens it. The claim becomes:

> The result does not depend on the assigned patterns being correct - all 120
> reassignments give rank 5 and 17 to 31 degrees. It depends only on the faults
> varying distinguishably, and specifically on the recoater and gas faults not
> sharing a pattern.

That is one named, physically obvious condition in place of five asserted ones.

## RENISHAW UNRESOLVED - modelled conservatively, and the claim is better for it

Amit could not obtain the verification, so the question of where LaserVIEW sits
in the optical path stays open. Resolved by taking the assumption that does
**not** flatter the paper - the same principle already applied to the dropped gas
convection channel and to plume attenuation.

### The decision

LaserVIEW is now modelled as a **melt-pool observable** (downstream of the
plume). Renishaw's row therefore reads 0.00 degrees like every other commercial
configuration.

Rationale: asserting the favourable reading risks publishing a false claim about
a commercial product. Understating costs nothing that a single sentence from the
vendor could not correct. Asymmetric downside, so take the safe side.

### The claim that replaces it is stronger

| configuration | power/gas, instantaneous |
|---|---|
| every named commercial suite examined | **0.00 confounded** |
| *any suite with upstream power monitoring* | ***84.02 separated*** |

**No commercial configuration we could establish separates power from gas.** The
84 degrees now belongs to a configuration *type* - "includes a direct measurement
of delivered laser power, sampled upstream of the process zone" - which follows
from our own analysis and needs no vendor verification at all.

That is a better paper claim than the original. It is a **design recommendation**
rather than a product endorsement, it cannot be falsified by a datasheet, and it
generalises to any machine anyone builds.

### What stays in the paper about Renishaw

One hedged paragraph: the review literature describes LaserVIEW as a photodiode
measuring laser energy; whether it samples upstream decides which of the two rows
applies; we could not establish it; we assume the unfavourable case. That is
honest, it flags a question worth answering, and it invites the vendor or a
reader to settle it - a legitimate thing for a paper to do.

### Pattern worth noting

This is the third time a choice has been made against the paper's own interest -
the gas convection channel, plume attenuation depending on power and speed, and
now LaserVIEW. All three make the instantaneous baseline look *less* confounded
or the suites look *worse* than the favourable reading would.

They should be collected into one short paragraph in the limitations section
rather than scattered. A reviewer who sees three conservative choices stated
together trusts the rest of the paper more, not less.

## VENDOR NAMES REMOVED FROM THE PAPER

Amit's decision: no actual company product is named. Implemented, and it
improved the section rather than costing anything.

### Why it is also the better academic choice

The mapping from product to observable rested on **secondary review literature,
not datasheets**. Detection bands are routinely withheld under supplier
confidentiality, and published descriptions of the same product disagree.
Attaching a named product to a computed diagnosability limit on that basis
asserts more than the evidence carries. The anonymity now *follows from* the
verification problem rather than being imposed on top of it.

### What it revealed

Stripping the names collapsed the table. **Across five commercial systems there
are only three distinct configurations** for this analysis - several vendors
ship what is effectively the same instrument set. The vendor-by-vendor
presentation hid that.

| configuration | inst. rank | class 1 | power/gas |
|---|---|---|---|
| A single coaxial photodiode | 1 | 0/10 | 0.00 |
| B photodiode + melt pool imaging | 2 | 4/10 | 0.00 |
| C two photodiodes, separate bands | 2 | 0/10 | 0.00 |
| D research reference | 3 | 5/10 | 0.00 |
| **E = C + upstream power monitoring** | 3 | 4/10 | **84.02** |

### The claim is now more general

Was: *"one named product separates power from gas."*

Is: *"no configuration built from melt-pool observables alone separates power
from gas, whatever its sensor count; adding upstream delivered-power sensing
does, at 84 degrees."*

The second holds for any machine anyone builds, cannot be contradicted by a
datasheet, and needs no verification beyond our own analysis.

### Where names legitimately remain

`07-literature-extraction.md` records Raj et al.'s own stated equipment when
describing their experiment. That is ordinary citation practice, not product
endorsement, and it stays.

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
