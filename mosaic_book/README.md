# Mystery Mosaics: an A4 colour-by-code book generator

Builds a printable book of "mystery mosaic" pages. Each page is covered in
small outlined dots, and every dot shows a code (1-9, 0, A-J) for one of 20
pens. Colouring the dots reveals a geometric pattern. Pages are white by
default (home printing); `--dark` gives black pages like the original kit.

```
pip install numpy reportlab
python build_book.py                      # all 130 designs -> out/mosaic_book.pdf (~5 MB)
python build_book.py --start 31 --pages 20 # designs 31-50 only
python build_book.py --seed 5             # same designs, new colours/sizes
python build_book.py --blank-backs        # blank page behind every design
python build_book.py --dark               # black pages
```

Book layout: cover, how-to page with colour key, one page per design, and
coloured answer thumbnails at the back.

| File | What it holds |
|---|---|
| `palette.py` | The 20 pens (code, name, hex) and the colour schemes. **Edit the codes here to match your pen caps.** |
| `patterns.py` | 130 designs. Collection 1 (No. 1-30): mandalas, spirals, chevrons, hex flowers, Truchet arcs... Collection 2 (No. 31-130): 14 classics (tumbling blocks, herringbone, basketweave, log cabin, bargello, houndstooth, Ohio star...) and 86 composed designs (14 motifs x 4 grids x 4 shading styles x 4 backgrounds). |
| `build_book.py` | Dot grid, page drawing, cover, key and answer pages. |

Tuning knobs (top of `build_book.py`): `PITCH` (dot spacing, 4.6 mm, about
40 x 62 = 2,480 dots per page), `DOT_D` (dot size), `FONT_SIZE`.

To add a design, write a function `f(X, Y, rng) -> int array` in
`patterns.py` and add it to `GENERATORS`.
