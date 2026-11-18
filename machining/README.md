# Nanometric orthogonal cutting: LAMMPS MD

A basic molecular dynamics model of a machining operation: a rigid diamond tool
cuts a single-crystal copper workpiece at constant speed and depth of cut. The model
is 2D plane-strain: the workpiece is periodic through its thickness (z).

```
          y
          ^            chip
          |          __/|  diamond tool (rigid)
          |  _______/   |  ---> moves in -x at 100 m/s
          | |  Cu   |___/  <- 10 deg clearance face
          | | Newtonian zone    | depth of cut 1.5 nm
          | |___________________|
          | thermostat layer (300 K, Langevin)
          | fixed layer
          +---------------------------------> x
```

## Parameters

| Item | Value |
|---|---|
| Workpiece | Cu, FCC, a = 3.615 Å, 19.9 × 8.0 × 2.2 nm (29,040 atoms) |
| Orientation | cut on the (010) surface along [-100] |
| Tool | diamond (a = 3.567 Å), rigid, 8,871 atoms |
| Tool geometry | rake angle 0°, clearance angle 10°, sharp edge |
| Cutting speed | 100 m/s (1 Å/ps) |
| Depth of cut | 1.5 nm |
| Cutting length | 10 nm (100 ps) |
| Temperature | 300 K, Langevin thermostat on the boundary layer |
| Timestep | 1 fs; 10 ps equilibration before cutting |
| Cu–Cu | EAM, Mishin et al., PRB 63, 224106 (2001) (`Cu_mishin1.eam.alloy`) |
| Cu–C | Morse: D₀ = 0.087 eV, α = 5.14 Å⁻¹, r₀ = 2.05 Å, cutoff 6 Å |
| C–C | none (the tool is rigid) |

Atom groups: a 1 nm **fixed** layer on the left and bottom keeps the workpiece in place.
A 1 nm **thermostat** layer next to it removes the cutting heat. Everything else
is the **Newtonian** zone, integrated with NVE.

All of these are variables at the top of `in.cutting`: `vcut`, `doc`, `rake`, `clear`,
`cutlen`, `T`, and the workpiece size `nx/ny/nz`.

## Running

Requirements: LAMMPS with the MANYBODY package. The PyPI wheel works:

```bash
pip install lammps mpich matplotlib numpy pillow
```

```bash
cd machining && mkdir -p run && cp in.cutting Cu_mishin1.eam.alloy run/ && cd run
```

```bash
mpirun -np 4 lmp -in in.cutting
```

```bash
cd .. && python postprocess.py run
```

On 4 cores the run takes about 30 minutes (around 58 timesteps/s).

## Outputs

* `run/forces.dat`: tool travel, cutting force Fx, thrust force Fy (nN), Newtonian-zone temperature, every 0.1 ps
* `run/dump.cutting`: atom snapshots every 2 ps (id, type, x, y, z, centrosymmetry, PE). Open them in OVITO for 3D views and dislocation analysis (DXA). Not committed because of size.
* `figures/forces.png`: force and temperature vs. tool travel
* `figures/snapshots.png`: four side views coloured by centrosymmetry parameter
* `figures/cutting.gif`: animation of the whole cut

## Caveats

* 100 m/s is fast compared with real ultra-precision machining (about 1–10 m/s). MD
  needs speeds like this to cover nanometres in nanoseconds. Expect higher forces
  and temperatures than you would get at lower speeds.
* The tool is rigid, so tool wear and tool deformation are not modelled.
* The workpiece is only 2.2 nm thick (periodic), which suppresses some 3D dislocation
  structures. Increase `nz` for a more 3D picture.
* The thermostat is applied only to the boundary layer, so the temperature rise
  in the Newtonian zone is real heating from plastic work and friction.
