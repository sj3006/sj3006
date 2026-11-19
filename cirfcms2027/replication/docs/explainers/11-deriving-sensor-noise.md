# Deriving the sensor noise, instead of asserting it

This is the record of how the three sensors' relative noise figures were derived,
what they came out to, and what changed in the paper as a result. It closes
errata E8.

Short version: the figures went from an asserted **1 : 1 : 0.03** to a derived
**1 : 0.142 : 1.061**, the camera and the pyrometer both moving, and in opposite
directions. Nothing in the paper's argument broke, several claims got stronger,
and two became qualitatively sharper.

---

## A. Why noise is part of the Jacobian, not an extra

Worth restating because it is the whole reason this matters.

The raw Jacobian `J[s,k] = (1/y_s) d y_s / d f_k` has three rows, one per sensor,
and each row carries that sensor's own units:

    photodiode   arbitrary radiometric units
    camera       square metres
    pyrometer    kelvin

So column k is a vector like `(1.52 a.u., 3.1e-9 m^2, 0.036 K)`. Two such columns
have **no meaningful angle between them**, because an angle needs all coordinates
in one unit. Change the camera from m^2 to mm^2 and every angle in the matrix
changes. A number that moves when you change a unit is not a result.

Whitening fixes exactly that. Dividing row s by that sensor's relative noise
sigma_s makes every row read in the same unit - *how many noise widths this
sensor moved* - and those are comparable across instruments:

        Jw[s,k] = (1 / sigma_s) * (1 / y_s) * (d y_s / d f_k)

Every quantity the paper reports - the pairwise angles, the rank, the condition
number, the three diagnosability classes - is computed on `Jw`, never on `J`.
The abstract's own criterion, *"signatures differing by less than the sensor
noise"*, cannot even be written down without sigma.

So the noise ratios are half of the measurement geometry. An asserted set
silently decides the answer, which is what the first draft did.

---

## B. The one assumption

    Each radiometric channel carries the same fractional noise eps on its
    measured signal.

That is a statement about detector class, not about any particular instrument,
and it is the only free quantity. Everything else follows from how each
instrument converts radiance into the number it reports.

Because **only ratios enter the whitening** - angles, rank and condition number
are invariant to a common scaling of all rows - `eps` cancels and never has to be
pinned down. This is why deriving the ratios beats citing any single vendor noise
figure: the ratios follow from physics, and the absolute scale is explicitly not
claimed.

Planck's second radiation constant throughout:

        c2 = h c / k_B = 1.4387769e-2 m K

and the logarithmic sensitivity of Planck spectral radiance to temperature,

        d ln L / d ln T  =  x e^x / (e^x - 1),      x = c2 / (lambda T)

whose Wien limit is just `x`. At the wavelengths and temperatures here the exact
form and the Wien limit agree to better than 1 %.

---

## C. Photodiode: the unit

The photodiode reading *is* a band-integrated radiometric power over the field of
view. A fractional radiometric error eps lands on it directly:

        sigma_pd = eps                  ratio 1.0000

This is not a free choice dressed up - it is the definition of the unit. The
first draft also used 1.0 here, but as a convention with no reason attached.

---

## D. Pyrometer: ratio inversion **amplifies** noise

The two-colour pyrometer reports a temperature inverted from the ratio of two
band powers. Two steps:

**1. Noise on the ratio.** With independent noise on each channel,
`ln R = ln P1 - ln P2` carries

        sigma_lnR = sqrt(2) * eps

**2. The inversion divides by the ratio's temperature sensitivity.** The code's
inverter is

        T = c2 (1/lam2 - 1/lam1) / [ ln R + 5 ln(lam1/lam2) ]

so differentiating,

        |d ln R / d ln T| = (c2 / T) (1/lam2 - 1/lam1)

At 750/950 nm and the model's reported T = 3030.6 K:

        1/lam2 - 1/lam1 = 1/950e-9 - 1/750e-9 = -2.807e5 m^-1
        (c2 / T) * 2.807e5 = (1.4387769e-2 / 3030.6) * 2.807e5 = 1.3326

Therefore

        sigma_pyr = sqrt(2) / 1.3326 = 1.0612 eps          ratio 1.0612

Checked three ways, which all agree:

| route | value |
|---|---|
| Wien expression above | 1.3326 -> **1.0612** |
| numerically through the code's own inverter (d lnT/d lnP1 = +0.7504, d lnT/d lnP2 = -0.7504) | **1.0612** |
| exact Planck d lnL/d lnT: 6.3412 at 750 nm, 5.0313 at 950 nm, difference 1.3099 | 1.0796 |

