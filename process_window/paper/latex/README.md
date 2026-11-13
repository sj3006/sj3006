# Paper source

`main.tex` + `references.bib`. Build: `pdflatex main && bibtex main && pdflatex main && pdflatex main`.

The ICML style file is not in the repo (icml.cc is not reachable from the
build machine, and the 2027 file is not out yet). Put `icml2027.sty` (or
`icml2026.sty`) and its `.bst` next to `main.tex` and it is picked up
automatically; without it the draft compiles in a two-column layout with
ICML-like margins. Red `[TBD]` marks numbers from runs in progress.
