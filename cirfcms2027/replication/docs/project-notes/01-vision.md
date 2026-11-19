# Vision and problem statement

## The pitch, in one paragraph

Metal AM machines ship with monitoring hardware, and the research community has
spent a decade proving that machine learning can classify defects from those
signals. What nobody has established is what those sensors can resolve *in
principle*. If two process faults produce measured signatures differing by less
than the sensor noise, no classifier separates them — that is a property of the
sensor configuration, not of the algorithm. This project builds a physics-based
forward model that predicts what each sensor would report under each fault, then
applies structural diagnosability analysis, standard in automotive and aerospace
fault diagnosis, to determine which faults a configuration can isolate. The output
tells a machine builder what monitoring hardware buys them before they buy it.

## Problem statement

In-situ monitoring is now standard on metal additive manufacturing systems.
Photodiodes, coaxial cameras, pyrometers and acoustic sensors are fitted as
standard, and a large literature reports high accuracies for classifying defects
from those signals using machine learning.

Those results share a structural weakness. Each is obtained on a defect class set
chosen by its own authors, under conditions they selected. A reported accuracy
therefore describes how one model performed on one self-selected problem. It does
not tell a machine builder, who must specify sensor hardware before any of that
data exists, which faults their configuration will be able to separate.

The question underneath is not about algorithms. Where two faults produce measured
signatures that differ by less than the sensor noise, no volume of training data
will distinguish them. The information is absent from the signal. The limit is
structural, and it can be determined from a model of the process and the sensors
before a single measurement is taken.

Structural diagnosability analysis answers exactly this question and is routine in
process control — anti-lock braking systems, turbo-shaft engines, sensor networks.
It has not been applied to additive manufacturing.

## What the paper claims

1. A physics-based forward model of LPBF sensor response under injected faults.
2. The first application of structural diagnosability analysis to LPBF monitoring.
3. A three-way classification of fault pairs per sensor configuration:
   - resolvable from the temporal and spatial structure of existing signals
   - resolvable only by adding a specific measurement
   - structurally irreducible for that configuration
4. A comparison of predicted limits against the class sets and accuracies
   reported in the published monitoring literature.

Claim 3 is what makes this more than a negative result. Claim 4 is the part that
tests whether the community's benchmarks have been avoiding the hard pairs.

## Why the third category matters most

Saying "these two faults will never be separable with any sensor package of this
type" is a stronger and more useful statement than any accuracy figure. It is also
the kind of claim that only a model-based analysis can make — no amount of
empirical work establishes an impossibility.

## Causes, not outcomes — read this before defending the paper

The single most likely reviewer objection is: "classifiers already report 99%
accuracy on defect detection, so how can you claim faults are indistinguishable?"

The answer is that the literature and this paper are answering different
questions.

Most published monitoring work classifies **outcomes**: keyhole pore, lack of
fusion, balling, conduction mode, nominal. Those describe what went wrong with the
material. This paper's fault modes are **causes**: low power, high speed, thin
powder layer, degraded gas flow, geometric heat accumulation. Those describe why
it went wrong.

Outcomes can be easy to separate while causes are hard. A keyhole melt pool and a
lack-of-fusion melt pool genuinely look different. But two causes that produce the
same melt pool state are, by construction, indistinguishable at that instant. A
paper classifying keyhole against lack of fusion never asks whether a given
lack-of-fusion event came from low power or from high scan speed, because both
land in the same outcome class. The confusion is invisible because the question is
never posed.

Four further reasons high accuracies coexist with genuine confounding:

- Many headline figures are binary detection (anomaly versus nominal), which is
  far easier than multi-class isolation.
- Tested fault magnitudes are usually large and widely spaced (nominal, -20%,
  +20%). This paper asks about local distinguishability near nominal. Those are
  our detectability threshold and our isolability angle respectively — both fall
  out of the same framework.
- Where confusable classes *are* included, published confusion matrices do show
  the failures (cracks predicted as pinholes, spatter confused with holes). That
  corroborates the prediction rather than contradicting it.
- Sequence models on video or full scan-line traces already exploit temporal
  structure, which is route A in `03-technical-stack.md`. The framework therefore
  *explains* why sequence models outperform instantaneous-feature models.

**Why causes matter even though the field monitors outcomes.** Outcomes tell an
operator that something went wrong. Causes tell them what to change. Detecting a
keyhole pore after the fact does not say whether to lower power or slow the scan,
and if those two are confounded in the sensor signal, no monitoring system can
say. Process control, parameter correction and root-cause analysis all need
causes.

State this distinction explicitly in the introduction. One sentence removes the
objection.

## Scope boundaries

In scope: one alloy, one process (LPBF), five fault modes, three to four sensor
models, single-track and layer-scale analysis.

Out of scope: multi-material, part-scale thermal history, microstructure,
closed-loop control design, any experimental validation.

## Positioning against the existing literature

The empirical monitoring literature is strong and should be acknowledged as such
in the introduction rather than ignored. The argument is not that those results
are wrong. It is that they are per-study and per-class-set, and that a
configuration-level answer requires a different kind of analysis.

Overclaiming here is the main review risk. Frame the contribution as a first
application of an established method, not as a new method.
