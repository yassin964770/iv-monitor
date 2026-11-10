# Figure 3 (proposed, not built yet): a green and a red light and a buzzer for the amount left, in the style of fig2.
# Pins are the ones the firmware already sets aside: green GPIO 26, red GPIO 27, buzzer GPIO 25. Only one light is on at
# a time; each LED still has its own 220 ohm resistor (about 5 to 6 mA from 3.3 V). The buzzer
# is a small active buzzer straight on the pin, no transistor: it beeps by itself when the pin is high.
W_PAGE, H_PAGE = 1480, 860
svg, notes = [], []
add = svg.append

R, K, G, O = "#D0342C", "#262626", "#2E9E57", "#F08A24"


def wire(points, color, w=3.4):
    pts = " ".join(f"{x},{y}" for x, y in points)
    add(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>')


def dot(x, y, c=K):
    add(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{c}" stroke="#fff" stroke-width="1.5"/>')


def pin(x, y, name, side, fill="#fff"):
    add(f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1.5" fill="#D4AF37" stroke="#8A6D1A" stroke-width="1"/>')
    tx, anchor = (x + 12, "start") if side == "L" else (x - 12, "end")
    add(f'<text x="{tx}" y="{y + 5}" class="pin" fill="{fill}" text-anchor="{anchor}">{name}</text>')


def title(x, y, en, ar, anchor="middle", width=260, small=False):
    left = {"middle": x - width / 2, "start": x, "end": x - width}[anchor]
    align = {"middle": "center", "start": "left", "end": "right"}[anchor]
    cls = "ttl small" if small else "ttl"
    notes.append(f'<div class="{cls}" style="left:{left}px;top:{y}px;width:{width}px;text-align:{align}"><b>{en}</b><span>{ar}</span></div>')


def resistor(x, y, bands, label):
    """A through-hole resistor lying along x, centred on (x, y)."""
    add(f'<line x1="{x - 52}" y1="{y}" x2="{x + 52}" y2="{y}" stroke="#9AA0A6" stroke-width="3"/>')
    add(f'<rect x="{x - 34}" y="{y - 12}" width="68" height="24" rx="10" fill="#E9D3A8" stroke="#B89B62" stroke-width="1.2"/>')
    for i, c in enumerate(bands):
        add(f'<rect x="{x - 22 + i * 12}" y="{y - 12}" width="6" height="24" fill="{c}"/>')
    add(f'<text x="{x}" y="{y - 20}" class="pin" fill="#444" text-anchor="middle">{label}</text>')


def led(x, y, color, glow):
    """An LED seen from the side: dome, rim, legs to the left (anode, long) and right (cathode, short)."""
    add(f'<circle cx="{x}" cy="{y}" r="30" fill="{glow}" opacity=".35"/>')
    add(f'<path d="M{x - 16} {y + 14} L{x - 16} {y - 4} A16 16 0 0 1 {x + 16} {y - 4} L{x + 16} {y + 14} Z" fill="{color}" stroke="#00000033" stroke-width="1"/>')
    add(f'<rect x="{x - 20}" y="{y + 12}" width="40" height="6" rx="2" fill="{color}" stroke="#00000033" stroke-width="1"/>')
    add(f'<ellipse cx="{x - 6}" cy="{y - 6}" rx="4" ry="7" fill="#fff" opacity=".55"/>')
    add(f'<text x="{x - 30}" y="{y + 36}" class="pm" text-anchor="middle">+</text>')
    add(f'<text x="{x + 30}" y="{y + 36}" class="pm" text-anchor="middle">−</text>')


# ---------- ground bus ----------
GND_Y = 700
add(f'<line x1="300" y1="{GND_Y}" x2="1330" y2="{GND_Y}" stroke="{K}" stroke-width="5" stroke-linecap="round"/>')
add(f'<text x="1342" y="{GND_Y + 6}" class="bus" fill="{K}">GND</text>')

# ---------- ESP32 ----------
EX0, EX1, EY0, EY1 = 380, 600, 160, 640
add(f'<rect x="{EX0}" y="{EY0}" width="{EX1 - EX0}" height="{EY1 - EY0}" rx="10" fill="#1D1E22" stroke="#0E0F11" stroke-width="1.5"/>')
add('<rect x="435" y="400" width="90" height="180" rx="6" fill="url(#can)" stroke="#9DA3AB" stroke-width="1.2"/>')
add('<text x="480" y="535" class="chip" text-anchor="middle">ESP32</text>')
add(f'<rect x="456" y="{EY1 - 2}" width="68" height="22" rx="3" fill="#B9BEC5" stroke="#8C9198" stroke-width="1"/>')
add(f'<text x="490" y="{EY1 - 10}" class="pin" fill="#C8CCD2" text-anchor="middle">micro-USB</text>')
pin(EX0, 590, "GND", "L")
PINS = {"g": (260, "GPIO 26"), "r": (360, "GPIO 27"), "bz": (500, "GPIO 25")}
for k, (y, n) in PINS.items():
    pin(EX1, y, n, "R")
title(490, 100, "ESP32 microcontroller", "المتحكم ESP32")
wire([(EX0, 590), (330, 590), (330, GND_Y)], K)
dot(330, GND_Y)

# ---------- two LEDs, each through its own 220 ohm resistor, to ground ----------
RX, LX, GX = 740, 900, 1000
for k, col, glow, en, ar in [("g", G, "#7CE3A0", "Green: plenty left", "أخضر: الكمية كافية"),
                             ("r", R, "#FF8A80", "Red: nearly empty", "أحمر: قرب ينتهي")]:
    y = PINS[k][0]
    wire([(EX1, y), (RX - 52, y)], col)
    resistor(RX, y, ["#C0392B", "#C0392B", "#5A3A1E", "#C9A227"], "220 Ω")      # red red brown gold
    wire([(RX + 52, y), (LX - 30, y)], col)
    led(LX, y - 8, col, glow)
    wire([(LX + 30, y), (GX, y)], K)
    dot(GX, y, K)
    title(GX + 26, y - 22, en, ar, "start", 240, small=True)
wire([(GX, PINS["g"][0]), (GX, GND_Y)], K)
dot(GX, GND_Y)

# ---------- buzzer straight on its pin ----------
BY = PINS["bz"][0]
ZX, ZY = 820, BY + 20
wire([(EX1, BY), (ZX - 50, BY)], O)
add(f'<line x1="{ZX - 50}" y1="{BY}" x2="{ZX - 36}" y2="{BY}" stroke="#9AA0A6" stroke-width="3"/>')
add(f'<circle cx="{ZX}" cy="{ZY}" r="44" fill="#1A1A1A" stroke="#000" stroke-width="1.2"/>')
add(f'<circle cx="{ZX}" cy="{ZY}" r="7" fill="#444"/>')
add(f'<text x="{ZX - 22}" y="{ZY - 12}" class="pm" text-anchor="middle" style="fill:#E0E0E0">+</text>')
add(f'<text x="{ZX + 22}" y="{ZY + 30}" class="pm" text-anchor="middle" style="fill:#E0E0E0">−</text>')
add(f'<line x1="{ZX + 36}" y1="{ZY + 20}" x2="{ZX + 50}" y2="{ZY + 20}" stroke="#9AA0A6" stroke-width="3"/>')
wire([(ZX + 50, ZY + 20), (ZX + 80, ZY + 20), (ZX + 80, GND_Y)], K)
dot(ZX + 80, GND_Y)
title(ZX - 70, ZY + 52, "Active buzzer, 2 legs", "جرس نشط بطرفين", "middle", 200, small=True)

# wire names
for k, (y, n) in PINS.items():
    add(f'<text x="690" y="{y - 8}" class="wl" text-anchor="middle">{n}</text>')

notes.append('<div class="foot">'
             '<p><b>Each LED: pin, then a 220 Ω resistor, then the long leg (+); the short leg (−) to ground.</b>'
             '<span>كل ليد: المنفذ، بعدين مقاومة 220 أوم، بعدين رجله الطويلة (+)، ورجله القصيرة (−) للأرضي.</span></p>'
             '<p><b>Buzzer: long leg (+) to GPIO 25, short leg (−) to ground, no resistor (an active buzzer).</b>'
             '<span>الجرس: رجله الطويلة (+) على GPIO 25، والقصيرة (−) للأرضي، بدون مقاومة (جرس نشط).</span></p>'
             '<p><b>All grounds are joined with the ESP32 ground.</b>'
             '<span>كل الأرضيات موصولة بأرضي ESP32.</span></p>'
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
  .pm{{font:600 16px 'IBM Plex Mono',monospace;fill:#333}}
  .leg{{font:600 12px 'IBM Plex Mono',monospace;fill:#444}}
  .bus{{font:600 16px 'IBM Plex Sans'}}
  .wl{{font:500 12.5px 'IBM Plex Mono',monospace;fill:#555}}
  .chip{{font:600 20px 'IBM Plex Sans';fill:#5E646C}}
  .foot{{position:absolute;left:70px;top:760px;width:1340px;display:flex;gap:50px}}
  .foot p{{margin:0;flex:1;line-height:1.3}}
  .foot b{{display:block;font-weight:500;font-size:15px}}
  .foot span{{display:block;font-family:'IBM Plex Sans Arabic',sans-serif;font-size:14px;color:#555;direction:rtl;text-align:left}}
</style></head><body>
<div class="page">
<svg width="{W_PAGE}" height="{H_PAGE}" viewBox="0 0 {W_PAGE} {H_PAGE}">
<defs>
<linearGradient id="can" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D3D7DC"/><stop offset="1" stop-color="#B3B9C0"/></linearGradient>
</defs>
{chr(10).join(svg)}
</svg>
{chr(10).join(notes)}
</div></body></html>"""
open(__file__.replace("make_fig3.py", "fig3-lights-buzzer.html"), "w", encoding="utf-8").write(html)
print("fig3-lights-buzzer.html written")
