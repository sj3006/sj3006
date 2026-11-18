"""Build an A4 "mystery mosaic" colour-by-code book as a PDF.

Each page is a black sheet covered in a hex-packed grid of small white dots.
Every dot carries a code (1-9, 0, A-J) naming the pen to colour it with.
Colouring all the dots reveals a geometric pattern.

Usage:
    python build_book.py                      # 30 pages -> out/mosaic_book.pdf
    python build_book.py --pages 10 --seed 7
    python build_book.py --blank-backs        # blank page after each design
"""
import argparse
import os

import numpy as np
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from palette import CODES, HEX, NAMES, PENS, SCHEMES
from patterns import ALL_GENERATORS as GENERATORS

PAGE_W, PAGE_H = A4
MARGIN = 10 * mm
HEADER_H = 20 * mm
FOOTER_H = 7 * mm
PITCH = 4.6 * mm          # distance between neighbouring dot centres
DOT_D = 4.05 * mm         # dot diameter
FONT = "Helvetica-Bold"
FONT_SIZE = 6.3
# Themes: "light" (white page, outlined dots; for home printing) or "dark"
THEMES = {
    "light": dict(page=white, ink=black, dot_line=HexColor("#8c8c8c"),
                  text=HexColor("#3a3a3a"), faint=HexColor("#777777")),
    "dark": dict(page=HexColor("#111111"), ink=white, dot_line=None,
                 text=HexColor("#2a2a2a"), faint=HexColor("#888888")),
}
T = THEMES["light"]
TEXT_GREY = T["text"]


# --------------------------------------------------------------------------
# Dot grid
# --------------------------------------------------------------------------

