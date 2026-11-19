"""Render the machining simulation with OVITO (pip install ovito).

Usage:  python ovito_render.py [machining.lammpstrj]
Writes: ovito/machining_3d.png      3D view at the end, Al coloured by height
        ovito/machining_slice.png   cross-section through the tool path (CNA)
        ovito/machining_steps.png   3D view at four moments of the run
        ovito/machining.gif         animation of the whole run
"""
import os
import sys

from ovito.io import import_file
from ovito.modifiers import (AffineTransformationModifier, ColorCodingModifier, CommonNeighborAnalysisModifier,
                             ExpressionSelectionModifier, AssignColorModifier,
                             SliceModifier, ClearSelectionModifier)
from ovito.vis import Viewport, TachyonRenderer, TextLabelOverlay

src = sys.argv[1] if len(sys.argv) > 1 else "machining.lammpstrj"
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ovito")
os.makedirs(out, exist_ok=True)
renderer = TachyonRenderer(ambient_occlusion=True, shadows=False)


def base_pipeline():
    p = import_file(src)
    types = p.source.data.particles_.particle_types_
    types.type_by_name_("Al").radius = 1.3
    types.type_by_name_("C").radius = 0.9
    p.source.data.cell_.vis.enabled = False
    # OVITO treats Z as "up"; the simulation uses Y as up.
    # Rotate for display only: (x, y, z) -> (x, -z, y)
    p.modifiers.append(AffineTransformationModifier(
        transformation=[[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]]))
    return p


def tool_grey(p):
    p.modifiers.append(ExpressionSelectionModifier(expression="ParticleType==2"))
    p.modifiers.append(AssignColorModifier(color=(0.25, 0.25, 0.28)))
    p.modifiers.append(ClearSelectionModifier())


# ----------------------------------------------------------------- 3D view
p3 = base_pipeline()
p3.modifiers.append(ExpressionSelectionModifier(expression="ParticleType==1"))
p3.modifiers.append(ColorCodingModifier(property="Position.Z", start_value=18.0, end_value=40.0,
                                        gradient=ColorCodingModifier.Rainbow(), only_selected=True))
p3.modifiers.append(ClearSelectionModifier())
tool_grey(p3)
p3.add_to_scene()

vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(0.45, 1.0, -0.8), fov=0.6)
label = TextLabelOverlay(text="Timestep [Timestep]            ",
                         font_size=0.035, text_color=(0.1, 0.1, 0.1),
                         alignment=0x0001 | 0x0020)  # left | top
vp.overlays.append(label)
vp.zoom_all()
nf = p3.source.num_frames

vp.render_image(filename=os.path.join(out, "machining_3d.png"), size=(1400, 900),
                frame=nf - 1, renderer=renderer, background=(1, 1, 1))

for i, f in enumerate([0, 8, 20, nf - 1]):
    vp.render_image(filename=os.path.join(out, f"_step{i}.png"), size=(900, 600),
                    frame=f, renderer=renderer, background=(1, 1, 1))

vp.render_anim(filename=os.path.join(out, "machining.gif"), size=(800, 520), fps=6,
               renderer=renderer, background=(1, 1, 1))
p3.remove_from_scene()

# ----------------------------------------------------------------- slice view
ps = base_pipeline()
ps.modifiers.append(ExpressionSelectionModifier(expression="ParticleType==1"))
ps.modifiers.append(CommonNeighborAnalysisModifier(only_selected=True))
ps.modifiers.append(ClearSelectionModifier())
ps.modifiers.append(SliceModifier(normal=(0, 1, 0), distance=-24.3, slab_width=6.0))
tool_grey(ps)
ps.add_to_scene()
vs = Viewport(type=Viewport.Type.Front)  # X to the right, height up
vs.overlays.append(TextLabelOverlay(
    text="Cross-section through tool path  (green = FCC, white = disordered/surface, red = stacking fault)            ",
    font_size=0.035, text_color=(0.1, 0.1, 0.1), alignment=0x0001 | 0x0020))
vs.zoom_all()
vs.render_image(filename=os.path.join(out, "machining_slice.png"), size=(1400, 700),
                frame=ps.source.num_frames - 1, renderer=renderer, background=(1, 1, 1))
ps.remove_from_scene()

# ----------------------------------------------------------------- 2x2 panel
from PIL import Image

tiles = [Image.open(os.path.join(out, f"_step{i}.png")) for i in range(4)]
w, h = tiles[0].size
panel = Image.new("RGB", (2 * w, 2 * h), "white")
for i, t in enumerate(tiles):
    panel.paste(t, ((i % 2) * w, (i // 2) * h))
panel.save(os.path.join(out, "machining_steps.png"))
for i in range(4):
    os.remove(os.path.join(out, f"_step{i}.png"))
print("written to", out)
