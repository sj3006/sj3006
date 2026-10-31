# Measuring the modulation profiles instead of asserting them

The five modulation profiles are this work's largest exposure. They drive the
entire accumulated-regime result - the shared-profile control shows that if all
five are identical, the enlarged observation collapses back to the instantaneous
one exactly - and four of the five are asserted rather than measured.

This file sets out a method for converting published melt pool measurements into
profile amplitudes, applies it to two of the five, and records what it would take
to fix the rest.

---

# Part A - The inversion method

## A1. The problem

A modulation profile is a claim about **fault severity**: "a gas fault is 6x
worse at the downstream end of the plate than the upstream end." Published
benchmark work does not measure fault severity. It measures **melt pool
geometry** - widths and depths in micrometres.

The two are connected by the forward model. So the conversion is:

    measured melt pool change  ->  [invert the forward model]  ->  fault units

Concretely: find the fault magnitude `f` that reproduces the measured melt pool
change, and that `f` is the measured amplitude of that fault channel.

## A2. Which dimension to invert through

**Depth, not width.** At the base case the model's depth error is +1.72 %, which
is 0.2x the measurement's own expanded uncertainty; its width error is -15.54 %,
3.4x that uncertainty, and systematically negative at all seven conditions (see
`06-the-base-case.md`). Inverting through width would propagate a known
one-sided model bias straight into the answer. Depth is the channel the model
gets right.

## A3. What the method inherits

The result is only as good as the forward model between the two. Any inversion
reported this way carries the model's own limitations - no Marangoni flow, no
vapour depression dynamics, an analytic keyhole patch - and must be reported as
a model-mediated estimate, not a direct measurement.

---

# Part B - Gas: the inversion works, and favours the paper

## B1. The measurement

Weaver et al.'s AM Bench pad scans, under a 4.3 m/s cross-flow, measure melt
pool depth on tracks scanned **parallel** to the gas flow against tracks scanned
**anti-parallel**:

| | depth change | note |
|---|---|---|
| perpendicular pads | **-3.6 %** | the built-in control: no gas-axis effect |
| parallel, weakest cross-section | -19.4 % | |
| parallel, mean of four | **-27.2 %** | |
| parallel, strongest | -31.5 % | |

The authors attribute it to increased vapour-plume interaction with the laser.

## B2. Inverted into fault units

Running the forward model's gas channel and solving for the magnitude that
reproduces each depth change:

| Weaver measurement | depth change | implied f_gas |
|---|---|---|
| perpendicular control | -3.6 % | **0.0467** |
| parallel, weakest | -19.4 % | 0.2749 |
| parallel, mean | **-27.2 %** | **0.4043** |
| parallel, strongest | -31.5 % | 0.4817 |

For reference, the model's gas response: f_gas of 0.05 gives -3.85 % depth, 0.20
gives -14.53 %, 0.40 gives -26.96 %.

## B3. The comparison that matters

The gas channel's effective severity swings from **0.0467 to 0.4043 inside a
single healthy build**, purely from scan direction. That is a ratio of

    0.4043 / 0.0467 = 8.66x

Our asserted gas profile swings **6.05x**. Converting to contrast units, where a
profile with contrast c swings by exp(2c):

    measured   c = ln(8.66)/2 = 1.079
    asserted   c = 0.90

**The one profile that can be checked against measurement is understated by
about 20 %, not overstated.** That is the direction that helps the paper, and it
is a far stronger statement than "we swept it and nothing broke".

## B4. Three caveats, all of which belong in the paper

**Different driver.** Weaver's variation is organised by *scan direction relative
to the gas flow*; the regressor used in this work is *position along the gas
axis*. The same work reports little or no trend of melt pool size with position
within a pad. The honest claim is that a gas-related modulation of the right
order exists and is deterministic, not that our specific driver is the measured
one.

**Healthy build, not a fault.** Weaver measured baseline plume behaviour in a
normal build. Our profile modulates a *degradation*. That a worse plume would
modulate the same way is plausible - more vapour means more of the same
interaction - but it is an extrapolation.

**Model-mediated.** The inversion runs through our forward model, so it inherits
its errors. Depth was chosen for this reason (A2), but the point stands.

---

# Part C - Geometry: the same method fails, informatively

