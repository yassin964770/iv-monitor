# Figure 1: the IV bag monitor as built, front view, redrawn from the photo of the finished board.
# Positions are in centimetres on the board (30 x 55), taken from the photo after correcting its perspective.
# Writes fig1-board.html; render.py turns it into a PNG.

S = 24              # pixels per centimetre
BX, BY = 360, 40    # where the board's top-left corner sits on the page
W_PAGE, H_PAGE = 1480, 1600


def X(x): return BX + x * S
def Y(y): return BY + y * S
def P(x, y): return f"{X(x):.1f},{Y(y):.1f}"


def path(points, close=False):
    d = "M" + " L".join(P(*p) for p in points)
    return d + (" Z" if close else "")


def smooth(points):
    """Catmull-Rom through the points, as cubic Beziers."""
    pts = [(X(x), Y(y)) for x, y in points]
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def rect(x, y, w, h, **a):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
    return f'<rect x="{X(x):.1f}" y="{Y(y):.1f}" width="{w * S:.1f}" height="{h * S:.1f}" {attrs}/>'


svg = []
add = svg.append

# ---------- the board ----------
add(f'<polygon points="{X(0)+7},{Y(0)-7} {X(30)+7},{Y(0)-7} {X(30)+7},{Y(55)-7} {X(30)},{Y(55)} {X(30)},{Y(0)} {X(0)},{Y(0)}" fill="#C7A574"/>')
add(rect(0, 0, 30, 55, fill="url(#ply)", stroke="#A98B5F", stroke_width=1.5))
for i, (y0, amp) in enumerate([(4, .5), (11, .8), (19, .4), (27, .9), (33, .5), (41, .7), (49, .4)]):
    pts = [(x, y0 + amp * ((-1) ** (k + i)) * (0.6 if k % 2 else 1)) for k, x in enumerate(range(0, 31, 5))]
    add(f'<path d="{smooth(pts)}" fill="none" stroke="#C9A97A" stroke-width="1" opacity=".35"/>')
for cx, cy in [(12.5, 22.5), (21.5, 37.5), (12, 51.5)]:   # knots, as in the photo
    add(f'<ellipse cx="{X(cx)}" cy="{Y(cy)}" rx="{.45*S}" ry="{.3*S}" fill="none" stroke="#B98F5C" stroke-width="1.4" opacity=".7"/>')

# ---------- breadboard: two 830-point boards side by side ----------
def breadboard(x0, y0):
    w, h = 5.5, 16.5
    add(rect(x0, y0, w, h, fill="#F5F5F1", stroke="#CBCBC3", stroke_width=1.2, rx=3))
    for rx_ in (0.35, w - 0.95):   # power rails on both long edges
        add(f'<line x1="{X(x0+rx_)}" y1="{Y(y0+.4)}" x2="{X(x0+rx_)}" y2="{Y(y0+h-.4)}" stroke="#D9534F" stroke-width="1"/>')
        add(f'<line x1="{X(x0+rx_+.6)}" y1="{Y(y0+.4)}" x2="{X(x0+rx_+.6)}" y2="{Y(y0+h-.4)}" stroke="#3B6FB6" stroke-width="1"/>')
    add(rect(x0 + 2.62, y0 + .3, .26, h - .6, fill="#E4E4DD"))   # centre channel
    cols = [x0 + .5, x0 + .75, x0 + 4.75, x0 + 5.0] + [x0 + 1.25 + .254 * i for i in range(5)] + [x0 + 3.0 + .254 * i for i in range(5)]
    for cx in cols:
        n = 60
        for j in range(n):
            cy = y0 + .55 + j * (h - 1.1) / (n - 1)
            add(f'<rect x="{X(cx)-1.1:.1f}" y="{Y(cy)-1.1:.1f}" width="2.2" height="2.2" fill="#BDBDB4"/>')

breadboard(16.8, 5.6)
breadboard(22.3, 5.6)

# ---------- ESP32 DevKit (USB at the top, module at the bottom) ----------
ex, ey, ew, eh = 20.1, 5.9, 2.9, 5.3
add(rect(ex, ey, ew, eh, fill="#1D1E22", stroke="#0E0F11", stroke_width=1, rx=2))
for j in range(15):
    for px in (ex + .22, ex + ew - .22):
        add(f'<circle cx="{X(px):.1f}" cy="{Y(ey + .35 + j * .33):.1f}" r="2.1" fill="#C9A440"/>')
