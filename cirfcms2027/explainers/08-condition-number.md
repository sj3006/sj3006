# Condition number: what it measures and why rank alone lies

Rank and condition number appear together in every table in this work. Rank is
the one people quote; the condition number is the one that stops rank from
misleading. This file builds the idea from the simplest question that leads to
it, then gives the exact definition the code uses.

---

# Part A - Building it up

## A1. "How loud is a fault?"

Every sensor has noise, so before comparing anything, divide each sensor's row
by its own noise size. One unit then means **one noise-width**, on every sensor
equally. That is all "whitening" means, and it is what makes a photodiode, a
camera reporting square metres and a pyrometer reporting kelvin comparable at
all.

Now the simplest question: if one fault happens at unit size, how far do the
readings move? Measure it as a single distance.

| fault | readings move, in noise-widths |
|---|---|
| power | 2.2948 |
| gas | 2.2948 |
| layer | 0.8426 |
| speed | 0.8210 |
| geometry | **0.1283** |

Power and gas are loud; geometry is nearly 18x quieter than power. Useful, but
not yet the condition number.

## A2. Mixtures, not single faults, are the real question

A machine does not politely fail one way at a time. Power can drift while the
gas degrades. So the set of things that can happen is not five faults, it is
every **mixture** of them.

What makes mixtures interesting rather than tedious: **a mixture can be louder
or quieter than any single fault**, because faults reinforce or cancel.

In this model the temperature depends on the product (absorptivity x power), and
in logs that is roughly

    f_power - f_gas

so power up *and* gas worse - both positive - partly **cancel**, while power
down with gas worse **reinforce**. That is not an interpretation imposed on the
numbers; it falls straight out of them, as A3 shows.

## A3. The two extreme questions

Across all unit-size mixtures:

**Loudest mixture** (readings move 3.4507 noise-widths):

    power -0.665   gas +0.665   speed +0.236   layer +0.244   geometry -0.018

Power *down*, gas *up* - precisely the reinforcing combination predicted above.

**Quietest mixture that is still visible** (0.0405 noise-widths):

    speed -0.615   geometry +0.708   layer +0.338   power -0.057   gas +0.057

Mostly a speed-against-geometry trade, quiet because geometry is the feeblest
channel to begin with.

**Completely silent mixture** (0.0000 noise-widths):

    power +0.670   gas +0.731   layer -0.112   speed -0.056

Both positive - the cancelling combination. More power, worse gas, and the melt
pool cannot tell. The paper's central confound appears here as a mixture with
zero loudness.

## A4. The condition number is the ratio

    condition number  =  loudest mixture / quietest mixture still visible
                      =  3.4507 / 0.0405
                      =  85.13

One number saying: **the best-heard fault mixture is 85 times louder than the
worst-heard one.**

The silent mixtures are excluded first, since including them makes the ratio
infinite and says nothing. **How many mixtures survive that exclusion is the
rank.** So rank and condition number are two readings off one measurement - rank
counts the survivors, the condition number measures the spread among them. That
is why they are always reported as a pair.

## A5. Why it matters

Noise does not play favourites: one noise-width in every direction, by
construction. Signal does: 3.45 noise-widths one way, 0.04 the other.

So the quiet direction is where you get fooled. Along the loud direction a fault
stands 3.45 noise-widths clear and you believe it. Along the quiet direction it
stands 0.04 clear, and ordinary noise looks exactly like a real fault. The
condition number is **how much worse the bad case is than the good case**, and
therefore how much a small reading error can be amplified into a large error in
the diagnosis.

This is checkable rather than merely assertable. A real fault of 5 % size
pointing along the quiet direction, against a plain 5 % power fault:

| | photodiode | camera | pyrometer |
|---|---|---|---|
| quiet direction | -0.083 % | -0.067 % | -0.002 % |
| plain power fault | +7.03 % | +6.02 % | +0.049 % |

7.03 / 0.083 = **84.7**, the condition number recovered from running the model.

## A6. Where the mathematical name comes in

The three loudness figures - 3.4507, 0.1545, 0.0405 - are the **singular
values**, and finding them is what the singular value decomposition does. The
idea came first: they are simply the loudest, middling and quietest mixtures.
The SVD is the tool that locates those mixtures, not the concept itself.

**Where those three numbers actually come from**, and why the pairwise angles
turn out to be the same computation seen from the other side, is derived in
`09-where-the-singular-values-come-from.md`.