The numerical route is the one used, because it is the sensitivity of the
instrument model actually in the code rather than of an idealisation of it. The
exact-Planck figure differs by 1.7 %, immaterial.

### What this means physically

**A two-colour pyrometer is a noisier relative instrument than the photodiode it
is built from.** Two bands only 200 nm apart at 3000 K have nearly the same
Planck sensitivity (6.34 against 5.03), so the ratio retains only the
*difference*, 1.33, and the inversion then divides by that small number. Taking
the ratio throws away most of the temperature sensitivity and amplifies what
noise remains.

The draft's 0.03 said the opposite, by a factor of 35.

---

## E. Camera: a threshold crossing, so eps becomes an isotherm shift

The camera reports geometric extents found by thresholding at the liquidus. The
clean way to propagate radiometric noise through that is to notice:

> A fractional radiance error eps is **indistinguishable from the threshold
> sitting at a different temperature**.

If the measured intensity is `(1+eps)` times the true one, the apparent boundary
sits where the true radiance is `L(T_liq)/(1+eps)`, i.e. at the isotherm

        d ln T_liq = - eps / (d ln L / d ln T)|_{T_liq}

At the camera band mid-point (850 nm) and the IN718 liquidus (1609 K):

        x = c2 / (lam T) = 1.4387769e-2 / (850e-9 * 1609) = 10.520
        d ln L / d ln T = 10.520       (Wien is excellent here: e^x/(e^x-1) = 1.000027)

So **eps = 1 % moves the apparent isotherm by only 0.095 % in temperature.**
Planck is very steep at the liquidus, which is precisely why thresholding
localises an edge well.

Then the isotherm shift is pushed through the model's **own dimension solver** -
no gradient estimation, no new approximation, the real code path:

| | width | length | area |
|---|---|---|---|
| nominal | 115.120 um | 415.472 um | 3.75649e-08 m^2 |
| eps = +1 % | 115.086 | 415.005 | 3.75115e-08 |
| eps = -1 % | 115.154 | 415.939 | 3.76183e-08 |
| **d ln / eps** | **0.0298** | **0.1124** | **0.1422** |

        sigma_cam = 0.1422 eps              ratio 0.1422

Note `0.0298 + 0.1124 = 0.1422` exactly, because `ln A = ln w + ln l + const` and
a common-mode error drives both together.

### Two things fall out of this

**1. The camera is the most *precise* of the three in relative terms**, by about
a factor of seven against the photodiode. That is the opposite of the draft's
assumption that it matched the photodiode.

**2. Width and length are not equally well localised - by a factor of 3.8.** The
lateral edge sits on a steep temperature gradient and moves 0.030 % per 1 % of
eps; the trailing edge sits in the melt pool's long thermal tail and moves
0.112 %. This is a **second, independent** reason - alongside the correlation
result in Section 4.3 of the paper - that melt pool width is the more informative
axis. Two different arguments, same conclusion, and they were not constructed to
agree.

### Convergence, because small derivatives deserve it

`d ln A / eps` is a 0.14 % response to a 1 % perturbation, so it is worth
checking it is physics and not quantisation.

    eps      dlnW/eps   dlnL/eps   dlnA/eps
    0.0800    0.02976    0.11273    0.14249
    0.0400    0.02976    0.11243    0.14219   (0.21 % vs previous)
    0.0200    0.02976    0.11243    0.14219   (0.00 %)
    0.0100    0.02976    0.11243    0.14219   (0.00 %)
    0.0050    0.02976    0.11243    0.14219   (0.00 %)
    0.0025    0.02976    0.11243    0.14219   (0.00 %)

Flat from 0.04 down to 0.0025. And against the solver grid:

    n_points  121   dlnA/eps 0.14219
    n_points  181   dlnA/eps 0.14109
    n_points  241   dlnA/eps 0.14172
    n_points  361   dlnA/eps 0.14243

a 0.9 % spread on the area. Width alone wobbles more, 0.0284 to 0.0298 (about
5 %), which is the sub-grid interpolation of a small quantity; it does not change
the factor-of-3.8 conclusion.

---

## F. The other four observables

Same reasoning, same code:

