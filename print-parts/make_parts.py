# The two printable parts of the cam valve as solid meshes: cam.stl and bridge.stl (Z up, mm), built from the same sizes
# as the drawings (valve_geometry.py). Also writes parts-3d.html, a viewer of the two parts with the meshes embedded.
# The STL files are in the position of use; the slicer turns them for printing (the cam top face down, the bridge on
# the back of its wall).
import base64, math, pathlib
import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold
from valve_geometry import *

here = pathlib.Path(__file__).parent


def stadium(half, w, n=24):
    """A slot shape along x, centred on the origin, counter-clockwise."""
    r = w / 2
    pts = [(half - r + r * math.cos(a), r * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, n)]
    pts += [(-(half - r) + r * math.cos(a), r * math.sin(a)) for a in np.linspace(math.pi / 2, 3 * math.pi / 2, n)]
    return pts


def ccw(pts):
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if area > 0 else pts[::-1]


def prism(pts, h, z0=0):
    return CrossSection([ccw(pts)]).extrude(h).translate([0, 0, z0])


def box(x0, x1, y0, y1, z0, z1):
    """A box given in the bridge's frame (x along the servo, y up, z towards the wall), made in the STL frame
    X = x, Y = -z, Z = y, which keeps it right-handed."""
    return Manifold.cube([x1 - x0, z1 - z0, y1 - y0]).translate([x0, -z1, y0])


def cyl(r, h, x, y, z0, seg=48):
    return Manifold.cylinder(h, r, r, seg).translate([x, y, z0])


# ---------- the cam: top view x = R sin u, y = R cos u, Z up from the servo side ----------
rim = [(R(k / 2) * math.sin(math.radians(k / 2)), R(k / 2) * math.cos(math.radians(k / 2))) for k in range(720)]
cam = prism(rim, CAM_T)
cam -= prism(spline_pts(), SPL_D, -.01)                                     # the servo's spline, in place of the horn
cam -= cyl(BORE / 2, CAM_T + 1, 0, 0, -.5)                                 # the horn's screw, its head on the top face
ENGRAVE = .4
for u in (15, 45, 130, 143):                                              # zone marks on the top face
    t = math.radians(u)
    ux, uy, nx, ny = math.sin(t), math.cos(t), math.cos(t), -math.sin(t)
    a, b, w = R(u) - 4, R(u) - 1.4, .3
    mark = [(ux * a + nx * w, uy * a + ny * w), (ux * b + nx * w, uy * b + ny * w), (ux * b - nx * w, uy * b - ny * w), (ux * a - nx * w, uy * a - ny * w)]
    cam -= prism(mark, ENGRAVE + .5, CAM_T - ENGRAVE)
tip = lambda u, r: (r * math.sin(math.radians(u)), r * math.cos(math.radians(u)))
cam -= prism([tip(80, R(80) - 1.6), tip(77.8, R(80) - 4.2), tip(82.2, R(80) - 4.2)], ENGRAVE + .5, CAM_T - ENGRAVE)   # mounting mark

# ---------- the bridge ----------
br = box(XL, -WIN, 0, 3, ZB, ZW)                       # pad on the left ear
br += box(WIN, XR, 0, 3, ZB, ZW)                       # pad on the right ear
br += box(XL, XR, 0, 3, ZW, D + WT)                    # front bar
br += box(WX0, WX1, 0, TOP, D, D + WT)                 # wall, its face presses the tube
br += box(WX0, WX1, CH0 - LIP, CH0, D - LIPD, D)       # lower lip
br += box(WX0, WX1, CH1, TOP, D - LIPD, D)             # upper lip
for x0 in RIBS:
    br += box(x0, x0 + 3, 3, RIB_TOP, ZW, D)           # ribs
for x in FING:                                         # clip fingers with a small snap bump at the tip
    lo0, hi0 = TUBE_Y - 2.1 - 1.5, TUBE_Y + 2.1
    br += box(x - 1.5, x + 1.5, lo0, lo0 + 1.5, D - 4.9, D)
    br += box(x - 1.5, x + 1.5, hi0, hi0 + 1.5, D - 4.9, D)
    br += box(x - 1.5, x + 1.5, lo0 + 1.5, lo0 + 1.9, D - 4.9, D - 4.1)
    br += box(x - 1.5, x + 1.5, hi0 - .4, hi0, D - 4.9, D - 4.1)
for x, z in SLOTS:                                     # slots along z: 1 mm either way
    slot = [(px + x, py - z) for py, px in stadium(SLOT_L / 2, SLOT_W)]   # long axis along the STL's Y (= -z)
    br -= prism(slot, 5, -1)


def save(m, name):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)
    assert t.is_watertight, name
    t.export(here / name)
    ext = t.bounds[1] - t.bounds[0]
    print(f"{name}: {len(t.faces)} faces, {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, {t.volume / 1000:.1f} cm3")
    size = " × ".join(f"{v:.1f}" for v in sorted(ext, reverse=True))
    return (here / name).read_bytes(), size, f"{t.volume / 1000 * 1.27:.0f}"   # PETG, 1.27 g/cm3, solid


(cam_b, cam_size, cam_g), (br_b, br_size, br_g) = save(cam, "cam.stl"), save(br, "bridge.stl")
html = (here / "parts-3d.template.html").read_text(encoding="utf-8")
for k, v in {"__CAM_STL__": base64.b64encode(cam_b).decode(), "__BRIDGE_STL__": base64.b64encode(br_b).decode(),
             "__CAM_SIZE__": cam_size, "__CAM_G__": cam_g, "__BR_SIZE__": br_size, "__BR_G__": br_g}.items():
    html = html.replace(k, v)
(here / "parts-3d.html").write_text(html, encoding="utf-8")
print("parts-3d.html", round(len(html) / 1024), "KB")