---

# Part B - The exact definition in the code

`rank_cond` in `src/locality_routeA.py`:

    Dw = whiten(D, sigmas)
    s  = np.linalg.svd(Dw, compute_uv=False)
    s  = s[s > s.max() * RANK_TOL]        # RANK_TOL = 1e-6
    return len(s), s[0] / s[-1]

In words: whiten, take the singular values, discard anything below 1e-6 of the
largest, count the survivors (rank) and divide the biggest survivor by the
smallest (condition number).

**This is not the textbook condition number.** The textbook definition is
sigma_max / sigma_min, which for a rank-deficient matrix like ours is infinite,
since sigma_min = 0. Ours is the ratio over the **retained** singular values -
the condition number of the part of the problem we have declared observable.

Worked, for the instantaneous 3 x 5 case:

    singular values   3.4507   0.1545   0.0405   0   0
    cut at 1e-6 x 3.4507 = 3.451e-06
    survivors         3        ->  rank 3
    condition         3.4507 / 0.0405 = 85.13

And for the enlarged 15 x 5 case:

    singular values   32.7682   8.5874   5.5473   3.3562   1.0816
    survivors         5        ->  rank 5
    condition         32.7682 / 1.0816 = 30.30

Note what improved with build context: not only **more** directions, 3 to 5, but
a **tighter spread**, 85 to 30. The fifth direction of the enlarged problem is
sturdier than the third direction of the instantaneous one.

---

# Part C - Why rank alone lies

This is the reason the quantity is in the paper at all.

Add four more observables to the three sensors and the rank rises from 3 to 4.
Quoted alone that sounds like a fourth fault direction became visible. The
loudness figures say otherwise:

    4.5825   0.4750   0.1993   0.0000200   0.0000039

The fourth mixture is **229,212 times quieter** than the first. It is "visible"
only in the sense that a number is not exactly zero. No instrument would act on
it, and the worst pairwise angle stays at 0.00 degrees.

| configuration | rank | condition | reading |
|---|---|---|---|
| 3 sensors, one instant | 3 | 85 | three usable directions |
| 15 build-context coefficients | 5 | **30** | five directions, and tighter |
| all seven observables | 4 | **229,212** | a fourth direction worth nothing |
| two idealised direct cause sensors | 5 | 546 | rank 5, 18x worse posed than context |
| four-sensor subsets, instantaneous | 4 | 4e5 - 8e5 | rows are near-duplicates |

The enlarged row is the paper's result in one line: build context does not merely
add directions, it makes the weakest one sturdier.

---

# Part D - A caveat worth knowing

Because the rank cut and the condition number share one threshold, both depend
on `RANK_TOL`. For the seven-observable case that dependence is uncomfortably
tight:

    cut falls at           4.582e-06
    5th singular value     3.864e-06      only 16 % below the cut

A tolerance of 8.4e-07 rather than 1e-06 would report **rank 5** and a condition
number of 1,185,837.

The substance is unaffected - at rank 5 the fifth direction would be a million
times weaker than the first, so even more useless - but **the integer in "seven
observables raise the rank only from three to four" is marginal.** The paper
leans on the condition number rather than the integer for exactly this reason,
which is the right instinct, but it does not say so explicitly.

This is a candidate entry for `10-errata-and-draft-2-changes.md` and has not
been logged there yet.

---

# The analogy, after the mechanics

Rank is how many microphones in the room are picking up something. The condition
number is the volume gap between the loudest and the faintest. A gap of 85 is a
difficult recording. A gap of 229,000 means the faintest microphone is recording
nothing you could ever use, however many more you buy.

---

# What this licenses

**It licenses** comparing two sensor configurations that happen to share a rank
and saying which is better posed; and declaring a direction useless despite its
being formally present.

**It does not license** any absolute error bar. The condition number is computed
on the **whitened** matrix, so it is a statement about *relative* noise across
sensors. Scale every sensor's noise by a common factor and the condition number
does not move - which is exactly why the paper can report it while declining to
claim absolute detection thresholds. See `04-noise-position.md`.

**It also does not license** reading the condition number as a probability or an
error bar on any particular fault. It is a worst-case ratio over mixtures. A
specific fault of interest may sit nowhere near the quiet direction and be
diagnosed far better than the condition number alone suggests - which is why the
paper reports pairwise angles as well, rather than condition number only.
