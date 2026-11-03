# Corrections to apply to the Overleaf copy

`overleaf/paper.tex` is the copy you are editing, so it has **not** been touched.
`paper/paper.tex` in this repository has had the corrections below applied and
recompiles to 7 pages two-column, 0 undefined references.

Apply these by hand, or if you have no edits yet, copy `paper/paper.tex` over
`overleaf/paper.tex` and change line 1 back to
`\documentclass[final,5p,times,twocolumn]{elsarticle}`.

Every change came from `python3 repro/check.py`, which now reports 234 of 234
claims reproducing. Nine were numbers that no longer reproduced; four were
sentences that were accurate but read as something stronger.

---

## Numbers that changed

### 1. Section 3.1 - depth calibration error: **13.0 % becomes 13.1 %**

```diff
- giving \textbf{11.7\,\% mean error on melt pool width and 13.0\,\% on depth}
+ giving \textbf{11.7\,\% mean error on melt pool width and 13.1\,\% on depth}
```

The 13.0 came from a fresh least-squares run; the -15.5 % / +1.7 % two sentences
later came from the constants stored in `eagar_tsai.py`, which is what every
other result in the paper uses. Two numbers in one paragraph from two slightly
different models. Everything now comes from the stored constants, and that makes
the depth figure 13.1 %.

### 2. Section 3.1 - the keyholing regime and the conduction baseline

```diff
- is necessary rather than optional: all seven cases keyhole, aspect ratios
- 1.45--4.28, and pure conduction gives 27.8\,\% depth error.
+ is necessary rather than optional: all seven cases keyhole, depth-to-width
+ ratios running 0.72--2.14 against the criterion's 0.67, and a pure conduction
+ fit given the same three free parameters leaves 23.6\,\% depth error against
+ 13.1\,\%, at an essentially unchanged 8.5\,\% on width.
```

Two problems. The quoted 1.45-4.28 was in depth-to-**half**-width, while the
criterion stated beside it is depth >= width / 1.5, i.e. 0.667 in
depth-to-width. A reader checking one against the other would conclude the cases
were nowhere near keyholing. And 27.8 % came from a one-parameter fit that held
conductivity and heat capacity at uncalibrated values and drove absorptivity to
0.95, which no nickel alloy shows at 1 um. At the same freedom as the adopted
fit it is 23.6 %, which is the honest comparison and still makes the point.

### 3. Section 3.1 - step convergence: **39.4 % becomes 39.3 %**

```diff
- entries still moving 39.4\,\%
+ entries still moving 39.3\,\%
```

Computed value 39.345, which rounds to 39.3.

### 4. Section 3.2 - the absorptivity self-consistency check

```diff
- implying a bare-solid
- absorptivity of 0.258 consistent with the fitted value.
+ implying a bare-solid
+ absorptivity of 0.258, inside the 0.25--0.35 reported for nickel alloys near
+ 1\,\textmu m --- a consistency the calibration was not built to produce.
```

Not a wrong number, a wrong sentence. 0.258 is derived *from* the fitted value
(0.384 divided by the powder enhancement 1.487), so saying it is "consistent
with the fitted value" is circular. What is actually consistent is 0.258 against
published bare-solid absorptivity for nickel alloys, which the fit never saw.

### 5. Section 3.5 - the coefficient-noise factor

```diff
- $\sigma_{(s,j)} = \sigma_s\sqrt{[(G^{\!\top}G)^{-1}]_{jj}}$, here 0.109 to 0.136, so fitting $N=84$ segments to five regressors buys roughly
- a ninefold noise reduction.
+ $\sigma_{(s,j)} = \sigma_s\sqrt{[(G^{\!\top}G)^{-1}]_{jj}}$, the square-root
+ factor running 0.109 to 0.136, so fitting $N=84$ segments to five regressors
+ buys a seven- to ninefold noise reduction.
```

0.109 to 0.136 is the **square-root factor**, not sigma. The coefficient noise
itself runs 0.0155 to 0.144, because it still carries each sensor's own sigma.
And the reduction is 7.3x to 9.2x across the five coefficients, so "roughly
ninefold" quoted only the best one.

### 6. Section 3.5 - the gas inversion: **0.047 becomes 0.046, 8.7x becomes 8.8x**

```diff
- $f_{\mathrm{gas}}=0.047$ for the control against $0.404$ for the parallel mean,
- an \textbf{8.7$\times$ swing within one healthy build}
+ $f_{\mathrm{gas}}=0.046$ for the control against $0.404$ for the parallel mean,
+ an \textbf{8.8$\times$ swing within one healthy build}
```

