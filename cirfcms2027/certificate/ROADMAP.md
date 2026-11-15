# What a monitoring agent is entitled to conclude

Journal extension of the CIRP conference paper. Simulation only; no experimental
campaign required. Target venues, in order of fit: Journal of Manufacturing
Systems, Advanced Engineering Informatics, Robotics and Computer-Integrated
Manufacturing.

## The claim

An AI assistant that reads in-situ monitoring data and names a process cause is
making a statement the data may not license. For some cause pairs the question
is not hard, it is undecidable: power and shielding gas sit at 0.00 degrees in
the whitened sensitivity geometry, so no classifier, no training set and no
language model separates them from melt-pool observables at a single instant.
An unconstrained agent will name one anyway.

This paper supplies the missing layer. Before the agent asserts a cause, a
statistical test on the sensitivity geometry returns the set of causes the
observation actually admits. The agent reports the set. The contribution is the
constraint, the proof that it is tight, and a measurement of how often
unconstrained agents violate it.

## The formal object

A fault is a type `k` and a magnitude `f`. To first order the whitened relative
sensor deviation is

    z_w = f * Jw[:,k] + e ,      e ~ N(0, I_S)

Profiling out the unknown magnitude leaves, for each candidate type `k`, a
residual

    R_k = || z_w ||^2 - <z_w, u_k>^2 ,     u_k = Jw[:,k] / || Jw[:,k] ||

which under the hypothesis that `k` is the true cause is distributed as
chi-squared on `S - 1` degrees of freedom, whatever the magnitude. The
**certificate set** is

    C_alpha(z) = { k : R_k <= q_{1-alpha}(S-1) }

and it contains the true cause with probability exactly `1 - alpha`. No prior,
no asymptotics, no training.

Geometrically, with `rho = || z_w ||` the whitened signal-to-noise ratio and
`psi_k` the angle between the observation and fault `k`'s signature direction,

    R_k = rho^2 sin^2(psi_k)   so   k in C_alpha  <=>  sin psi_k <= sqrt(q)/rho

The certificate is a cone of half-angle `psi* = arcsin(sqrt(q)/rho)` about the
observation. Every fault direction inside the cone is admissible.

### This derives the conference paper's separation floor

Two faults at mutual angle `D` both fall inside the cone when the observation
sits near their bisector, so the pair is resolvable only if

    D > 2 * arcsin( sqrt(q_{1-alpha}(S-1)) / rho )

The 10 degree floor of the conference paper was a stated convention. It is
instead an implicit assumption about signal-to-noise, and this inequality makes
it explicit. Section 1 of the results reports the exact `rho` it corresponds to.

## Work packages

### WP1  Inference core  (`inference.py`)
Residuals, certificate sets, cone half-angles, the resolvability inequality, and
the floor-to-SNR correspondence. Instantaneous and build-context regimes share
one implementation; the build-context case is the same algebra on the enlarged
Jacobian with coefficient noise and `S*N - 1` degrees of freedom.
**Status: done.**

### WP2  Equivalence structure  (`classes.py`)
The ambiguity graph at a given `(rho, alpha)`: an edge wherever a pair is not
resolvable. Report connected components and the maximal cliques of the
complement, and state plainly which is conservative. Resolvability is not
transitive, so the graph is the honest object and components are a summary.
Sweep `rho` to show the partition coarsening, and identify which merges are
structural (power/gas, from the rank bound) rather than merely noise-limited.
**Status: done** (`classes.py`). Instantaneously all five causes form one class
up to rho = 56 and a four-member clique at rho = 120; with build context, five
singletons from rho = 14 up.

### WP3  Case generator and the exact test  (`cases.py`)
Observations drawn from the **full nonlinear forward model**, not the
linearisation, so the certificate test faces the same model error an agent would.

The linearised residual is only valid in a bounded signal-to-noise window, which
is measured rather than assumed: coverage holds at rho = 28 but falls to 0.68 by
rho = 120, because the exact response curves away from its own linear signature
and that departure enters the residual as a bias. The certificate is therefore
built on the exact profile residual

    R_k(z) = min over f of || z_w - g_k(f) / (sigma eps) ||^2

with `g_k` the exact forward response, which restores nominal coverage at every
signal-to-noise ratio tested. Response curves are cached as monotone cubic
interpolants over a magnitude grid, 49 forward evaluations per fault, so the
per-case cost is a table lookup. The linearised test is kept as a reported
comparison, not as the method.
Magnitudes are chosen to hit a target whitened SNR, `f_k = rho / ||Jw[:,k]||`,
rather than a common `f`: the fault magnitudes are severity indices on different
scales, so a shared `f` would not compare equal severities. Each case records
the truth, the observation, the certificate, and the linearisation residual.
**Status: done** (`cases.py`). Exact coverage 0.940 to 0.957 at every signal
level in both regimes, against 0.784 for the linearised test at rho = 120.

### WP4  Agent backends  (`agents.py`)
A common interface returning a reported set of causes plus a stated confidence.
- `MaximumLikelihood`: argmin R_k, a single cause always. The conventional
  baseline, and the thing a classifier does.
