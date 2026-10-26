#!/usr/bin/env bash
# Build both layouts. Usage: ./build.sh
set -e
cd "$(dirname "$0")"

# 1. The format as supplied: elsarticle "preprint", single column.
pdflatex -interaction=nonstopmode paper.tex >/dev/null
pdflatex -interaction=nonstopmode paper.tex >/dev/null

# 2. The published Procedia CIRP layout: two column. This is the one that
#    must fit the page limit, and it currently comes to exactly 6 pages.
sed 's/^\\documentclass\[preprint,times\]{elsarticle}/\\documentclass[final,5p,times,twocolumn]{elsarticle}/' \
    paper.tex > paper_2col.tex
pdflatex -interaction=nonstopmode paper_2col.tex >/dev/null
pdflatex -interaction=nonstopmode paper_2col.tex >/dev/null

echo "paper.pdf      $(pdfinfo paper.pdf      | awk '/^Pages/{print $2}') pages (preprint, single column)"
echo "paper_2col.pdf $(pdfinfo paper_2col.pdf | awk '/^Pages/{print $2}') pages (Procedia two column)"