add(rect(ex + .45, ey + 2.6, 2.0, 2.45, fill="#C3C8CF", stroke="#9DA3AB", stroke_width=1, rx=1.5))
add(f'<text x="{X(ex+1.45)}" y="{Y(ey+3.95)}" class="chip">ESP32</text>')
add(rect(ex + .55, ey + 1.0, .45, .45, fill="#E9E9E9", rx=1))   # buttons
add(rect(ex + 1.9, ey + 1.0, .45, .45, fill="#E9E9E9", rx=1))
add(rect(ex + 1.1, ey - .25, .7, .55, fill="#B9BEC5", stroke="#8C9198", stroke_width=1))   # micro-USB socket
# USB cable to the ESP32: plug, then out over the top and down the right side
add(rect(ex + 1.0, 4.0, .9, 1.65, fill="#202022", rx=3))
usb_esp = [(21.45, 4.0), (21.7, 2.6), (23.5, 1.0), (26.4, 1.0), (28.2, 3.0), (29.1, 9.0), (28.6, 15.5), (26.4, 22.5), (24.4, 28.5), (24.3, 34.5), (25.0, 39.5), (24.5, 47.5), (22.2, 52.5), (21.6, 55.0)]

# ---------- OLED 0.96 in, pins on its top edge ----------
ox, oy = 24.3, 6.5
add(rect(ox, oy, 2.7, 2.8, fill="#22508E", stroke="#173A69", stroke_width=1, rx=2))
for i in range(4):
    add(f'<circle cx="{X(ox + .82 + i*.36):.1f}" cy="{Y(oy + .3):.1f}" r="2.3" fill="#C9A440"/>')
add(rect(ox + .12, oy + .65, 2.46, 1.85, fill="#0A0E13", rx=1))
for i, (t, sz) in enumerate([("292", 13), ("ml left", 6.5)]):
    add(f'<text x="{X(ox+1.35)}" y="{Y(oy + 1.55 + i*.6)}" font-size="{sz}" class="oled">{t}</text>')

# ---------- HX711 ----------
hx, hy = 20.3, 12.8
add(rect(hx, hy, 3.4, 2.1, fill="#2F7D4E", stroke="#215C39", stroke_width=1, rx=2))
for j in range(6):
    add(f'<circle cx="{X(hx + .22):.1f}" cy="{Y(hy + .25 + j*.32):.1f}" r="2" fill="#C9A440"/>')
for j in range(4):
    add(f'<circle cx="{X(hx + 3.18):.1f}" cy="{Y(hy + .5 + j*.36):.1f}" r="2" fill="#C9A440"/>')
add(rect(hx + 1.15, hy + .62, 1.1, .85, fill="#151515", rx=1))
add(f'<text x="{X(hx+1.7)}" y="{Y(hy+1.9)}" class="silk">HX711</text>')

# ---------- jumpers on the breadboard, tidied but following the photo ----------
def jumper(pts, color, w=2.6):
    if color == "#F2F2F2":
        add(f'<path d="{smooth(pts)}" fill="none" stroke="#9A9A9A" stroke-width="{w+1.2}" stroke-linecap="round"/>')
    add(f'<path d="{smooth(pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')

R, K, WH, G, B, O, BR = "#D0342C", "#262626", "#F2F2F2", "#2E9E57", "#2F6FD1", "#F08A24", "#7A4A2A"
# HX711 right side to the ESP32: VCC, GND, DT, SCK
jumper([(hx + 3.18, hy + .5), (24.6, 12.6), (23.6, 10.4), (22.78, 9.5)], R)
jumper([(hx + 3.18, hy + .86), (25.2, 13.2), (24.2, 11.2), (22.78, 10.8)], K)
jumper([(hx + 3.18, hy + 1.22), (24.4, 13.9), (21.0, 12.2), (20.32, 10.2)], G)
jumper([(hx + 3.18, hy + 1.58), (24.8, 14.9), (20.6, 12.6), (20.32, 9.6)], B)
# OLED pins (GND, VCC, SCL, SDA) to the ESP32
jumper([(ox + .82, oy + .3), (24.9, 5.5), (23.6, 6.1), (22.78, 7.1)], K)
jumper([(ox + 1.18, oy + .3), (25.4, 5.1), (21.2, 5.1), (20.32, 6.6)], R)
jumper([(ox + 1.54, oy + .3), (25.9, 5.3), (23.9, 6.6), (22.78, 6.4)], WH)
jumper([(ox + 1.90, oy + .3), (26.4, 5.6), (24.0, 7.4), (22.78, 6.75)], "#8E5BD6")
# ESP32 GND to the ground rail, joined with the servo's ground
jumper([(22.78, 11.0), (23.5, 15.8), (26.95, 18.8)], K)
# Load cell wires into the HX711's E+, E-, A-, A+
for i, (c, dy) in enumerate([(R, .25), (K, .57), (WH, .89), (G, 1.21)]):
    jumper([(15.6 + i*.12, 12.9 + i*.18), (18.0, 13.2 + i*.2), (19.4, hy + dy), (hx + .22, hy + dy)], c, 2.2)
