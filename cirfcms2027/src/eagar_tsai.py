"""
Eagar-Tsai thermal model for a moving Gaussian heat source on a semi-infinite
substrate. Tier-0 of the LPBF diagnosability analysis: every sensor model and
every fault signature derives from the temperature field this produces.

Reference
---------
Eagar, T.W. and Tsai, N.-S. (1983), "Temperature fields produced by traveling
distributed heat sources", Welding Journal 62(12), 346-355.

Solution
--------
Superposition of instantaneous point sources, doubled for the adiabatic free
surface (image source), with the in-plane Gaussian of the beam convolved into
the diffusion kernel so that the in-plane variance becomes (sigma^2 + 2*alpha*t').

    dT(x,y,z) = A*P / (rho*cp * 2*pi^(3/2)*sqrt(alpha))
                * integral_0^inf  exp(-((x + v*t')^2 + y^2) / (2*(sigma^2 + 2*alpha*t'))
                                      - z^2 / (4*alpha*t'))
                                 / ((sigma^2 + 2*alpha*t') * sqrt(t'))  dt'

Coordinates are in the beam frame: the beam sits at the origin and travels in
+x, so material behind the beam is at negative x. z increases into the solid.

The substitution t' = u^2 removes the 1/sqrt(t') singularity at the origin and
gives an integrand that fixed-order Gauss-Legendre handles cleanly:

    dT = A*P / (rho*cp * pi^(3/2)*sqrt(alpha))
         * integral_0^umax exp(...) / (sigma^2 + 2*alpha*u^2)  du

Units are SI throughout: W, m, s, K. Convert at the boundary, never inside.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "Material",
    "Beam",
    "IN718",
    "sigma_from_spot_diameter",
    "temperature_field",
    "melt_pool_dimensions",
    "quadrature_convergence",
]


@dataclass(frozen=True)
class Material:
    """Constant-property material model.

    Eagar-Tsai assumes temperature-independent properties. Real IN718 varies
    strongly between room temperature and the melt pool, so these are *effective*
    values chosen to represent the near-melt regime. The mismatch is absorbed by
    the fitted absorptivity, which is why absorptivity is a calibration target and
    not a physical constant here.
    """

    name: str
    rho: float          # density, kg/m^3
    cp: float           # specific heat capacity, J/(kg*K)
    k: float            # thermal conductivity, W/(m*K)
    t_solidus: float    # K
    t_liquidus: float   # K
    t_ambient: float    # K, baseplate / preheat temperature
    t_vaporisation: float  # K, reference only - the model does not cap at it

    @property
    def alpha(self) -> float:
        """Thermal diffusivity, m^2/s."""
        return self.k / (self.rho * self.cp)


# ---------------------------------------------------------------------------
# PROVISIONAL PROPERTY VALUES - verify against a citable source before Gate 1.
#
# These are literature-typical effective values for IN718 in the near-melt
# regime. They are good enough to get the model running and to check that
# parameter sweeps behave correctly, but the calibration in Gate 1 must cite a
# real source for each number. Flagged in 05-risks-and-decisions.md.
# ---------------------------------------------------------------------------
IN718 = Material(
    name="IN718 (provisional effective properties)",
    rho=8190.0,
    cp=650.0,
    k=30.0,
    t_solidus=1533.0,
    t_liquidus=1609.0,
    t_ambient=293.0,
    t_vaporisation=3190.0,
)


@dataclass(frozen=True)
class Beam:
    """Laser parameters.

    `sigma` is the standard deviation of the Gaussian *intensity* distribution,
    so the surface flux is q(r) = A*P/(2*pi*sigma^2) * exp(-r^2/(2*sigma^2)).
    Use `sigma_from_spot_diameter` rather than guessing - a factor-of-two error
    in the spot convention will quietly wreck the calibration.
    """

    power: float          # W, nominal laser power
    speed: float          # m/s, scan speed
    sigma: float          # m, Gaussian intensity std dev
    absorptivity: float   # dimensionless, fitted at Gate 1


def sigma_from_spot_diameter(diameter: float) -> float:
    """Gaussian std dev from a quoted spot diameter.

    For a Gaussian beam the 1/e^2 diameter and the D4sigma diameter coincide, and
    both give sigma = D/4. Machine datasheets usually quote one of these two, so
    this single conversion covers the common cases. If a datasheet quotes a
    full-width-half-maximum instead, use sigma = FWHM / 2.3548.
    """
    return diameter / 4.0


def temperature_field(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    beam: Beam,
    material: Material,
    n_quad: int = 200,
    u_max: float | None = None,
) -> np.ndarray:
    """Quasi-steady temperature field in the beam frame.

    Parameters
    ----------
    x, y, z
        Broadcastable coordinate arrays, metres. Beam at the origin travelling
        in +x; z >= 0 into the solid.
    n_quad
        Gauss-Legendre node count. Check sufficiency with
        `quadrature_convergence` rather than trusting the default.
    u_max
        Upper limit of the substituted integration variable (u^2 = t'). Defaults
        to a value covering both the diffusion and advection timescales of the
        requested domain.

    Returns
    -------
    Temperature in K, broadcast to the shape of x+y+z.
    """
    alpha = material.alpha
    x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))

    if u_max is None:
        # Cover whichever is slower: diffusing across the domain, or the beam
        # traversing it. t_max in time units, then u_max = sqrt(t_max).
        span = max(
            float(np.ptp(x)) if x.size > 1 else 0.0,
            float(np.ptp(y)) if y.size > 1 else 0.0,
            float(np.ptp(z)) if z.size > 1 else 0.0,
            4.0 * beam.sigma,
        )
        t_diff = span**2 / alpha
        t_adv = span / beam.speed if beam.speed > 0 else t_diff
        u_max = float(np.sqrt(10.0 * max(t_diff, t_adv)))

    nodes, weights = np.polynomial.legendre.leggauss(n_quad)
    # map [-1, 1] -> [0, u_max]
    u = 0.5 * u_max * (nodes + 1.0)
    w = 0.5 * u_max * weights

    # Accumulate over quadrature nodes rather than broadcasting them as an extra
    # axis. Broadcasting is tidier but costs O(grid * n_quad) memory, which OOMs
    # on a 3D grid at useful resolution; this is O(grid) and no slower in
    # practice because each node is still a single vectorised pass.
    acc = np.zeros(x.shape, dtype=float)
    x2 = x
    y2 = y * y
    z2 = z * z
    with np.errstate(divide="ignore", invalid="ignore", over="ignore", under="ignore"):
        for u_i, w_i in zip(u, w):
            t_prime = u_i * u_i
            in_plane_var = beam.sigma**2 + 2.0 * alpha * t_prime
            x_shift = x2 + beam.speed * t_prime
            exponent = -(x_shift * x_shift + y2) / (2.0 * in_plane_var)
            if t_prime > 0.0:
                exponent = exponent - z2 / (4.0 * alpha * t_prime)
            else:
                exponent = np.where(z2 == 0.0, exponent, -np.inf)
            acc += w_i * np.exp(exponent) / in_plane_var

    acc = np.nan_to_num(acc, nan=0.0, posinf=0.0, neginf=0.0)

    prefactor = (
        beam.absorptivity
        * beam.power
        / (material.rho * material.cp * np.pi**1.5 * np.sqrt(alpha))
    )
    return material.t_ambient + prefactor * acc


def _crossing(coord: np.ndarray, values: np.ndarray, level: float) -> float:
    """Last coordinate at which `values` crosses `level`, linearly interpolated.

    Grid-snapped isotherm extents quantise the melt pool to one cell, which is
    far too coarse for calibration or for any correlation claim. Interpolating
    the crossing recovers sub-grid resolution at no cost.
    """
    above = values >= level
    if not above.any():
        return 0.0
    i = int(np.where(above)[0].max())
    if i + 1 >= len(values):
        return float(coord[i])
    v0, v1 = values[i], values[i + 1]
    if v0 == v1:
        return float(coord[i])
    frac = (v0 - level) / (v0 - v1)
    return float(coord[i] + frac * (coord[i + 1] - coord[i]))


def melt_pool_dimensions(
    beam: Beam,
    material: Material,
    n_quad: int = 100,
    grid_half_width: float | None = None,
    n_points: int = 121,
) -> dict[str, float]:
    """Melt pool width, depth and length from the liquidus isotherm.

    Extents are linearly interpolated across the isotherm crossing rather than
    snapped to the grid, so they are not quantised to the cell size. All lengths
    in metres.
    """
    if grid_half_width is None:
        grid_half_width = 12.0 * beam.sigma

    x = np.linspace(-3.0 * grid_half_width, grid_half_width, n_points)
    y = np.linspace(0.0, grid_half_width, n_points)
    z = np.linspace(0.0, grid_half_width, n_points)

    # Surface plane (z = 0) for width and length.
    xx, yy = np.meshgrid(x, y, indexing="ij")
    surf = temperature_field(xx, yy, np.zeros_like(xx), beam, material, n_quad=n_quad)
    molten_surf = surf >= material.t_liquidus

    if not molten_surf.any():
        return dict(width=0.0, depth=0.0, length=0.0,
                    peak_temperature=float(surf.max()), grid_spacing=float(x[1] - x[0]))

    ix = int(np.unravel_index(surf.argmax(), surf.shape)[0])
    width = 2.0 * _crossing(y, surf[ix, :], material.t_liquidus)

    xi = np.where(molten_surf.any(axis=1))[0]
    length = float(x[xi].max() - x[xi].min())

    # Depth: maximum over x of the interpolated z-crossing on the y = 0 plane.
    # The deepest point sits slightly behind the hottest surface point, so taking
    # the crossing only at argmax(T_surface) underestimates it.
    xzx, xzz = np.meshgrid(x, z, indexing="ij")
    midplane = temperature_field(xzx, np.zeros_like(xzx), xzz, beam, material, n_quad=n_quad)
    depth = max(_crossing(z, midplane[i, :], material.t_liquidus) for i in range(len(x)))

    return dict(
        width=width,
        depth=depth,
        length=length,
        peak_temperature=float(surf.max()),
        grid_spacing=float(x[1] - x[0]),
    )


def quadrature_convergence(
    beam: Beam, material: Material, counts: tuple[int, ...] = (50, 100, 200, 400, 800)
) -> list[tuple[int, float]]:
    """Peak surface temperature versus node count, for choosing `n_quad`.

    Run this once per parameter regime. If the last two entries differ by more
    than a fraction of a kelvin, raise the node count.
    """
    out = []
    for n in counts:
        t = temperature_field(
            np.array([0.0]), np.array([0.0]), np.array([0.0]), beam, material, n_quad=n
        )
        out.append((n, float(t.ravel()[0])))
    return out
