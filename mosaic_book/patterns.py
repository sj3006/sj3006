"""Geometric pattern generators.

Every generator takes dot centre coordinates X, Y (numpy arrays) and a random
generator, and returns an integer array: the "band" each dot belongs to.
Bands are later mapped onto the colours of a scheme (band % len(scheme)).

Coordinates are centred on the page: X runs from -1 (left) to +1 (right) and
Y from about -1.45 (bottom) to +1.45 (top). The dot pitch is about 0.05, so a
band narrower than ~0.12 will look noisy; keep frequencies modest.
"""
import numpy as np

TAU = 2 * np.pi


def _polar(X, Y, cx=0.0, cy=0.0):
    dx, dy = X - cx, Y - cy
    return np.hypot(dx, dy), np.arctan2(dy, dx)


def _rot(X, Y, a):
    c, s = np.cos(a), np.sin(a)
    return c * X - s * Y, s * X + c * Y


# --------------------------------------------------------------------------
# Radial designs
# --------------------------------------------------------------------------

def concentric_rings(X, Y, rng):
    r, _ = _polar(X, Y)
    w = rng.uniform(0.13, 0.2)
    return np.floor(r / w).astype(int)


def mandala(X, Y, rng):
    r, t = _polar(X, Y)
    petals = rng.choice([6, 8, 10, 12])
    amp = rng.uniform(0.12, 0.22)
    w = rng.uniform(0.17, 0.24)
    rr = r + amp * np.abs(np.cos(petals / 2 * t)) * np.minimum(r * 3, 1)
    return np.floor(rr / w).astype(int)


