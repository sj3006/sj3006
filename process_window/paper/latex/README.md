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

References: every entry in `references.bib` was checked on 2026-11-13
against the publisher, proceedings or an indexing record (volume, pages, DOI
where one exists). One detail is open: the volume and pages of
`waudbysmith2024betting` (JRSS B 2024), because the publisher page could not
be reached from the build machine.
