# The user guide, in Arabic: power, network setup, the three ways to open the dashboard, what it does, the screen,
# and fixes. Writes guide.html and guide.pdf (A4). Pictures: the device's screens drawn as the firmware draws them,
# phone sketches, a QR code to the online dashboard, and the local page's screenshot with numbered markers.
import json, pathlib
import segno
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
img = here / "img"
LINK = "https://yassin964770.github.io/iv-monitor/"

# ---------- the OLED, drawn the way screen.ino draws it (64 x 128 after turning, text cells 6 x 8 per size) ----------
class Oled:
    def __init__(self):
        self.el = []

    def text(self, s, x, y, size=1, ink="#fff"):
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        self.el.append(f'<text x="{x}" y="{y + 7 * size}" font-size="{10 * size}" fill="{ink}" '
                       f'textLength="{6 * size * len(s) - size}" lengthAdjust="spacingAndGlyphs">{s}</text>')

    def centred(self, s, y, size=1, ink="#fff"):
        x = (64 - len(s) * 6 * size) / 2
        self.text(s, max(x, 0), y, size, ink)

    def wrapped(self, s, y):
        rest = s.strip()
        while rest:
            cut = len(rest)
            if cut > 10:
                cut = rest.rfind(" ", 0, 11)
                if cut <= 0: cut = 10
            self.centred(rest[:cut], y)
            rest = rest[cut:].strip()
            y += 10
        return y

    def rect(self, x, y, w, h, fill=True):
        self.el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#fff" if fill else "none"}" stroke="#fff" stroke-width="{0 if fill else 1}"/>')

    def message(self, title, *lines):
        self.rect(0, 0, 64, 13)
        self.centred(title[:10], 3, 1, "#000")
        y = 22
        for s in lines:
            if s: y = self.wrapped(s, y) + 6
        return self

    def svg(self, width=118):
        return (f'<div class="oled" dir="ltr"><svg viewBox="-1 -1 66 130" width="{width}" font-family="IBM Plex Mono" font-weight="600">'
                f'<rect x="-1" y="-1" width="66" height="130" fill="#05070a"/>{"".join(self.el)}</svg></div>')


def screen_setup():
    return Oled().message("Setup", "Join IV-Monitor", "Pass 12345678", "Open 192.168.4.1").svg()

def screen_connected():
    return Oled().message("Connected", "Yassin", "192.168.100.184", "also IV-Monitor").svg()

def screen_address(router):
    o = Oled()
    o.rect(0, 0, 64, 13); o.centred("OPEN PAGE", 3, 1, "#000")
    o.centred("in browser" if router else "IV-Monitor", 17)
    y = 30
    for part in (["192.", "168.", "100.", "184"] if router else ["192.", "168.", "4.", "1"]):
        o.centred(part, y, 2); y += 18
    if router: o.centred("iv-monitor", 104); o.centred(".local", 114)
    else: o.wrapped("Pass 12345678", 104)
    return o.svg()

def screen_main():
    o = Oled()
    for i in range(3):   # Wi-Fi bars, all three: good signal
        h = 3 + i * 2; o.rect(i * 4, 7 - h, 3, h)
    o.el.append('<circle cx="17" cy="4" r="2" fill="#fff"/><circle cx="21" cy="3" r="3" fill="#fff"/><circle cx="25" cy="4" r="2" fill="#fff"/><rect x="17" y="4" width="9" height="3" fill="#fff"/>')
    o.text("320g", 64 - 24, 0)
    o.rect(0, 10, 64, 1)
    o.centred("290", 16, 3); o.centred("ml left", 42); o.rect(0, 53, 64, 1)
    o.centred("time left", 57); o.centred("9:04", 68, 2); o.rect(0, 85, 64, 1)
    o.centred("32", 89, 2); o.centred("ml/h", 105)
    o.el.append('<rect x="0.5" y="115.5" width="63" height="12" fill="none" stroke="#fff" stroke-width="1"/>')
    o.centred("OPEN", 118)
    return o.svg(170)

def screen_closed_band():
    o = Oled()
    o.rect(0, 115, 64, 13); o.centred("CLOSED", 118, 1, "#000")
    o.el.insert(0, '<rect x="0" y="100" width="64" height="15" fill="#05070a"/>')
    return f'<div class="band" dir="ltr"><svg viewBox="0 112 64 17" width="170" font-family="IBM Plex Mono" font-weight="600"><rect x="0" y="112" width="64" height="17" fill="#05070a"/>{"".join(o.el)}</svg></div>'