The inversion now runs to a tolerance of 1e-9 in `src/weaver_pads.py` rather
than being read off a coarse bracket. The contrast, 1.08, and the understatement,
20 %, both survive unchanged.

### 7. Section 4.1 - the power-law fit quality

```diff
- Each dimension is a power law in $(P,v,d)$ to $R^{2}\ge0.94$,
+ Width and depth are each a power law in $(P,v,d)$ to $R^{2}\ge0.94$,
```

Length drops to 0.93 on the wide-spot grid. Width and depth are the two the
sentence goes on to discuss, so restricting the claim to them loses nothing.

### 8. Section 4.5 - the permutation sweep. **This was the real error.**

```diff
- 20\,\% \emph{stronger} than assumed. The headline moves by under half a degree
- across all 120 permutations of profile assignment, the full range of the
- unmeasured conductivity coupling, and all four noise sets of
- Section~\ref{sec:noise}; segment count is the one real requirement, at
- $11.23^\circ$ for $N=12$ and $22.90^\circ$ for $N=30$, flat thereafter.
+ 20\,\% \emph{stronger} than assumed. The headline moves by under half a degree
+ across the full range of the unmeasured conductivity coupling and all four
+ noise sets of Section~\ref{sec:noise}. Reassigning which fault follows which
+ build variable moves it further, the worst pair running $16.2^\circ$ to
+ $30.1^\circ$ across all 120 permutations, but \textbf{every one of the 120
+ leaves rank five and all ten pairs above the floor} --- the result needs the
+ patterns to differ, not any particular fault to own any particular one.
+ Segment count is the one real requirement, at $11.23^\circ$ for $N=12$ and
+ $22.90^\circ$ for $N=30$ on a near-square plan, flat thereafter.
```

"Under half a degree across all 120 permutations" was wrong by a factor of
nearly twenty. Across the 120 reassignments the worst pair runs 16.23 to 30.13
degrees - a spread of 14 degrees, up to 8.7 degrees from the identity
assignment. The figure had been taken from the **sensor-subset** column of a
different sweep, where the headline genuinely does move only 24.89 to 25.31.

What is true, and is still a strong robustness result, is that all 120 leave
rank 5 and all ten pairs above the floor. The claim is now that, which is what
the mathematics actually supports: permuting the driver columns permutes the
columns of the projection matrix, so the *set* of signature directions is
preserved up to relabelling.

The same sentence in the conclusions needs the same fix:

```diff
- strength, across all 120 permutations, under all four noise sets and at fault
- magnitudes from 0.2\,\% to 20\,\%, with a shared-profile control reproducing the
- instantaneous result exactly.
+ strength, under all four noise sets, at fault magnitudes from 0.2\,\% to
+ 20\,\%, and in all 120 reassignments of profile to fault, with a shared-profile
+ control reproducing the instantaneous result exactly.
```

Also note "on a near-square plan" added to the segment-count figures. The worst
pair depends on the plan's **shape** as well as its size: at N = 30 it is 22.90
on a 3 x 10 plan but 14.97 on a 2 x 15 and 18.17 on a 6 x 5. Quoting a figure
against N alone is not reproducible without saying which family of plans.

### 9. Section 4.5 - the contrast threshold: **50 % becomes 45 %**

```diff
- below 25\,\% of the strength assumed here and the hardest, power/speed, at
- \textbf{50\,\%}, so a machine whose patterns are half as strong still resolves
+ below 25\,\% of the strength assumed here and the hardest, power/speed, at
+ \textbf{45\,\%}, so a machine whose patterns are half as strong still resolves
```

`matrix.contrast_to_clear` searched a fixed grid, so it returned the first grid
point above the floor rather than the threshold. Solved by bisection the pair
clears at 0.451. "Half as strong still resolves every pair" is now true with
margin rather than exactly on the boundary.

### 10. Section 4.5 - driver misattribution: **85 % becomes 84 %, 12.21 becomes 12.07**

```diff
- profile leaves layer/geometry above the floor until that profile is roughly
- 85\,\% support-driven ($12.21^\circ$ at 80\,\%), and mixing the power fault's
+ profile leaves layer/geometry above the floor until that profile is roughly
+ 84\,\% support-driven ($12.07^\circ$ at 80\,\%), and mixing the power fault's
```

The old figures came from a scratchpad script whose renormalisation differed
from `observables._range_normalise`. The committed version agrees with the rest
of the model, and as a consequence the mixing test at fraction 1 now reproduces
the collapse test exactly, which the old one did not.

### 11. Section 5.1 - the fitted exponent at 100 W: **0.50 becomes 0.51**

