# Coefficient noise: why sigma_s is the wrong number, and what replaces it

The enlarged observation replaces one reading per sensor with five regression
coefficients per sensor. Those coefficients are quieter than the reading they
came from, and they are not all equally quiet. This file derives the noise on
each one from scratch, with the matrix algebra the derivation needs.

The quantity being explained is the one in Section 3.5 of the paper:

    sigma_(s,j) = sigma_s * sqrt( [ (G^T G)^-1 ]_jj )

**Reading note.** The square root is essential and is easy to lose when copying
this out of a rendered PDF - the radical does not survive text extraction.
Without it the formula is wrong and the numbers below do not follow.

---

# Part A - The precursors

## A1. What is being estimated

At each of N = 84 segments a sensor gives one reading. Collect the relative
residuals - how far each reading sits from its healthy value - in a column
vector `r` of length 84.

The claim is that those residuals are a combination of five **known** context
variables: a constant, position along the gas-flow axis, layer parity, turn
density, and support depth. Stack them as the columns of a **design matrix**
`G` of shape 84 x 5, and write

    r  =  G beta  +  epsilon

with `beta` the five unknown coefficients and `epsilon` the measurement noise.
Those five numbers replace the single reading, which is where

    3 sensors x 5 coefficients = 15 observables

comes from. Shapes, since they drive everything else:

    r        84 x 1      one residual per segment
    G        84 x 5      known context, one column per regressor
    beta      5 x 1      what we estimate
    G^T G     5 x 5      the Gram matrix

The first six rows of the actual `G`:

     1    -1.6125   -1    +2.2113   +1.4926
     1    -1.3644   -1    +0.3246   +1.3084
     1    -1.1163   -1    -0.1104   +1.1242
     1    -0.8682   -1    -0.3374   +0.9401
     1    -0.6202   -1    -0.6243   +0.7559
     1    -0.3721   -1    -0.6902   +0.5717

Column 1 is the intercept, all ones. The other four are standardised. Every
column therefore has norm exactly sqrt(84) = 9.1652, which matters in A4.

## A2. The Gram matrix G^T G

`G^T` is `G` with rows and columns exchanged, so it is 5 x 84 and the product
`G^T G` is **5 x 5**. Entry (i, j) is the dot product of regressor i with
regressor j:

    [G^T G]_ij  =  g_i . g_j

It is the table of how much each regressor overlaps every other one. Ours:

| | intercept | gas axis | parity | turns | support |
|---|---|---|---|---|---|
| **intercept** | 84.00 | 0.00 | 0.00 | -0.00 | 0.00 |
| **gas axis** | 0.00 | 84.00 | 0.00 | 1.47 | 0.00 |
| **parity** | 0.00 | 0.00 | 84.00 | -1.77 | -15.79 |
| **turns** | -0.00 | 1.47 | -1.77 | 84.00 | 47.93 |
| **support** | 0.00 | 0.00 | -15.79 | 47.93 | 84.00 |

Three things to read off it.

**The diagonal is 84**, because each column has norm sqrt(84), so
g_j . g_j = 84 = N.

**Most off-diagonals are about zero.** Those regressors are essentially
orthogonal and carry independent information.

**Two are not.** Turn density and support depth overlap at 47.93 out of 84, a
correlation of 0.57. Parity and support overlap at -15.79, a correlation of
-0.19.

That overlap is the same phenomenon as the fault confounding the paper is
about - two things that vary together are hard to tell apart - appearing here
among the context regressors rather than among the faults.

## A3. Least squares, and where (G^T G)^-1 comes from

Choose `beta` to minimise the squared mismatch || r - G beta ||^2. Differentiate
with respect to `beta`, set to zero, and the result is the **normal equations**

    G^T G beta  =  G^T r

Multiply both sides by the inverse of the 5 x 5 matrix `G^T G`:

    beta_hat  =  (G^T G)^-1 G^T r

So `(G^T G)^-1` is not decoration. It is the thing that undoes the overlap
between regressors. Were the regressors perfectly orthogonal it would be a plain
diagonal matrix; the more they overlap, the more work it does. Ours:

     0.0119  -0.0000  -0.0000   0.0000  -0.0000
    -0.0000   0.0119   0.0000  -0.0003   0.0002
    -0.0000   0.0000   0.0125  -0.0016   0.0033
     0.0000  -0.0003  -0.0016   0.0179  -0.0105
    -0.0000   0.0002   0.0033  -0.0105   0.0185

## A4. How noise propagates through a matrix

This is the step the whole formula rests on. Write

    M  =  (G^T G)^-1 G^T          (a fixed 5 x 84 matrix)

so that `beta_hat = M r`. For any fixed matrix M and random vector r,

    Cov(beta_hat)  =  M Cov(r) M^T

Assume the noise on each segment is independent with the same size sigma_s, so
`Cov(r) = sigma_s^2 I`. Then

    Cov(beta_hat) = sigma_s^2 M M^T
                  = sigma_s^2 (G^T G)^-1 G^T . G (G^T G)^-1
                  = sigma_s^2 (G^T G)^-1 (G^T G) (G^T G)^-1
                  = sigma_s^2 (G^T G)^-1

The middle two factors cancel, and `(G^T G)^-1` is symmetric so its transpose is
itself. **That cancellation is why this single matrix carries the entire noise
answer.**

