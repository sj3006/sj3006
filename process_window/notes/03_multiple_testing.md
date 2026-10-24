# Note 3: testing many settings at once

Companion to Day 4 (Bretz et al. 2009). Read note 1 first.

## 1. The problem

Testing one setting at alpha = 5% is wrong 5% of the time at most. Testing
144 settings, each at 5%, can make at least one mistake far more often than
5%. The certified window is only useful if it is entirely right, so we
control the **family-wise error rate (FWER)**: the chance of *any* unsafe
setting in the window.

## 2. Bonferroni: split the budget

Give each of K tests the budget alpha / K. By the union bound,
P(any mistake) <= sum of individual mistake chances <= K * alpha/K = alpha.
It works under any dependence between tests.

Cost in our betting tests: certifying needs wealth K/alpha instead of 1/alpha,
so ln K more nats of evidence. At a growth rate of about 0.04 nats per clean
coupon (note 1, section 4), splitting over 432 tests (3 modes x 144 settings)
costs about ln(432) / 0.04 = 150 extra coupons per certified setting. That's
the price of `structure="none"` and `structure="spread"`.

## 3. Fixed-sequence testing: a free ride when hypotheses are ordered

If tests come in a fixed order and you stop at the first one you can't
reject, you can run *every* test at the full alpha, with no splitting. The
reason: the first true null in the order is the only one that can be the
first mistake, and it gets a single shot at alpha.

This is why our chains need no correction inside a chain (Theorem 1,
step 2). The physics ordering hands us natural sequences: walk from safe to
risky along a row.

## 4. Graphical procedures: passing budget along

Bretz et al. generalize both: draw the hypotheses as nodes, give each an
initial share of alpha, and when a hypothesis is rejected, pass its share
along arrows to other nodes. Bonferroni is "no arrows"; fixed sequence is "a
single line of arrows". These procedures are shortcuts for closed testing,
which is why they control FWER.

In our setting it would be natural to pass budget from a chain that has
finished (walked all the way to its risky end) to chains still working.

**Why this is not yet in the code.** The classical proof assumes each test is
a single p-value computed once. Ours are e-processes watched continuously,
and a chain's budget would then *increase over time* in a data-dependent
way. Ville's inequality is about a fixed threshold 1/alpha, so it no longer
applies directly. Two candidate fixes, to work out in week 3:

1. When budget arrives at a chain, start a *fresh* e-process for the
   received share, so each piece of budget has its own fixed threshold.
   The open question is whether the sum over all pieces held by true nulls
   stays at most alpha when the pieces arrive at data-dependent times.
2. Use known closed-testing results for e-values (Vovk & Wang, "Confidence
   and discoveries with e-values", Statistical Science 2023, and follow-ups)
   to define the procedure directly through e-value combinations.

Expected payoff: at most a factor of about 2 in budget, so ln 2 = 0.7 nats
per certification. Worth doing for the paper, not urgent.

## 5. Where this left us (and what the experiments changed)

Our first design used chains everywhere (free ride inside chains, Bonferroni
across rows). Experiments showed that **chains cost more coupons than they
save in budget** when the grid is fine, because they force us to certify
every point on the walk, including expensive ones near the window edge.
Note 4 explains this and how it reshapes the theory.

## 6. Check yourself

1. With K = 3 modes x 16 rows = 48 chains, how many extra nats does each
   certification need compared with a single test? With 3 x 256 one-point
   chains?
2. Why does fixed-sequence testing need the order to be chosen before the
   data? Give an example of a data-dependent order that breaks it.
3. In the hybrid structure (half the budget to chains, half to one-point
   chains), why does a point that is current in both families get to use
   the larger of its two budgets?

(1: ln 48 = 3.9 nats; ln 768 = 6.6 nats. 3: the union bound in Theorem 1
already pays for both families, so whichever threshold is crossed first is
a valid certification.)
