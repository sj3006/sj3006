# Literature landscape

Result of roughly twenty novelty searches run during planning. Recorded so the
work is not repeated, and because knowing what is occupied is as useful as
knowing what is not.

## What is occupied — do not propose these

**PINN / neural operator surrogates for LPBF melt pools and thermal fields.**
Saturated 2023–2026. Multi-track, Marangoni, gas dynamics, cooling rates all
covered. Real-time distortion via physics-informed neural operator appeared
Nov 2025. Geometry-agnostic thermal GNNs go back to 2021.

**Dimensionless groups as ML features for melt pool prediction.** Multiple
papers plus a US patent (11,491,729, "Non-dimensionalization of variables to
enhance machine learning in additive manufacturing processes"). A Buckingham-Pi
melt pool analysis appeared in *Additive Manufacturing Letters* 2026, and
simulation-based multi-material ML with dimensionless ratios and extrapolation to
new materials appeared March 2026. This killed a candidate project outright.

**Multi-class defect classification from raw signals in LPBF.** Heavily worked:
CNNs on photodiode traces, acoustic emission classifiers, high-speed imaging,
transfer learning across materials (316L to CuSn8), contrastive fusion,
bi-stream cross-mode networks, domain adaptation. Accuracies to 99.9% reported for
process parameter fluctuation identification.

**Multi-sensor fusion for LPBF monitoring.** Feature-level and deep fusion both
well developed. The field already states as consensus that single sensors are
insufficient — which is the qualitative conclusion our matrix formalises.

**Physics-based overheating constraints replacing geometric overhang rules.**
Done in the topology optimisation community.

**Scan path / sequence optimisation.** Reinforcement learning and sensitivity
with sequential inherent strain both published.

**Multi-laser load balancing.** *Additive Manufacturing* 2023 plus a patent
(US 12,257,627).

**Binder jet sintering distortion.** Viscoplastic models with gravity and setter
friction, anisotropic shrinkage models, green density effects on distortion, and a
Nov 2025 review of binder jet modelling approaches.

**Powder spreading.** DEM with JKR cohesion is standard; DEM-FEM and CFD-DEM gas
coupling both exist.

## What is not occupied

**Model-based diagnosability analysis applied to AM.** Searches on
"diagnosability", "fault isolability" and "structural diagnosability" combined
with additive manufacturing returned nothing formal. The method itself is mature
in control — anti-lock braking, turbo-shaft engines, sensor networks, and
discrete-event systems diagnosability has explicit manufacturing applications.
This is a domain transfer, which is a legitimate CIRP conference contribution.

**Lattice Boltzmann for shielding gas and spatter transport.** Every published
treatment uses finite volume plus DEM or DPM. LBM is used extensively for LPBF
melt pools (Körner lineage, KiSSAM) but not for the chamber gas problem, where its
strengths actually apply. Parked, not pursued — the risk was toolchain setup.

**Toolpath-resolved lack-of-fusion prediction.** Components all exist; nobody has
assembled them at individual scan-vector resolution with contour/hatch/downskin
parameter sets and scanner dynamics. Parked.

## Datasets investigated

**RAISE-LPBF** — Blanc, Ahar, De Grave, *Additive Manufacturing Letters*
7:100161, 2023. 316L, on-axis video at 20 kHz, power and speed independently
sampled per scan line. Repo: `github.com/Flanders-Make-vzw/RAISE_LPBF_Laser_benchmark`
(note: loader file is `datasets.py`, not `dataset.py` as the README says).
Licence CC BY-NC 4.0. **Hosting at makebench.eu was unreachable from two
independent networks during planning.** A possible mirror exists at
`huggingface.co/datasets/ppak10/RAISE-LPBF-Part-X16`, unverified.

HDF5 structure, derived from the loader source:

```
<file>.hdf5
└── <object>                 # top-level groups: objects / parts
    └── <layer>              # second level: layers
        ├── frame            # (N, H, W) uint8 frames
        ├── scan_line_index  # (N,) scan line each frame belongs to
        └── laser_params     # (n_scan_lines, 2) -> [speed, power]
```

Note the column order: **speed first, power second.** Label normalisation
defaults are `speed_mean=900`, `power_mean=215`, which indicates the parameter
regime.

**MeltpoolNet** — Akbari et al., *Additive Manufacturing* 55:102817, 2022.
`github.com/BaratiLab/MeltpoolNet`. Two CSVs, verified by direct inspection:
1796 regression rows, 1688 of them PBF; 633 SS316L, 368 Ti-6Al-4V, 140 IN718.
Power, velocity, beam diameter, conductivity, density, Cp and melting temperature
all well populated — everything needed for dimensionless groups. Their own feature
set uses raw values plus one-hot material encoding; zero occurrences of
"enthalpy", "dimensionless" or "Peclet" in their notebook. The gap in *their*
paper is real, but the idea is occupied elsewhere (see above), so this was
dropped. **Unit inconsistency warning:** beam diameter spans 0.62 to 700 and
velocity 0.6 to 8000, mixing units within columns.

**Empa acoustic emission dataset** — `zenodo.org/records/10449883`, Jan 2024.
Covers lack-of-fusion, conduction and keyhole regimes. Labelled by regime rather
than continuous parameters, so weaker for parameter-space geometry work.

## Method of decision

The plan settled on diagnosability not because it is the most novel idea
considered, but because it is the only one with **no external dependency**. Every
other candidate required a dataset, a toolchain or a novelty claim that failed
under scrutiny. For a fixed deadline, removing failure modes outside your control
beats maximising novelty.
