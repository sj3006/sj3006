# Submission form fields and pre-submission checklist

## Title

Certifying Safe Operating Regions under Monotone Failure Modes

## TL;DR (one sentence)

When every failure mode of a system is monotone in its knobs, closed
testing with betting e-processes certifies the safe operating region with
a family-wise guarantee at a cost that scales with the region's edge, not
its area, which is several times cheaper than full-grid Learn-then-Test on
language-model sampling settings and process windows.

## Keywords

anytime-valid inference; e-values; betting; closed testing; multiple
testing; monotonicity; safe region; level-set estimation; adaptive
experimental design; Learn-then-Test; LLM sampling; additive manufacturing

## Primary area (pick at submission)

Probabilistic methods / statistical inference (anytime-valid testing),
with "safety" and "applications" as secondary areas if the form allows.

## Abstract (plain text, as in the paper; about 330 words)

Many systems are configured by a few continuous knobs, and each setting
can fail in more than one way: a language model sampled at low temperature
degenerates into repetition and at high temperature into incoherence; a
laser powder bed fusion process at low energy leaves unmelted powder and
at high energy drills keyhole pores. Practitioners need the safe operating
region, the settings where every failure mode is rare. Each failure rate
can only be estimated from trials at that very setting, so evaluating a
grid of configurations costs in proportion to its area. We study
certifying a safe region with a family-wise guarantee when every
configuration needs its own trials, using the one piece of structure
these systems share: each failure mode is monotone in known directions.
We give (i) the cone rule, a closed-testing procedure with betting
e-processes that is valid at any stopping time and under any adaptive
choice of trials, and under monotonicity reduces to two cumulative sums;
(ii) a search algorithm for the fixed-confidence problem that stops on its
own once the target region is certified; (iii) lower bounds showing that
with the ordering the cost is governed by the region's edge and without it
by its area, and an upper bound for the search within logarithmic and
multiple-testing factors of the ordered lower bound. On the sampling
settings of language models, where repetition and incoherence rates are
measured from real generations, the method certifies half of the safe
region with 2.1x fewer generations than testing without the ordering on a
12x12 grid and 4.3x fewer on a 23x23 grid (3.1x and 8.1x fewer than
full-grid Learn-then-Test), pilot study included, and 1.6-2.0x fewer on
two larger models. Across this, additive manufacturing process windows
and a drug-combination screen it needs 1.3-9x fewer trials than adaptive
testing without the ordering and, on 48x48 grids, 19-26x fewer than a
full grid with fixed-sequence testing, with no unsafe setting certified in
any run, while Gaussian-process baselines (level-set estimation,
BEAM-style active search, safe expansion) carry no such guarantee: a
tuning whose error rate stays near 5% on one problem certifies unsafe
settings in up to 42.5% of runs on another, and the data do not say which
tuning to trust.

## Optional shorter abstract (about 190 words), if you prefer one

Many systems are configured by a few knobs, and each setting can fail in
several ways: a language model sampled too cold repeats itself and too hot
becomes incoherent; a laser powder bed fusion process leaves unmelted
powder at low energy and keyhole pores at high energy. We certify the safe
operating region, where every failure rate is below its tolerance, with a
family-wise guarantee, when each setting needs its own trials. The
structure we use is that each failure mode is monotone in known
directions. We give a closed-testing rule with betting e-processes that is
valid under any adaptive allocation and reduces to two cumulative sums; a
search algorithm that stops once the target region is certified; and lower
bounds showing that the cost scales with the region's edge with the
ordering and with its area without it, with the search within logarithmic
and multiple-testing factors of the ordered bound. On language-model
sampling settings measured from real generations, the method needs 2-4x
fewer generations than testing without the ordering and 3-8x fewer than
full-grid Learn-then-Test; on manufacturing and drug-combination problems,
up to 26x fewer than a full grid, with no unsafe setting certified in any
run. Tuned Gaussian-process baselines have no such guarantee.

## Pre-submission checklist

- [x] Anonymous: author block "Anonymous Authors"; PDF metadata author
      "Anonymous Authors"; no names, paths or e-mails in the PDF text.
- [x] Main text within 8 pages (ends near the top of page 8); Impact Statement,
      references and appendices after it.
- [x] Impact Statement present.
- [x] Supplement: dist/supplement.zip (scripts/make_supplement.py),
      anonymized and scanned; tests pass from the unpacked copy.
- [x] Every reference checked against a publisher or indexing record
      (one open item: page range of Waudby-Smith and Ramdas 2024).
- [ ] Switch to the ICML 2027 style files when released (drop
      icml2027.sty/.bst into paper/latex/; main.tex picks them up).
- [ ] Re-run the anonymity scan after the last edit
      (python3 scripts/make_supplement.py fails if anything identifying
      is left in the code archive; for the PDF: pdfinfo main.pdf and
      pdftotext main.pdf - | grep -i <your name>).
- [ ] Confirm the licence for the code release (MIT placeholder).
- [ ] Decide on co-authors; ICML requires every author to have an
      OpenReview profile before the deadline.
- [ ] Check the call for papers for the reviewer requirement (in recent
      years authors were asked to serve as reviewers).