def dot_grid():
    """Hex-packed dot centres (points) filling the drawing area."""
    left, right = MARGIN, PAGE_W - MARGIN
    bottom, top = MARGIN + FOOTER_H, PAGE_H - MARGIN - HEADER_H
    row_h = PITCH * np.sqrt(3) / 2
    n_rows = int((top - bottom - DOT_D) // row_h) + 1
    n_cols = int((right - left - DOT_D - PITCH / 2) // PITCH) + 1
    used_w = (n_cols - 1) * PITCH + PITCH / 2
    used_h = (n_rows - 1) * row_h
    x0 = (left + right - used_w) / 2
    y0 = (bottom + top - used_h) / 2
    xs, ys = [], []
    for r in range(n_rows):
        off = PITCH / 2 if r % 2 else 0
        for c in range(n_cols):
            xs.append(x0 + off + c * PITCH)
            ys.append(y0 + r * row_h)
    xs, ys = np.array(xs), np.array(ys)
    cx, cy = (left + right) / 2, (bottom + top) / 2
    half_w = used_w / 2 + DOT_D / 2
    # normalised coords: X in [-1, 1], Y scaled by the same factor
    X = (xs - cx) / half_w
    Y = (ys - cy) / half_w
    return xs, ys, X, Y


def make_design(index, seed):
    """Return (title, codes-per-dot) for design number `index`."""
    name, gen = GENERATORS[index % len(GENERATORS)]
    rng = np.random.default_rng(seed * 1000 + index)
    _, _, X, Y = dot_grid()
    bands = gen(X, Y, rng)
    scheme_name = list(SCHEMES)[rng.integers(len(SCHEMES))]
    scheme = list(SCHEMES[scheme_name])
    # Use as many scheme colours as the pattern has distinct bands
    uniq = np.unique(bands)
    n = min(len(scheme), len(uniq))
    start = rng.integers(len(scheme))
    colours = [scheme[(start + i) % len(scheme)] for i in range(n)]
    lookup = {b: colours[i % n] for i, b in enumerate(uniq)}
    codes = np.array([lookup[b] for b in bands])
    return name, scheme_name, codes


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------

def fill_page(c, colour=None):
    c.setFillColor(colour if colour is not None else T["page"])
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)


def draw_test_strip(c, y, size=6.2 * mm, gap=1.9 * mm):
    """Row of 20 labelled circles to try each pen on (like the kit's strip)."""
    total = len(CODES) * size + (len(CODES) - 1) * gap
    x = (PAGE_W - total) / 2
    for code in CODES:
        _dot_style(c, 0.6)
        c.circle(x + size / 2, y, size / 2, stroke=1 if T["dot_line"] else 0, fill=1)
        c.setFillColor(TEXT_GREY)
        c.setFont(FONT, 7.5)
        c.drawCentredString(x + size / 2, y - 2.6, code)
        x += size + gap


def _dot_style(c, width=0.45):
    c.setFillColor(white)
    if T["dot_line"] is not None:
        c.setStrokeColor(T["dot_line"])
        c.setLineWidth(width)


def draw_mosaic_page(c, number, codes, used):
    fill_page(c)
    # header
    c.setFillColor(T["ink"])
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, PAGE_H - MARGIN - 4 * mm, f"MYSTERY MOSAIC  No. {number:03d}")
    c.setFont("Helvetica", 7.5)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 4 * mm,
                      "Pens needed: " + "  ".join(used))
    draw_test_strip(c, PAGE_H - MARGIN - 13 * mm)
    # dots
    xs, ys, _, _ = dot_grid()
    # one reusable dot drawing, stamped at every position (keeps the PDF small)
    if not getattr(c, "_dot_form", False):
        r = DOT_D / 2 + 1
        c.beginForm("dot", lowerx=-r, lowery=-r, upperx=r, uppery=r)
        _dot_style(c)
        c.circle(0, 0, DOT_D / 2, stroke=1 if T["dot_line"] is not None else 0, fill=1)
        c.endForm()
        c._dot_form = True
    for x, y in zip(xs, ys):
        c.saveState()
        c.translate(round(x, 2), round(y, 2))
        c.doForm("dot")
        c.restoreState()
    c.setFillColor(TEXT_GREY)
    c.setFont(FONT, FONT_SIZE)
    half = {k: c.stringWidth(k, FONT, FONT_SIZE) / 2 for k in CODES}
    t = c.beginText()
    t.setFont(FONT, FONT_SIZE)
    t.setFillColor(TEXT_GREY)
    for x, y, code in zip(xs, ys, codes):
        t.setTextOrigin(round(x - half[code], 2), round(y - FONT_SIZE * 0.35, 2))
        t.textOut(code)
    c.drawText(t)
    # footer
    c.setFillColor(T["faint"])
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_W / 2, MARGIN, f"{number}")
    c.showPage()


def draw_coloured(c, codes, ox, oy, scale):
    """Draw a finished (coloured) mosaic, scaled, with origin offset."""
    xs, ys, _, _ = dot_grid()
    x_min, y_min = xs.min() - DOT_D, ys.min() - DOT_D
    w = xs.max() - x_min + DOT_D
    h = ys.max() - y_min + DOT_D
    c.setFillColor(T["page"])
    c.setStrokeColor(HexColor("#bbbbbb"))
    c.setLineWidth(0.5)
    c.rect(ox, oy, w * scale, h * scale, stroke=1, fill=1)
    if not getattr(c, "_colour_forms", False):     # one unit dot per colour
        for k in CODES:
            c.beginForm("col_" + k, lowerx=-1.1, lowery=-1.1, upperx=1.1, uppery=1.1)
            c.setFillColor(HexColor(HEX[k]))
            c.circle(0, 0, 1, stroke=0, fill=1)
            c.endForm()
        c._colour_forms = True
    c.saveState()
    c.translate(ox, oy)
    c.scale(scale, scale)
    r = DOT_D / 2
    for x, y, code in zip(xs, ys, codes):
        c.saveState()
        c.transform(r, 0, 0, r, round(x - x_min, 1), round(y - y_min, 1))
        c.doForm("col_" + code)
        c.restoreState()
    c.restoreState()
    return w * scale, h * scale