# Servo lead on the breadboard: signal to GPIO 32, power to the rails fed by the cut USB cable
jumper([(23.4, 20.4), (21.6, 16.8), (20.32, 11.0)], O)
jumper([(23.7, 20.6), (26.0, 20.0), (26.95, 19.6)], R)
jumper([(24.0, 20.8), (26.6, 20.9), (27.55, 19.6)], BR)
add(rect(23.15, 20.1, 1.15, .55, fill="#1A1A1A", rx=1.5))   # servo connector seated in the board

# ---------- arm block and load cell (they stand out from the board, drawn in oblique) ----------
dx, dy = .32, -.26   # one centimetre of depth, going back into the board
def box(x, y, w, h, depth, front, top, side, stroke):
    bx, by = depth * dx, depth * dy
    add(f'<path d="{path([(x, y), (x+bx, y+by), (x+w+bx, y+by), (x+w, y)], True)}" fill="{top}" stroke="{stroke}" stroke-width="1"/>')
    add(f'<path d="{path([(x+w, y), (x+w+bx, y+by), (x+w+bx, y+h+by), (x+w, y+h)], True)}" fill="{side}" stroke="{stroke}" stroke-width="1"/>')
    add(rect(x, y, w, h, fill=front, stroke=stroke, stroke_width=1))

box(4.1, 7.3, 2.6, 2.7, 8, "#EBD7B0", "#F4E6C8", "#D5BA8A", "#B39566")          # arm block, 4 x 4 cm, screwed to the board
box(2.15, 8.55, 1.35, 1.35, 6.2, "#CDD2D8", "#E3E7EB", "#A9B0B8", "#8D949C")   # 3 kg bar, fixed end on the block, free end towards us
add(rect(2.3, 8.75, 1.05, .75, fill="#EAF4EA", stroke="#5B8E5B", stroke_width=.8))
add(f'<text x="{X(2.82)}" y="{Y(9.2)}" class="tiny" fill="#2F6B2F">3kg</text>')
add(f'<path d="M{X(2.82)},{Y(9.27)} l0,{.18*S} m-3,-3 l3,3 l3,-3" stroke="#2F6B2F" stroke-width=".9" fill="none"/>')
add(f'<rect x="{X(4.05)-3}" y="{Y(5.95)}" width="6" height="{.75*S}" fill="#9C9C9C"/>')   # bolt through the fixed end
add(f'<rect x="{X(4.05)-6}" y="{Y(5.85)}" width="12" height="4" rx="1" fill="#B5B5B5"/>')
# load cell cable: red, black, white, green, taped to the board on its way to the breadboard
lc = [(4.4, 6.9), (6.3, 6.4), (9.8, 8.5), (12.6, 9.6), (14.2, 11.4), (15.6, 12.9)]
for i, c in enumerate([R, K, WH, G]):
    jumper([(x + i*.1, y + i*.13) for x, y in lc], c, 1.9)
add(f'<path d="{path([(11.3, 14.4), (14.3, 8.9), (15.4, 9.45), (12.4, 14.95)], True)}" fill="#1C1C1C"/>')   # black tape strip
add(f'<path d="{path([(11.6, 14.25), (14.5, 9.05), (14.75, 9.18), (11.85, 14.38)], True)}" fill="#3A3A3A"/>')

