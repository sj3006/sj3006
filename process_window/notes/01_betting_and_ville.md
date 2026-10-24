# Note 1: testing by betting, and why you may peek

Companion to Day 1 (Shafer 2021) and Day 2 (Ramdas et al. 2023). Read this
first, then the papers. Everything here is used directly in
`pwcert/eprocess.py`.

## 1. The question for one setting

Fix one setting (say 200 W, 800 mm/s) and one failure mode (lack of fusion).
Each coupon is a defect (Y = 1) or not (Y = 0). The unknown defect rate is p.
We want to claim "p < eps" (for example eps = 5%) and be wrong at most
alpha = 5% of the time.

In statistics we set up the claim we want to *disprove* as the null
hypothesis:

    H0: p >= eps        (the setting is bad)

Certifying the setting means rejecting H0.

## 2. The bet

Start with wealth K_0 = 1. Before coupon t is inspected, choose a bet
lam_t >= 0. After seeing Y_t, wealth is multiplied by

    1 + lam_t * (eps - Y_t).

- Good coupon (Y = 0): multiply by 1 + lam_t * eps (a small gain).
- Defect (Y = 1): multiply by 1 - lam_t * (1 - eps) (a big loss).

Worked numbers with eps = 0.05 and lam = 1:

| coupon | outcome | factor | wealth |
|---|---|---|---|
| 1 | good | 1.05 | 1.05 |
| 2 | good | 1.05 | 1.10 |
| ... | good | 1.05 | ... |
| 30 | good | 1.05 | 4.32 |
| 31 | defect | 0.05 | 0.22 |

lam = 1 is reckless: one defect wipes out 95% of the wealth. The code caps
lam at 0.8 / (1 - eps), so a defect costs at most 80%.

**Rule:** certify the setting the first time wealth reaches 1/alpha (= 20).

## 3. Why the rule is safe (the whole argument)

Suppose H0 is true, so p >= eps. Then the expected multiplier on any coupon,
given everything seen so far, is

    E[1 + lam_t (eps - Y_t) | past] = 1 + lam_t (eps - p) <= 1,

because lam_t >= 0 was chosen before seeing Y_t, and eps - p <= 0. So the
gambler's expected wealth can never grow. That makes the wealth process a
*nonnegative supermartingale*: a fair-or-worse game you can't go below zero
in.

**Ville's inequality (1939):** for a nonnegative supermartingale starting at
1,

    P( wealth ever reaches 1/alpha ) <= alpha.

"Ever" is the important word. It covers every coupon, all at once, so you
may check after every coupon and stop the moment you like the answer. That
is what "anytime-valid" means. An ordinary p-value does not allow this: if
you recompute a p-value after every coupon and stop when it dips below 0.05,
your real error rate is far above 5%.

Intuition for Ville: a gambler in a game that's fair-or-worse, starting with
$1, reaches $20 with probability at most 1/20. Otherwise the gambler could
"buy" the strategy "play until $20, then stop" and make money on average in
a game that doesn't allow that. (The formal proof is optional stopping
applied to the stopping time "first time wealth >= 1/alpha"; see Ramdas et
al. 2023, section 3, or the Lattimore & Szepesvari bandit book, chapter 3.)

Notice what the argument does **not** need:

- It doesn't care how lam_t was chosen, as long as it was chosen before
  seeing Y_t. So a simulator, a hunch, or past data can choose it. A bad
  simulator only makes the gambler lose money and certify slowly. It can
  never cause a false certification more than alpha of the time.
- It doesn't need a fixed sample size. Stop whenever.
- It doesn't need p to be a nice number, or any model of the process.

This is why the guarantee in our paper survives a wrong simulator.

## 4. Link to the success-run rule you already use

The zero-failure success-run rule says: to show reliability R = 1 - eps with
confidence C = 1 - alpha, test n = ln(alpha) / ln(1 - eps) parts with no
failures. For eps = alpha = 0.05 that's 58.4, so 59 parts.

The best possible bet when the true rate is p = 0 grows wealth at rate
ln(1 / (1 - eps)) per coupon (you bet the maximum lam = 1/(1 - eps), and
every coupon is good). Reaching 1/alpha takes ln(1/alpha) / ln(1/(1 - eps))
coupons, which is exactly the success-run number. So **the success-run rule
is the betting test with the most aggressive bet.** The betting version is
the generalization that can also absorb occasional defects, and that lets
you stop early or continue as data comes in.

More generally, against a true rate p < eps, the best long-run growth rate
of log-wealth is the KL divergence between Bernoulli(p) and Bernoulli(eps):

    KL(p || eps) = p ln(p/eps) + (1 - p) ln((1 - p)/(1 - eps)),

so certification takes about ln(1/alpha) / KL(p || eps) coupons. Read this
as: the closer p is to eps, the more coupons you need, blowing up as p
approaches eps. This formula will be the "per-point cost" in our
sample-complexity theorem.

Our experiment 1 (`results/exp01_power.csv`) shows ~73 coupons at p = 0,
above the 58 floor, because the cap (0.8) keeps the gambler from betting
everything.

## 5. The betting strategies in the code

- **fixed:** always bet the same lam. Simple, but bad if p is near eps.
- **agrapa:** estimate p from prior + data, then bet the amount that would
  be best if the estimate were right (lam = E[X] / E[X^2] with
  X = eps - Y). The prior is where the simulator enters.
- **mixture:** split the $1 across eight gamblers with different fixed bets
  and add up their wealth. Robust because one of them is always close to the
  right bet. Averages of valid wealth processes are valid.
- **hedge:** half the money in agrapa, half in mixture. You lose at most a
  factor 2 relative to whichever does better.

Finding from experiment 1: seeding the bets with an accurate simulator helps
only slightly (73 vs 78 coupons), and a pessimistic one hurts (about 120).
So the simulator's main value in this project is in *where* to test, not in
*how much* to bet. Keep that in mind when we write the method section.

## 6. Check yourself

1. Why must lam_t be chosen before Y_t is seen? What goes wrong in step 3
   if it isn't?
2. If lam_t = 0 for every coupon, what happens to the wealth, and is the
   test still valid?
3. Why can't a lying simulator push the false-certification rate above
   alpha?
4. Using the KL formula, roughly how many coupons does a setting with
   p = 0.02 need at eps = 0.05, alpha = 0.05? Compare with the medians in
   `results/exp01_power.csv` (look at the hedge rows).

(Answers to 4: KL(0.02 || 0.05) is about 0.0118, and ln 20 / 0.0118 is
about 250. The hedge medians are about 210-280.)
