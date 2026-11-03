# Overleaf bundle

Upload `paper.tex` to Overleaf. That is the whole project — one file, no
figures, no separate bibliography, no custom class. Compile with **pdfLaTeX**.

`elsarticle` ships with Overleaf's TeX Live, so nothing needs installing.

## The two layouts

The first line selects the layout:

```latex
\documentclass[final,5p,times,twocolumn]{elsarticle}   % submission layout (current)
\documentclass[preprint,times]{elsarticle}             % wide single column, easier to mark up
```

Page counts differ because a column holds less, not because the text differs.
**The page limit applies to the two-column layout.**

## Before submitting

Placeholders marked in the source:

- author block, affiliation and corresponding-author details
- `\journal{}` and the conference line Procedia requires
- acknowledgements / funding (marked `TODO`)

## Keeping this in sync

`paper.tex` here is generated from `../paper/paper.tex` with only the
documentclass line changed. If you edit here and want the change to survive,
copy it back — or just tell me and I will.