# ---------- IV bottle, hung upside down from the free end of the load cell ----------
add(f'<path d="{smooth([(2.5, 9.9), (2.2, 10.9), (2.6, 11.9)])}" fill="none" stroke="#6E3FB0" stroke-width="2.4"/>')   # tie
add(f'<path d="{smooth([(3.1, 9.9), (3.5, 10.9), (3.0, 11.9)])}" fill="none" stroke="#6E3FB0" stroke-width="2.4"/>')
bt, bb_, bl, br_ = 12.0, 26.4, 0.4, 8.4
cx = (bl + br_) / 2
body = (f"M{X(cx-1.1)},{Y(bt)} C{X(cx-3.4)},{Y(bt+.1)} {X(bl)},{Y(bt+1.4)} {X(bl)},{Y(bt+3.6)} "
        f"L{X(bl)},{Y(bb_-3.4)} C{X(bl)},{Y(bb_-1.6)} {X(cx-1.6)},{Y(bb_-.9)} {X(cx-1.0)},{Y(bb_)} "
        f"L{X(cx+1.0)},{Y(bb_)} C{X(cx+1.6)},{Y(bb_-.9)} {X(br_)},{Y(bb_-1.6)} {X(br_)},{Y(bb_-3.4)} "
        f"L{X(br_)},{Y(bt+3.6)} C{X(br_)},{Y(bt+1.4)} {X(cx+3.4)},{Y(bt+.1)} {X(cx+1.1)},{Y(bt)} Z")
add(f'<clipPath id="bottle"><path d="{body}"/></clipPath>')
add(f'<path d="{body}" fill="#F3F8FB" stroke="#9FB4C2" stroke-width="1.4"/>')
add(f'<rect x="{X(bl)}" y="{Y(16.2)}" width="{(br_-bl)*S}" height="{(bb_-16.2)*S}" fill="#D3E8F3" clip-path="url(#bottle)"/>')   # about 290 ml left
add(f'<line x1="{X(bl)}" y1="{Y(16.2)}" x2="{X(br_)}" y2="{Y(16.2)}" stroke="#A9CDE0" stroke-width="1.2" clip-path="url(#bottle)"/>')
add(rect(bl + .35, 18.6, br_ - bl - .7, 5.0, fill="#FFFFFF", stroke="#D9C9CC", stroke_width=.8, opacity=.95))
add(rect(bl + .35, 22.8, br_ - bl - .7, .8, fill="#E9B8C3", opacity=.9))
add(f'<text x="{X(cx)}" y="{Y(19.6)}" class="label-tiny">Sodium Chloride 0.9%</text>')
add(f'<text x="{X(cx)}" y="{Y(20.4)}" class="label-tiny" fill="#7B8A94">500 ml  IV infusion</text>')
add(f'<path d="M{X(cx-2.6)},{Y(bt+1.2)} C{X(bl+.5)},{Y(bt+2.5)} {X(bl+.6)},{Y(16)} {X(bl+.6)},{Y(17)}" stroke="#FFFFFF" stroke-width="5" fill="none" opacity=".8"/>')
add(rect(cx - .95, 26.3, 1.9, 1.0, fill="#E9EEF2", stroke="#9FB4C2", stroke_width=1, rx=2))   # cap
add(rect(cx - .3, 27.25, .6, .9, fill="#EEF2F5", stroke="#9FB4C2", stroke_width=1))           # spike
add(rect(cx - .55, 28.1, 1.1, 4.4, fill="#F4F9FC", stroke="#9FB4C2", stroke_width=1.2, rx=4))   # drip chamber
add(rect(cx - .5, 31.0, 1.0, 1.45, fill="#D3E8F3", rx=3))
add(f'<ellipse cx="{X(cx)}" cy="{Y(29.6)}" rx="2.6" ry="3.4" fill="#BFDDEC"/>')
add(rect(cx - .15, 32.45, .3, .5, fill="#9FB4C2"))

# ---------- tube: drip chamber, across the board, through the pinch, down to the patient ----------
tube = [(cx, 32.9), (cx + .3, 34.6), (8.4, 36.0), (12.0, 35.8), (16.2, 36.3), (18.6, 37.9), (19.85, 40.0), (19.6, 43.5), (18.0, 47.5), (16.0, 51.5), (15.3, 55.0), (15.2, 58.5)]
add(f'<path d="{smooth(tube)}" fill="none" stroke="#A9BFCB" stroke-width="7" stroke-linecap="round"/>')
add(f'<path d="{smooth(tube)}" fill="none" stroke="#EEF6FA" stroke-width="4" stroke-linecap="round"/>')

# ---------- anvil block and servo (the pinch valve) ----------
box(19.1, 37.4, 4.1, 9.6, 3, "#EBD7B0", "#F4E6C8", "#D5BA8A", "#B39566")
# the tube passes in front of the block, where the servo horn presses it
add(f'<path d="{smooth(tube[5:9])}" fill="none" stroke="#A9BFCB" stroke-width="7" stroke-linecap="round"/>')
add(f'<path d="{smooth(tube[5:9])}" fill="none" stroke="#EEF6FA" stroke-width="4" stroke-linecap="round"/>')
sx, sy = 21.0, 41.6
add(rect(sx - .65, sy + .55, 5.7, .9, fill="#2A2A2A", rx=2))       # mounting tabs
for hxp in (sx - .35, sx + 4.75):
    add(f'<circle cx="{X(hxp)}" cy="{Y(sy+1.0)}" r="3" fill="#EBD7B0"/>')
