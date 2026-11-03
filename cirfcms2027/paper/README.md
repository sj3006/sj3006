# Submittable LaTeX paper

`paper.tex` is the manuscript. It uses the `elsarticle` preamble exactly as
supplied.

## Building

    ./build.sh

produces two PDFs from the one source:

| file | layout | pages |
|---|---|---|
| `paper.pdf` | `preprint`, single column, as the supplied preamble sets | 12 |
| `paper_2col.pdf` | `final,5p,twocolumn` --- the published Procedia CIRP page | **6** |

The page limit applies to the Procedia layout, and the paper is **exactly 6
pages** there, references included. The single-column preprint is longer simply
because one column holds less; it is the same text.

To switch the main file over permanently, replace the first line with the
commented alternative given directly beneath it.

## What had to be cut to reach 6 pages

Content removed, in case any of it should come back if the venue allows more:

- Two of the four figures. Their numbers are all stated in the text: separation
  versus fault magnitude (`fig3_magnitude.png`), and robustness to profile
  misspecification (`fig4_robustness.png`).
- A third figure, build context versus idealised added measurements
  (`fig7_added_sensor.png`); its comparison is given numerically in Section 4.7.
- The profile-contrast figure (`fig2_contrast_threshold.png`); the result is one
  sentence in Section 4.5.
- The sensor-subset misspecification paragraph (errors 2.148 / 0.365 / 0.293 /
  0.288). Retained in full in `explainers/05-validation-and-robustness.md`, D3.
- Three citations: MeltpoolNet (Akbari et al.), the Liu 2023 lock-in follow-up,
  and NIST AMS 100-35 (Lane et al.). The claims they supported either have
  sibling citations or were reworded to stand without one.

### Cut a third time for E1, E3, S2 and the P1 reframing

Those four added a grid-independent validation test, the gas-profile inversion
and the machine-specificity framing --- about another column. Recovered by:
consolidating the profile discussion, which by then repeated across Sections 3.5,
4.5 and 5.3; merging two introduction paragraphs and two limitations paragraphs;
shortening the abstract, where each full-width line is worth two column lines;
and dropping **Reijonen et al. (2020)**, by then cited once in a sentence whose
claim Reijonen (2024) carries alone, the porosity finding it uniquely supported
having been compressed away earlier.

### Cut again when the derived noise figures were added

Deriving the sensor noise (errata E8) added a methods subsection and moved most
numbers in the paper, which cost roughly a page and a half. What went, beyond
another compression pass over essentially every paragraph:

- **All figures.** `fig6_matrix.png` was the last one standing and is now
  Table~1, the same information as exact numbers in about two thirds of the
  space. With the derived figures every instantaneous bar sits near zero, so the
  chart had half its data as invisible slivers; the table is both smaller and
  more precise. **The paper currently has no figures**, which is unusual for
  Procedia and is the first thing to reinstate if a seventh page is available.
- **The configuration table.** Four of its five rows had become identical
  (0/10 and 0.00 degrees for A through D), so it carried almost no information.
  The five classes are now enumerated in prose with their ranks.
- **The standalone "A design rule" subsection**, folded into the end of
  Section 4.7 as two sentences.
- **One citation**, Frisk et al. (2017), the FDI toolbox paper. It appeared only
  alongside Krysander and Frisk (2008), which carries the same claim.

The figure files are all kept in this directory so they can be reinstated.

## Still to do before submission

1. **Author block and affiliation** --- currently a marked placeholder.
2. **Acknowledgements / funding** --- marked `TODO` in the source.
3. **Journal name** in `\journal{}`, and the conference line Procedia requires.
4. **Trapp et al. (2017)** --- volume **9** is now confirmed and in the
   bibliography; the page range still is not (publisher hosts are blocked from
   this machine). Believed to be 341--349. The DOI is confirmed.
5. **The Reijonen comparison** (Section 5.1). The paper now specifies it
   correctly --- a fitted exponent must be compared against a fitted exponent,
   and this model gives $-0.429$ over 0.4--2.2\,m\,s$^{-1}$, not the Jacobian
   entry $-0.483$ (errata E7). What is still needed from that paper's full text
   is the fitted `b` **with its range of validity**, and the power fit's
   **intercept**, without which the paper cannot say whether their power result
   disagrees with ours at all.
6. **Consider restoring a figure.** See the cut list above.
7. **BUILD THE REPRODUCE HARNESS.** Agreed as the last job before submission,
   deliberately deferred so it is built once against final numbers.

   Five numbers in this project's history failed to reproduce (the VED
   correlations, the layer-channel figures in the `FaultCouplings` docstring, the
   collinearity indices, the first draft's singular values, and the fourth noise
   assumption set which existed in the paper but not in the code). All five have
   the same cause: a number computed in a working session, written into prose,
   and never given a home in the repository. None is instability in the
   pipeline, which is deterministic - W1 was caught precisely *because* case 0 is
   asserted to reproduce a stored Jacobian, and matches it to 0.00e+00.

   Every number now in the paper was regenerated from the code, but by hand, in
   ad-hoc scripts. **Nothing in the repository knows what the paper claims**, so
   a change to the model would silently invalidate the PDF again.

   The fix:

   - `src/reproduce.py` computes every quoted figure and writes
     `paper/numbers.tex` as `\newcommand` definitions
   - `paper.tex` uses `\WorstEnlarged` in place of a literal `24.90`, so there is
     no second copy to drift
   - a `--check` mode diffs against stored values and exits non-zero, suitable
     for gating a commit

   Scope: the paper quotes roughly 60 numbers. Do the ~25 load-bearing ones
   first - every angle, rank, condition number, count and noise figure - and
   list the remainder in `reproduce.py` as not yet covered, so the gap stays
   visible rather than being assumed away.

8. **The layer modulation profile** is the one remaining item from the profile
   plan (errata P1, Level 1). It needs the full text of Liu et al. (2022) and the
   2023 lock-in follow-up, which measure local powder layer thickness in situ;
   their layer-to-layer spread gives the contrast directly, with no model in the
   loop, so it would be a cleaner result than the gas inversion.

## Numbers

Every figure quoted in the paper was regenerated from the current code during
drafting, not copied from the earlier markdown draft. Three claims in that draft
did not reproduce and were corrected here:

- The collinearity-index figures (141 869 -> 2.1) did not reproduce and were
  replaced throughout by the condition number, which is cleaner and was verified.

Two further corrections in that list have since been superseded by the derived
noise figures (errata E8), which changed the whitening and so most numbers in the
paper. Current values, all from `src/noise.py`'s derived set:

- Whitened singular values **13.14 / 0.0638 / 0.00513**, rank 3, condition
  number **2562**. (The first draft listed 2.928 / 0.0407 / 0.0054; the asserted
  noise gave 3.451 / 0.155 / 0.041 and a condition number of 85.)
- Seven observables attain rank **3**, not 4, the fourth singular value sitting
  at 2e-7 of the leading one against the 1e-6 threshold. Under the asserted noise
  it reached 4, which shows the integer was tolerance-sensitive; the paper now
  reports the singular values and the threshold rather than the bare rank.
- Enlarged: rank 5, worst pair **24.90 degrees**, condition number 50, all ten
  pairs clearing the floor. (Asserted noise gave 25.83 and 30.)
- Instantaneous class 1 for the baseline suite is **0/10**, not 5/10.

The before-and-after table for every affected quantity is in
`explainers/11-deriving-sensor-noise.md`, section H.
