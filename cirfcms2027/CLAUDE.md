# Working agreements for this project

## Explaining things: start from first principles

Amit's standing instruction, and it applies every time he questions a term, a
method, a number or a choice — not only when he asks for an explanation.

Build the answer from the ground up:

1. **Define the object itself** before using it. What *is* a Jacobian, a
   collinearity index, a whitening transform. Not "it measures sensitivity" —
   the actual definition, with its shape and what each entry means.
2. **Show it with our real numbers**, not a generic example. Print the actual
   matrix from the actual run.
3. **Do the arithmetic that produces the result**, so the number is traceable.
   "Divide these two columns element-wise and you get −4.96, −5.00, −4.67 —
   nearly constant, so they're parallel, so the angle is 0.99°."
4. **Give every number context.** 35 W/mK means nothing alone; "IN718 is about
   11 cold and 30 near melting, copper is 400" makes it mean something.
5. **One analogy, placed after the mechanics**, never instead of them. Two roads
   leaving a town. A thermometer that can't tell flu from infection.
6. **Say what it does and does not license us to claim.** Where the method is
   valid, where it breaks, what the honest version of the sentence is.

The response that earned this instruction explained the Jacobian: definition,
our 3x5 matrix printed out, the element-wise division that yields the confounding
angle, the Taylor-expansion meaning of linearisation, the two-roads analogy, then
the consequence for paper structure. Match that depth.

## Other standing points

- Correct false premises immediately and plainly, before answering around them.
  Several have come up (the dataset we "decided" on, the alloy we "chose", the
  model being "happy" when it was uncalibrated).
- Flag the limits of my own verification. If I read a loader and inferred a file
  format rather than opening a file, say so.
- Run the check rather than asserting the answer. Several of this project's real
  findings — the keyholing regime, the step-size non-convergence, the locality
  of diagnosability — came from testing a claim instead of stating it.
- Prose over bullets where prose reads better. Sentence case headings.