# ---------- phone sketches ----------
def phone(inner, caption=""):
    return f'<div class="phone"><div class="notch"></div><div class="scr">{inner}</div></div>'

wifi_list = phone("""
  <div class="ph-bar">الواي فاي</div>
  <div class="ph-row on"><span>IV-Monitor</span><i class="lock"></i></div>
  <div class="ph-pass"><small>كلمة المرور</small><b dir="ltr">12345678</b></div>
  <div class="ph-row"><span>Yassin</span><i class="lock"></i></div>
  <div class="ph-row"><span>Home-5G</span><i class="lock"></i></div>
""")
portal_menu = phone("""
  <div class="wm" dir="ltr"><h4>IV Monitor</h4><small>WiFiManager</small>
  <div class="wm-btn hi">Configure WiFi</div><div class="wm-btn">Info</div><div class="wm-btn">Exit</div></div>
""")
portal_pick = phone("""
  <div class="wm" dir="ltr"><div class="wm-net hi">Yassin <span>&#9679;&#9679;&#9679;</span></div>
  <div class="wm-net">Neighbour <span>&#9679;&#9679;</span></div><div class="wm-net">Office-WiFi <span>&#9679;</span></div>
  <div class="wm-in">Yassin</div><div class="wm-in pw">&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;</div>
  <div class="wm-btn hi">Save</div></div>
""")

# ---------- the power picture ----------
power_svg = """
<svg viewBox="0 0 520 250" width="100%">
  <rect x="40" y="20" width="180" height="210" rx="6" fill="#E6CB9E" stroke="#A98B5F"/>
  <rect x="120" y="45" width="80" height="110" rx="3" fill="#F5F5F1" stroke="#CBCBC3"/>
  <rect x="140" y="55" width="26" height="50" rx="2" fill="#1D1E22"/><rect x="172" y="58" width="22" height="22" rx="2" fill="#22508E"/>
  <rect x="140" y="118" width="30" height="18" rx="2" fill="#2F7D4E"/>
  <path d="M70 60 q-12 6 -12 22 v50 q0 18 24 20 q24 -2 24 -20 v-50 q0 -16 -12 -22 z" fill="#EEF6FA" stroke="#9FB4C2"/>
  <rect x="150" y="175" width="34" height="30" rx="3" fill="#232323"/>
  <path d="M153 48 C150 30 240 20 250 60 L262 150" fill="none" stroke="#151515" stroke-width="5"/>
  <path d="M175 150 C190 170 238 150 262 168" fill="none" stroke="#151515" stroke-width="5"/>
  <path d="M262 150 C300 160 320 190 330 196" fill="none" stroke="#151515" stroke-width="5"/>
  <path d="M262 168 C300 182 330 200 370 196" fill="none" stroke="#151515" stroke-width="5"/>
  <rect x="300" y="196" width="190" height="44" rx="10" fill="#3A3D42"/>
  <rect x="318" y="190" width="24" height="10" rx="2" fill="#1c1c1c"/><rect x="358" y="190" width="24" height="10" rx="2" fill="#1c1c1c"/>
  <circle cx="470" cy="226" r="3.5" fill="#6BD48A"/>
  <circle cx="153" cy="48" r="11" fill="none" stroke="#0b6e69" stroke-width="2.5"/><text x="153" y="53" text-anchor="middle" class="n">1</text>
  <circle cx="232" cy="160" r="11" fill="none" stroke="#0b6e69" stroke-width="2.5"/><text x="232" y="165" text-anchor="middle" class="n">2</text>
</svg>"""

# ---------- QR to the online dashboard ----------
qr = segno.make(LINK, error="m")
qr_svg = qr.svg_inline(scale=4, dark="#12302f", border=2, omitsize=True)   # viewBox only, so it scales without cropping

# ---------- the local page with numbered markers ----------
boxes = json.loads((img / "local-boxes.json").read_text())
W0, H0 = boxes["size"]
B = boxes["boxes"]
marks = [  # number, element, which side of it the marker sits
    (1, "ml", "tl"), (2, "rate", "tl"), (3, "left", "tl"), (4, "g", "tl"), (5, "chart", "l"), (6, "bClose", "l"),
    (7, "tareBtn", "l"), (8, "calBtn", "l"), (9, "emptyG", "l"), (10, "alerts", "r"), (11, "lowMl", "l"),
    (12, "autoCloseMl", "l"), (13, "openDeg", "l"), (14, "saveBtn", "l"), (15, "vReal", "l"), (16, "wifiBtn", "l")]
