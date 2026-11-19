#!/usr/bin/env bash
# Build the paper. Figures come from ../figures, which `python3 ../figures.py`
# regenerates from ../results.json.
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
echo "pages: $(pdfinfo paper.pdf | awk '/Pages/{print $2}')"