| observable | sigma/eps | why |
|---|---|---|
| photodiode | 1.0000 | the unit |
| camera (area) | 0.1422 | threshold shift, width + length |
| pyrometer (750/950) | 1.0612 | ratio inversion |
| camera_width | 0.0298 | steep lateral gradient |
| camera_length | 0.1124 | shallow trailing edge |
| photodiode_swir (1500-1700) | 1.0000 | also a band-integrated power; its band differs, not its transduction |
| pyrometer_wide (700/1600) | 0.3583 | widely separated bands give |dlnR/dlnT| = 3.947, so it is *three times quieter* than the narrow pair |

The wide-band pyrometer result is worth a note: separating the bands recovers
much of the temperature sensitivity the narrow pair throws away. It is still
worth nothing diagnostically (0.00 degrees on the worst pair), because its
problem is redundancy with the photodiode, not precision - which is the paper's
point about precision being irrelevant, arriving from a new direction.

---

## G. Why this set is conservative

Two choices inside the derivation could have gone the other way. Both were taken
in the direction that **costs** this analysis.

**1. No perimeter averaging on the area channel.** Independent per-pixel
detection noise would average down along the melt pool boundary by sqrt(N_el).
At this model's grid spacing (12.40 um elements on a 901.6 um perimeter) that is
sqrt(72.7) = 8.53, which would make the camera 0.0167 rather than 0.1422 - quieter
still. It was not applied, because N_el depends on a camera's instantaneous field
of view, which this model does not represent. **Inventing one would be asserting
an instrument parameter, which is the thing this derivation exists to stop
doing.** The unaveraged, larger figure is used.

**2. Width and length are whitened as independent.** Under a purely common-mode
radiance error their edge displacements are perfectly correlated, the covariance
is rank one, and the differential combination would be *noise-free* - which would
make splitting the camera axes infinitely valuable. That is unphysical. Treating
the two as independent understates the split's value rather than overstating it.

**And one point in the other direction, which honesty requires stating.** The
common-mode part of a real system's radiometric error **cancels in the
pyrometer's ratio**, since both bands share the optical path - that is why people
build two-colour pyrometers. A system whose noise is dominated by slow gain or
emissivity drift rather than by detection noise would therefore have a much
quieter pyrometer, approaching the 0.03 the draft asserted.

So **0.03 is not arbitrary so much as the gain-dominated limit, asserted without
saying so.** For *per-segment* diagnosability the detection-noise limit is the
right one: gain is static over a segment, and a shared bias does not discriminate
between two fault hypotheses at the same operating point. Both limits are swept.

### The four assumption sets

The draft swept four sets centred on its own assumption, so the sweep could not
have failed (errata E8c). The new four are the derived set plus the named limits
of each choice above, plus the agnostic case:

| set | photodiode | camera | pyrometer | what it is |
|---|---|---|---|---|
| **derived** | 1.000 | 0.1422 | 1.0612 | detection-noise limit. The default. |
| gain dominated | 1.000 | 0.1422 | 0.03 | the pyrometer's ratio rejects common-mode drift |
| averaged camera | 1.000 | 0.0167 | 1.0612 | per-pixel noise averages along the perimeter |
| equal noise | 1.000 | 1.000 | 1.000 | assumes nothing about transduction |

Enlarged worst-pair angle across all four: **24.89 to 24.98 degrees**. The two
open choices in the derivation are worth under a tenth of a degree.

---

## H. What changed in the paper

