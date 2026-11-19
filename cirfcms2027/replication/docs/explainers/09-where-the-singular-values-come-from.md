# Where the singular values come from: the two Gram matrices

`08-condition-number.md` says the condition number is the loudest fault mixture
divided by the quietest visible one, and quotes 3.4507 and 0.0405 without
showing where those come from. This file derives them, and in doing so connects
two things that look separate in the paper: the **pairwise angles** and the
**condition number** are the same object viewed from opposite sides.

---

# Part A - From the model to a matrix

## A1. Eleven model runs

One run at zero fault, then +h and -h for each of five faults, central
differences, relative to nominal. That gives the Jacobian `J` (3 sensors x 5
faults):

|  | power | speed | layer | gas | geometry |
|---|---|---|---|---|---|
| photodiode | 1.51768 | -0.48347 | -0.58388 | -1.51769 | 0.06536 |
| camera | 1.22347 | -0.41977 | -0.45569 | -1.22347 | 0.09297 |
| pyrometer | 0.03632 | -0.01542 | -0.01205 | -0.03632 | -0.00178 |

## A2. Whitening, and why it is not cosmetic

Divide each row by that sensor's relative noise, sigma = (1.0, 1.0, 0.03):

|  | power | speed | layer | gas | geometry |
|---|---|---|---|---|---|
| photodiode | 1.51768 | -0.48347 | -0.58388 | -1.51769 | 0.06536 |
| camera | 1.22347 | -0.41977 | -0.45569 | -1.22347 | 0.09297 |
| **pyrometer** | **1.21074** | **-0.51395** | **-0.40167** | **-1.21082** | **-0.05948** |

The first two rows are untouched; the pyrometer row is multiplied by 33.3.

**This step does real work.** In raw units the pyrometer looks negligible - its
entries are forty times smaller than the photodiode's. After whitening it is
comparable. A faint signal from a quiet instrument carries as much information
as a loud signal from a noisy one, and whitening is what puts that on the
record. Every unit from here on is a **noise-width**.

---

# Part B - The two Gram matrices

A Gram matrix is a table of dot products. `Jw` can be multiplied by its own
transpose two ways, giving two different tables that answer two different
questions.

## B1. A = Jw Jw^T, 3 x 3, SENSOR against SENSOR

Entry (i, j) is (row i) . (row j), that is

    sum over the 5 faults of [sensitivity of sensor i to fault k]
                           x [sensitivity of sensor j to fault k]

Faults have been summed over; nothing about them survives in the shape.

|  | photodiode | camera | pyrometer |
|---|---|---|---|
| photodiode | 5.18565 | 4.18877 | 4.15427 |
| camera | 4.18877 | 3.38626 | 3.35595 |
| pyrometer | 4.15427 | 3.35595 | 3.36098 |

**The diagonal** is each sensor's own total squared response - how much that
instrument moves, in total, across everything that can go wrong. Check: the
photodiode row of `Jw`, squared and summed, is 5.18565.

**The off-diagonal** is how much two sensors move *together*. Normalise it,
dividing entry (i,j) by sqrt(A_ii A_jj), and it becomes a plain correlation:

|  | photodiode | camera | pyrometer |
|---|---|---|---|
| photodiode | 1.00000 | **0.99960** | **0.99508** |
| camera | 0.99960 | 1.00000 | **0.99477** |
| pyrometer | 0.99508 | 0.99477 | 1.00000 |

**Every pair of sensors is more than 99.4 % correlated.** A photodiode, a camera
measuring area and a two-colour pyrometer - three physically different
instruments - respond to the five faults in almost exactly the same pattern.

That is the entire problem of the paper, visible in one 3 x 3 table, before any
eigenvalue is taken.

## B2. B = Jw^T Jw, 5 x 5, FAULT against FAULT

Multiply the other way and the roles swap: now the sensors are summed over and
the table compares faults. Normalised the same way, **its entries are exactly
the cosines of the pairwise angles**:

|  | power | speed | layer | gas | geometry |
|---|---|---|---|---|---|
| power | 1.00000 | -0.99229 | -0.99818 | **-1.00000** | 0.47878 |
| speed | -0.99229 | 1.00000 | 0.98300 | 0.99230 | -0.38036 |
| layer | -0.99818 | 0.98300 | 1.00000 | 0.99817 | -0.52405 |
| gas | **-1.00000** | 0.99230 | 0.99817 | 1.00000 | -0.47875 |
| geometry | 0.47878 | -0.38036 | -0.52405 | -0.47875 | 1.00000 |

    arccos(|-1.00000|)  = 0.0017 deg    power / gas
    arccos(|-0.99229|)  = 7.1179 deg    power / speed