```diff
- reaching 0.337 at 400\,W, where this model gives 0.50, 0.44 and 0.47 at 100, 285
+ reaching 0.337 at 400\,W, where this model gives 0.51, 0.44 and 0.47 at 100, 285
```

0.511 on 25 log-spaced speeds. This is the least linear of the three fits
(R^2 = 0.997 against 0.999) and it moves between 0.505 and 0.513 with the
sampling, which is worth knowing but does not touch the point, which is that the
exponent is flat where Reijonen's grows.

### 12. Section 5.2 - the geometry inversion: **+733 K becomes +687 K**

```diff
- The geometry inversion fails, returning $+733$\,K of preheat because a pad
+ The geometry inversion fails, returning $+687$\,K of preheat because a pad
```

The errata record had +687 K and the explainer had +733 K; the committed
computation in `src/weaver_pads.py` gives 687.4. Nothing reproduced 733.

---

## Sentences that were accurate but read as more than they were

### 13. Section 4.2 - the exactness of the confound, strengthened

```diff
- the same temperature at every point, hence identical readings from any instrument
- that could be built, verified to eight significant figures on all three.
+ the same temperature at every point, hence identical readings from any instrument
+ that could be built --- the two faults cancel bit-identically in double
+ precision on all three.
```

The readings do not agree to eight figures, they agree to all sixteen: the
relative difference is exactly zero at every magnitude from 2 % to 20 %. The
paper was understating its own result.

### 14. Section 4.6 - five systems, three configurations, five classes

```diff
- Five commercial systems were surveyed and collapse to three distinct
- configurations, reported as classes rather than products: \textbf{A}, a single
+ Five commercial systems were surveyed and present only three distinct
+ observable sets. Those are reported as classes rather than products, alongside
+ a single-photodiode floor and the research reference: \textbf{A}, a single
```

The old sentence said "three distinct configurations" and then listed five
classes. A and D are reference points - a single-photodiode floor and the
research baseline - not surveyed products, and E is a configuration type.

### 15. Section 4.7 - what splitting the camera is worth

```diff
- rather than as an area is worth \textbf{+23.89$^\circ$} on the binding pair
- accumulated ($24.90^\circ$ to $48.79^\circ$) and is the only change resolving
- anything \emph{per segment}, taking that count from none of ten to \textbf{seven
- of ten} (Table~\ref{tab:matrix});
+ rather than as an area is worth \textbf{+23.89$^\circ$} on the pair that binds
+ the baseline accumulated result ($24.90^\circ$ to $48.79^\circ$), after which
+ power/geometry binds instead at $25.26^\circ$, so the suite's worst accumulated
+ pair gains only $0.35^\circ$. What the split buys outright is \emph{per
+ segment}: it is the only change resolving anything there, taking that count
+ from none of ten to \textbf{seven of ten} (Table~\ref{tab:matrix});
```

+23.89 degrees is right, and it is on power/speed, which is the pair that binds
the baseline. But once the camera is split power/speed stops binding: the suite's
worst accumulated pair becomes power/geometry at 25.26, so the **suite** gains
0.35 degrees, not 23.89. A reader comparing this against the "+0.01" for a SWIR
photodiode a line later - which is quoted on the same pair but happens also to
be the worst - would draw the wrong conclusion about what the split buys
accumulated. What it does buy outright is the per-segment result, which is the
stronger claim anyway.

The conclusions sentence gets the same qualifier:

```diff
- valuable addition is free, reporting the camera's two axes separately being worth
- $+23.89^\circ$ and the only change resolving anything per segment.
+ valuable addition is free, reporting the camera's two axes separately being
+ worth $+23.89^\circ$ on the pair that binds the baseline and being the only
+ change resolving anything per segment.
```

### 16. Section 5.1 - "19 works extracted"

```diff
- unrealisable, and the reason is itself a result. Of 19 works extracted --- in-situ
+ unrealisable, and the reason is itself a result. Of 19 works surveyed --- in-situ
```

The table has 19 rows, but one of them is recorded explicitly as a rejected
non-candidate, so it is not an in-situ monitoring study with a stated input and
output. "Surveyed" is accurate where "extracted ... with a stated input signal
and output" was not. The counts the sentence goes on to give - seven and three -
are unaffected and are now checked by `src/literature_census.py`.

---

## Nothing changed in

The abstract, Table 1 (all thirty angles and all three counts reproduce exactly),
Section 3.6 on the noise derivation, Section 4.3 on the melt pool limit, and
Section 4.4's headline figures. The 0.00 degrees, the 24.90 degrees, the rank
3 to 5, the 2562 to 50 condition number, the 0.99960 / 0.99508 / 0.99477
correlations and the singular values all stand as printed.