| quantity | asserted 1:1:0.03 | derived 1:0.142:1.061 |
|---|---|---|
| sensor correlations | 0.99960 / 0.99508 / 0.99477 | **identical** - see below |
| instantaneous singular values | 3.451, 0.155, 0.041 | 13.14, 0.0638, 0.00513 |
| instantaneous rank / condition number | 3 / 85 | 3 / **2562** |
| instantaneous worst pair | 0.00 deg | 0.00 deg |
| **instantaneous class 1, baseline** | **5/10** | **0/10** |
| seven observables, attained rank | 4 | **3** (4th at 2e-7 of the leading) |
| enlarged rank | 5 | 5 |
| **enlarged worst pair** | **25.83 deg** | **24.90 deg** |
| enlarged power/gas | 29.34 deg | 29.34 deg (unchanged) |
| enlarged condition number | 30 | 50 |
| enlarged class 1 | 10/10 | 10/10 |
| contrast: pairs clearing at <= 0.25 | 8/10 | 5/10 |
| contrast: hardest pair clears at | 0.40 | 0.50 (power/speed) |
| 120 profile permutations | 17.13-30.58 deg | **24.89-25.29 deg** |
| conductivity coupling sweep | 25.83 throughout | 24.90 throughout |
| segment count N=12 / N=30 | 11.74 / 23.91 | 11.23 / 22.90 |
| secant magnitude study | rank 5, 22.19-36.90, cond 30-43 | rank 5, **12.82-37.95**, cond 47-62 |
| no-interpolation cross-check | 0.10 deg | **0.04 deg** |
| config A-D power/gas | 0.00 deg | 0.00 deg |
| config E power/gas | 84.02 deg | 84.02 deg |
| config class-1 counts A-E | 0, 4, 0, 5, 4 | 0, 0, 0, 0, 4 |
| direct sensor on one cause | clears 8/10, worst 3.46 | clears 4/10, worst 0.32 |
| gas + layer direct sensors | rank 5, 7.12 deg, 9/10 | rank 5, 0.70 deg, 7/10 |
| **split the camera axes** | **+13.40 deg**, 25.83 -> 39.23 | **+23.89 deg**, 24.90 -> 48.79 |
| split camera, instantaneous class 1 | (not reported) | **0/10 -> 7/10** |
| SWIR photodiode / wide pyrometer | -0.08 / -0.13 deg | +0.01 / 0.00 deg |

### The correlation table does not move at all

Worth its own line. The normalised sensor Gram matrix is

        A_ij / sqrt(A_ii A_jj)  where  A = Jw Jw^T

and the sigma's cancel exactly in that normalisation. **The sensor correlation
table is invariant to the noise assumption** - it is the same matrix whether you
whiten or not. So the plainest statement of the paper's central problem, that
three physically different instruments agree to better than 0.994, depends on
none of this. That is a genuine strengthening and the paper now says so.

### What got stronger

- **The central claim is cleaner.** Instantaneously the baseline suite now
  resolves **nothing**, not five of ten; over a build it still resolves
  everything. "None per segment, all ten over a build" is a starker result than
  "five, then ten", and it follows from no longer granting the pyrometer an
  unjustified 35x precision advantage.
- **The rank bound is tighter.** Seven observables now attain rank 3 against the
  structural bound of 4, rather than reaching 4.
- **The permutation sweep collapsed to a narrow band**, 24.89-25.29 against
  17.13-30.58, so profile *assignment* matters far less than the draft implied.
- **The split-camera recommendation became the paper's strongest practical
  result**: +23.89 degrees rather than +13.40, and the only change that makes
  anything resolvable per segment at all.
- **The noise position moved from a disclaimer to a contribution.** The draft had
  a section apologising for the absence of citable noise figures. It now derives
  them.

### What got weaker, stated plainly

- **The instantaneous regime is much more confounded.** 0/10 rather than 5/10.
  Everything useful now depends on accumulation over a build or on splitting the
  camera axes.
- **The profiles must now be strictly distinct.** The draft said two specific
  collapses (recoater/gas, speed/gas) would defeat the method and every other was
  survivable. Now *every* collapse falls below the floor, the mildest leaving
  4.63 degrees. The honest statement is: no pair of faults may share a spatial
  signature.
- **The contrast margin is thinner.** The hardest pair clears at 50 % of the
  asserted profile strength rather than 40 %, so the conclusion survives the real
  profiles being 2x weaker rather than 2.5x.
- **The nonlinear margin is thinner.** The worst enlarged angle over the
  magnitude sweep is 12.82 degrees at a +20 % fault, 1.3x the floor, against
  22.19 degrees and 2.2x before.
- **The attained rank of 3 versus 4 is tolerance-sensitive.** The fourth
  direction sits at 2e-7 of the leading singular value against a 1e-6 threshold.
  The paper reports the singular values and the threshold rather than just the
  integer, because the integer is the fragile part and the physical statement -
  that the fourth direction is useless - is not.

---

## I. Where it lives in the code

`src/noise.py`, which is the single source for every noise figure in the study.
It holds the derivation in its docstring, `DERIVED` with the seven values,
`derive()` to recompute them from the model and Planck's law, and `verify()`,
which recomputes and asserts the hardcoded values still reproduce. Every
reporting script calls `verify()`.

Before this, the figures were hardcoded in six places across five modules
(`locality_routeA.py`, `observables.py`, `commercial.py`, `matrix.py` twice, and
`route_b.py`), which is how errata E9 happened - the paper claimed four
assumption sets and the code contained three.

Run `python3 src/noise.py` for the full derivation with every intermediate.