add(rect(sx, sy, 4.4, 4.1, fill="#232323", stroke="#111", stroke_width=1, rx=3))
add(rect(sx + 2.3, sy + 1.4, 1.7, .9, fill="#C9D86A", rx=1))       # sticker
add(f'<text x="{X(sx+3.15)}" y="{Y(sy+2.02)}" class="tiny" fill="#2D2D2D">SERVO</text>')
add(f'<circle cx="{X(sx+1.0)}" cy="{Y(sy+1.0)}" r="{.55*S}" fill="#3A3A3A" stroke="#111" stroke-width="1"/>')
add(f'<path d="M{X(sx+1.0)},{Y(sy+1.0)} L{X(sx-.45)},{Y(sy-1.05)}" stroke="#2C2C2C" stroke-width="{.55*S}" stroke-linecap="round"/>')   # horn, pressing the tube
add(f'<circle cx="{X(sx+1.0)}" cy="{Y(sy+1.0)}" r="3.5" fill="#9A9A9A"/>')
# servo lead: brown, red, orange, up the board to the tape
sl = [(sx, sy + 3.5), (17.4, 44.6), (15.0, 41.0), (14.3, 35.5), (15.6, 30.6), (18.9, 27.6)]
for i, c in enumerate([BR, R, O]):
    jumper([(x + i*.12, y - i*.1) for x, y in sl], c, 2.0)

# ---------- USB cables and the taped bundle ----------
cut = [(20.6, 55.0), (22.4, 50.2), (22.9, 42.5), (22.2, 35.5), (20.3, 30.6), (19.3, 27.6)]
for pts in (cut, usb_esp):
    add(f'<path d="{smooth(pts)}" fill="none" stroke="#151515" stroke-width="5.5" stroke-linecap="round"/>')
    add(f'<path d="{smooth(pts)}" fill="none" stroke="#3C3C3C" stroke-width="1.4" stroke-linecap="round" opacity=".7"/>')
add(f'<path d="{smooth([(18.9, 28.6), (19.6, 26.6), (21.4, 24.0), (23.0, 21.4), (23.6, 20.6)])}" fill="none" stroke="#1B1B1B" stroke-width="{.95*S}" stroke-linecap="round"/>')   # tape over servo lead and cut cable
add(f'<path d="{smooth([(19.25, 27.9), (19.9, 26.4), (21.5, 24.1), (23.1, 21.5)])}" fill="none" stroke="#3B3B3B" stroke-width="2" stroke-linecap="round" opacity=".8"/>')

# ---------- below the board: the power source ----------
add(f'<path d="{smooth([(21.6, 55.0), (21.2, 57.5), (21.6, 59.6)])}" fill="none" stroke="#151515" stroke-width="5.5"/>')
add(f'<path d="{smooth([(20.6, 55.0), (19.6, 57.4), (19.6, 59.6)])}" fill="none" stroke="#151515" stroke-width="5.5"/>')
add(rect(16.6, 60.2, 8.6, 3.6, fill="#3A3D42", stroke="#24262A", stroke_width=1.2, rx=8))
for ux in (18.95, 20.95):
    add(rect(ux, 59.55, 1.3, .75, fill="#202020", rx=1.5))
add(f'<circle cx="{X(24.3)}" cy="{Y(62)}" r="3" fill="#6BD48A"/>')