The 0.0017 rather than exactly 0 is finite-difference residue on what is an
exact algebraic identity; it is reported as 0.00.

**On the minus sign.** More power raises the product (absorptivity x power);
worse gas lowers it. So the two point in opposite directions along one line.
Anti-parallel is just as indistinguishable as parallel - a fault pair differing
only in sign still cannot be separated - which is why the angle takes the
absolute value of the cosine.

## B3. The two matrices are one object

A and B have **the same nonzero eigenvalues**:

    A (3 x 3):   11.907373   0.023875   0.001643
    B (5 x 5):   11.907373   0.023875   0.001643   0   0

B carries two extra zeros because there are five faults but only rank 3.

So **the pairwise angle machinery and the condition number machinery are the
same computation taken from opposite sides.** `Jw^T Jw` normalised gives the
angles between faults; `Jw Jw^T` gives the agreement between sensors; their
shared eigenvalues give the rank and the condition number. The paper presents
these as three separate measures. They are three readings of one matrix.

---

# Part C - What the square root of an eigenvalue represents

## C1. The derivation, in four lines

Take any fault mixture `v` of unit size. The readings move by `Jw v`, and the
size of that movement is ||Jw v||. Square it:

    ||Jw v||^2  =  (Jw v)^T (Jw v)  =  v^T (Jw^T Jw) v

Now ask which unit `v` makes that largest. Maximising a quadratic form over the
unit sphere is a standard result: **the maximum is the largest eigenvalue, and
it is attained at the corresponding eigenvector.** Likewise the minimum and the
smallest eigenvalue. So

> **An eigenvalue is the squared length of the sensor response to the best, or
> worst, unit fault mixture. Its eigenvector is that mixture.**

The square root undoes the squaring and returns to the units of the readings.
Dot products always produce squares of lengths; the root brings you back.

## C2. Verified, not asserted

Push each unit eigenvector through `Jw` and measure the response:

| eigenvector | \|\|v\|\| | \|\|Jw v\|\| | sqrt(eigenvalue) |
|---|---|---|---|
| 1st | 1.0000 | **3.450706** | **3.450706** |
| 2nd | 1.0000 | 0.154516 | 0.154516 |
| 3rd | 1.0000 | 0.040536 | 0.040536 |

Exact agreement. So 3.4507 is not an abstract index. It is *the readings move
3.4507 noise-widths for the loudest unit fault mixture*, and 0.0405 is *0.0405
noise-widths for the quietest visible one*.

    condition number = 3.450706 / 0.040536 = 85.13

## C3. Units check

    Jw entry          noise-widths of sensor movement per unit fault
    A entry           (noise-widths per unit fault)^2
    eigenvalue of A   same, squared
    sqrt(eigenvalue)  noise-widths per unit fault   <- back to Jw's own units

---

# Part D - Why one eigenvalue swallows almost everything

The trace of A - the sum of its diagonal - is **11.932892**, and that is the
total response energy available. Three independent checks give the same figure:

    trace(A)                          = 11.932892
    sum of squared entries of Jw      = 11.932892
    sum of the eigenvalues            = 11.932892

The largest eigenvalue alone is 11.907373, which is **99.79 %** of it.

**Why.** Because of the 99.4 %+ correlations in B1. When three rows nearly
coincide, their contributions pile into a single direction instead of spreading
over three. Had the sensors been independent, the trace would have split roughly
evenly and the condition number would have been near 1.

Note too that the top eigenvalue, 11.907, is **larger than any diagonal entry**
(the largest is the photodiode's 5.186). The sensors reinforce one another along
the direction they agree on. They are loud together in that one direction and
nearly deaf in every other.

**That single fact - 99.79 % of the energy in one direction - is the condition
number of 85, the rank of 3, and the power/gas confound. Three names for one
situation.**

---

# What this licenses

**It licenses** stating that the three-sensor suite is near-redundant as a
measured property rather than an impression: the sensor correlation matrix in
B1 is the direct evidence, and it needs no eigenvalue to read.

**It licenses** treating the angles, the rank and the condition number as
consistent by construction rather than as three independent confirmations. They
are not independent evidence of anything - they are the same matrix reported
three ways, and the paper should not imply otherwise.

**It does not license** reading the 99.79 % as a property of melt pool physics
in general. It is a property of *these three observables under these noise
ratios*. Changing the noise ratios changes the whitening and therefore the
split - see C5 in `05-validation-and-robustness.md`, where the condition number
moves between 30 and 61 across the swept ratio sets while the worst angle barely
moves at all.
