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