# ---------- labels ----------
# (side, label top y in px, target point in cm, English, Arabic)
labels = [
    ("L", 168, (2.8, 9.0), "Load cell, 3 kg", "خلية الحمل، 3 كغم"),
    ("L", 250, (6.1, 9.5), "Wooden arm holding the load cell", "ذراع خشبي يحمل خلية الحمل"),
    ("L", 470, (1.2, 17.5), "IV bottle, hung from the load cell", "قنينة المحلول، معلّقة بخلية الحمل"),
    ("L", 735, (cx - .55, 30.3), "Drip chamber", "حجرة التنقيط"),
    ("L", 900, (8.4, 36.0), "IV tube", "أنبوب المحلول"),
    ("L", 1424, (15.2, 58.4), "To the patient", "إلى المريض"),
    ("R", 52, (21.45, 4.6), "USB cable to the ESP32", "كيبل USB للـESP32"),
    ("R", 150, (25.65, 8.0), "OLED screen, 0.96 in", "شاشة OLED بقياس 0.96 إنش"),
    ("R", 236, (22.95, 10.4), "ESP32 microcontroller", "المتحكم ESP32"),
    ("R", 322, (22.9, 14.1), "HX711 amplifier", "مضخّم الإشارة HX711"),
    ("R", 408, (27.2, 16.5), "Breadboard", "لوحة التوصيل"),
    ("R", 600, (21.2, 25.0), "Servo lead and power wires, taped", "سلك السيرفو وسلك التغذية، مثبّتان بشريط"),
    ("R", 800, (19.8, 40.0), "Pinch point: the horn presses the tube", "نقطة الضغط: ذراع السيرفو يعصر الأنبوب"),
    ("R", 1010, (24.6, 44.6), "Servo motor, the valve", "محرك سيرفو يعمل كصمام"),
    ("R", 905, (22.3, 39.2), "Wooden block behind the tube", "قطعة خشب خلف الأنبوب"),
    ("R", 1180, (22.85, 47.0), "Cut USB cable: 5 V and GND for the servo", "كيبل USB مقصوص: 5 فولت والأرضي للسيرفو"),
    ("R", 1440, (25.2, 61.6), "Power bank, or a USB charger with two ports", "باور بانك، أو شاحن USB بمنفذين"),
]
leaders, notes = [], []
for side, top, (tx, ty), en, ar in labels:
    ly = top + 20
    if side == "L":
        ax = BX - 26
        notes.append(f'<div class="lab left" style="top:{top}px;right:{W_PAGE - ax + 8}px"><b>{en}</b><span>{ar}</span></div>')
    else:
        ax = BX + 30 * S + 26
        notes.append(f'<div class="lab right" style="top:{top}px;left:{ax + 8}px"><b>{en}</b><span>{ar}</span></div>')
    leaders.append(f'<polyline points="{ax},{ly} {ax + (12 if side == "L" else -12)},{ly} {X(tx):.1f},{Y(ty):.1f}" fill="none" stroke="#3B3B3B" stroke-width="1.1"/>')
    leaders.append(f'<circle cx="{X(tx):.1f}" cy="{Y(ty):.1f}" r="3.2" fill="#3B3B3B" stroke="#FFFFFF" stroke-width="1.2"/>')

html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@400;500&display=swap" rel="stylesheet">
<style>
  html,body{{margin:0;background:#fff}}
  .page{{position:relative;width:{W_PAGE}px;height:{H_PAGE}px;background:#fff;font-family:'IBM Plex Sans',sans-serif;color:#1F1F1F}}
  svg{{position:absolute;inset:0}}
  .lab{{position:absolute;width:330px;line-height:1.25}}
  .lab b{{display:block;font-weight:600;font-size:16px;letter-spacing:-.005em}}
  .lab span{{display:block;font-family:'IBM Plex Sans Arabic',sans-serif;font-size:15px;color:#555;direction:rtl}}
  .left{{text-align:right}} .left span{{text-align:right}}
  .right{{text-align:left}} .right span{{text-align:left}}
  .chip{{font:600 9px 'IBM Plex Sans';fill:#5E646C;text-anchor:middle}}
  .silk{{font:600 7px 'IBM Plex Sans';fill:#E8F2EA;text-anchor:middle}}
  .oled{{font-family:'IBM Plex Sans';font-weight:600;fill:#DCEBFF;text-anchor:middle}}
  .tiny{{font:600 6.5px 'IBM Plex Sans';text-anchor:middle}}
  .label-tiny{{font:600 8.5px 'IBM Plex Sans';fill:#B04A63;text-anchor:middle}}
</style></head><body>
<div class="page">
<svg width="{W_PAGE}" height="{H_PAGE}" viewBox="0 0 {W_PAGE} {H_PAGE}">
<defs><linearGradient id="ply" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#EBD3A8"/><stop offset="1" stop-color="#DFC191"/></linearGradient></defs>
{chr(10).join(svg)}
{chr(10).join(leaders)}
</svg>
{chr(10).join(notes)}
</div></body></html>"""
open(__file__.replace("make_fig1.py", "fig1-board.html"), "w", encoding="utf-8").write(html)
print("fig1-board.html written")