- `Certificate`: returns C_alpha. Coverage is 1 - alpha by construction; its
  cost is mean set size.
- `Language model`, unconstrained: the observation and the process context in
  prose, the five candidate causes described physically, no Jacobian. Asked for
  a cause.
- `Language model`, constrained: the same, with the certificate supplied in the
  prompt, instructed that it may not narrow beyond it without naming an
  admissible probe, and with the intersection enforced in code rather than
  trusted to the instruction.

**Status: done** (`agents.py`). Two further arms were added because without
them a language-model score means nothing: `Everything`, which hedges on all
five and so scores a perfect zero over-attribution, and `Chance`, which fixes
the zero point of the skill metric. Both prompt styles are committed verbatim,
neutral and operator, so the difference between asking "which causes are
consistent" and "what went wrong" is measurable rather than an unstated
confound. A `ScriptedBackend` replays recorded replies so the scoring can be
changed and re-run without paying for the calls again.

### WP5  Benchmark  (`benchmark.py`)
Metrics, over a case set stratified by SNR, regime and suite:
- **over-attribution rate**: the agent asserted a unique cause while the
  certificate held two or more. The headline number.
- **certified coverage**: truth inside the reported set.
- **set size**: the price of honesty, in mean causes reported.
- **admissibility**: reported set is a subset of the certificate.
- **decisiveness**: named one cause when the certificate held one. Required,
  because over-attribution alone is trivially optimised by never committing.
- **skill**: accuracy among over-attributions against the chance rate on those
  same cases, normalised so chance is zero and perfect is one.

**Status: done** (`benchmark.py`). The deterministic arms run with no external
service and are reported below. The language-model arms need a credential,
which is the one open decision.

Measured on 6000 cases per regime, 300 per fault and signal level:

| arm | coverage | mean set | over-att | decisive | skill |
|---|---|---|---|---|---|
| oracle | 1.000 | 1.00 | 1.000 | 1.000 | 1.00 |
| maximum likelihood | 0.440 | 1.00 | 1.000 | 1.000 | 0.17 |
| certificate | 0.951 | 3.70 | 0.000 | 1.000 | n/a |
| everything | 1.000 | 5.00 | 0.000 | 0.000 | n/a |
| chance | 0.201 | 1.00 | 1.000 | 1.000 | -0.08 |

Instantaneous regime, where 87.6 % of cases are ambiguous. The build-context
regime has 2 ambiguous cases in 6000, so over-attribution has no signal there
and decisiveness carries the measurement instead.

### WP6  Probe planning  (`probe.py`)
Where a degeneracy can be broken by changing the operating point, and the
structural ceiling where it cannot. **Status: done**, and the result is
negative, which is more useful than the positive one would have been.

The Jacobian factors as `J = M C`: `C` is 4 by 5 and says how each fault moves
each of the four physical channels, `M` is 3 by 4 and says how each observable
responds to each channel. A probe changes `M` and can never touch `C`. Since a
power fault raises absorbed power and a gas fault lowers it and neither does
anything else, `C[:, power] = -C[:, gas]` exactly, so `(M C)[:, power]` and
`(M C)[:, gas]` are antiparallel for every `M` whatever. The null space of `C`
is one-dimensional and is exactly that direction.

So the conference paper's claim strengthens. There, power and gas were
confounded for one suite at one operating point. Here they are confounded for
every suite at every operating point and in any stack of operating points, and
the proof is four entries of a matrix rather than a numerical coincidence.

Probing does not rescue the other nine pairs either. Two well-chosen operating
points take the second-worst pair from 0.32 to 5.95 degrees, short of the
floor; four points reach nominal rank 4 with a condition number of 289000,
which is rank in name only. The reason is that the preheat channel is
intrinsically weak, `M[:, preheat]` being three orders of magnitude below
`M[:, absorbed power]` at every operating point, because a kelvin of preheat
barely moves a pool running near 3000 K.

What escapes the ceiling is not a richer observation but differential
modulation: build context works because `B[:, power]` and `B[:, gas]` are not
proportional even though the channel columns are. That makes WP6 the complement
of the build-context result rather than a competitor to it, and it supplies the
sentence the paper wants: the only thing that separates a power fault from a gas
fault is that the two vary differently across a build.

## Open decisions

1. **Whose account runs the language-model arms.** The only thing now
   blocking a result. Everything else in WP4 and WP5 is built and tested. If the runs should happen here, an API credential for
   `api.anthropic.com` can be requested in-session; if the paper should report
   several vendors, the keys and the cost belong on the authors' side and the
   harness will take them from the environment.
2. **How many fault types the agent chooses among.** Five is the conference
   paper's set. Including a "no fault" option changes the test to a composite
   null and is worth doing, but it is a second test, not a sixth column.
3. **Whether the build-context arm needs its own prompt.** The coefficient
   matrix is 3 by 5 per segment group and does not read naturally as prose.

## What is deliberately not claimed

The agent does not do the inference better than an estimator; it does not do it
as well. The geometry and the residual test do the inference. The agent's role
is orchestration over evidence with no numerical form and communication of a
hedged conclusion. The paper says so, in those words, in the introduction.
