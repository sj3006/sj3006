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
