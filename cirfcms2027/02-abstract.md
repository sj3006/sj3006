# Abstract

## Title

**Primary:** Model-based diagnosability analysis of in-situ sensor suites for
laser powder bed fusion

**Alternative**, if the venue tolerates a question title — states the
contribution better and gets read more:
Which process faults can be told apart? Diagnosability limits of in-situ
monitoring in laser powder bed fusion

## Submission abstract

> In-situ monitoring is standard on metal additive manufacturing systems, and
> machine learning classifiers now report high accuracies for detecting defects
> from photodiode, acoustic and imaging signals. Those results are obtained per
> study, on defect class sets chosen by their authors, and they do not answer a
> question a machine builder faces before specifying hardware: which faults can a
> given sensor configuration separate in principle, and which remain confounded
> regardless of the classifier used. Where two faults produce signatures differing
> by less than the sensor noise, no volume of training data will distinguish them,
> and the limit is structural rather than algorithmic. This paper applies
> structural diagnosability analysis, established in process control for
> automotive and aerospace systems but not previously used in additive
> manufacturing, to laser powder bed fusion. A reduced-order process model
> generates the response of a specified sensor suite to injected fault modes,
> covering laser power and scan speed deviation, thin powder layers from recoater
> short-feed, degraded shielding gas flow, and geometry-driven heat accumulation.
> Pairwise distinguishability is evaluated against noise levels taken from
> published sensor characterisations. The result is a diagnosability matrix per
> sensor configuration, separating fault pairs into those resolvable from the
> temporal and spatial structure of existing signals, those requiring an
> additional measurement, and those structurally irreducible for the
> configuration. Matrices are reported for configurations found on current
> commercial machines, and the predicted limits are compared against the defect
> classes and accuracies reported in the monitoring literature.

Roughly 250 words. If the limit is 200, cut the final sentence and fold the
literature comparison into the preceding one.

**Keywords:** Additive manufacturing; Process monitoring; Diagnosability;
Fault diagnosis; Laser powder bed fusion

## What this commits to, and what it leaves open

Committed: the framework, the five fault modes, noise calibration from published
characterisations, and the three-way matrix. All four are under our control and
will exist regardless of how the numbers land.

Deliberately open: *which* pairs turn out confounded. Whatever the analysis
returns is a valid result, so there is no outcome that makes the abstract untrue.

Softly worded on purpose: the literature comparison says the predicted limits are
*compared* against reported accuracies, not that they agree. If the comparison
comes out messy it can still be reported honestly.

## Note on the noise source

An earlier draft took noise levels from a specific public dataset. That was
changed to "published sensor characterisations" so that nothing in the abstract
depends on obtaining any particular dataset. Benchmark data can still be used if
it becomes available, but the promise does not rest on it.

## Causes versus outcomes

The abstract says "fault modes", which is correct but easy to misread as defect
classes. Make sure the introduction states plainly that the analysis concerns
process **causes** (power, speed, layer thickness, gas flow, geometric heat
accumulation), not defect **outcomes** (keyhole, lack of fusion, balling).

Reviewers who conflate the two will think the paper contradicts well-established
classification results. It does not — see `01-vision.md` for the full argument. If
the word count allows, add "process fault causes" rather than "fault modes" in the
method sentence.

## Framing variant

If the conference track is digital-twin flavoured, lead the method sentence with
the process model as a twin of the machine and its sensors. The content is
unchanged; it just lands in the right session.
