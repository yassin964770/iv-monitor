# Sizes and the cam profile of the cam valve, shared by the drawings (make_drawings.py) and the printable parts
# (make_parts.py). All in mm.
#
# The servo is the TowerPro MG945 sold by Ardunic (ARD-001743): 40.7 x 19.7 x 42.9 mm, TowerPro's standard case.
# TowerPro's drawing of that case (on the MG996R sheet) gives: body 40.3 long and 20 wide, 53.6 across the ears,
# ears' top face 26.6 above the bottom, case top 36.6, spline top 42.9. So, from the ears' top face: case top +10,
# spline top +16.3. Read off the same drawing by proportion (not printed on it): the shaft sits 9.75 off the body's
# centre, and the ear notches 24.1 from the centre along the body and 5.3 either side across it. Assumed, not on any
# drawing: a 4 mm long 25T spline (so the boss top, where the cam rests, is at +12.3) and the 4.1 mm tube.
import math

OD, WALL = 4.1, .55
WF = math.pi * OD / 2
D = 27.6                       # shaft axis to the pressing face
CX = 9.75                      # shaft axis from the servo body's centre
CAM_Y, CAM_T = 12.3, 7.0       # cam underside, resting on the output gear's collar, above the ears' top face; cam thickness
TUBE_Y = CAM_Y + CAM_T / 2
# The cam goes straight onto the servo's output spline, in place of the two-arm horn: a 25-tooth hole with 0.1 mm play
# (MG945, like the MG995/MG996R, has a 25T spline about 5.9 mm across), held by the horn's own screw through the bore.
SPL_N, SPL_RO, SPL_RI, SPL_D = 25, 3.05, 2.80, 4.2
BORE = 3.2


def spline_pts():
    return [((SPL_RO if i % 2 == 0 else SPL_RI) * math.cos(math.pi * i / SPL_N), (SPL_RO if i % 2 == 0 else SPL_RI) * math.sin(math.pi * i / SPL_N))
            for i in range(2 * SPL_N)]


def squeeze(gap):
    h = min(OD, max(gap, .85))
    f = min(1.05, max(0, (OD - h) / (OD - 2 * WALL)))
    w = OD + f * (WF - OD)
    return h, w, max(0, h - 2 * WALL), max(0, w - 2 * WALL)


PINCH = .002
k_of = lambda a, b: (a * b) ** 3 / (a * a + b * b) if a > 0 and b > 0 else 0
K_OPEN = k_of((OD - 2 * WALL) / 2, (OD - 2 * WALL) / 2)


def raw_flow(gap):
    _, _, hin, win = squeeze(gap)
    k = k_of(win / 2, hin / 2)
    return 1 / (1 + PINCH * K_OPEN / k) if k else 0


FULL = raw_flow(4.6)
flow = lambda gap: raw_flow(gap) / FULL


def gap_for(q):
    if q <= 0:
        return 2 * WALL
    lo, hi = 2 * WALL, 4.6
    for _ in range(50):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if flow(m) < q else (lo, m)
    return (lo + hi) / 2


sstep = lambda t: t * t * (3 - 2 * t)
G_REG = gap_for(.95)


def gap_at(u):
    u %= 360
    if u < 15: return 4.6
    if u < 45: return 4.6 + (G_REG - 4.6) * sstep((u - 15) / 30)
    if u < 130: return gap_for(.95 * (1 - (u - 45) / 85))
    if u < 135: return 1.1 - .1 * (u - 130) / 5
    if u < 139: return 1 - .15 * (u - 135) / 4
    if u < 143: return .85 + .15 * (u - 139) / 4
    if u < 160: return 1
    if u < 230: return 1 + 3.6 * sstep((u - 160) / 70)
    return 4.6


R = lambda u: D - gap_at(u)
R_MAX = max(R(u / 2) for u in range(720))

# Servo angle = u + 10: the mark u = 80 faces the bridge at servo 90; open at 20, regulating 55 to 140, shut at 160.
SERVO = lambda u: u + 10


# ---------- the bridge (x along the servo, y up from the ears' top face, z from the shaft towards the wall) ----------
XL, XR, WIN = -26.8, 38, 20.65    # plate ends (the left one at the ear's end), half-length of the window round the servo's top
ZB, ZW = -10, 10.3                # plate back edge (the ears' far side), window's front edge (0.3 clear of the body)
WT, LIP, LIPD = 4, 3, 4           # wall thickness, lip thickness, how far the lips stand out
CH0, CH1 = TUBE_Y - 4, TUBE_Y + 4 # the channel
TOP = CH1 + LIP
WX0, WX1 = -16, 36                # wall ends
FING = [CX - 22, CX + 22]         # clip fingers
HOLE_X, HOLE_Z = 24.1, 5.3        # the ears' screw notches
SLOTS = [(-HOLE_X, HOLE_Z), (-HOLE_X, -HOLE_Z), (HOLE_X, HOLE_Z), (HOLE_X, -HOLE_Z)]
SLOT_W, SLOT_L = 3.8, 5.8         # wide enough for an M3 screw with 0.4 mm either way; 1 mm of travel towards and away from the cam
RIBS = [-16, 33]
RIB_TOP = CH0 - LIP              # ribs run up to the lower lip