def layered_mandala(X, Y, rng):
    """Rings whose petal count doubles going outwards, with alternating petals."""
    r, t = _polar(X, Y)
    base = rng.choice([4, 5, 6, 8])
    w = rng.uniform(0.2, 0.26)
    ring = np.floor(r / w).astype(int)
    petals = base * (1 + ring // 2)
    local = (r % w) / w
    edge = 0.55 + 0.4 * np.abs(np.cos(petals * t / 2 + ring))
    inside = local < edge
    return np.where(inside, ring * 2, ring * 2 + 1)


def starburst(X, Y, rng):
    r, t = _polar(X, Y)
    rays = rng.choice([12, 16, 20, 24])
    w = rng.uniform(0.25, 0.35)
    sector = np.floor((t + np.pi) / TAU * rays).astype(int)
    ring = np.floor(r / w).astype(int)
    return ring * 2 + ((sector + ring) % 2)


def spiral(X, Y, rng):
    r, t = _polar(X, Y)
    arms = rng.choice([3, 4, 5, 6])
    k = rng.uniform(2.5, 4.0) * rng.choice([-1, 1])
    v = (t / TAU) * arms + r * k
    # modulo `arms` so the colours line up across the +/-pi seam
    return np.floor(v).astype(int) % arms


def dartboard(X, Y, rng):
    r, t = _polar(X, Y)
    sectors = rng.choice([8, 12, 16])
    w = rng.uniform(0.16, 0.22)
    ring = np.floor(r / w).astype(int)
    sec = np.floor((t + np.pi) / TAU * sectors).astype(int)
    return (ring % 3) * 2 + ((ring + sec) % 2)


def rose(X, Y, rng):
    r, t = _polar(X, Y)
    k = rng.choice([3, 4, 5, 6, 7])
    w = rng.uniform(0.18, 0.25)
    rr = r / (0.55 + 0.45 * np.abs(np.cos(k * t)))
    return np.floor(rr / w).astype(int)


def kaleidoscope(X, Y, rng):
    """Fold the plane into mirrored wedges and tile each with triangles."""
    r, t = _polar(X, Y)
    n = rng.choice([6, 8])
    wedge = TAU / n
    tf = np.abs((t % wedge) - wedge / 2)
    u, v = r * np.cos(tf), r * np.sin(tf)
    s = rng.uniform(0.28, 0.36)
    a = np.floor(u / s).astype(int)
    b = np.floor((u * 0.5 + v * 0.866) / s).astype(int)
    c = np.floor((u * 0.5 - v * 0.866) / s).astype(int)
    return (a + b + c) % 3 + 3 * (a % 2)


def superellipse(X, Y, rng):
    p = rng.choice([0.6, 0.8, 3.0, 4.0])
    w = rng.uniform(0.13, 0.18)
    d = (np.abs(X) ** p + np.abs(Y) ** p) ** (1 / p)
    return np.floor(d / w).astype(int)


def octagram(X, Y, rng):
    """Eight-point star rings (a square overlaid with a rotated square)."""
    w = rng.uniform(0.14, 0.2)
    a = np.maximum(np.abs(X), np.abs(Y))
    b = (np.abs(X) + np.abs(Y)) / np.sqrt(2)
    star = np.minimum(a, b) if rng.random() < 0.5 else np.maximum(a, b)
    return np.floor(star / w).astype(int)


def sunrise(X, Y, rng):
    """A half sun at the bottom with rays, concentric arcs on top."""
    cy = -1.45
    r, t = _polar(X, Y, 0, cy)
    rays = rng.choice([14, 18, 22])
    sun = r < 0.6
    sec = np.floor(t / np.pi * rays).astype(int)
    ring = np.floor((r - 0.6) / 0.22).astype(int)
    return np.where(sun, np.floor(r / 0.2).astype(int),
                    3 + ring * 2 + (sec + ring) % 2)


# --------------------------------------------------------------------------
# Square / linear designs
# --------------------------------------------------------------------------

def nested_squares(X, Y, rng):
    a = rng.uniform(0, np.pi / 4) if rng.random() < 0.4 else 0
    U, V = _rot(X, Y, a)
    w = rng.uniform(0.12, 0.17)
    return np.floor(np.maximum(np.abs(U), np.abs(V)) / w).astype(int)


def diamonds(X, Y, rng):
    w = rng.uniform(0.13, 0.18)
    return np.floor((np.abs(X) + np.abs(Y)) / w).astype(int)


def argyle(X, Y, rng):
    s = rng.uniform(0.35, 0.5)
    u = np.floor((X + Y) / s).astype(int)
    v = np.floor((X - Y) / s).astype(int)
    # inner diamond inside each tile
    fu = ((X + Y) / s) % 1 - 0.5
    fv = ((X - Y) / s) % 1 - 0.5
    inner = np.maximum(np.abs(fu), np.abs(fv)) < 0.22
    return np.where(inner, 4 + (u % 2), (u + v) % 2 + 2 * ((u - v) // 2 % 2 == 0))


def chevron(X, Y, rng):
    w = rng.uniform(0.13, 0.18)
    period = rng.uniform(0.35, 0.55)
    zig = np.abs(((X / period) % 1) - 0.5) * period
    return np.floor((Y + zig * 1.6) / w).astype(int)


def waves(X, Y, rng):
    w = rng.uniform(0.13, 0.18)
    f = rng.uniform(2.5, 4.5)
    amp = rng.uniform(0.12, 0.22)
    if rng.random() < 0.5:
        X, Y = Y, X
    return np.floor((Y + amp * np.sin(X * f * np.pi)) / w).astype(int)


def checker_bands(X, Y, rng):
    a = rng.choice([0, np.pi / 4])
    U, V = _rot(X, Y, a)
    s = rng.uniform(0.18, 0.26)
    cu, cv = np.floor(U / s).astype(int), np.floor(V / s).astype(int)
    band = np.floor(np.hypot(X, Y) / 0.45).astype(int)
    return band * 2 + (cu + cv) % 2


def plaid(X, Y, rng):
    s = rng.uniform(0.12, 0.16)
    a = np.floor(X / s).astype(int) % rng.choice([3, 4])
    b = np.floor(Y / s).astype(int) % rng.choice([3, 4])
    return np.where((a == 0) & (b == 0), 0,
                    np.where(a == 0, 1, np.where(b == 0, 2, 3 + (a + b) % 2)))


def zigzag_columns(X, Y, rng):
    w = rng.uniform(0.18, 0.25)
    period = rng.uniform(0.3, 0.45)
    zig = np.abs(((Y / period) % 1) - 0.5) * period
    return np.floor((X + 1 + zig) / w).astype(int)


def pinwheel(X, Y, rng):
    """Square tiles, each split into four triangles like a paper pinwheel."""
    s = rng.uniform(0.4, 0.5)
    gx, gy = np.floor(X / s).astype(int), np.floor(Y / s).astype(int)
    fx, fy = X / s - gx - 0.5, Y / s - gy - 0.5
    quad = np.where(np.abs(fx) > np.abs(fy),
                    np.where(fx > 0, 0, 2), np.where(fy > 0, 1, 3))
    # rotate the colouring per tile so neighbours swirl
    return (quad + gx + gy) % 4 + 4 * (np.hypot(fx, fy) < 0.15)


# --------------------------------------------------------------------------
# Tilings
# --------------------------------------------------------------------------

def _hex_centres(X, Y, s):
    """Nearest centre on a hexagonal lattice of spacing s."""
    h = s * np.sqrt(3) / 2
    row = np.round(Y / h)
    off = (row % 2) * s / 2
    col = np.round((X - off) / s)
    best = None
    for dr in (-1, 0, 1):
        rr = row + dr
        o = (rr % 2) * s / 2
        cc = np.round((X - o) / s)
        cx, cy = cc * s + o, rr * h
        d = np.hypot(X - cx, Y - cy)
        if best is None:
            best = [d, cx, cy, rr, cc]
        else:
            m = d < best[0]
            for i, v in enumerate((d, cx, cy, rr, cc)):
                best[i] = np.where(m, v, best[i])
    return best


def hex_flowers(X, Y, rng):
    s = rng.uniform(0.55, 0.75)
    d, cx, cy, rr, cc = _hex_centres(X, Y, s)
    t = np.arctan2(Y - cy, X - cx)
    petal = d / (s * 0.5) < 0.55 + 0.4 * np.abs(np.cos(3 * t))
    centre = d < s * 0.12
    group = ((rr.astype(int) + 2 * cc.astype(int)) % 3)
    return np.where(centre, 0, np.where(petal, 1 + group, 4))


def honeycomb(X, Y, rng):
    s = rng.uniform(0.3, 0.42)
    d, cx, cy, rr, cc = _hex_centres(X, Y, s)
    ring = np.floor(d / (s * 0.22)).astype(int)
    return ring + ((rr.astype(int) + cc.astype(int)) % 2) * 3


def fish_scales(X, Y, rng):
    """Overlapping semicircular scales; lower rows sit on top."""
    s = rng.uniform(0.32, 0.42)
    h = s / 2
    out = np.full(X.shape, -1)
    base = np.floor(Y / h).astype(int)
    for dr in (2, 1, 0):          # higher rows first, lower rows drawn on top
        row = base + dr
        off = (row % 2) * s / 2
        cx = np.round((X - off) / s) * s + off
        cy = row * h
        d = np.hypot(X - cx, Y - cy)
        inside = d < s / 2
        ring = np.where(d < s * 0.18, 0, np.where(d < s * 0.34, 1, 2))
        val = ring + 3 * ((row // 2) % 2)
        out = np.where(inside, val, out)
    return np.where(out < 0, 2, out)


def circle_grid(X, Y, rng):
    s = rng.uniform(0.38, 0.5)
    gx, gy = np.round(X / s), np.round(Y / s)
    d = np.hypot(X - gx * s, Y - gy * s)
    ring = np.floor(d / (s * 0.18)).astype(int)
    return np.where(ring >= 3, 3 + ((gx + gy) % 2).astype(int), ring)


def flower_of_life(X, Y, rng):
    """Count how many lattice circles cover each dot."""
    s = rng.uniform(0.38, 0.5)
    h = s * np.sqrt(3) / 2
    count = np.zeros_like(X, dtype=int)
    rows = int(np.ceil(1.6 / h)) + 2
    cols = int(np.ceil(1.1 / s)) + 2
    for r in range(-rows, rows + 1):
        for c in range(-cols, cols + 1):
            cx, cy = c * s + (r % 2) * s / 2, r * h
            count += (np.hypot(X - cx, Y - cy) < s).astype(int)
    return count


def truchet(X, Y, rng):
    s = rng.uniform(0.3, 0.4)
    gx, gy = np.floor(X / s).astype(int), np.floor(Y / s).astype(int)
    fx, fy = X / s - gx, Y / s - gy
    flip = rng.integers(0, 2, size=(200, 200))
    f = flip[(gx + 100) % 200, (gy + 100) % 200].astype(bool)
    fx = np.where(f, 1 - fx, fx)
    d1 = np.hypot(fx, fy)
    d2 = np.hypot(1 - fx, 1 - fy)
    d = np.minimum(d1, d2)
    band = np.floor(d / 0.25).astype(int)
    return np.where(band >= 2, 2 + ((gx + gy) % 2), band)


def triangles(X, Y, rng):
    s = rng.uniform(0.28, 0.36)
    h = s * np.sqrt(3) / 2
    row = np.floor(Y / h).astype(int)
    u = X / s + (row % 2) * 0.5
    fy = (Y / h) - row
    col = np.floor(u).astype(int)
    fu = u - col
    up = fy < 1 - np.abs(fu - 0.5) * 2
    band = np.floor(np.hypot(X, Y) / 0.5).astype(int)
    return band * 2 + up.astype(int)


def islamic_stars(X, Y, rng):
    s = rng.uniform(0.45, 0.6)
    gx, gy = np.round(X / s), np.round(Y / s)
    U, V = X - gx * s, Y - gy * s
    a = np.maximum(np.abs(U), np.abs(V))
    b = (np.abs(U) + np.abs(V)) / np.sqrt(2)
    star = np.maximum(a, b) / (s / 2)
    band = np.floor(star / 0.33).astype(int)
    return np.where(band >= 3, 3 + ((gx + gy) % 2).astype(int), band)


def ripples(X, Y, rng):
    """Two pebbles dropped in a pond: rings from two centres, alternating."""
    p1 = np.array([rng.uniform(-0.4, 0.4), rng.uniform(0.3, 0.7)])
    p2 = np.array([rng.uniform(-0.4, 0.4), -rng.uniform(0.3, 0.7)])
    w = rng.uniform(0.17, 0.22)
    r1 = np.floor(np.hypot(X - p1[0], Y - p1[1]) / w).astype(int)
    r2 = np.floor(np.hypot(X - p2[0], Y - p2[1]) / w).astype(int)
    return (r1 % 3) + 3 * ((r1 + r2) % 2)


GENERATORS = [
    ("Mandala Bloom", mandala),
    ("Concentric Rings", concentric_rings),
    ("Chevron Stripes", chevron),
    ("Hex Flower Garden", hex_flowers),
    ("Spiral Galaxy", spiral),
    ("Argyle", argyle),
    ("Eight-Point Stars", islamic_stars),
    ("Starburst", starburst),
    ("Ocean Waves", waves),
    ("Truchet Arcs", truchet),
    ("Layered Mandala", layered_mandala),
    ("Nested Squares", nested_squares),
    ("Fish Scales", fish_scales),
    ("Rose Curve", rose),
    ("Honeycomb", honeycomb),
    ("Kaleidoscope", kaleidoscope),
    ("Diamonds", diamonds),
    ("Flower of Life", flower_of_life),
    ("Dartboard", dartboard),
    ("Plaid", plaid),
    ("Octagram", octagram),
    ("Circle Grid", circle_grid),
    ("Sunrise", sunrise),
    ("Triangle Tiles", triangles),
    ("Zigzag Columns", zigzag_columns),
    ("Pinwheel", pinwheel),
    ("Checker Bands", checker_bands),
    ("Superellipse", superellipse),
    ("Ripples", ripples),
    ("Spiral Twist", spiral),
]


# ==========================================================================
# Collection 2: 100 more designs
#   14 hand-made classics + 86 composed (motif x grid x style x background)
# ==========================================================================

def _cell(X, Y, s, kind):
    """Split the page into cells. Returns local coords u, v (cell units,
    centred, roughly -0.5..0.5) and integer cell indices gx, gy."""
    if kind == "square":
        gx, gy = np.round(X / s), np.round(Y / s)
        return X / s - gx, Y / s - gy, gx.astype(int), gy.astype(int)
    if kind == "brick":
        gy = np.round(Y / s)
        off = (gy % 2) * 0.5
        gx = np.round(X / s - off)
        return X / s - gx - off, Y / s - gy, gx.astype(int), gy.astype(int)
    if kind == "diamond":
        U, V = _rot(X, Y, np.pi / 4)
        gx, gy = np.round(U / s), np.round(V / s)
        u, v = _rot(U / s - gx, V / s - gy, -np.pi / 4)
        return u, v, gx.astype(int), gy.astype(int)
    if kind == "hex":
        d, cx, cy, rr, cc = _hex_centres(X, Y, s)
        return (X - cx) / s, (Y - cy) / s, cc.astype(int), rr.astype(int)
    if kind == "centre":
        z = np.zeros(X.shape, dtype=int)
        return X / s, Y / s, z, z
    raise ValueError(kind)


def _m_star(n):
    def f(u, v):
        r, t = np.hypot(u, v), np.arctan2(v, u) - np.pi / 2
        return r / (0.72 + 0.28 * np.cos(n * t))
    return f


def _m_flower(n):
    def f(u, v):
        r, t = np.hypot(u, v), np.arctan2(v, u)
        return r / (0.62 + 0.38 * np.abs(np.cos(n / 2 * t)))
    return f


def _m_octagram(u, v):
    a = np.maximum(np.abs(u), np.abs(v))
    b = (np.abs(u) + np.abs(v)) / np.sqrt(2)
    return np.minimum(a, b) * 1.15


MOTIFS = {
    "Circles":        lambda u, v: np.hypot(u, v),
    "Squares":        lambda u, v: np.maximum(np.abs(u), np.abs(v)),
    "Diamonds":       lambda u, v: (np.abs(u) + np.abs(v)) * 0.8,
    "Hexagons":       lambda u, v: np.maximum(np.abs(u) * 0.866 + np.abs(v) * 0.5, np.abs(v)),
    "Octagons":       lambda u, v: np.maximum(np.maximum(np.abs(u), np.abs(v)),
                                              (np.abs(u) + np.abs(v)) / np.sqrt(2)),
    "Eight-Point Stars": _m_octagram,
    "Five-Point Stars":  _m_star(5),
    "Six-Point Stars":   _m_star(6),
    "Four-Petal Flowers": _m_flower(4),
    "Six-Petal Flowers":  _m_flower(6),
    "Crosses":        lambda u, v: np.minimum(np.maximum(2.4 * np.abs(u), np.abs(v)),
                                              np.maximum(np.abs(u), 2.4 * np.abs(v))),
    "Lenses":         lambda u, v: np.maximum(np.hypot(u - 0.28, v), np.hypot(u + 0.28, v)) - 0.12,
    "Astroids":       lambda u, v: (np.abs(u) ** 0.6 + np.abs(v) ** 0.6) ** (1 / 0.6) * 0.55,
    "Clovers": lambda u, v: np.minimum.reduce([np.hypot(u - a, v - b)
                                   for a, b in ((.17, 0), (-.17, 0), (0, .17), (0, -.17))]) + 0.08,
}

GRIDS = {"square": "Square Grid", "brick": "Brick Grid",
         "diamond": "Diamond Grid", "hex": "Hex Grid"}
STYLES = ["rings", "outlined", "split", "alternating"]
BACKS = ["checker", "page rings", "diagonal", "plain"]


def make_composed(grid, motif, style, back):
    mfun = MOTIFS[motif]

    def gen(X, Y, rng):
        s = rng.uniform(0.6, 0.78) if grid != "hex" else rng.uniform(0.62, 0.8)
        u, v, gx, gy = _cell(X, Y, s, grid)
        d = mfun(u, v)
        R = 0.44                                  # motif radius in cell units
        w = max(0.13, 0.13 / s)                   # band width >= ~2.5 dots
        inside = d < R
        if style == "rings":
            m = np.floor(d / w).astype(int)
        elif style == "outlined":
            m = np.where(d > R - 0.11 / s, 0, np.where(d < 0.09 / s, 2, 1))
        elif style == "split":
            q = (u * v > 0).astype(int)
            m = np.where(d < 0.09 / s, 2, q)
        else:                                     # alternating cell colours
            m = np.where(d > R - 0.11 / s, 0, 1 + ((gx + gy) % 2))
        if back == "checker":
            b = (gx + gy) % 2
        elif back == "page rings":
            b = np.floor(np.hypot(X, Y) / 0.5).astype(int) % 3
        elif back == "diagonal":
            b = np.floor((X + Y) / 0.45).astype(int) % 2
        else:
            b = np.zeros(X.shape, dtype=int)
        return np.where(inside, m, 10 + b)
    return gen


def make_centred(motif):
    mfun = MOTIFS[motif]

    def gen(X, Y, rng):
        d = mfun(X, Y)
        w = rng.uniform(0.13, 0.17)
        return np.floor(d / w).astype(int)
    return gen


# ---- hand-made classics ---------------------------------------------------

def tumbling_blocks(X, Y, rng):
    s = rng.uniform(0.42, 0.55)
    d, cx, cy, rr, cc = _hex_centres(X, Y, s)
    t = np.arctan2(Y - cy, X - cx)
    return (np.floor(((t - np.pi / 2) % TAU) / (TAU / 3)).astype(int)
            + 3 * (np.floor(np.hypot(X, Y) / 0.7).astype(int) % 2))


def herringbone(X, Y, rng):
    s = rng.uniform(0.25, 0.32)
    w = rng.uniform(0.14, 0.18)
    c = np.floor(X / s).astype(int)
    lx = X - c * s
    sign = np.where(c % 2 == 0, 1, -1)
    idx = np.floor((Y + sign * lx) / w).astype(int)
    return (idx + c) % 3 + 3 * (c % 2)


def basketweave(X, Y, rng):
    s = rng.uniform(0.42, 0.5)
    gx, gy = np.floor(X / s).astype(int), np.floor(Y / s).astype(int)
    fx, fy = X / s - gx, Y / s - gy
    vertical = (gx + gy) % 2 == 0
    strip = np.where(vertical, np.floor(fx * 3), np.floor(fy * 3)).astype(int)
    return strip + 3 * vertical


def log_cabin(X, Y, rng):
    s = rng.uniform(0.8, 1.0)
    u, v, gx, gy = _cell(X, Y, s, "square")
    flip = np.where((gx + gy) % 2 == 0, 1, -1)
    ring = np.floor(np.maximum(np.abs(u), np.abs(v)) / 0.13).astype(int)
    light = (u * flip + v) > 0
    return np.where(ring == 0, 0, ring * 2 + light)


def bargello(X, Y, rng):
    p = rng.uniform(0.45, 0.6)
    h = rng.uniform(0.35, 0.5)
    w = rng.uniform(0.11, 0.14)
    f = np.abs(((X / p) % 1) - 0.5) * 2
    return np.floor((Y + h * (1 - f) ** 2) / w).astype(int)


def houndstooth(X, Y, rng):
    q = rng.uniform(0.1, 0.13)
    i, j = np.floor(X / q).astype(int), np.floor(Y / q).astype(int)
    A, B = (i // 2) % 2, (j // 2) % 2
    tone = np.where(A == B, A, (i + j) % 2)
    return tone + 2 * (np.floor((Y + 1.5) / 0.75).astype(int) % 2)


def quatrefoil(X, Y, rng):
    s = rng.uniform(0.6, 0.75)
    u, v, gx, gy = _cell(X, Y, s, "square")
    a = 0.19
    q = np.minimum.reduce([np.hypot(u - a, v), np.hypot(u + a, v),
                           np.hypot(u, v - a), np.hypot(u, v + a)])
    inside = q < 0.2
    ring = (q < 0.1).astype(int) + (np.hypot(u, v) < 0.12)
    bg = 5 + (np.abs(u) + np.abs(v) > 0.62).astype(int)
    return np.where(inside, ring + 2 * ((gx + gy) % 2), bg)


def rainbow_arches(X, Y, rng):
    s = rng.uniform(0.6, 0.75)
    h = s / 2
    row = np.floor(Y / h).astype(int)
    off = (row % 2) * s / 2
    cx = np.round((X - off) / s) * s + off
    d = np.hypot(X - cx, Y - row * h)
    band = np.floor(d / (s / 2 / 4)).astype(int)
    return np.where(d < s / 2, band, 4)


def sawtooth(X, Y, rng):
    p = rng.uniform(0.3, 0.42)
    w = rng.uniform(0.13, 0.17)
    if rng.random() < 0.5:
        X, Y = Y, X
    return np.floor((Y + (X % p) * 1.2) / w).astype(int)


def interlocking_triangles(X, Y, rng):
    w = rng.uniform(0.2, 0.26)
    up = np.maximum(-Y, Y * 0.5 + np.abs(X) * 0.866)
    dn = np.maximum(Y, -Y * 0.5 + np.abs(X) * 0.866)
    return np.floor(up / w).astype(int) + np.floor(dn / w).astype(int)


def ohio_star(X, Y, rng):
    s = rng.uniform(0.9, 1.05)
    gx, gy = np.floor(X / s + 0.5).astype(int), np.floor(Y / s + 0.5).astype(int)
    fx, fy = X / s + 0.5 - gx, Y / s + 0.5 - gy
    a, b = np.floor(fx * 3).astype(int), np.floor(fy * 3).astype(int)
    lx, ly = fx * 3 - a - 0.5, fy * 3 - b - 0.5
    centre = (a == 1) & (b == 1)
    corner = (a != 1) & (b != 1)
    # which quarter-triangle of the edge square, relative to the block centre
    dirx, diry = 1 - a, 1 - b                      # points towards the centre
    along = np.where(dirx != 0, lx * dirx, ly * diry)
    across = np.where(dirx != 0, ly, lx)
    side = np.abs(across) > np.abs(along)
    tri = np.where(side, 1, np.where(along > 0, 2, 3))
    par = 4 * ((gx + gy) % 2)
    return np.where(centre, 0 + par, np.where(corner, 3, tri + np.where(tri == 3, 0, par)))


def corner_sunburst(X, Y, rng):
    cx, cy = rng.choice([-1, 1]) * 1.0, rng.choice([-1, 1]) * 1.45
    r, t = _polar(X, Y, cx, cy)
    rays = rng.choice([20, 26, 32])
    sec = np.floor(t / np.pi * rays).astype(int)
    ring = np.floor(r / 0.42).astype(int)
    return ring * 2 + (sec + ring) % 2


def polka_gradient(X, Y, rng):
    s = rng.uniform(0.3, 0.36)
    u, v, gx, gy = _cell(X, Y, s, "brick")
    size = 0.12 + 0.3 * (Y + 1.45) / 2.9
    d = np.hypot(u, v)
    return np.where(d < size, 1 + (gy % 3), np.where(d < size + 0.14, 0, 4))


def trellis(X, Y, rng):
    s = rng.uniform(0.38, 0.48)
    a = ((X + Y) / s) % 1
    b = ((X - Y) / s) % 1
    line = (a < 0.24) | (b < 0.24)
    knot = (a < 0.24) & (b < 0.24)
    ring = np.floor(np.hypot(X, Y) / 0.45).astype(int) % 3
    return np.where(knot, 0, np.where(line, 1, 2 + ring))


CLASSICS = [
    ("Tumbling Blocks", tumbling_blocks),
    ("Herringbone", herringbone),
    ("Basketweave", basketweave),
    ("Log Cabin Quilt", log_cabin),
    ("Bargello Flames", bargello),
    ("Houndstooth", houndstooth),
    ("Quatrefoil", quatrefoil),
    ("Rainbow Arches", rainbow_arches),
    ("Sawtooth", sawtooth),
    ("Interlocking Triangles", interlocking_triangles),
    ("Ohio Star Quilt", ohio_star),
    ("Corner Sunburst", corner_sunburst),
    ("Polka Gradient", polka_gradient),
    ("Trellis", trellis),
]


def _composed_list(n_tiled=78):
    import itertools
    # centred big motifs (mandala-like); skip shapes already in collection 1
    centred = [m for m in MOTIFS if m not in
               ("Circles", "Squares", "Diamonds", "Eight-Point Stars", "Astroids", "Hexagons")]
    singular = {"Crosses": "Cross", "Lenses": "Lens"}
    out = [(f"Giant {singular.get(m, m[:-1])}", make_centred(m)) for m in centred]
    # near-duplicates of collection 1
    skip = {("hex", "Hexagons", "rings"), ("square", "Circles", "rings"),
            ("square", "Eight-Point Stars", "rings")}
    combos = [c for c in itertools.product(GRIDS, MOTIFS, STYLES)
              if c not in skip]
    order = np.random.default_rng(2026).permutation(len(combos))
    chosen, seen = [], {}
    for k in order:                               # spread motifs evenly
        g, m, st = combos[k]
        if seen.get(m, 0) >= (n_tiled + len(MOTIFS) - 1) // len(MOTIFS):
            continue
        seen[m] = seen.get(m, 0) + 1
        chosen.append((g, m, st))
        if len(chosen) == n_tiled:
            break
    for i, (g, m, st) in enumerate(chosen):
        back = BACKS[i % len(BACKS)]
        label = {"rings": "Ringed", "outlined": "Outlined",
                 "split": "Split", "alternating": "Alternating"}[st]
        out.append((f"{label} {m} · {GRIDS[g]}", make_composed(g, m, st, back)))
    return out


_composed = _composed_list()
GENERATORS_2 = CLASSICS + _composed[: 100 - len(CLASSICS)]
assert len(GENERATORS_2) == 100, len(GENERATORS_2)
ALL_GENERATORS = GENERATORS + GENERATORS_2
