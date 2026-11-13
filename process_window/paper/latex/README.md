# Paper source

`main.tex` + `references.bib`. Build:
`pdflatex main && bibtex main && pdflatex main && pdflatex main`.

The ICML 2026 style files (`icml2026.sty`, `icml2026.bst`, `fancyhdr.sty`,
`algorithm.sty`, `algorithmic.sty`, from media.icml.cc) are in this folder
and are picked up automatically. When the 2027 files come out, drop
`icml2027.sty` and its `.bst` here; `main.tex` prefers them. The ICML style
needs TeX Live's `latex-extra` collection (for `forloop.sty`); on Debian or
Ubuntu, `apt-get install texlive-latex-extra`. Without the style files the
draft falls back to a two-column layout with ICML-like margins.

Page budget: ICML allows 8 pages of main text. The main text currently ends
on page 6; references and the proofs appendix follow.

Open items in `references.bib`: one entry (`beam2026`, arXiv 2601.17587)
still needs its author list checked. Entries marked "from memory" are
standard references not yet checked against the publisher's record.
