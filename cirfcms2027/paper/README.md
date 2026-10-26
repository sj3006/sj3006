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

Only `fig6_matrix.png` (the diagnosability matrix) remains in the paper. The
other figure files are kept in this directory so they can be reinstated.

## Still to do before submission

1. **Author block and affiliation** --- currently a marked placeholder.
2. **Acknowledgements / funding** --- marked `TODO` in the source.
3. **Journal name** in `\journal{}`, and the conference line Procedia requires.
4. **Trapp et al. (2017)** --- volume and page numbers could not be confirmed
   from this machine (publisher hosts are blocked); the DOI is confirmed. Add
   volume/pages, believed to be 9:341--349.
5. **The Reijonen comparison** (Section 5.1) is proposed in the paper as the
   decisive test of the forward model. If the fitted exponent `b` can be read
   from that paper, it is directly comparable to our Jacobian entry of
   $-0.483$, and the power response to $+1.518$. Worth doing before submission
   because it could also contradict the model.

## Numbers

Every figure quoted in the paper was regenerated from the current code during
drafting, not copied from the earlier markdown draft. Three claims in that draft
did not reproduce and were corrected here:

- The seven-observable rank is **4**, not 3, with the fourth direction at a
  condition number of 2.3e5. The draft said rank stayed at 3.
- The whitened singular values are 3.451 / 0.155 / 0.041; the draft listed
  2.928 / 0.0407 / 0.0054.
- The collinearity-index figures (141 869 -> 2.1) did not reproduce and were
  replaced throughout by the condition number (85 -> 30), which is cleaner and
  was verified.