SHOT_W = 228   # width the screenshot is shown at, in CSS px
k = SHOT_W / W0
pins = []
for n, el, side in marks:
    x, y, w, h = B[el]
    cx, cy = {"r": (x + w + 4, y + h / 2), "l": (x - 4, y + h / 2), "t": (x + w / 2, y - 2), "c": (x + w / 2, y + h / 2), "tl": (x + 2, y - 14)}[side]
    pins.append(f'<b class="pin" style="left:{cx * k:.0f}px;top:{cy * k:.0f}px">{n}</b>')
shot_h = H0 * k

legend = [
    ("الكمية المتبقية بالمل، وتحتها حالة المحلول: طبيعي، أو الكمية منخفضة، أو توقف التدفق، أو الصمام مغلق."),
    ("معدل التدفق بالمل في الساعة. يظهر بعد دقيقتين من القراءات."),
    ("الوقت المتبقي حتى تفرغ القنينة، بالساعات والدقائق."),
    ("الوزن الحالي على الخطاف بالغرام."),
    ("مخطط الوزن خلال آخر 5 دقائق: خط ينزل ببطء يعني أن المحلول ينزل."),
    ("فتح الصمام وإغلاقه. المحرك يعصر الأنبوب أقل من ثانية ثم يرتاح."),
    ("تصفير الميزان: أزل القنينة عن الخطاف، اضغط «تصفير» ثم «تأكيد»."),
    ("المعايرة: علّق وزناً تعرفه، اكتب وزنه بالغرام، واضغط «معايرة»."),
    ("وزن القنينة الفارغة مع الأنبوب، حتى تُحسب الكمية المتبقية صحيحة."),
    ("تفعيل التنبيه: عند انخفاض الكمية أو توقف التدفق يضيء الضوء الأحمر ويصفّر الجرس وتومض الشاشة. مطفأ في البداية."),
    ("الكمية التي يعتبرها الجهاز منخفضة."),
    ("الإغلاق التلقائي: يغلق الصمام وحده عند هذه الكمية. الصفر يعني أنه معطّل."),
    ("زاوية الفتح وزاوية الإغلاق. زر «اختبار» يحرّك المحرك إلى الزاوية لتجربتها قبل الحفظ."),
    ("حفظ الإعدادات في الجهاز. تبقى محفوظة بعد إطفائه."),
    ("حالة الصمام الفعلية: إذا حرّكت الصمام بيدك، صحّح الحالة المعروضة من هنا دون أن يتحرك المحرك."),
    ("اسم الشبكة وعنوان الجهاز، وزر ربط الجهاز بشبكة واي فاي أخرى."),
]
legend_html = "".join(f"<li><b>{i + 1}</b><span>{t}</span></li>" for i, t in enumerate(legend))

