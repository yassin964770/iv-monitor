# Figure 2: wiring diagram of the IV bag monitor as built (no buzzer, LEDs or button: they are not on the board).
# Pins from the firmware: HX711 DT 18, SCK 19; OLED SDA 21, SCL 22 on 3V3; servo signal 32.
# Power: one USB cable into the ESP32; a second USB cable, cut, gives the servo 5 V and GND. Grounds joined.
W_PAGE, H_PAGE = 1480, 1000
UP = 150   # everything is drawn 150 px lower than it shows, then lifted
svg, notes = [], []
add = svg.append

R, K, WH, G, B, PU, O, BR = "#D0342C", "#262626", "#F2F2F2", "#2E9E57", "#2F6FD1", "#8E5BD6", "#F08A24", "#7A4A2A"


def wire(points, color, w=3.4):
    pts = " ".join(f"{x},{y}" for x, y in points)
    if color == WH:
        add(f'<polyline points="{pts}" fill="none" stroke="#8C8C8C" stroke-width="{w + 1.6}" stroke-linejoin="round" stroke-linecap="round"/>')
    add(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>')


def dot(x, y, c=K):
    add(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{c}" stroke="#fff" stroke-width="1.5"/>')


def pin(x, y, name, side, fill="#fff"):
    """A pin on a component edge, its name inside the component."""
    add(f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1.5" fill="#D4AF37" stroke="#8A6D1A" stroke-width="1"/>')
    tx = x + 12 if side == "L" else x - 12
    anchor = "start" if side == "L" else "end"
    if side == "B":
        add(f'<text x="{x}" y="{y - 13}" class="pin" fill="{fill}" text-anchor="middle">{name}</text>')
    else:
        add(f'<text x="{tx}" y="{y + 5}" class="pin" fill="{fill}" text-anchor="{anchor}">{name}</text>')


def title(x, y, en, ar, anchor="middle", width=260):
    left = {"middle": x - width / 2, "start": x, "end": x - width}[anchor]
    align = {"middle": "center", "start": "left", "end": "right"}[anchor]
    notes.append(f'<div class="ttl" style="left:{left}px;top:{y}px;width:{width}px;text-align:{align}"><b>{en}</b><span>{ar}</span></div>')


# ---------- buses ----------
add('<line x1="580" y1="210" x2="1020" y2="210" stroke="#D0342C" stroke-width="5" stroke-linecap="round"/>')
add('<line x1="570" y1="1035" x2="1220" y2="1035" stroke="#262626" stroke-width="5" stroke-linecap="round"/>')
add('<text x="1032" y="216" class="bus" fill="#B02A23">3.3 V</text>')
add('<text x="1232" y="1041" class="bus" fill="#262626">GND</text>')

# ---------- load cell ----------
add('<rect x="70" y="428" width="200" height="56" rx="4" fill="url(#alu)" stroke="#8D949C" stroke-width="1.4"/>')
add('<rect x="140" y="436" width="62" height="40" rx="3" fill="#B7BEC6" stroke="#8D949C" stroke-width="1"/>')
for cx in (92, 114, 226, 248):
    add(f'<circle cx="{cx}" cy="456" r="6.5" fill="#fff" stroke="#8D949C" stroke-width="1.2"/>')
add('<rect x="150" y="443" width="42" height="26" rx="2" fill="#EAF4EA" stroke="#5B8E5B" stroke-width="1"/>')
add('<text x="171" y="461" class="pin" fill="#2F6B2F" text-anchor="middle">3 kg</text>')
title(170, 360, "Load cell, 3 kg", "خلية الحمل، 3 كغم")
lc_colors = [(R, "E+"), (K, "E−"), (WH, "A−"), (G, "A+")]
for i, (c, _) in enumerate(lc_colors):
    y0, py, vx = 440 + 12 * i, 420 + 40 * i, 320 - 10 * i
    wire([(270, y0), (vx, y0), (vx, py), (340, py)], c, 3)

# ---------- HX711 ----------
add('<rect x="340" y="380" width="200" height="220" rx="8" fill="#2F7D4E" stroke="#215C39" stroke-width="1.5"/>')
add('<rect x="405" y="455" width="70" height="70" rx="3" fill="#151515"/>')
add('<text x="440" y="580" class="silk" text-anchor="middle">HX711</text>')
for i, (_, n) in enumerate(lc_colors):
    pin(340, 420 + 40 * i, n, "L")
for y, n in [(420, "VCC"), (470, "DT"), (530, "SCK"), (570, "GND")]:
    pin(540, y, n, "R")
title(440, 300, "HX711 amplifier", "مضخّم الإشارة HX711")

# ---------- ESP32 ----------
add('<rect x="680" y="300" width="220" height="480" rx="10" fill="#1D1E22" stroke="#0E0F11" stroke-width="1.5"/>')
add('<rect x="735" y="565" width="90" height="180" rx="6" fill="url(#can)" stroke="#9DA3AB" stroke-width="1.2"/>')
add('<text x="780" y="700" class="chip" text-anchor="middle">ESP32</text>')
add('<rect x="756" y="770" width="68" height="22" rx="3" fill="#B9BEC5" stroke="#8C9198" stroke-width="1"/>')   # micro-USB
add('<text x="790" y="764" class="pin" fill="#C8CCD2" text-anchor="middle">micro-USB</text>')
for y, n in [(380, "3V3"), (470, "GPIO 18"), (530, "GPIO 19"), (640, "GND")]:
    pin(680, y, n, "L")
for y, n in [(420, "GPIO 22"), (480, "GPIO 21"), (650, "GPIO 32")]:
    pin(900, y, n, "R")
title(790, 226, "ESP32 microcontroller", "المتحكم ESP32")

# ---------- OLED ----------
add('<rect x="1060" y="330" width="200" height="230" rx="8" fill="#22508E" stroke="#173A69" stroke-width="1.5"/>')
add('<rect x="1120" y="350" width="124" height="190" rx="4" fill="#0A0E13"/>')
add('<text x="1182" y="440" class="oled" font-size="40" text-anchor="middle">292</text>')
add('<text x="1182" y="468" class="oled" font-size="15" text-anchor="middle">ml left</text>')
for y, n in [(370, "VCC"), (420, "SCL"), (480, "SDA")]:
    pin(1060, y, n, "L")
pin(1220, 560, "GND", "B")
title(1160, 254, "OLED screen, 0.96 in", "شاشة OLED بقياس 0.96 إنش")

# ---------- servo ----------
add('<rect x="1028" y="668" width="174" height="22" rx="4" fill="#2A2A2A"/>')   # mounting tabs
for hx in (1040, 1190):
    add(f'<circle cx="{hx}" cy="679" r="5" fill="#fff"/>')
add('<rect x="1046" y="630" width="138" height="112" rx="8" fill="#232323" stroke="#111" stroke-width="1.5"/>')
add('<circle cx="1090" cy="660" r="17" fill="#3A3A3A" stroke="#111" stroke-width="1.2"/>')
add('<line x1="1090" y1="660" x2="1060" y2="616" stroke="#2C2C2C" stroke-width="13" stroke-linecap="round"/>')
add('<circle cx="1090" cy="660" r="5" fill="#9A9A9A"/>')
add('<rect x="1118" y="700" width="56" height="24" rx="2" fill="#C9D86A"/>')
add('<text x="1146" y="717" class="pin" fill="#2D2D2D" text-anchor="middle">SERVO</text>')
title(1352, 640, "Servo motor, the valve", "محرك سيرفو يعمل كصمام", width=220)

# ---------- power source and the two USB cables ----------
add('<rect x="700" y="842" width="200" height="86" rx="14" fill="#3A3D42" stroke="#24262A" stroke-width="1.5"/>')
add('<circle cx="880" cy="910" r="4" fill="#6BD48A"/>')
for ux in (740, 830):
    add(f'<rect x="{ux}" y="830" width="40" height="16" rx="2" fill="#1C1C1C"/>')
title(800, 940, "Power bank or 2-port USB charger", "باور بانك أو شاحن USB بمنفذين", width=320)
# cable 1: into the ESP32's micro-USB
add('<polyline points="760,830 760,806 790,806 790,792" fill="none" stroke="#151515" stroke-width="8" stroke-linejoin="round"/>')
# cable 2: cut, its red and black wires out of the sheath
add('<polyline points="850,830 850,806 930,806" fill="none" stroke="#151515" stroke-width="8" stroke-linejoin="round"/>')
add('<rect x="926" y="799" width="16" height="14" rx="2" fill="#151515"/>')
wire([(942, 802), (970, 802), (970, 685), (1046, 685)], R)
wire([(942, 810), (948, 810), (948, 1035)], K)
add('<text x="958" y="770" class="pin" fill="#B02A23" text-anchor="end">5 V</text>')
notes.append('<div class="ttl small" style="left:1014px;top:766px;width:200px;text-align:left"><b>Cut USB cable</b><span>كيبل USB مقصوص</span></div>')

# ---------- signal and supply wires ----------
wire([(540, 420), (580, 420), (580, 210)], R)              # HX711 VCC
wire([(540, 470), (680, 470)], G)                          # DT
wire([(540, 530), (680, 530)], B)                          # SCK
wire([(540, 570), (570, 570), (570, 1035)], K)              # HX711 GND
wire([(680, 380), (620, 380), (620, 210)], R)              # ESP32 3V3 out
wire([(680, 640), (640, 640), (640, 1035)], K)              # ESP32 GND
wire([(900, 420), (1060, 420)], WH)                        # SCL
wire([(900, 480), (1060, 480)], PU)                        # SDA
wire([(1060, 370), (1020, 370), (1020, 210)], R)           # OLED VCC
wire([(1220, 560), (1220, 1035)], K)                        # OLED GND
wire([(900, 650), (1046, 650)], O)                         # servo signal
wire([(1046, 715), (1000, 715), (1000, 1035)], BR)          # servo ground (brown)
for x, y in [(580, 210), (620, 210), (1020, 210)]:
    dot(x, y, R)
for x in (570, 640, 948, 1000, 1220):
    dot(x, 1035)

# wire names, on the wires
for x, y, t in [(610, 462, "DT"), (610, 522, "SCK"), (980, 412, "SCL"), (980, 472, "SDA"), (975, 642, "Signal")]:
    add(f'<text x="{x}" y="{y}" class="wl" text-anchor="middle">{t}</text>')
# servo lead colours where they leave the servo
for y, t in [(650, "orange"), (685, "red"), (715, "brown")]:
    pass

notes.append('<div class="foot">'
             '<p><b>The servo takes 5 V straight from the second USB cable, not from the ESP32.</b>'
             '<span>السيرفو يأخذ 5 فولت مباشرة من كيبل USB الثاني، وليس من متحكم ESP32.</span></p>'
             '<p><b>All grounds are joined: ESP32, HX711, screen, servo and the cut cable.</b>'
             '<span>كل الأرضيات موصولة ببعض: ESP32 وHX711 والشاشة والسيرفو والكيبل المقصوص.</span></p>'
             '</div>')

html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@400;500&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  html,body{{margin:0;background:#fff}}
  .page{{position:relative;width:{W_PAGE}px;height:{H_PAGE}px;background:#fff;font-family:'IBM Plex Sans',sans-serif;color:#1F1F1F}}
  svg{{position:absolute;inset:0}}
  .ttl{{position:absolute;line-height:1.25}}
  .ttl b{{display:block;font-weight:600;font-size:17px}}
  .ttl span{{display:block;font-family:'IBM Plex Sans Arabic',sans-serif;font-size:15px;color:#555;direction:rtl}}
  .ttl.small b{{font-size:14px}} .ttl.small span{{font-size:13px}}
  .pin{{font:500 13px 'IBM Plex Mono',monospace}}
  .bus{{font:600 16px 'IBM Plex Sans'}}
  .wl{{font:500 12.5px 'IBM Plex Mono',monospace;fill:#555}}
  .chip{{font:600 20px 'IBM Plex Sans';fill:#5E646C}}
  .silk{{font:600 18px 'IBM Plex Sans';fill:#E8F2EA}}
  .oled{{font-family:'IBM Plex Sans';font-weight:600;fill:#DCEBFF}}
  .foot{{position:absolute;left:70px;top:1080px;width:1340px;display:flex;gap:60px}}
  .foot p{{margin:0;flex:1;line-height:1.3}}
  .foot b{{display:block;font-weight:500;font-size:15px}}
  .foot span{{display:block;font-family:'IBM Plex Sans Arabic',sans-serif;font-size:14px;color:#555;direction:rtl;text-align:left}}
</style></head><body>
<div class="page">
<svg width="{W_PAGE}" height="{H_PAGE}" viewBox="0 {UP} {W_PAGE} {H_PAGE}">
<defs>
<linearGradient id="alu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6E9ED"/><stop offset="1" stop-color="#BCC2C9"/></linearGradient>
<linearGradient id="can" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D3D7DC"/><stop offset="1" stop-color="#B3B9C0"/></linearGradient>
</defs>
{chr(10).join(svg)}
</svg>
<div style="position:absolute;left:0;top:-{UP}px;width:100%;height:100%">
{chr(10).join(notes)}
</div>
</div></body></html>"""
open(__file__.replace("make_fig2.py", "fig2-wiring.html"), "w", encoding="utf-8").write(html)
print("fig2-wiring.html written")
