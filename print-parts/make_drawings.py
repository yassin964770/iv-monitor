# Workshop drawings of the two printed parts of the cam valve: the cam (in place of the servo's two-arm horn) and the
# fixed bridge that holds the tube. Same sizes and the same cam profile as servo-cam-valve-3d.html.
# Writes cam-valve-drawings.pdf (two A4 landscape sheets), a PNG of each sheet, and cam-profile.csv (the rim, every degree).
# Sizes rest on a standard MG945 servo and a 4.1 mm tube: they are to be corrected once the real parts are measured.
import csv, math, pathlib
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent

from valve_geometry import *

# ---------- SVG drawing kit (page units are mm) ----------
INK, THIN, MUTED, HATCH = "#13201f", "#3c4b4a", "#6b7b79", "#7c8b89"


class Sheet:
    def __init__(self):
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def line(self, x1, y1, x2, y2, w=.35, c=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="{w}"{d}/>')

    def path(self, d, w=.35, c=INK, fill="none", dash=None):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" stroke="{c}" stroke-width="{w}" fill="{fill}"{ds} stroke-linejoin="round"/>')

    def circle(self, x, y, r, w=.35, c=INK, dash=None, fill="none"):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" stroke="{c}" stroke-width="{w}" fill="{fill}"{ds}/>')

    def text(self, x, y, s, size=2.6, anchor="middle", ar=False, c=INK, rot=0, weight=400):
        fam = "IBM Plex Sans Arabic" if ar else "IBM Plex Mono"
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        dr = ' direction="rtl" unicode-bidi="embed"' if ar else ""
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{c}" text-anchor="{anchor}"{dr}{tr}>{s}</text>')

    def centre(self, x, y, r):
        self.line(x - r, y, x + r, y, .18, THIN, "4 1 .6 1")
        self.line(x, y - r, x, y + r, .18, THIN, "4 1 .6 1")

    def dim(self, x1, y1, x2, y2, off, label, size=2.6, ext=1.2):
        """A dimension between two points, its line offset `off` mm to the left of the direction 1 -> 2."""
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = uy, -ux
        a = (x1 + nx * off, y1 + ny * off)
        b = (x2 + nx * off, y2 + ny * off)
        sgn = 1 if off >= 0 else -1
        self.line(x1 + nx * sgn * .8, y1 + ny * sgn * .8, a[0] + nx * sgn * ext, a[1] + ny * sgn * ext, .18, THIN)
        self.line(x2 + nx * sgn * .8, y2 + ny * sgn * .8, b[0] + nx * sgn * ext, b[1] + ny * sgn * ext, .18, THIN)
        self.add(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{THIN}" stroke-width=".18" '
                 f'marker-start="url(#arr)" marker-end="url(#arr)"/>')
        ang = math.degrees(math.atan2(uy, ux))
        if ang >= 90 or ang < -90:
            ang -= 180
        mx, my = (a[0] + b[0]) / 2 + nx * sgn * 1.1, (a[1] + b[1]) / 2 + ny * sgn * 1.1
        if sgn > 0 and ny > .5 or sgn < 0 and ny < -.5:   # label below a horizontal line: drop it under
            my += size * .7
        self.text(mx, my, label, size, rot=ang)

    def leader(self, x1, y1, x2, y2, label, anchor="start", ar=False, size=2.6):
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{THIN}" stroke-width=".18" marker-start="url(#arr)"/>')
        self.text(x2 + (1 if anchor == "start" else -1 if anchor == "end" else 0), y2 + .9, label, size, anchor, ar)

    def hatch(self, d):
        self.add(f'<path d="{d}" fill="url(#hatch)" stroke="{INK}" stroke-width=".35" stroke-linejoin="round"/>')

    def svg(self):
        return ('<svg class="draw" viewBox="0 0 297 210" width="297mm" height="210mm" xmlns="http://www.w3.org/2000/svg">'
                '<defs><marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="2.4" markerHeight="2.4" orient="auto-start-reverse">'
                f'<path d="M0,1.5 L10,5 L0,8.5 z" fill="{THIN}"/></marker>'
                f'<pattern id="hatch" width="1.4" height="1.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.4" stroke="{HATCH}" stroke-width=".22"/></pattern>'
                '</defs>' + "".join(self.parts) + "</svg>")


def poly(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def frame(sh):
    sh.add(f'<rect x="8" y="8" width="281" height="194" fill="none" stroke="{INK}" stroke-width=".5"/>')


# ================= sheet 1: the cam =================
s1 = Sheet(); frame(s1)
S = 1.5


def top_xy(ox, oy, u, r, mirror=False):
    t = math.radians(u)
    x, y = r * math.sin(t), r * math.cos(t)
    return ox + (-x if mirror else x) * S, oy - y * S


def rim(ox, oy, mirror=False):
    pts = [top_xy(ox, oy, k / 2, R(k / 2), mirror) for k in range(720)]
    return poly(pts)


def stadium(ox, oy, half, w, dash=None, sh=s1, width=.35):
    r = w / 2
    x0, x1 = ox - (half - r) * S, ox + (half - r) * S
    d = (f"M{x0:.2f} {oy - r * S:.2f} L{x1:.2f} {oy - r * S:.2f} A{r * S:.2f} {r * S:.2f} 0 0 1 {x1:.2f} {oy + r * S:.2f} "
         f"L{x0:.2f} {oy + r * S:.2f} A{r * S:.2f} {r * S:.2f} 0 0 1 {x0:.2f} {oy - r * S:.2f} Z")
    sh.path(d, width, INK if not dash else THIN, dash=dash)


# --- top view
ox, oy = 70, 88
s1.text(ox, 30, "منظر من الأعلى", 3.4, ar=True, weight=600)
s1.path(rim(ox, oy), .5)
s1.centre(ox, oy, R_MAX * S + 4)
s1.circle(ox, oy, BORE / 2 * S)
s1.circle(ox, oy, SPL_RO * S, .25, THIN, "1.5 .8")
for u in (15, 45, 130, 143):                                   # engraved zone marks on the top face
    a, b = top_xy(ox, oy, u, R(u) - 4), top_xy(ox, oy, u, R(u) - 1.4)
    s1.line(*a, *b, .35)
    c = top_xy(ox, oy, u, R(u) + 4.2)
    s1.text(c[0], c[1] + .9, f"{u}°", 2.3, c=MUTED)
mk = top_xy(ox, oy, 80, R(80) - 1.6)                             # mounting mark: a small triangle at u = 80
t = math.radians(80)
tip = (mk[0], mk[1])
base1 = top_xy(ox, oy, 80 - 2.2, R(80) - 4.2)
base2 = top_xy(ox, oy, 80 + 2.2, R(80) - 4.2)
s1.path(poly([tip, base1, base2]), .25, fill=INK)
for u, name in ((2, "فتح"), (30, "سريعة"), (106, "ضبط"), (151, "قفل")):
    c = top_xy(ox, oy, u, R(u) + 9.5)
    s1.text(c[0], c[1] + 1, name, 3, ar=True, c=THIN, weight=600)
c = top_xy(ox, oy, 80, R(80) + 16)
s1.leader(*top_xy(ox, oy, 80, R(80) - 3), c[0] - 1, c[1] - 5, "علامة التركيب", "start", ar=True)
# radius call-outs
p = top_xy(ox, oy, 240, R(240)); s1.leader(ox, oy, *p, "", "start"); s1.text(p[0] - 1.5, p[1] + 3, f"R{R(240):.2f}", 2.6, "end")
p = top_xy(ox, oy, 200, R(200)); s1.leader(ox, oy, *p, "", "start"); s1.text(p[0] - 1.5, p[1] + 3.5, f"R{R(200):.2f}", 2.6, "end")
s1.leader(ox + BORE / 2 * S * .71, oy - BORE / 2 * S * .71, ox + 14, oy - 16, f"Ø{BORE}", "start")
# closing direction: the contact meets larger u, so the cam turns anticlockwise seen from above
r_arr = 9
a0, a1 = math.radians(200), math.radians(290)
s1.add(f'<path d="M{ox + r_arr * math.cos(a0) * S:.2f} {oy - r_arr * math.sin(a0) * S:.2f} A{r_arr * S} {r_arr * S} 0 0 0 '
       f'{ox + r_arr * math.cos(a1) * S:.2f} {oy - r_arr * math.sin(a1) * S:.2f}" fill="none" stroke="{MUTED}" stroke-width=".3" marker-end="url(#arr)"/>')
s1.text(ox - 6, oy + 20.5, "اتجاه الإغلاق", 2.4, ar=True, c=MUTED)
# section line A-A along the pocket
for sx in (-1, 1):
    x = ox + sx * (R_MAX + 6) * S
    s1.line(x, oy, x - sx * 5, oy, .6)
    s1.add(f'<line x1="{x - sx * 2.5:.2f}" y1="{oy:.2f}" x2="{x - sx * 2.5:.2f}" y2="{oy + 4:.2f}" stroke="{INK}" stroke-width=".35" marker-end="url(#arr)"/>')
    s1.text(x - sx * 2.5, oy - 1.6, "A", 3, weight=600)

# --- bottom view (servo side), mirrored
bx, by = 172, 88
s1.text(bx, 30, "منظر من الأسفل، جهة السيرفو", 3.4, ar=True, weight=600)
s1.path(rim(bx, by, True), .5)
s1.centre(bx, by, R_MAX * S + 4)
s1.path(poly([(bx - x * S, by - y * S) for x, y in spline_pts()]), .3)
s1.circle(bx, by, BORE / 2 * S)
s1.leader(bx + SPL_RO * S * .71, by + SPL_RO * S * .71, bx + 12, by + 16, "", "middle")
s1.text(bx + 12, by + 19.6, "فتحة مسنن الشفت", 2.5, ar=True, c=THIN)
s1.text(bx + 12, by + 23.2, f"{SPL_N}T  Ø{2 * SPL_RO:.2f} × {SPL_D}", 2.4)

# --- section A-A
sx0, sy0 = 70, 172          # centre of the bore, on the cam's underside
r_left, r_right = R(270), R(90)
s1.text(sx0, 148, "المقطع A-A", 3.4, ar=True, weight=600)
P = lambda x, y: (sx0 + x * S, sy0 - y * S)
left = [(-r_left, 0), (-SPL_RO, 0), (-SPL_RO, SPL_D), (-BORE / 2, SPL_D), (-BORE / 2, CAM_T), (-r_left, CAM_T)]
right = [(BORE / 2, SPL_D), (SPL_RO, SPL_D), (SPL_RO, 0), (r_right, 0), (r_right, CAM_T), (BORE / 2, CAM_T)]
s1.hatch(poly([P(*q) for q in left])); s1.hatch(poly([P(*q) for q in right]))
s1.line(sx0, sy0 - CAM_T * S - 3, sx0, sy0 + 3, .18, THIN, "4 1 .6 1")
s1.dim(*P(r_right, 0), *P(r_right, CAM_T), -5, f"{CAM_T:.0f}")
s1.dim(*P(-SPL_RO, 0), *P(-SPL_RO, SPL_D), 12, f"{SPL_D}")
s1.dim(*P(-SPL_RO, 0), *P(SPL_RO, 0), -5, f"Ø{2 * SPL_RO:.2f}")
s1.dim(*P(-BORE / 2, CAM_T), *P(BORE / 2, CAM_T), 4, f"Ø{BORE}")
s1.dim(*P(-r_left, CAM_T), *P(r_right, CAM_T), 9, f"{r_left + r_right:.2f}")

# ================= sheet 2: the bridge =================
s2 = Sheet(); frame(s2)

# --- top view: x to the right, z up the page (the wall at the top)
tx, ty = 24, 34
T2 = lambda x, z: (tx + (x - XL) * S, ty + (D + WT - z) * S)
s2.text(T2(5.5, 0)[0], 16.5, "منظر من الأعلى", 3.4, ar=True, weight=600)
plate = [(XL, ZB), (-WIN, ZB), (-WIN, ZW), (WIN, ZW), (WIN, ZB), (XR, ZB), (XR, D + WT), (XL, D + WT)]
s2.path(poly([T2(*q) for q in plate]), .5)
s2.path(poly([T2(*q) for q in [(WX0, D - LIPD), (WX1, D - LIPD), (WX1, D + WT), (WX0, D + WT)]]), .35)   # upper lip and wall
s2.line(*T2(WX0, D), *T2(WX1, D), .18, THIN, "1.5 .8")                                                    # pressing face, under the lip
for x0 in (-16, 33):                                                                                       # ribs
    s2.path(poly([T2(*q) for q in [(x0, ZW), (x0 + 3, ZW), (x0 + 3, D - LIPD), (x0, D - LIPD)]]), .35)
for x in FING:                                                                                             # clip fingers, under the lip
    s2.path(poly([T2(*q) for q in [(x - 1.5, D - 4.9), (x + 1.5, D - 4.9), (x + 1.5, D), (x - 1.5, D)]]), .25, THIN, dash="1.5 .8")
for x, z in SLOTS:                                                                                         # slots along z, 1 mm either way
    cx_, cz_ = T2(x, z)
    r = SLOT_W / 2 * S
    s2.path(f"M{cx_ - r:.2f} {cz_ - 1 * S:.2f} A{r:.2f} {r:.2f} 0 0 1 {cx_ + r:.2f} {cz_ - 1 * S:.2f} L{cx_ + r:.2f} {cz_ + 1 * S:.2f} "
            f"A{r:.2f} {r:.2f} 0 0 1 {cx_ - r:.2f} {cz_ + 1 * S:.2f} Z", .35)
s2.path(poly([T2(*q) for q in [(-20.35, -9.85), (20.35, -9.85), (20.35, 9.85), (-20.35, 9.85)]]), .2, MUTED, dash="5 1 1 1 1 1")
s2.centre(*T2(CX, 0), 6)
s2.line(*T2(0, -12.5), *T2(0, 12.5), .18, THIN, "4 1 .6 1")
s2.dim(*T2(XL, ZB), *T2(XR, ZB), -6, f"{XR - XL:.1f}")
s2.dim(*T2(-HOLE_X, ZB), *T2(HOLE_X, ZB), -12, f"{2 * HOLE_X:.1f}")
s2.dim(*T2(XR, -HOLE_Z), *T2(XR, HOLE_Z), -4, f"{2 * HOLE_Z:.1f}")
s2.dim(*T2(XR, 0), *T2(XR, D), -11, f"{D}")
s2.dim(*T2(XR, D), *T2(XR, D + WT), -4, f"{WT:.0f}")
s2.dim(*T2(-WIN, ZW), *T2(WIN, ZW), -3.5, f"{2 * WIN:.1f}")
s2.dim(*T2(0, 0), *T2(CX, 0), -13, f"{CX}")
s2.dim(*T2(WX0, D + WT), *T2(WX1, D + WT), 6, f"{WX1 - WX0:.0f}")

# --- front view from the cam side: x to the right, y up
fx, fy = 24, 128
F2 = lambda x, y: (fx + (x - XL) * S, fy + (TOP - y) * S)
s2.text(F2(5.5, 0)[0], 121, "منظر أمامي، من جهة الكامة", 3.4, ar=True, weight=600)
s2.path(poly([F2(*q) for q in [(XL, 0), (XR, 0), (XR, 3), (XL, 3)]]), .5)                          # plate edge
s2.path(poly([F2(*q) for q in [(WX0, 3), (WX1, 3), (WX1, TOP), (WX0, TOP)]]), .5)                   # wall
for y0 in (CH0 - LIP, CH1):                                                                         # lips
    s2.path(poly([F2(*q) for q in [(WX0, y0), (WX1, y0), (WX1, y0 + LIP), (WX0, y0 + LIP)]]), .35)
for x0 in (-16, 33):                                                                                # ribs
    s2.path(poly([F2(*q) for q in [(x0, 3), (x0 + 3, 3), (x0 + 3, RIB_TOP), (x0, RIB_TOP)]]), .35)
for x in FING:
    for y0 in (TUBE_Y - 2.1 - 1.5, TUBE_Y + 2.1):
        s2.path(poly([F2(*q) for q in [(x - 1.5, y0), (x + 1.5, y0), (x + 1.5, y0 + 1.5), (x - 1.5, y0 + 1.5)]]), .35)
s2.line(*F2(XL - 3, TUBE_Y), *F2(XR + 3, TUBE_Y), .18, THIN, "4 1 .6 1")
s2.line(*F2(CX, -2), *F2(CX, TOP + 2), .18, THIN, "4 1 .6 1")
s2.path(poly([F2(*q) for q in [(CX - R_MAX, CAM_Y), (CX + R_MAX, CAM_Y), (CX + R_MAX, CAM_Y + CAM_T), (CX - R_MAX, CAM_Y + CAM_T)]]), .2, MUTED, dash="5 1 1 1 1 1")
for yv, lab in ((3, "3"), (CH0 - LIP, f"{CH0 - LIP:.2f}"), (CH0, f"{CH0:.2f}"), (CH1, f"{CH1:.2f}"), (TOP, f"{TOP:.2f}")):
    a = F2(XR + 2, yv); s2.line(*F2(WX1 + .8, yv), a[0] + 4, a[1], .18, THIN)
    s2.text(a[0] + 5, a[1] + .9, lab, 2.4, "start")
s2.text(F2(XR + 2, -1)[0] + 5, F2(XR, -2.8)[1] + .9, "من الأذنين", 2.3, "start", ar=True, c=MUTED)
s2.dim(*F2(FING[0], CH0), *F2(FING[1], CH0), -9, "44")
s2.dim(*F2(XL, 0), *F2(XL, TOP), 4, f"{TOP:.2f}")
s2.text(F2(CX, 0)[0], F2(0, TUBE_Y)[1] - 2.5, "مجرى الأنبوب", 2.4, ar=True, c=THIN)

# --- section B-B through the shaft axis: z to the right, y up
qx, qy = 182, 44
Q2 = lambda z, y: (qx + (z + 2) * S, qy + (TOP - y) * S)
s2.text(Q2(15, 0)[0], 28, "المقطع B-B عند محور الشفت", 3.4, ar=True, weight=600)
body = [(ZW, 0), (D + WT, 0), (D + WT, TOP), (D - LIPD, TOP), (D - LIPD, CH1), (D, CH1), (D, CH0), (D - LIPD, CH0),
        (D - LIPD, CH0 - LIP), (D, CH0 - LIP), (D, 3), (ZW, 3)]
s2.hatch(poly([Q2(*q) for q in body]))
s2.line(*Q2(0, -3), *Q2(0, TOP + 3), .18, THIN, "4 1 .6 1")
s2.text(Q2(0, -6)[0], Q2(0, -6)[1], "محور الشفت", 2.4, ar=True, c=MUTED)
s2.circle(*Q2(D - OD / 2, TUBE_Y), OD / 2 * S, .3, MUTED)
s2.path(poly([Q2(*q) for q in [(-2, CAM_Y), (D - 1, CAM_Y), (D - 1, CAM_Y + CAM_T), (-2, CAM_Y + CAM_T)]]), .2, MUTED, dash="5 1 1 1 1 1")
s2.path(poly([Q2(*q) for q in [(-2, -3), (9.85, -3), (9.85, 9), (-2, 9)]]), .2, MUTED, dash="5 1 1 1 1 1")
s2.text(Q2(10, CAM_Y + CAM_T / 2)[0], Q2(10, CAM_Y + CAM_T / 2)[1] + 1, "الكامة مسكّرة، الفتحة 1.0", 2.4, ar=True, c=MUTED)
s2.text(Q2(4, 3)[0], Q2(4, 3)[1] + 1, "السيرفو", 2.4, ar=True, c=MUTED)
s2.dim(*Q2(0, TOP), *Q2(D, TOP), 5, f"{D}")
s2.dim(*Q2(D, TOP), *Q2(D + WT, TOP), 5, f"{WT:.0f}")
s2.dim(*Q2(D - LIPD, CH0 - LIP), *Q2(D, CH0 - LIP), -4, f"{LIPD:.0f}")
s2.dim(*Q2(D + WT, CH0), *Q2(D + WT, CH1), -5, "8")
s2.dim(*Q2(D + WT, CH1), *Q2(D + WT, TOP), -5, "3")

# ---------- the profile table and the sheets ----------
rows = [0, 15, 25, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 130, 135, 139, 143, 150, 160, 200, 230]
zone = lambda u: "فتح" if u < 15 or u >= 230 else "سريعة" if u < 45 else "ضبط" if u < 130 else "قفل" if u < 160 else "رجوع"
table = "".join(f"<tr><td>{u}</td><td>{SERVO(u) if u <= 150 else ''}</td><td>{R(u):.2f}</td><td>{gap_at(u):.2f}</td>"
                f"<td>{round(flow(gap_at(u)) * 100) if u <= 160 else ''}</td><td class='z'>{zone(u)}</td></tr>" for u in rows)
table += "<tr><td>230-360</td><td></td><td>23.00</td><td>4.60</td><td></td><td class='z'>فتح</td></tr>"

with open(here / "cam-profile.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["u_deg", "radius_mm", "x_mm", "y_mm", "gap_mm", "servo_deg"])
    for u in range(360):
        r = R(u)
        w.writerow([u, f"{r:.3f}", f"{r * math.sin(math.radians(u)):.3f}", f"{r * math.cos(math.radians(u)):.3f}",
                    f"{gap_at(u):.3f}", SERVO(u) if u <= 150 else ""])

CSS = """
@page { size: A4 landscape; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; background: #fff; color: #13201f; font-family: 'IBM Plex Sans Arabic', sans-serif }
.page { width: 297mm; height: 210mm; position: relative; overflow: hidden; page-break-after: always }
.page:last-child { page-break-after: auto }
svg.draw { position: absolute; inset: 0 }
.box { position: absolute; font-size: 8.4pt; line-height: 1.45 }
.box h3 { font-size: 9.5pt; margin: 0 0 1.2mm; font-weight: 600 }
.box ol, .box ul { margin: 0; padding-inline-start: 4.5mm }
.box li { margin-bottom: .9mm }
.num { font-family: 'IBM Plex Mono', monospace; direction: ltr; unicode-bidi: isolate }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; line-height: 1.25 }
th, td { border-bottom: .2mm solid #c9d3d1; padding: .35mm 1mm; text-align: center; font-family: 'IBM Plex Mono', monospace }
th { font-family: 'IBM Plex Sans Arabic', sans-serif; font-weight: 600; font-size: 7.4pt; background: #eef2f1 }
td.z { font-family: 'IBM Plex Sans Arabic', sans-serif }
.title { position: absolute; right: 8mm; bottom: 8mm; width: 104mm; border: .5mm solid #13201f; display: grid; grid-template-columns: 1fr 1fr; font-size: 8pt }
.title div { border: .2mm solid #13201f; padding: 1mm 2mm }
.title .name { grid-column: 1 / 3; font-size: 12pt; font-weight: 600 }
.title b { font-weight: 600; color: #4b5b5a; font-size: 7pt; display: block }
"""


def page(svg, boxes, title, sheet_no, scale):
    return (f'<section class="page">{svg}{boxes}<div class="title" dir="rtl"><div class="name">{title}</div>'
            f'<div><b>المشروع</b>صمام الكامة لجهاز مراقبة المغذي</div><div><b>اللوحة</b><span class="num">{sheet_no} / 2</span></div>'
            f'<div><b>المادة</b>PETG، حشوة 100%</div><div><b>المقياس</b><span class="num">{scale}</span>، الأبعاد بالملم</div>'
            f'<div style="grid-column:1/3"><b>الحالة</b>أبعاد السيرفو من مخطط TowerPro لهيكل MG945. تتأكد بالقياس: طول مسنن الشفت وقطر الأنبوب</div></div></section>')


cam_boxes = f"""
<div class="box" dir="rtl" style="right:12mm; top:13mm; width:62mm">
  <h3>نقاط الحافة</h3>
  <table><tr><th>u°</th><th>السيرفو°</th><th>R</th><th>الفتحة</th><th>الجريان%</th><th>المنطقة</th></tr>{table}</table>
  <div style="font-size:7.2pt; color:#4b5b5a; margin-top:1mm">R من محور الشفت. الفتحة بين الحافة ووجه الجسر عند هذه الزاوية. الجريان تقدير محسوب. كل درجة بالملف <span class="num" style="white-space:nowrap">cam-profile.csv</span>.</div>
</div>
<div class="box" dir="rtl" style="left:122mm; top:138mm; width:60mm">
  <h3>الطباعة والتركيب</h3>
  <ol>
    <li>اطبعها والوجه العلوي على السرير، ففتحة المسنن تطلع لفوق بدون دعامات.</li>
    <li>تنركب على مسنن الشفت مباشرة بدل الريشتين، وبرغي الريشتين يشدها من فوق.</li>
    <li>على <span class="num">90°</span> ركّبها بحيث علامة التركيب أقرب ما يكون للجسر. الفتح <span class="num">20°</span>، الضبط <span class="num">55°</span> إلى <span class="num">140°</span>، السد <span class="num">160°</span>.</li>
    <li>العلامات محفورة <span class="num">0.4</span> ملم على الوجه العلوي.</li>
  </ol>
</div>"""

bridge_boxes = f"""
<div class="box" dir="rtl" style="left:178mm; top:86mm; width:103mm">
  <h3>الطباعة والتركيب</h3>
  <ol>
    <li>اطبعه وظهر الجدار على السرير: الحافتين والضلعين والمشابك والقاعدة كلها تطلع لفوق، بدون دعامات.</li>
    <li>القاعدة تنحط على أذنين السيرفو، والأذنين على تبويبي حامل السيرفو من اردونك (<span class="num">ARD-080016</span>). أربع براغي <span class="num">M3 × 12</span> مع صواميل تمر بالجسر والأذنين والحامل. والحامل ينربط على اللوح من صفيحته الطويلة، فالشفت يطلع لبرة من اللوح.</li>
    <li>الفتحات الطويلة تسمح بتحريك الجسر <span class="num">1</span> ملم نحو الكامة أو بعيد عنها: اضبطه على السد الكامل وشد البراغي.</li>
    <li>الأنبوب ينكبس بين أصابع المشبكين (الفتحة <span class="num">4.2</span>، الإصبع <span class="num">3 × 1.5 × 4.9</span>)، ويمر بالمجرى بين الحافتين.</li>
    <li>الفتحات الطويلة <span class="num">{SLOT_W} × {SLOT_L}</span>. الضلعين سمكهن <span class="num">3</span> وارتفاعهن <span class="num">{RIB_TOP - 3:.1f}</span> فوق القاعدة.</li>
    <li>الخطوط المتقطعة الرفيعة للسيرفو والكامة والأنبوب، للتوضيح، ومو جزء من القطعة.</li>
  </ol>
</div>"""

html = f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><title>مخططات صمام الكامة</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{page(s1.svg(), cam_boxes, "القطعة 1: الكامة، بدل الريشتين", 1, "1.5 : 1")}
{page(s2.svg(), bridge_boxes, "القطعة 2: الجسر الثابت", 2, "1.5 : 1")}
</body></html>"""

(here / "drawings.html").write_text(html, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1123, "height": 794}, device_scale_factor=2)
    pg.goto((here / "drawings.html").as_uri())
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    pg.pdf(path=str(here / "cam-valve-drawings.pdf"), width="297mm", height="210mm", print_background=True)
    for i, el in enumerate(pg.query_selector_all(".page")):
        el.screenshot(path=str(here / f"sheet{i + 1}.png"))
    b.close()
print("R range", round(R(0), 2), round(R_MAX, 2), "reg gap", round(G_REG, 3), "R(90)", round(R(90), 2))