def draw_cover(c, codes):
    fill_page(c)
    xs, ys, _, _ = dot_grid()
    scale = 0.72
    w = (xs.max() - xs.min() + 2 * DOT_D) * scale
    draw_coloured(c, codes, (PAGE_W - w) / 2, 32 * mm, scale)
    c.setFillColor(T["ink"])
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 35 * mm, "MYSTERY MOSAICS")
    c.setFont("Helvetica", 13)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 45 * mm,
                        "Geometric patterns  ·  colour by code  ·  20 pens")
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(T["faint"])
    c.drawCentredString(PAGE_W / 2, 18 * mm, "Slow art. Calm mind.")
    c.showPage()


def draw_key_page(c):
    fill_page(c, white)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, PAGE_H - 30 * mm, "How to colour")
    c.setFont("Helvetica", 11)
    lines = [
        "Every white dot shows a code. Colour the dot with the pen that has that code.",
        "You can't tell what the picture is until enough dots are filled in. That's the mystery.",
        "Use the row of circles at the top of each page to test your pens first.",
        "Each page lists the pens it needs. The finished designs are at the back of the book.",
    ]
    for i, t in enumerate(lines):
        c.drawString(20 * mm, PAGE_H - (42 + i * 7) * mm, t)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, PAGE_H - 82 * mm, "Colour key")
    col_x = [20 * mm, 110 * mm]
    for i, (code, name, hexv) in enumerate(PENS):
        x = col_x[i // 10]
        y = PAGE_H - (95 + (i % 10) * 13) * mm
        c.setFillColor(HexColor(hexv))
        c.circle(x + 5 * mm, y + 2 * mm, 4.5 * mm, stroke=0, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 14 * mm, y, code)
        c.setFont("Helvetica", 12)
        c.drawString(x + 24 * mm, y, name)
    c.showPage()


def draw_answer_pages(c, designs):
    xs, ys, _, _ = dot_grid()
    scale = 0.205
    w = (xs.max() - xs.min() + 2 * DOT_D) * scale
    h = (ys.max() - ys.min() + 2 * DOT_D) * scale
    per_page = 16
    for p in range(0, len(designs), per_page):
        fill_page(c, white)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(MARGIN + 4 * mm, PAGE_H - 18 * mm, "Finished designs")
        gap_x = (PAGE_W - 4 * w) / 5
        for i, (num, name, codes) in enumerate(designs[p:p + per_page]):
            col, row = i % 4, i // 4
            ox = gap_x + col * (w + gap_x)
            oy = PAGE_H - 24 * mm - (row + 1) * (h + 10 * mm)
            draw_coloured(c, codes, ox, oy, scale)
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(ox + w / 2, oy - 4 * mm, f"No. {num:03d}")
            c.setFont("Helvetica", 6)
            c.drawCentredString(ox + w / 2, oy - 7 * mm, name)
        c.showPage()


def blank(c):
    fill_page(c, white)
    c.showPage()


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=len(GENERATORS),
                    help=f"number of designs (default: all {len(GENERATORS)})")
    ap.add_argument("--start", type=int, default=1, help="first design number")
    ap.add_argument("--dark", action="store_true", help="black pages (like the kit)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="out/mosaic_book.pdf")
    ap.add_argument("--blank-backs", action="store_true",
                    help="insert a blank page after each design (single-sided use)")
    args = ap.parse_args()

    global T, TEXT_GREY
    T = THEMES["dark" if args.dark else "light"]
    TEXT_GREY = T["text"]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    designs = []
    for i in range(args.start - 1, min(args.start - 1 + args.pages, len(GENERATORS))):
        name, scheme, codes = make_design(i, args.seed)
        designs.append((i + 1, name, codes))

    c = canvas.Canvas(args.out, pagesize=A4, pageCompression=1)
    c.setTitle("Mystery Mosaics")
    draw_cover(c, designs[0][2])
    draw_key_page(c)
    for num, name, codes in designs:
        used = [k for k in CODES if k in set(codes)]
        draw_mosaic_page(c, num, codes, used)
        if args.blank_backs:
            blank(c)
    draw_answer_pages(c, designs)
    c.save()
    n_dots = len(designs[0][2])
    print(f"Wrote {args.out}: {len(designs)} designs, {n_dots} dots per page")


if __name__ == "__main__":
    main()
