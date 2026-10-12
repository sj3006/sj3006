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

**The headline numbers move** and these are now canonical: power/gas
0.00 -> **41.44 deg**, worst pair **38.49 deg** (power/layer), rank 3 -> 5,
worst finite collinearity index 141,869 -> **2.1**. The projection matrix is also
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