html = f"""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>دليل استخدام جهاز مراقبة المحلول الوريدي</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  @page {{ size: A4; margin: 0 }}
  :root {{ --ink:#12302f; --muted:#53696a; --line:#d5dfdc; --accent:#0b6e69; --soft:#eef2f1; --warnbg:#fbecd2; --warn:#8a5200 }}
  * {{ box-sizing: border-box }}
  html, body {{ margin:0; background:#fff; color:var(--ink); font-family:'IBM Plex Sans Arabic',sans-serif; font-size:12.5pt; line-height:1.65 }}
  .page {{ width:210mm; height:297mm; padding:16mm 17mm 14mm; position:relative; overflow:hidden; page-break-after:always }}
  .page:last-child {{ page-break-after:auto }}
  .foot {{ position:absolute; bottom:8mm; left:17mm; right:17mm; display:flex; justify-content:space-between; font-size:9pt; color:var(--muted); border-top:1px solid var(--line); padding-top:2mm }}
  h1 {{ font-size:25pt; line-height:1.3; margin:0 0 3mm; font-weight:700 }}
  h2 {{ font-size:17pt; margin:0 0 4mm; display:flex; align-items:center; gap:4mm; font-weight:700 }}
  h2 .step {{ width:11mm; height:11mm; border-radius:50%; background:var(--accent); color:#fff; display:grid; place-items:center; font-size:15pt; flex:none }}
  h3 {{ font-size:13.5pt; margin:6mm 0 2mm; font-weight:600 }}
  p {{ margin:0 0 3mm }}
  .lead {{ font-size:13.5pt; color:var(--muted); margin-bottom:6mm }}
  ol, ul {{ margin:0 0 3mm; padding-inline-start:6mm }}
  li {{ margin-bottom:1.5mm }}
  .ltr, code {{ direction:ltr; unicode-bidi:isolate; font-family:'IBM Plex Mono',monospace; font-size:.92em; font-weight:500 }}
  .note {{ background:var(--soft); border-radius:3mm; padding:3.5mm 5mm; margin:4mm 0; font-size:11.5pt }}
  .note.warn {{ background:var(--warnbg) }}
  .note b {{ display:block; margin-bottom:1mm }}
  .row {{ display:flex; gap:7mm; align-items:flex-start }}
  .grow {{ flex:1 }}
  figure {{ margin:0; text-align:center }}
  figcaption {{ font-size:10pt; color:var(--muted); margin-top:1.5mm; line-height:1.4 }}
  .oled {{ display:inline-block; padding:7px; background:#22508E; border-radius:6px; box-shadow:0 1px 0 #173A69 }}
  .oled svg, .band svg {{ display:block; direction:ltr }}
  .oled text, .band text {{ direction:ltr; unicode-bidi:normal }}
  .band {{ display:inline-block; padding:5px; background:#22508E; border-radius:5px }} .band svg {{ display:block }}
  .phone {{ width:38mm; height:76mm; border:2.2mm solid #1f2326; border-radius:7mm; position:relative; background:#fff; margin:0 auto; overflow:hidden }}
  .notch {{ width:14mm; height:2.4mm; background:#1f2326; border-radius:0 0 2mm 2mm; margin:0 auto }}
  .scr {{ padding:2.5mm 2.4mm; font-size:8.6pt; line-height:1.4 }}
  .ph-bar {{ font-weight:600; margin-bottom:2mm }}
  .ph-row {{ display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding:1.6mm 0; direction:ltr }}
  .ph-row.on {{ color:var(--accent); font-weight:600 }}
  .lock {{ width:2.4mm; height:2.4mm; border:1.5px solid currentColor; border-radius:.6mm; display:inline-block }}
  .ph-pass {{ background:var(--soft); border-radius:1.5mm; padding:1.5mm 2mm; margin:1mm 0 2mm }}
  .ph-pass small {{ display:block; color:var(--muted); font-size:8pt }}
  .wm {{ text-align:center; font-family:Arial,sans-serif; font-size:9pt }}
  .wm h4 {{ margin:2mm 0 0; font-size:11pt }} .wm small {{ color:#888 }}
  .wm-btn {{ background:#e7e7e7; border-radius:1.2mm; padding:1.8mm; margin-top:2.2mm; font-weight:bold }}
  .wm-btn.hi {{ background:#1fa3ec; color:#fff }}
  .wm-net {{ text-align:left; padding:1.4mm 1mm; border-bottom:1px solid #eee; display:flex; justify-content:space-between }}
  .wm-net.hi {{ background:#e6f4fd }} .wm-net span {{ color:#1fa3ec; font-size:7pt }}
  .wm-in {{ text-align:left; border:1px solid #ccc; border-radius:1mm; padding:1.4mm; margin-top:2mm; font-size:8.5pt }}
  .steps {{ counter-reset:s; list-style:none; padding:0 }}
  .steps > li {{ counter-increment:s; position:relative; padding-inline-start:9mm; margin-bottom:2.6mm }}
  .steps > li::before {{ content:counter(s); position:absolute; inset-inline-start:0; top:.3mm; width:6.2mm; height:6.2mm; border-radius:50%; border:1.6px solid var(--accent); color:var(--accent); font-weight:700; font-size:10.5pt; display:grid; place-items:center }}
  .three {{ display:grid; grid-template-columns:1fr; gap:3mm }}
  .way {{ border:1px solid var(--line); border-radius:3mm; padding:3mm 5mm; font-size:11.5pt; line-height:1.55; display:flex; gap:5mm; align-items:center }}
  .way h3 {{ margin:0 0 1mm }}
  .way .tag {{ color:var(--accent); font-weight:700; font-size:10pt }}
  .qr svg {{ display:block; width:26mm; height:26mm }}
  table {{ border-collapse:collapse; width:100%; font-size:11pt; margin:3mm 0 }}
  th, td {{ border-bottom:1px solid var(--line); padding:2.2mm 2mm; text-align:right; vertical-align:top }}
  th {{ color:var(--muted); font-weight:600; font-size:10pt }}
  .shot {{ position:relative; width:{SHOT_W}px; height:{shot_h:.0f}px; flex:none; border-radius:10px; overflow:visible; box-shadow:0 0 0 1px var(--line) }}
  .shot img {{ width:100%; display:block; border-radius:10px }}
  .pin {{ position:absolute; width:18px; height:18px; margin:-9px 0 0 -9px; border-radius:50%; background:#d9480f; color:#fff; font-size:10.5px; font-weight:700; display:grid; place-items:center; font-family:'IBM Plex Mono'; box-shadow:0 0 0 2px #fff }}
  .legend {{ list-style:none; padding:0; margin:0; font-size:11pt; line-height:1.5 }}
  .legend li {{ display:flex; gap:2.5mm; margin-bottom:2.8mm }}
  .legend li b {{ flex:none; width:5.6mm; height:5.6mm; border-radius:50%; background:#d9480f; color:#fff; font-size:8.5pt; display:grid; place-items:center; font-family:'IBM Plex Mono'; margin-top:.4mm }}
  .screens {{ display:flex; gap:6mm; justify-content:center; align-items:flex-start }}
  .callouts {{ list-style:none; padding:0; font-size:11pt }}
  .callouts li {{ margin-bottom:2mm }}
  .callouts b {{ color:var(--accent) }}
  .cover-fig img {{ width:100%; display:block }}
</style></head><body>

<section class="page">
  <h1>دليل استخدام جهاز مراقبة المحلول الوريدي</h1>
  <p class="lead">كيف تشغّل الجهاز، وتربطه بالواي فاي، وتفتح لوحة التحكم، وماذا تفعل بها.</p>
  <div>
    <div>
      <p>الجهاز يزن قنينة المحلول طوال الوقت، ويحسب منها الكمية المتبقية وسرعة نزول المحلول والوقت الباقي حتى تفرغ. يعرض ذلك على شاشته الصغيرة، وعلى لوحة تحكم تفتحها من الموبايل أو اللابتوب. ومن اللوحة تفتح الأنبوب أو تغلقه بمحرك صغير يعصره.</p>
      <div class="row" style="gap:12mm"><div class="grow"><h3>ما تحتاجه</h3>
      <ul>
        <li>الجهاز على اللوح الخشبي، والقنينة معلّقة بخلية الحمل.</li>
        <li>كيبلا USB الخارجان من أسفل الجهاز.</li>
        <li>باور بانك، أو شاحن USB فيه منفذان.</li>
        <li>موبايل أو لابتوب فيه متصفح.</li>
      </ul></div><div><h3>محتويات الدليل</h3>
      <ol>
        <li>التشغيل</li><li>ربط الجهاز بالواي فاي</li><li>فتح لوحة التحكم، بثلاث طرق</li>
        <li>ماذا تفعل باللوحة</li><li>شاشة الجهاز</li><li>مشاكل وحلولها</li>
      </ol></div></div>
    </div>
    <figure class="cover-fig" style="width:112mm;margin:0 auto"><img src="../report-figures/fig1-board.png"><figcaption>الجهاز كما بُني، وأسماء أجزائه</figcaption></figure>
  </div>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>1</span></div>
</section>

<section class="page">
  <h2><span class="step">1</span>التشغيل</h2>
  <figure style="margin:2mm 0 5mm">{power_svg}<figcaption>الكيبلان يدخلان معاً في الباور بانك أو الشاحن</figcaption></figure>
  <ol class="steps">
    <li>اشبك <b>الكيبل الأول</b> في الباور بانك أو الشاحن. هذا الكيبل يدخل في المتحكم (اللوحة السوداء الصغيرة)، ويشغّل الجهاز كله.</li>
    <li>اشبك <b>الكيبل الثاني</b>، وهو الكيبل المقصوص، في المنفذ الآخر. هذا يشغّل محرك الصمام فقط.</li>
    <li>بعد ثوانٍ تضيء الشاشة وتكتب <span class="ltr">IV Monitor</span> ثم <span class="ltr">Starting</span>، ثم يبدأ الاتصال بالواي فاي.</li>
  </ol>
  <div class="note"><b>الكيبلان ضروريان معاً</b>بدون الكيبل الثاني يعمل الوزن والشاشة واللوحة، لكن الصمام لا يتحرك.</div>
  <div class="note warn"><b>لا تعتمد على منفذ اللابتوب</b>تشغيل الواي فاي يحتاج تياراً لا تعطيه بعض منافذ اللابتوب، فيطفئ الجهاز ويعيد التشغيل مرة بعد مرة. استعمل باور بانك أو شاحناً، وكيبلاً قصيراً جيداً.</div>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>2</span></div>
</section>

<section class="page">
  <h2><span class="step">2</span>ربط الجهاز بالواي فاي</h2>
  <p>تفعل هذا <b>أول مرة فقط</b>، أو عندما تنقل الجهاز إلى مكان فيه شبكة أخرى. في المكان نفسه يتذكر الجهاز الشبكة ويتصل وحده كل مرة.</p>
  <div class="row" style="margin:4mm 0 5mm; justify-content:space-between">
    <figure>{screen_setup()}<figcaption>الشاشة تطلب الإعداد</figcaption></figure>
    <figure>{wifi_list}<figcaption>ادخل شبكة IV-Monitor</figcaption></figure>
    <figure>{portal_menu}<figcaption>اضغط Configure WiFi</figcaption></figure>
    <figure>{portal_pick}<figcaption>اختر الشبكة واحفظ</figcaption></figure>
  </div>
  <ol class="steps">
    <li>شغّل الجهاز. إذا لم يجد شبكة يعرفها، تظهر على شاشته كلمة <span class="ltr">Setup</span>.</li>
    <li>من الموبايل افتح إعدادات الواي فاي، واتصل بشبكة <span class="ltr">IV-Monitor</span>. كلمة المرور <span class="ltr">12345678</span>.</li>
    <li>تفتح صفحة الإعداد وحدها. إذا لم تفتح، افتح المتصفح واكتب <span class="ltr">192.168.4.1</span>.</li>
    <li>اضغط <span class="ltr">Configure WiFi</span>، واختر شبكة المكان، واكتب كلمة مرورها، ثم اضغط <span class="ltr">Save</span>.</li>
    <li>تظهر على الشاشة كلمة <span class="ltr">Connected</span> مع اسم الشبكة وعنوان الجهاز. انتهى الربط.</li>
  </ol>
  <div class="row">
    <div class="grow">
      <div class="note"><b>انتبه</b>
        صفحة الإعداد تنتظر 3 دقائق فقط. إذا فاتتك، افصل الكهرباء وأعد وصلها.<br>
        الجهاز يرى شبكات <span class="ltr">2.4 GHz</span> فقط. إذا لم تظهر شبكتك في القائمة، فالراوتر يبث على <span class="ltr">5 GHz</span> فقط أو بعيد.<br>
        لا تغيّر شيئاً في زر <span class="ltr">Setup</span> داخل صفحة الإعداد، فهو للمطوّر.
      </div>
      <p><b>إذا لم تربطه بأي شبكة</b> يبقى الجهاز يعمل كاملاً، وتصل إليه من شبكته الخاصة (الطريقة الثالثة في الصفحة التالية).</p>
      <p><b>لتغيير الشبكة لاحقاً</b> افتح اللوحة من الطريقة الثانية أو الثالثة، ثم «الإعدادات والمعايرة»، واضغط «ربط الجهاز بشبكة واي فاي أخرى». يعيد الجهاز التشغيل على صفحة الإعداد، فكرر الخطوات من 2 إلى 5.</p>
    </div>
    <figure>{screen_connected()}<figcaption>تم الربط</figcaption></figure>
  </div>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>3</span></div>
</section>

<section class="page">
  <h2><span class="step">3</span>فتح لوحة التحكم</h2>
  <p>اللوحة واحدة تقريباً، وتصل إليها بثلاث طرق. إذا لم تنجح طريقة، جرّب التي بعدها.</p>
  <div class="three">
    <div class="way">
      <div class="qr">{qr_svg}</div>
      <div class="grow">
        <span class="tag">الطريقة الأولى</span>
        <h3>من أي مكان، عبر الإنترنت</h3>
        <p>امسح الرمز، أو افتح الرابط: <span class="ltr">yassin964770.github.io/iv-monitor</span></p>
        <p style="margin:0">تعمل إذا كان الجهاز متصلاً بشبكة فيها إنترنت، وفي موبايلك إنترنت من أي نوع. أعلى اللوحة يكتب «الجهاز متصل» حين تصل القراءات. إذا كتب «الجهاز غير متصل» فبعض الشبكات تمنع هذا الاتصال، فاستعمل الطريقة الثانية أو الثالثة.</p>
      </div>
    </div>
    <div class="way">
      {screen_address(True).replace('width="118"', 'width="84"')}
      <div class="grow">
        <span class="tag">الطريقة الثانية</span>
        <h3>على شبكة الواي فاي نفسها</h3>
        <p>اتصل بالشبكة التي ربطت بها الجهاز، واكتب في المتصفح العنوان الظاهر على شاشته، مثل <span class="ltr">192.168.100.184</span>. أو اكتب <span class="ltr">iv-monitor.local</span>، وهذا لا يعمل على بعض أجهزة أندرويد، فاستعمل الأرقام.</p>
        <p style="margin:0">تعرض الشاشة العنوان إلى أن يفتح أحد اللوحة، ثم تنتقل إلى القراءات. العنوان مكتوب أيضاً أسفل اللوحة في الطريقة الأولى.</p>
      </div>
    </div>
    <div class="way">
      {screen_address(False).replace('width="118"', 'width="84"')}
      <div class="grow">
        <span class="tag">الطريقة الثالثة</span>
        <h3>شبكة الجهاز الخاصة</h3>
        <p>الجهاز يبث شبكته <span class="ltr">IV-Monitor</span> طوال الوقت. اتصل بها (كلمة المرور <span class="ltr">12345678</span>) وافتح <span class="ltr">192.168.4.1</span>.</p>
        <p style="margin:0">تعمل في أي مكان، بلا راوتر ولا إنترنت. قد يقول الموبايل «لا يوجد إنترنت»، فاختر البقاء متصلاً.</p>
      </div>
    </div>
  </div>
  <table>
    <tr><th></th><th>تحتاج إنترنت</th><th>تعمل من خارج المكان</th><th>كل الإعدادات</th></tr>
    <tr><td>الطريقة الأولى</td><td>نعم</td><td>نعم</td><td>أغلبها، عدا التنبيه وتصحيح حالة الصمام وتغيير الشبكة</td></tr>
    <tr><td>الطريقة الثانية</td><td>لا</td><td>لا</td><td>نعم</td></tr>
    <tr><td>الطريقة الثالثة</td><td>لا</td><td>لا</td><td>نعم</td></tr>
  </table>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>4</span></div>
</section>

<section class="page">
  <h2><span class="step">4</span>ماذا تفعل باللوحة</h2>
  <div class="row" style="gap:9mm">
    <div class="shot"><img src="img/local-full.png">{"".join(pins)}</div>
    <div class="grow"><ol class="legend">{legend_html}</ol></div>
  </div>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>5</span></div>
</section>

<section class="page">
  <h2><span class="step">4</span>ماذا تفعل باللوحة، تتمة</h2>
  <h3 style="margin-top:0">قبل أول استعمال: المعايرة</h3>
  <p>المعايرة محفوظة في الجهاز. أعدها فقط إذا كانت القراءة غير صحيحة، أو بعد تغيير خلية الحمل.</p>
  <ol class="steps">
    <li>أزل كل شيء عن الخطاف، واضغط «تصفير» ثم «تأكيد». يصبح الوزن صفراً.</li>
    <li>علّق شيئاً تعرف وزنه بدقة، مثل علبة وزنها 500 غرام، واكتب وزنه واضغط «معايرة».</li>
    <li>اكتب وزن القنينة الفارغة مع الأنبوب في «وزن الكيس الفارغ»، واضغط «حفظ الإعدادات».</li>
    <li>علّق قنينة المحلول. بعد دقيقتين يظهر معدل التدفق والوقت المتبقي.</li>
  </ol>
  <h3>الصمام</h3>
  <p>«إغلاق» يحرّك المحرك فيعصر الأنبوب على قطعة الخشب ويوقف المحلول، و«فتح» يرخيه. إذا لم يُغلق الأنبوب تماماً، زد «زاوية الإغلاق» قليلاً وجرّبها بزر «اختبار» ثم احفظ.</p>
  <p>إذا فعّلت الإغلاق التلقائي، يغلق الجهاز الصمام وحده عند الكمية التي حددتها، وتكتب اللوحة «أُغلق تلقائياً».</p>
  <h3>التنبيه</h3>
  <p>على الجهاز ضوءان وجرس. الضوء الأخضر يعني أن كل شيء طبيعي. التنبيه مطفأ في البداية، وإذا فعّلته من الإعدادات فعندما تقل الكمية عن الحد، أو يتوقف المحلول والصمام مفتوح: ينطفئ الأخضر ويضيء الأحمر، ويصفّر الجرس صفيراً متقطعاً، وتومض الشاشة بكلمة <span class="ltr">LOW</span> أو <span class="ltr">NO FLOW</span>. الحد تختاره من «الكمية المنخفضة» في الإعدادات، ويتوقف التنبيه عند إغلاق الصمام.</p>
  <h3>اللوحة على الإنترنت</h3>
  <p>فيها القراءات والصمام والمعايرة والإعدادات نفسها، وأسفلها سطر عن حال الجهاز: منذ متى يعمل، واسم الشبكة، وعنوان صفحته المحلية، وقوة الإشارة. أما تفعيل التنبيه وتصحيح حالة الصمام وتغيير الشبكة فمن الطريقة الثانية أو الثالثة فقط.</p>
  <figure style="margin-top:4mm"><img src="img/online-top.png" style="width:46mm;height:52mm;object-fit:cover;object-position:top;border-radius:8px;box-shadow:0 0 0 1px var(--line)"><figcaption>اللوحة على الإنترنت</figcaption></figure>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>6</span></div>
</section>

<section class="page">
  <h2><span class="step">5</span>شاشة الجهاز</h2>
  <div class="row" style="gap:10mm;align-items:center">
    <figure>{screen_main()}</figure>
    <ul class="callouts grow">
      <li><b>أعلى اليسار:</b> أشرطة الواي فاي، وعددها قوة الإشارة. بجانبها غيمة إذا كانت اللوحة على الإنترنت متصلة. إذا انقطع الراوتر يظهر شريط <span class="ltr">NO WI-FI</span>، والجهاز يعيد المحاولة وحده.</li>
      <li><b>أعلى اليمين:</b> الوزن بالغرام.</li>
      <li><b>الرقم الكبير:</b> الكمية المتبقية بالمل.</li>
      <li><b>الوسط:</b> الوقت المتبقي، بالساعات والدقائق.</li>
      <li><b>تحته:</b> معدل التدفق بالمل في الساعة. قبل دقيقتين يكتب العد التنازلي.</li>
      <li><b>الأسفل:</b> حالة الصمام. <span class="ltr">OPEN</span> بإطار، و<span class="ltr">CLOSED</span> بخلفية بيضاء، و<span class="ltr">AUTO CLOSE</span> إذا أُغلق تلقائياً.</li>
    </ul>
  </div>
  <figure style="margin-top:3mm">{screen_closed_band()}<figcaption>الصمام مغلق</figcaption></figure>
  <p style="margin-top:5mm">عند التشغيل تعرض الشاشة عنوان اللوحة، وتبدّل كل 5 ثوانٍ بين عنوان الراوتر وشبكة الجهاز الخاصة، إلى أن يفتح أحد اللوحة.</p>

  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>7</span></div>
</section>

<section class="page">
  <h2><span class="step">6</span>مشاكل وحلولها</h2>
  <table>
    <tr><th style="width:42%">المشكلة</th><th>الحل</th></tr>
    <tr><td>الشاشة تنطفئ وتشتغل مرة بعد مرة</td><td>الكهرباء ضعيفة. استعمل باور بانك أو شاحناً، وكيبلاً قصيراً جيداً.</td></tr>
    <tr><td>الصمام لا يتحرك</td><td>تأكد أن الكيبل الثاني (المقصوص) موصول بالكهرباء.</td></tr>
    <tr><td>اللوحة على الإنترنت تكتب «الجهاز غير متصل»</td><td>انظر أعلى شاشة الجهاز: إذا لم تظهر أشرطة الواي فاي فالجهاز غير متصل بالراوتر. إذا ظهرت، فالشبكة تمنع الاتصال، فاستعمل الطريقة الثانية أو الثالثة.</td></tr>
    <tr><td>شبكة المكان لا تظهر في قائمة الإعداد</td><td>الراوتر يبث على <span class="ltr">5 GHz</span> فقط، أو بعيد. قرّب الجهاز، أو استعمل نقطة اتصال الموبايل.</td></tr>
    <tr><td>الوزن أو الكمية غير منطقيين</td><td>صفّر الميزان والخطاف فارغ، ثم أعد المعايرة.</td></tr>
    <tr><td>اللوحة تقول الصمام مفتوح وهو مغلق</td><td>صحّحها من «حالة الصمام الفعلية» في الإعدادات.</td></tr>
    <tr><td>نسيت العنوان</td><td>استعمل الطريقة الثالثة: شبكة <span class="ltr">IV-Monitor</span> والعنوان <span class="ltr">192.168.4.1</span> لا يتغيران.</td></tr>
  </table>
  <div class="foot"><span>دليل استخدام جهاز مراقبة المحلول الوريدي</span><span>8</span></div>
</section>
</body></html>"""

(here / "guide.html").write_text(html, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto((here / "guide.html").as_uri())
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    pg.pdf(path=str(here / "guide.pdf"), format="A4", print_background=True, prefer_css_page_size=True)
    for i, el in enumerate(pg.query_selector_all(".page")):   # page images, to check the layout
        el.screenshot(path=str(here / "img" / f"_page{i + 1}.png"))
    b.close()
print("guide.pdf written")
