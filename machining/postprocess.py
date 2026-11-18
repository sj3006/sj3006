"""Post-process the LAMMPS nanometric cutting run.

Reads  : forces.dat, dump.cutting   (written by in.cutting)
Writes : figures/forces.png, figures/snapshots.png, figures/cutting.gif

Usage  : python postprocess.py [run_dir]
"""
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image

run = sys.argv[1] if len(sys.argv) > 1 else "run"
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(out, exist_ok=True)


def read_dump(path):
    """Yield (timestep, dict-of-columns) for every frame of a custom dump."""
    with open(path) as f:
        while True:
            line = f.readline()
            if not line:
                return
            if not line.startswith("ITEM: TIMESTEP"):
                continue
            step = int(f.readline())
            f.readline()
            n = int(f.readline())
            for _ in range(4):  # box header + 3 bounds lines
                f.readline()
            cols = f.readline().split()[2:]
            data = np.loadtxt(f, max_rows=n)
            yield step, {c: data[:, i] for i, c in enumerate(cols)}


# ---------------------------------------------------------------- forces
d = np.loadtxt(os.path.join(run, "forces.dat"))
travel, fx, fy, temp = d[:, 2] / 10.0, d[:, 3], d[:, 4], d[:, 5]  # nm, nN, nN, K


def smooth(y, w=21):
    return np.convolve(y, np.ones(w) / w, mode="same")


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
ax1.plot(travel, fx, color="#1f77b4", alpha=0.25, lw=0.8)
ax1.plot(travel, smooth(fx), color="#1f77b4", lw=2, label="Cutting force $F_x$")
ax1.plot(travel, fy, color="#d62728", alpha=0.25, lw=0.8)
ax1.plot(travel, smooth(fy), color="#d62728", lw=2, label="Thrust force $F_y$")
ax1.axhline(0, color="k", lw=0.5)
ax1.set_ylabel("Force on tool (nN)")
ax1.legend(frameon=False)
ss = travel > 3.0  # steady state: after the chip has formed
ax1.set_title(
    f"Steady state (>3 nm): $F_x$ = {fx[ss].mean():.1f} nN, "
    f"$F_y$ = {fy[ss].mean():.1f} nN, $F_y/F_x$ = {fy[ss].mean()/fx[ss].mean():.2f}",
    fontsize=10,
)
ax2.plot(travel, temp, color="#ff7f0e", lw=1.5)
ax2.set_ylabel("Newtonian-zone T (K)")
ax2.set_xlabel("Tool travel (nm)")
fig.tight_layout()
fig.savefig(os.path.join(out, "forces.png"), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- snapshots
norm = Normalize(0, 12)  # centrosymmetry: 0 = perfect FCC, >~8 = surface/defect
frames = list(read_dump(os.path.join(run, "dump.cutting")))


def draw(ax, step, a):
    tool = a["type"] == 2
    cu = ~tool
    # thin slice in z keeps the picture readable
    zmid = 0.5 * (a["z"].min() + a["z"].max())
    sl = np.abs(a["z"] - zmid) < 4.0
    ax.scatter(a["x"][tool & sl], a["y"][tool & sl], s=1.2, c="#555555", lw=0)
    sc = ax.scatter(a["x"][cu & sl], a["y"][cu & sl], s=1.6, c=a["c_csym"][cu & sl],
                    cmap="viridis", norm=norm, lw=0)
    ax.set_aspect("equal")
    ax.set_xlim(60, 260)
    ax.set_ylim(-5, 140)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"t = {step * 0.001:.0f} ps,  tool travel = {step * 0.001:.0f} A", fontsize=9)
    return sc


picks = [frames[i] for i in np.linspace(0, len(frames) - 1, 4).astype(int)]
fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for ax, (step, a) in zip(axes.flat, picks):
    sc = draw(ax, step, a)
cb = fig.colorbar(sc, ax=axes, shrink=0.6, label="Centrosymmetry parameter (Cu)")
fig.suptitle("Orthogonal cutting of Cu(010) with a rigid diamond tool, 100 m/s, 1.5 nm depth")
fig.savefig(os.path.join(out, "snapshots.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- animation
imgs = []
for step, a in frames:
    fig, ax = plt.subplots(figsize=(7, 5))
    draw(ax, step, a)
    fig.tight_layout()
    fig.canvas.draw()
    imgs.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("P", palette=Image.ADAPTIVE))
    plt.close(fig)
imgs[0].save(os.path.join(out, "cutting.gif"), save_all=True, append_images=imgs[1:], duration=150, loop=0)

print(f"{len(frames)} frames; steady-state Fx = {fx[ss].mean():.2f} nN, Fy = {fy[ss].mean():.2f} nN, "
      f"final T = {temp[-1]:.0f} K")
print("figures written to", out)
