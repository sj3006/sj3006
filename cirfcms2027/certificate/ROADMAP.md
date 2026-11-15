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

### WP3  Case generator  (`cases.py`)
Observations drawn from the **full nonlinear forward model**, not the
linearisation, so the certificate test faces the same model error an agent would.
Magnitudes are chosen to hit a target whitened SNR, `f_k = rho / ||Jw[:,k]||`,
rather than a common `f`: the fault magnitudes are severity indices on different
scales, so a shared `f` would not compare equal severities. Each case records
the truth, the observation, the certificate, and the linearisation residual.

### WP4  Agent backends  (`agents.py`)
A common interface returning a reported set of causes plus a stated confidence.
- `MaximumLikelihood`: argmin R_k, a single cause always. The conventional
  baseline, and the thing a classifier does.
- `Certificate`: returns C_alpha. Coverage is 1 - alpha by construction; its
  cost is mean set size.
- `Language model`, unconstrained: the observation and the process context in
  prose, the five candidate causes described physically, no Jacobian. Asked for
  a cause.
- `Language model`, constrained: the same, with the certificate supplied as a
  tool result, and instructed that it may not narrow beyond it without naming
  an admissible probe.

### WP5  Benchmark  (`benchmark.py`)
Metrics, over a case set stratified by SNR, regime and suite:
- **over-attribution rate**: the agent asserted a unique cause while the
  certificate held two or more. The headline number.
- **certified coverage**: truth inside the reported set.
- **set size**: the price of honesty, in mean causes reported.
- **admissibility**: reported set is a subset of the certificate.
Deterministic baselines run with no external service. The language-model arms
need an API credential, which is the one open decision (see below).

### WP6  Probe planning  (`probe.py`, optional)
Where a degeneracy can be broken by changing the operating point, and the
structural ceiling where it cannot. Carried only if WP1 to WP5 land early; this
is idea 3 from the brainstorm and can be a separate paper.

## Open decisions

1. **Whose account runs the language-model arms.** Needed before WP5 can
   report. If the runs should happen here, an API credential for
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