## C1. The attempt

Weaver's pads are **+24.3 %** deeper than single tracks (Y-pad odd-track mean
173.6 um against the case-0 single track at 139.7 um), which the authors
attribute to heat buildup. That is exactly what the geometry fault represents,
so the same inversion should apply.

It returns **f_geometry = 6.87**, that is **+687 K** of preheat.

## C2. Why that is not a measurement

Two readings, and both are worth recording.

**The comparison is contaminated.** A pad differs from a single track by more
than preheat: the laser is partially **remelting adjacent solidified tracks**, a
mechanism the geometry fault does not represent at all. So +687 K is an upper
bound on the preheat-equivalent, with a second effect folded into it.

**The model's preheat channel may be under-responsive.** +100 K of preheat buys
only +2.23 % melt pool depth in this model. If real heat accumulation in a
poorly supported region is worth several hundred kelvin, then the paper's
results, quoted "per 100 K", are being reported at an unrealistically small fault
size. Nothing breaks - geometry is already separated at 58-68 degrees in every
configuration - but the unit is probably understated and the paper should not
imply otherwise.

**Conclusion: gas inverts cleanly, geometry does not.** Reporting only the
successful one would be cherry-picking; both belong in the record.

---

# Part D - The remaining three

| profile | status | route | effort |
|---|---|---|---|
| **gas** | **inverted, B above** | Weaver AM Bench pad scans | done |
| **layer** | obtainable now | Liu et al. (2022), and the 2023 lock-in follow-up, measure **local powder layer thickness in situ**. Their layer-to-layer spread gives this contrast **directly - no inversion, no model in the loop**. | needs the full text |
| **geometry** | attempted, failed | a cleaner source would be an overhang or thin-wall dataset where preheat is the dominant difference, rather than a pad where remelting confounds it | moderate |
| **speed** | bounded only | scanner tracking error against vector length is a standard measurement; Weaver themselves cite turnaround work where "double-wide" melt pools form | moderate |
| **power** | likely stays asserted | needs laser output stability over build-length timescales; no obvious benchmark source | hard |

Power matters least: it carries the **smallest** asserted contrast (0.3 against
1.0 for layer), and the contrast sweep shows the binding pairs survive scaling to
0.33 of asserted strength.

---

# Part E - What would actually fix this

Three levels, and only the first is cheap.

## E1. Measure what can be measured

The gas inversion above, plus Liu's layer thickness figures, would move **two of
five** profiles from asserted to measured. The remaining three would be reported
as bounded by the contrast sweep. That is achievable for draft 2 and is mostly
reading rather than computing.

## E2. Change what the paper asserts, which is the real fix

Even five perfectly measured profiles would not settle this, because **the
profiles are machine- and build-specific**. A different gas nozzle geometry, a
different scan strategy, a different part produces different patterns. There is
no universal set of five numbers to go and measure.

So the honest fix is not to measure harder, it is to stop asserting at all:

- report the result **as a function of profile strength**, which the contrast
  sweep already half does, and
- give the reader the **recipe to measure their own profiles on their own
  machine** - which is what Part A is.

That converts the weakness into the contribution. The deliverable becomes "here
is the method, here is how you calibrate it for your machine, and here is how
much pattern strength you need for it to work," rather than "here is the answer
for the machine we assumed."

## E3. The requirement is weaker than it looks

Worth stating because it changes what has to be measured at all. The collapse
test (C3 in `05-validation-and-robustness.md`) shows the method does not need
five accurate contrasts. It needs the patterns to be **distinct**, and it fails
only in two specific cases: recoater sharing with gas (3.84 degrees) and speed
sharing with gas (8.12 degrees).

So the quantity that must be established is not "how strong is each profile" but
**"are the recoater, gas and speed signatures distinguishable on this machine"**
- a far weaker and far more achievable claim, and one the Weaver data already
supports for the recoater/gas pair, since the measured gas signature alternates
at track scale while a recoater signature alternates at layer scale.

## E4. What stays future work

No benchmark dataset with **deliberately induced machine faults** exists. Until
one does, no profile can be measured on a genuinely faulted build rather than
inferred from a healthy one. That is the experiment this paper should name as
the natural follow-on, and it is the only thing that would fully close the gap.
