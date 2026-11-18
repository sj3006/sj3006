"""Quick-look plots for the LAMMPS 3D aluminium cutting run.

Reads  : <run>/forces.dat, <run>/dump/cut.*.gz   (written by in.cutting)
Writes : figures/forces.png, figures/snapshots.png

Usage  : python postprocess.py [run_dir]

For proper 3D visualisation open <run>/dump/cut.*.gz in OVITO (see README).
"""
import glob
import gzip
import os
import re
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

run = sys.argv[1] if len(sys.argv) > 1 else "run"
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(out, exist_ok=True)


def read_frame(path):
    """Return a dict of numeric columns from one gzipped LAMMPS custom dump frame."""
    with gzip.open(path, "rt") as f:
        lines = f.readlines()
    cols = lines[8].split()[2:]
    rows = [ln.split() for ln in lines[9:]]
    a = {}
    for i, c in enumerate(cols):
        if c == "element":
            continue
        a[c] = np.array([float(r[i]) for r in rows])
    return a


# ---------------------------------------------------------------- forces
d = np.loadtxt(os.path.join(run, "forces.dat"))
travel, fx, fy, fz, temp = d[:, 2] / 10.0, d[:, 3], d[:, 4], d[:, 5], d[:, 6]


def smooth(y, w=21):
    return np.convolve(y, np.ones(w) / w, mode="same")


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
for y, col, lab in [(fx, "#1f77b4", "Cutting force $F_x$"),
                    (fy, "#d62728", "Thrust force $F_y$"),
                    (fz, "#7f7f7f", "Lateral force $F_z$")]:
    ax1.plot(travel, y, color=col, alpha=0.2, lw=0.8)
    ax1.plot(travel, smooth(y), color=col, lw=2, label=lab)
ax1.axhline(0, color="k", lw=0.5)
ax1.set_ylabel("Force on tool (nN)")
ax1.legend(frameon=False, ncol=3, fontsize=9)
ss = travel > 2.0  # after the chip has formed
ax1.set_title(f"Mean after 2 nm of travel: $F_x$ = {fx[ss].mean():.1f} nN, "
              f"$F_y$ = {fy[ss].mean():.1f} nN", fontsize=10)
ax2.plot(travel, temp, color="#ff7f0e", lw=1.5)
ax2.set_ylabel("Newtonian-zone T (K)")
ax2.set_xlabel("Tool travel (nm)")
fig.tight_layout()
fig.savefig(os.path.join(out, "forces.png"), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- snapshots
files = sorted(glob.glob(os.path.join(run, "dump", "cut.*.gz")),
               key=lambda p: int(re.search(r"cut\.(\d+)\.gz", p).group(1)))
first, last = read_frame(files[0]), read_frame(files[-1])
step_last = int(re.search(r"cut\.(\d+)\.gz", files[-1]).group(1))
norm = Normalize(-3.36, -2.6)  # Al PE/atom: bulk ~ -3.36 eV, surface/defects higher


def view(ax, a, h, v, title, slab=None):
    tool = a["type"] == 2
    keep = np.ones_like(tool) if slab is None else slab(a)
    al = ~tool & keep
    ax.scatter(a[h][tool & keep], a[v][tool & keep], s=0.6, c="#555555", lw=0)
    sc = ax.scatter(a[h][al], a[v][al], s=0.8, c=a["c_pe"][al], cmap="viridis",
                    norm=norm, lw=0)
    ax.set_aspect("equal")
    ax.set_xlabel(f"{h} (A)")
    ax.set_ylabel(f"{v} (A)")
    ax.set_title(title, fontsize=10)
    return sc


zmid = 0.5 * (first["z"].min() + first["z"].max())
centre = lambda a: np.abs(a["z"] - zmid) < 6.0  # 1.2 nm slice through the tool centre

fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
view(axes[0], first, "x", "y", "Side view, start (centre slice)", centre)
sc = view(axes[1], last, "x", "y", f"Side view after {step_last/1000:.0f} A of travel (centre slice)", centre)
fig.colorbar(sc, ax=axes[:2], shrink=0.8, label="Al potential energy (eV/atom)", location="bottom")

# top view as a height map: highest Al atom in each 4 A x 4 A column
al = last["type"] == 1
xb = np.arange(last["x"][al].min() - 1, last["x"][al].max() + 4, 4.0)
zb = np.arange(last["z"][al].min() - 1, last["z"][al].max() + 4, 4.0)
ix, iz = np.digitize(last["x"][al], xb) - 1, np.digitize(last["z"][al], zb) - 1
hmap = np.full((len(zb), len(xb)), np.nan)
np.fmax.at(hmap, (iz, ix), last["y"][al])
hm = axes[2].imshow(hmap, origin="lower", extent=(xb[0], xb[-1] + 4, zb[0], zb[-1] + 4),
                    cmap="terrain", interpolation="nearest")
tl = last["type"] == 2
axes[2].scatter(last["x"][tl], last["z"][tl], s=0.5, c="#555555", alpha=0.15, lw=0)
axes[2].set_aspect("equal")
axes[2].set_xlabel("x (A)")
axes[2].set_ylabel("z (A)")
axes[2].set_title("Top view: groove and side burrs (tool shaded)", fontsize=10)
fig.colorbar(hm, ax=axes[2], shrink=0.8, label="Height y (A)", location="bottom")
fig.suptitle("3D cutting of Al(010) with a rigid diamond tool: 100 m/s, 1.5 nm depth of cut")
fig.savefig(os.path.join(out, "snapshots.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"{len(files)} frames; mean Fx = {fx[ss].mean():.2f} nN, Fy = {fy[ss].mean():.2f} nN, "
      f"final T = {temp[-1]:.0f} K; figures in {out}")
