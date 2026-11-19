# The forward chain: inputs to temperature field to pool size to sensor readings

Reference document. Everything here is traceable to `src/eagar_tsai.py` and
`src/sensors.py`. All numbers are the healthy nominal condition: 285 W,
0.960 m/s, spot sigma 16.75 um, IN718.

There is **no reverse run anywhere in this project.** Every computation goes
forwards. The inverse question is asked by comparing catalogue entries, never by
running the model backwards.

    fault  ->  six model inputs  ->  temperature field  ->  pool size  ->  three sensor numbers
              (see explainer 01)        stage A              stage B           stage C

---

## Stage A: inputs to a temperature field

### The model

**Eagar-Tsai.** A Gaussian laser spot moving at constant speed over a
semi-infinite solid, solved analytically by convolving a moving point source with
a Gaussian in space and integrating over time.

    dT(x,y,z) = A*P / (rho*cp*pi^1.5*sqrt(alpha))
                * INTEGRAL from 0 to inf of
                    exp[ -((x + v*t')^2 + y^2) / (2*(sigma^2 + 2*alpha*t'))
                         - z^2 / (4*alpha*t') ]
                    / ( (sigma^2 + 2*alpha*t') * sqrt(t') )  dt'

Read it as: *heat deposited t' seconds ago has spread into a blob. Add up all the
blobs.*

| term | meaning |
|---|---|
| `t'` | how long ago that parcel of heat was deposited |
| `sigma^2 + 2*alpha*t'` | the blob has widened sideways by diffusion since then |
| `x + v*t'` | the beam has moved on since then |
| `z^2 / (4*alpha*t')` | how far the heat has reached downwards |
| `alpha = k/(rho*cp)` | thermal diffusivity: how fast heat spreads |

### Our numbers

    alpha     = 35.0 / (8190 * 450)                           = 9.497e-6 m^2/s
    prefactor = 0.384 * 285 / (8190 * 450 * 5.568 * 3.0817e-3)
              = 1.7305e-3  K*m^2

Evaluated at four points:

    T(beam centre, surface)  = 23649 K     <- unphysical, see below
    T(60 um to the side)     =  1201 K
    T(60 um down)            =   702 K
    T(200 um behind)         =  2706 K

### Numerics

The integral has no closed form. It is evaluated with 200-point Gauss-Legendre
quadrature under the substitution `t' = u^2`, which removes the `1/sqrt(t')`
singularity at the origin. Sufficiency is checked with `quadrature_convergence`
rather than assumed.

**An implementation note that matters.** Broadcasting the quadrature nodes as an
extra array axis is tidier but costs O(grid x n_quad) memory - a 161x161x80 grid
with 400 nodes is 6.6 GB and was killing the process. Accumulating node by node
is O(grid), and turned out 65x faster as well (2.58 s to 0.04 s).

### The 23649 K peak is nonsense, and we never use it

Steel boils near 3190 K. A pure conduction model has no vaporisation, no latent
heat and no convective loss, so its peak temperature is meaningless and diverges
at the source.

This is fine, because **nothing in the study uses the peak.** We use only the
liquidus isotherm, which sits far from the singularity and is well behaved. The
sensor models additionally cap temperature at the boiling point before computing
any radiance.

### The keyhole correction

Pure conduction under-predicts melt depth once the pool enters keyholing, where a
vapour depression forms and the beam drills in. Honarmandi et al. (2021) give an
empirical criterion and an analytic patch, both adopted here.

Criterion: keyholing when `depth >= width / 1.5`, applied to the *measured*
dimensions so that the test does not depend on the model being corrected.

Gladush-Smurov depth (Honarmandi Eq. 5):

    d_k = mu*P / (2*pi*kappa*T_b) * ln[ (sigma + alpha/v) / sigma ]

Corrected depth = conduction depth + C * d_k, with C fitted at Gate 1 alongside
absorptivity, conductivity and heat capacity against seven published Weaver
single-track measurements. Result: 11.7% error on width, 13.0% on depth.

---

## Stage B: temperature field to pool size

The melt pool is wherever `T > liquidus (1609 K)`. So walk outward from the
centre and find where the temperature crosses that level.

### The arithmetic, sideways (width)

    y = 45 um  ->  T = 3045.71 K
    y = 50 um  ->  T = 2182.21 K    <- above liquidus
    y = 55 um  ->  T = 1596.46 K    <- below liquidus
    y = 60 um  ->  T = 1200.84 K

Crossing lies between 50 and 55 um. Interpolate linearly:

    fraction = (2182.21 - 1609.0) / (2182.21 - 1596.46) = 0.9786
    edge     = 50 + 0.9786 * 5                          = 54.893 um
    WIDTH    = 2 * 54.893                               = 109.79 um

(That walk used a coarse 25-point grid for legibility. The production grid gives
115.12 um. Same arithmetic, finer steps.)

### Why interpolate rather than count cells

The entire paper lives in small differences between sensor readings. Snapping the
isotherm to the nearest grid point quantises the answer in roughly 5 um jumps,
and that quantisation appears in the Jacobian as signal that is not physics.
Interpolating removes it.

This was a real bug, and it had two further instances found later: melt pool
*length* was still being snapped while width and depth were interpolated (about
1.6% quantisation, fixed with a two-sided span function), and melt *depth* was
being read at the hottest surface point rather than maximised along the
centreline, which under-read depth by 50.8 vs 34.4 um.

### Depth and length

Same procedure. Depth: walk downwards, and maximise the crossing over x along the
y = 0 midplane. Length: walk fore and aft, two-sided.

Healthy pool: **115.12 um wide, 69.70 um deep, 415.47 um long.**

---

## Stage C: field and pool to three sensor numbers

Grid: 121 x 121 over a 1.5 mm field of view, cell area 3.125e-10 m^2.
Temperature capped at the boiling point of 3190 K before any radiance is
computed - 50 cells were above it.

### Photodiode

**Planck's law** gives how brightly a surface at temperature T glows at
wavelength lambda:

    B(lambda, T) = 2*h*c^2 / lambda^5 / ( exp(h*c / (lambda*kB*T)) - 1 )

    B(850 nm, 1609 K) = 7.245e+09 W/(m^2 sr m)
    B(850 nm, 2500 K) = 3.082e+11       <- 42x brighter for 55% more temperature
    B(850 nm, 3190 K) = 1.338e+12

That steepness is why a photodiode is sensitive at all.

Procedure: integrate B over the detector band (700-1000 nm, 12 wavelength
samples), sum over the grid, multiply by cell area.

    photodiode = 8.383867e-03   (instrument-arbitrary units)

Gain and emissivity are unknown but constant, and they scale the signal without
rotating its direction, so they do not affect any angle.

### Camera

    area = pi/4 * width * length
         = pi/4 * 115.12 um * 415.47 um
         = 3.756490e-08 m^2

An ellipse computed from the *interpolated* dimensions, not by counting cells
above the liquidus - same quantisation argument as stage B, worth about 0.3%.

### Pyrometer

Measure brightness at **two** wavelengths and take the ratio. The ratio depends
on temperature but not on emissivity, which cancels. That is why two-colour
pyrometry is used in practice.

    sum of B(750 nm) over the view = 8.1976e+13
    sum of B(950 nm) over the view = 9.5306e+13
    ratio R                        = 0.860133

Invert with the Wien approximation:

    T = (h*c/kB) * (1/lambda2 - 1/lambda1) / [ ln R + 5*ln(lambda1/lambda2) ]

    h*c/kB                   = 1.438777e-02 m*K
    (1/950n - 1/750n)        = -2.8070e+05 1/m
    ln R                     = -0.150668
    5*ln(lambda1/lambda2)    = -1.181944
    denominator              = -1.332612
    pyrometer                = 3030.64 K

**Why ratio two integrated band powers rather than read the hottest pixel.**
Taking the ratio at the single hottest pixel returned exactly the boiling point
for every condition, because the cap saturates there. The result was a dead row
in the Jacobian - 0.000% change for all five faults, carrying no information at
all. That is an artefact of the cap, not physics. Ratioing band powers integrated
over the field of view is both informative and closer to what a real coaxial
pyrometer does.

---

## The complete chain, one worked example

Healthy versus a 5% power deficit versus a gas plume of optical depth 0.05:

| | power | absorptivity | pool W x D x L (um) | photodiode | camera | pyrometer |
|---|---|---|---|---|---|---|
| healthy | 285.00 | 0.3840 | 115.12 x 69.70 x 415.47 | 8.384e-3 | 3.756e-8 | 3030.64 |
| power -5% | 270.75 | 0.3840 | 113.61 x 67.70 x 395.20 | 7.763e-3 | 3.526e-8 | 3026.10 |
| gas 0.05 | 285.00 | 0.3653 | 113.64 x 67.75 x 395.69 | 7.777e-3 | 3.532e-8 | 3026.12 |

As percentage change from healthy:

| fault | photodiode | camera | pyrometer |
|---|---|---|---|
| power -5% | **-7.401%** | **-6.130%** | **-0.150%** |
| gas 0.05 | **-7.233%** | **-5.983%** | **-0.149%** |
| layer 5% thinner | -2.772% | -2.248% | -0.035% |

A weak laser and a degraded gas atmosphere produce the same three numbers to
within a rounding error. **That is the problem the paper exists to analyse, and
it is visible in raw readings before any mathematics is applied.**
