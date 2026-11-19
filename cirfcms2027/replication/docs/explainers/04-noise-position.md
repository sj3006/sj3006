# The noise position: a declared deviation from the abstract

The accepted abstract states that *"pairwise distinguishability is evaluated
against noise levels taken from published sensor characterisations."* It was
not. This document states what was done instead, why, and what it costs, so the
deviation is declared in the paper rather than left for a reviewer to find.

## What was sought, and what was found

One figure proved citable:

    camera     Weaver et al. (IMMI 13:363-379, 2024) report U(k=2) = 6.2 um on a
               136.3 um melt pool width. A 95% interval, so sigma = 3.1 um, i.e.
               **2.3% relative**.

Nothing comparable was found for a coaxial photodiode or a two-colour pyrometer
*in process*. The nearest candidate, NIST AMS 100-35 (Lane, Jacquemetton, Piltch
& Beckett, 2020), was read in full and rejected: it is a **thermal calibration**
study, not a noise characterisation. It gives a calibration RMSE of 4.934 deg C
and a 10 uV multimeter resolution on a 35 mV scale - neither of which is
in-process sensor noise. The system it describes has no camera, and its
wavelength channels are never characterised.

Quoting those numbers as "noise levels from published sensor characterisations"
would have looked rigorous and been wrong.

## What was done instead

Noise is treated as a **ratio between sensors** and swept. Three assumption sets,
with every conclusion required to hold under all three:

    study default     photodiode 1.0,  camera 1.0,  pyrometer 0.03
    equal noise       all 1.0
    fine pyrometer    photodiode 1.0,  camera 1.0,  pyrometer 0.003

## Why ratios are sufficient for what is claimed

The quantities this paper reports - pairwise angles, rank, condition number - are
all **invariant to scaling every sensor's noise by a common factor**. Whitening
divides each row by its own sigma; a common factor rescales the whole matrix and
changes neither the angles between its columns nor its singular value ratios.

So the absolute noise level is not merely unknown, it is **irrelevant to the
reported results**. Only relative noise matters, and that is what is swept.

## What it costs, stated plainly

**Detection thresholds cannot be claimed.** "Is a 3% power deviation visible
above noise?" is an absolute question and this work does not answer it. Every
reported result is about *isolation* - telling two faults apart - not detection.

This compounds with a second limitation already recorded: fault magnitude for
layer, gas and geometry is a physical quantity but the faults are not on a common
severity scale, so comparisons across pairs at fixed magnitude are not meaningful
either. The two limitations bite the same claim and should be stated together.

## Two findings that came out of sweeping rather than assuming

**The pyrometer has an optimum.** Making it quieter does not monotonically
improve the suite. At a noise ratio near 0.03 the pairwise angles peak and fall
away in both directions, because whitening by 1/sigma lets an over-specified
sensor dominate the matrix, and one scalar cannot separate five faults. A fixed
"best available" noise figure would have hidden this.

**The rank limit bites before noise does.** Three sensors cannot span five faults
at any noise level. That ceiling is reached before sensor quality becomes the
binding constraint, which is why the central result does not rest on the figures
that were unavailable.

## The three options, and the recommendation

1. **Find citable in-process characterisations before submission.** Preferred if
   they exist; the search so far has not found them.
2. **Reword the abstract clause at submission.** Possible if the venue permits
   edits between abstract acceptance and full paper.
3. **State the position in the paper and justify the ratio sweep**, on the
   invariance argument above.

**Recommendation: option 3, with option 1 attempted first.** It is honest, the
justification is mathematical rather than rhetorical, and the sweep is stronger
evidence than any single citable figure would have been - a result that holds
across a 10x range of relative noise is more robust than one computed at a
number taken from a paper about a different instrument.

The sentence for the paper, roughly:

> No in-process noise characterisation was found for the coaxial photodiode or
> two-colour pyrometer; the one citable figure is a melt pool width uncertainty
> of 2.3% relative. Sensor noise is therefore treated as a ratio and swept over
> three assumption sets. This is sufficient for the isolability results reported
> here, which depend only on relative noise: pairwise angles, rank and condition
> number are invariant to a common scaling of all sensor noise. Absolute
> detection thresholds are correspondingly not claimed.
