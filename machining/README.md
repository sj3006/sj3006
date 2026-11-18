# 3D nanometric cutting of aluminium: LAMMPS MD

A basic, lightweight 3D molecular dynamics model of a machining operation. A rigid
diamond tool cuts a free-standing single-crystal aluminium block at constant speed
and depth of cut. The tool is narrower than the block, so you get a real 3D picture:
a chip on the rake face, a machined groove, and side burrs where material flows
sideways around the tool.

```
            y (up)
            |         chip
            |        __/ |   diamond tool (rigid, 4.5 nm wide in z)
            |  _____/    |   ---> moves in -x at 100 m/s
            | |   Al     |__/  <- 10 deg clearance face
            | |                |  depth of cut 1.5 nm
            | |________________|
            | thermostat layer (300 K)
            | fixed layer (bottom and left end)
            +-----------------------------> x (cutting direction is -x)
           /
          z (width, free surfaces on both sides)
```

## Parameters

| Item | Value |
|---|---|
| Workpiece | Al, FCC, a = 4.05 Å, 14.2 × 6.1 × 6.9 nm (35,700 atoms) |
| Orientation | x = [100], y = [010], z = [001]; cut on the (010) surface along [-100] |
| Tool | diamond (a = 3.567 Å), rigid, 10,037 atoms, 4.5 nm wide |
| Tool geometry | rake angle 0°, clearance angle 10°, sharp edge |
| Cutting speed | 100 m/s (1 Å/ps) |
| Depth of cut | 1.5 nm |
| Cutting length | 7 nm (70 ps) |
| Temperature | 300 K, Langevin thermostat on the boundary layer |
| Timestep | 1 fs; 5 ps equilibration before cutting |
| Boundaries | non-periodic in all directions (free 3D block) |
| Al–Al | EAM, Mendelev et al., Phil. Mag. 88, 1723 (2008) (`Al_mm.eam.fs`) |
| Al–C | Morse: D₀ = 0.4691 eV, α = 1.738 Å⁻¹, r₀ = 2.246 Å, cutoff 6.5 Å |
| C–C | none (the tool is rigid) |

Atom groups: a 0.8 nm **fixed** layer at the bottom and the left end holds the block
in place. A 0.8 nm **thermostat** layer next to it removes heat. All other Al atoms
are **Newtonian** (NVE), so the heating you see in the cutting zone is real.

Every parameter is a variable at the top of `in.cutting`.

## Files

| Path | What it is |
|---|---|
| `in.cutting` | LAMMPS input script |
| `Al_mm.eam.fs` | Al EAM potential (ships with LAMMPS) |
| `postprocess.py` | force plot and quick 2D snapshots (matplotlib) |
| `results/dump/cut.*.gz` | **trajectory for OVITO**: 36 frames, one every 2 ps (2 Å of tool travel) |
| `results/final.data` | final configuration (LAMMPS data file) |
| `results/forces.dat` | tool travel, Fx, Fy, Fz (nN), Newtonian-zone temperature, every 0.1 ps |
| `results/log.lammps` | full LAMMPS log |
| `figures/` | force/temperature plot and snapshots |

Dump columns: `id type element x y z c_pe`. Type 1 is Al and type 2 is C;
the `element` column lets OVITO name the particle types automatically. `c_pe` is the
per-atom potential energy in eV.

## Viewing in OVITO

1. **File → Load File** and pick `results/dump/cut.0.gz`. OVITO detects the
   numbered sequence `cut.*.gz` on its own. If it doesn't, type `cut.*.gz` as the
   file name. Gzipped dumps are read directly; there's no need to unzip them.
2. Press play on the animation bar to watch the cut.
3. Useful modifiers:
   - **Common neighbor analysis** (adaptive): FCC shows green, HCP (stacking faults)
     red, and disordered/surface atoms white. The tool's carbon atoms come out as
     "Other". To ignore them, first add an **Expression selection** with
     `ParticleType==1` (Al only), then tick *Use only selected particles* in CNA.
   - **Dislocation analysis (DXA)** with input crystal FCC shows the dislocation
     lines that come off the cutting edge.
   - **Slice** with normal (0,0,1) at the centre of the width gives the classic
     side view of chip formation.
   - **Color coding** on `c_pe` or on `Position.Y` highlights the chip and the burrs.

## Re-running it yourself

Requirements: LAMMPS with the MANYBODY and COMPRESS packages. The PyPI wheel has both:

```bash
pip install lammps mpich matplotlib numpy
```

```bash
cd machining && mkdir -p run && cp in.cutting Al_mm.eam.fs run/ && cd run
```

```bash
mpirun -np 4 lmp -in in.cutting
```

```bash
cd .. && python postprocess.py run
```

The run takes about 35 minutes on 4 cores (around 37 timesteps/s for 45.7k atoms).
Output goes to `run/` (gitignored); the committed copy is in `results/`.

## Caveats

* 100 m/s is much faster than real ultra-precision machining (about 1–10 m/s).
  MD needs speeds like this to cut nanometres in nanoseconds, so forces and
  temperatures come out higher than they would at lower speeds.
* The tool is rigid, so tool wear is not modelled.
* The Al–C Morse parameters are values commonly used in Al nanocutting MD.
  They give fairly strong adhesion, so expect some Al to stick to the tool.
* The block is small (about 7 nm wide), so the fixed bottom layer is close to the cut.
  Make `ny`/`nz` larger for less boundary influence; the cost grows with atom count.
