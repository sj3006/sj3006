# Quick 3D nanometric cutting of aluminium: LAMMPS MD

A small, fast 3D molecular dynamics model of a machining operation. A rigid diamond
tool cuts a free-standing single-crystal aluminium block at constant speed and depth
of cut. The tool is narrower than the block, so the result is truly 3D: a chip forms
on the rake face, a groove is left behind, and side burrs appear where material
flows sideways around the tool.

The whole run takes **about 20–25 seconds on 4 CPU cores**.

```
            y (up)
            |        chip
            |       _/|    diamond tool (rigid, 2 nm wide in z)
            |  ____/  |    ---> moves in -x at 200 m/s
            | |  Al   |_/  <- 10 deg clearance face
            | |          |  depth of cut 0.8 nm
            | |__________|
            | thermostat layer (300 K)
            | fixed layer (bottom and left end)
            +-----------------------> x
           /
          z (width: free surfaces on both sides)
```

## Parameters

| Item | Value |
|---|---|
| Workpiece | Al, FCC, a = 4.05 Å, 6.5 × 3.2 × 3.2 nm (4,096 atoms) |
| Orientation | x = [100], y = [010], z = [001]; cut on the (010) surface along [-100] |
| Tool | diamond (a = 3.567 Å), rigid, 1,091 atoms, 2.0 nm wide |
| Tool geometry | rake angle 0°, clearance angle 10°, sharp edge |
| Cutting speed | 200 m/s (2 Å/ps) |
| Depth of cut | 0.8 nm |
| Cutting length | 2.0 nm (10 ps) |
| Temperature | 300 K, Langevin thermostat on the boundary layer |
| Timestep | 2 fs; 1 ps equilibration, then 10 ps of cutting (5,500 steps in total) |
| Boundaries | non-periodic in all directions (free 3D block in a fixed box) |
| Al–Al | EAM, Mendelev et al., Phil. Mag. 88, 1723 (2008) (`Al_mm.eam.fs`) |
| Al–C | Morse: D₀ = 0.28 eV, α = 2.78 Å⁻¹, r₀ = 2.20 Å, cutoff 5 Å |
| C–C | none (the tool is rigid) |

Atom groups: a 0.4 nm **fixed** layer at the bottom and left end holds the block in
place. The next 0.8 nm is a **thermostat** layer that removes heat. All other Al
atoms are **Newtonian** (plain NVE).

Every parameter is a variable at the top of `in.cutting`.

## Results of the committed run

* Mean cutting force Fx ≈ 8.7 nN and thrust force Fy ≈ 3.0 nN, averaged after the
  tool engages at about 0.6 nm of travel.
* The Newtonian-zone temperature climbs from about 316 K to about 430 K by the end of the cut.
* A chip piles up on the rake face, and side burrs form on both sides of the groove.

See `figures/forces.png` and `figures/snapshots.png`.

## Files

| Path | What it is |
|---|---|
| `in.cutting` | LAMMPS input script |
| `Al_mm.eam.fs` | Al EAM potential (ships with LAMMPS) |
| `postprocess.py` | force plot and quick 2D snapshots (matplotlib) |
| `results/dump/cut.*.gz` | **trajectory for OVITO**: 21 frames, one every 0.5 ps (1 Å of tool travel) |
| `results/final.data` | final configuration (LAMMPS data file, also opens in OVITO) |
| `results/forces.dat` | step, time, tool travel, Fx, Fy, Fz (nN), Newtonian-zone T, every 0.05 ps |
| `results/log.lammps` | full LAMMPS log |
| `figures/` | force/temperature plot and snapshots |

Dump columns: `id type element x y z c_pe`. Type 1 is Al and type 2 is C;
the `element` column lets OVITO name the particle types. `c_pe` is per-atom
potential energy in eV.

## Viewing in OVITO

1. **File → Load File** and pick `results/dump/cut.0.gz`. OVITO detects the
   numbered sequence `cut.*.gz` on its own. If it doesn't, type `cut.*.gz` as the
   file name. OVITO reads `.gz` directly; there's no need to unzip.
2. Press play on the animation bar to watch the cut.
3. Useful modifiers:
   - **Common neighbor analysis** (adaptive): FCC shows green, HCP (stacking faults)
     red, and disordered/surface atoms white. To keep the tool out of it, first add an
     **Expression selection** with `ParticleType==1` (Al only), then tick
     *Use only selected particles* in CNA.
   - **Slice** with normal (0,0,1) through the middle of the width gives the classic side
     view of chip formation.
   - **Color coding** on `c_pe` (energy) or `Position.Y` (height) highlights the chip
     and the burrs.
   - **Dislocation analysis (DXA)** with input crystal FCC shows any dislocation lines.

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

Output goes to `run/`, which is gitignored; the committed copy is in `results/`.
On one core it takes roughly 35–40 s.

## Caveats

* The model is deliberately tiny so that it runs in seconds. The fixed and thermostat
  layers are close to the cutting zone, and the numbers are noisy. Increase `nx/ny/nz`
  and `cutlen` for a more realistic run; the cost grows with atom count × steps.
* 200 m/s is much faster than real ultra-precision machining (about 1–10 m/s). MD
  needs high speeds to cut nanometres in picoseconds.
* The tool is rigid, so wear is not modelled.
* The Al–C Morse parameters are illustrative values for a weakly adhesive
  diamond/Al contact. Check them against the literature before quoting forces
  quantitatively.