A covariance matrix holds **variances on its diagonal**. So the variance of
coefficient j is `sigma_s^2 [(G^T G)^-1]_jj`, and its standard deviation - the
noise on that coefficient - is the square root:

    sigma_(s,j)  =  sigma_s * sqrt( [ (G^T G)^-1 ]_jj )

---

# Part B - The numbers

## B1. The five values

| regressor j | [(G^T G)^-1]_jj | sqrt of it | noise reduction |
|---|---|---|---|
| intercept | 0.011905 | **0.109109** | 9.17x |
| gas axis | 0.011910 | 0.109134 | 9.16x |
| layer parity | 0.012484 | 0.111731 | 8.95x |
| turn density | 0.017866 | 0.133664 | 7.48x |
| support depth | 0.018507 | **0.136040** | 7.35x |

which is the paper's "between 0.109 and 0.136".

## B2. Where the ninefold comes from

If the regressors were perfectly orthogonal with norm sqrt(N), then
`G^T G = N I`, so `(G^T G)^-1 = I / N`, every diagonal entry is 1/N, and

    sqrt(1/N) = 1/sqrt(84) = 0.109109

That is **exactly** the intercept's value, because its column is orthogonal to
all the others. And 1/0.109109 = 9.17 = sqrt(84).

**The "ninefold" is literally sqrt(N).**

**Physically.** Each coefficient is a weighted sum of 84 independent noisy
measurements. Independent noises add in quadrature and grow as sqrt(N), while
the signal adds coherently and grows as N. Net gain sqrt(N).

## B3. Why the other four fall short

Because of the overlap in A2. Multiplying each diagonal entry by N gives the
**variance inflation factor**, the standard measure of how much collinearity
costs:

| regressor | VIF |
|---|---|
| intercept | 1.00 |
| gas axis | 1.00 |
| layer parity | 1.05 |
| turn density | 1.50 |
| support depth | 1.55 |

Support depth pays a 55 % variance penalty for sharing information with turn
density. All five are well below the usual VIF > 5 concern threshold, so the
design matrix is in good shape - but the spread is not nothing, as B5 shows.

## B4. How it enters the rest of the machinery

`coefficient_sigmas` returns 15 numbers: the five above, tiled once per sensor
and scaled by that sensor's own relative noise.

    photodiode (sigma_s = 1.00):  0.1091  0.1091  0.1117  0.1337  0.1360
    camera     (sigma_s = 1.00):  0.1091  0.1091  0.1117  0.1337  0.1360
    pyrometer  (sigma_s = 0.03):  0.0033  0.0033  0.0034  0.0040  0.0041

Each of the 15 rows of the enlarged Jacobian is divided by its own
`sigma_(s,j)` before any angle, rank or condition number is computed.

## B5. What went wrong, stated precisely

The original code whitened every coefficient by the raw `sigma_s` instead of
`sigma_s * sqrt([(G^T G)^-1]_jj)`. It is worth separating the two things that
error did, because only one of them corrupted the published numbers.

**The common part - the roughly 9x - did not corrupt the angles.** It is nearly
a single scalar across all 15 rows, and angles, rank and condition number are
all invariant to a common scaling of the whole matrix. What it does affect is
any *absolute* statement about noise, which is why the factor is worth
reporting at all: the enlarged observation genuinely is about nine times quieter
than a single reading.

**The spread is what did the damage.**

    0.136040 / 0.109109 = 1.2468

a 24.7 % variation between the best- and worst-determined coefficients. Using
one `sigma_s` for all five flattens that spread, which is a **non-uniform**
reweighting of rows relative to the truth - and non-uniform row scaling rotates
the columns, so it changes every angle.

So the honest summary: the formula buys a real sqrt(84) noise reduction, and the
thing that made the earlier angles wrong was the roughly 25 % relative
misweighting the same formula encodes. Entry E4 of
`05-validation-and-robustness.md` records both effects together without
separating them; this file is the one that says which of the two actually moved
the numbers.

`pair_angles` and `rank_cond` now refuse a noise vector whose length does not
match the matrix, rather than broadcasting it, so the specific mistake cannot
recur silently.

---

# One analogy, after the mechanics

Think of each coefficient as a vote counted from 84 ballots. Counting 84 noisy
ballots instead of one shrinks the error by sqrt(84), about 9 - that is the
diagonal of `(G^T G)^-1` in the ideal case. But two of the five questions on the
ballot are phrased similarly enough that 57 % of voters answer them together,
so separating those two answers needs more ballots to reach the same confidence.
That is the 1.55 variance inflation on support depth. The matrix `(G^T G)^-1`
does the bookkeeping for both effects at once.

---

# What this licenses

**It licenses** reporting the enlarged observation as about nine times quieter
per coefficient than a single reading, with the caveat that the exact factor
runs 7.35x to 9.17x depending on the regressor; and treating the 15 whitened
rows as correctly weighted relative to one another.

**It does not license** any absolute detection threshold. `sigma_s` itself is a
*ratio* swept over four assumption sets, not a calibrated figure - see
`04-noise-position.md`. The formula says how the regression redistributes
whatever noise the sensor has; it says nothing about how large that noise is.

**It also does not license** reading the sqrt(N) gain as free accuracy. It
assumes the noise on each segment is independent and identically distributed.
Correlated segment-to-segment noise - drift, a thermal transient across the
build - would break that assumption and the true gain would be smaller. Nothing
in this study tests that assumption, and it is the natural next thing to
challenge in this part of the method.
