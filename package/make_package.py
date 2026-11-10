# The project package: a formal Arabic PDF on the technology and on each attached file, and a zip of the code as it
# was last uploaded to the board (6 Nov 2026, 12:35, commit 4dfd2bd). The firmware and the dashboard are taken from
# that commit; iv_monitor.ino is the working copy, whose only difference is its header comment (same build size).
# Writes package/IV-Monitor-technical.pdf and ../iv-monitor-code.zip.
import pathlib, shutil, subprocess, zipfile
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
repo = here.parent
TITLE = "الوصف التقني لجهاز مراقبة المحلول الوريدي"
PDF_NAME = "IV-Monitor-technical.pdf"

# ---------- the files that go in the zip: (path in the zip, where it comes from) ----------
FROM_HEAD = ["iv_monitor/screen.ino", "iv_monitor/page.h", "dashboard/index.html", ".github/workflows/pages.yml"]
stage = here / "iv-monitor"
shutil.rmtree(stage, ignore_errors=True)
for path in FROM_HEAD:
    data = subprocess.run(["git", "show", f"4dfd2bd:{path}"], cwd=repo, capture_output=True, check=True).stdout
    (stage / path).parent.mkdir(parents=True, exist_ok=True)
    (stage / path).write_bytes(data)
shutil.copy(repo / "iv_monitor/iv_monitor.ino", stage / "iv_monitor/iv_monitor.ino")
(stage / "figures").mkdir()
shutil.copy(repo / "report-figures/fig1-board.png", stage / "figures/fig1-board.png")
shutil.copy(repo / "report-figures/fig2-wiring.png", stage / "figures/fig2-wiring.png")
shutil.copy(repo / "report-figures/fig3-lights-buzzer.png", stage / "figures/fig3-lights-buzzer.png")


def size(path):
    n = (stage / path).stat().st_size
    return f"{n / 1024:.1f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"


def lines(path):
    return len((stage / path).read_text(encoding="utf-8").splitlines())


files = [
    ("iv_monitor/iv_monitor.ino", f"{lines('iv_monitor/iv_monitor.ino')} سطراً، {size('iv_monitor/iv_monitor.ino')}",
     "الملف الرئيس للبرنامج الثابت: الثوابت والإعدادات الافتراضية، وقراءة HX711 وترشيحها، وحساب الكمية والمعدل، والتحكم بالمحرك، وإعداد الشبكة، وخادم الويب وواجهة HTTP، وعميل MQTT والتحقق من توقيع الأوامر، والحفظ في الذاكرة غير المتطايرة، والأوامر عبر المنفذ التسلسلي."),
    ("iv_monitor/screen.ino", f"{lines('iv_monitor/screen.ino')} سطراً، {size('iv_monitor/screen.ino')}",
     "رسم شاشة OLED: الكمية المتبقية، والزمن المتبقي، والمعدل، وشريط حالة الصمام، وعنوان الصفحة، وشاشات بدء التشغيل والشبكة. يُبنى مع الملف الرئيس في البرنامج نفسه."),
    ("iv_monitor/page.h", f"{lines('iv_monitor/page.h')} سطراً، {size('iv_monitor/page.h')}",
     "الصفحة المحلية كاملة (HTML وCSS وJavaScript) نصاً ثابتاً مضمّناً في البرنامج الثابت، يخدمه الجهاز على العنوان <code>/</code>."),
    ("dashboard/index.html", f"{lines('dashboard/index.html')} سطراً، {size('dashboard/index.html')}",
     "لوحة التحكم على الإنترنت: صفحة ثابتة تتصل بخادم MQTT من المتصفح، وتعرض الحالة الحية، وتوقّع الأوامر وترسلها. يحدد الثابت <code>DEVICE</code> فيها الخادم واسم الجهاز ومفتاح التحكم."),
    (".github/workflows/pages.yml", f"{lines('.github/workflows/pages.yml')} سطراً",
     "سير عمل GitHub Actions الذي ينشر مجلد <code>dashboard</code> على GitHub Pages عند كل دفع إلى الفرع <code>main</code>."),
    ("figures/fig1-board.png", size("figures/fig1-board.png"), "رسم الجهاز كما بُني، مع أسماء أجزائه (الشكل 2 في هذه الوثيقة)."),
    ("figures/fig2-wiring.png", size("figures/fig2-wiring.png"), "مخطط التوصيل الكهربائي (الشكل 3 في هذه الوثيقة)."),
    ("figures/fig3-lights-buzzer.png", size("figures/fig3-lights-buzzer.png"), "توصيل المصباحين والجرس (الشكل 4 في هذه الوثيقة)."),
    (PDF_NAME, "", "هذه الوثيقة."),
]
def size_cell(b):
    # "736 سطراً، 31.1 KB" -> the size on one line, the line count under it, each in its own direction
    parts = [s.strip() for s in b.split("،")] if b else []
    out = []
    for s in reversed(parts):
        out.append(f"<span class='l'>{s}</span>" if "B" in s else s)
    return "<br>".join(out)


files_rows = "".join(f"<tr><td class='l'><code>{a}</code></td><td>{c}</td><td style='white-space:nowrap'>{size_cell(b)}</td></tr>" for a, b, c in files)

consts = [
    ("AP_SSID", "اسم شبكة الجهاز الخاصة: <code>IV-Monitor</code>"),
    ("AP_PASS", "كلمة مرور شبكة الجهاز: <code>12345678</code>"),
    ("DEFAULT_MQTT_HOST", "خادم MQTT الافتراضي: <code>broker.hivemq.com</code>"),
    ("DEFAULT_MQTT_PORT", "منفذ الاتصال الافتراضي بـ TLS: <code>8883</code>"),
    ("DEFAULT_CONTROL_KEY", "مفتاح توقيع الأوامر، ويطابق قيمة <code>key</code> في الثابت <code>DEVICE</code> بملف اللوحة"),
    ("PIN_DT، PIN_SCK", "منفذا HX711: <code>GPIO 18</code> و<code>GPIO 19</code>"),
    ("PIN_SERVO", "منفذ إشارة المحرك: <code>GPIO 32</code>"),
]
consts_rows = "".join(f"<tr><td class='l'><code>{a}</code></td><td>{b}</td></tr>" for a, b in consts)


def foot(n):
    return f'<div class="foot"><span>{TITLE}</span><span class="pn"></span></div>'


# ---------- system architecture ----------
arch = """
<svg dir="ltr" viewBox="0 0 720 430" width="100%" font-family="IBM Plex Sans" font-size="12.5">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#3b4b4b"/></marker></defs>
  <g stroke="#3b4b4b" stroke-width="1.6" fill="none" marker-end="url(#ar)">
    <path d="M150 80 H226"/><path d="M150 190 H226"/>
    <path d="M354 80 H430"/><path d="M430 128 H354"/>
    <path d="M290 230 V300"/><path d="M354 190 H430"/>
    <path d="M354 345 H430"/><path d="M560 345 H600"/><path d="M640 300 V250"/>
  </g>
  <g fill="#fff" stroke="#9fb3b0" stroke-width="1.3">
    <rect x="20" y="50" width="130" height="60" rx="8"/><rect x="20" y="160" width="130" height="60" rx="8"/>
    <rect x="226" y="40" width="128" height="190" rx="10" fill="#eaf3f1" stroke="#0b6e69"/>
    <rect x="430" y="50" width="130" height="94" rx="8"/><rect x="430" y="160" width="130" height="60" rx="8"/>
    <rect x="226" y="300" width="128" height="90" rx="10"/><rect x="430" y="300" width="130" height="90" rx="8"/>
    <rect x="590" y="160" width="110" height="90" rx="8"/><rect x="590" y="300" width="110" height="90" rx="8"/>
  </g>
  <g fill="#12302f" text-anchor="middle">
    <text x="85" y="76" font-weight="600">Load cell 3 kg</text><text x="85" y="94" fill="#53696a">IV bottle weight</text>
    <text x="85" y="186" font-weight="600">HX711</text><text x="85" y="204" fill="#53696a">24-bit ADC</text>
    <text x="290" y="110" font-weight="700" font-size="15">ESP32</text><text x="290" y="130" fill="#53696a">Firmware</text>
    <text x="290" y="150" fill="#53696a">Measurement</text><text x="290" y="168" fill="#53696a">Control</text><text x="290" y="186" fill="#53696a">Networking</text>
    <text x="495" y="78" font-weight="600">Servo motor</text><text x="495" y="96" fill="#53696a">Pinch valve</text><text x="495" y="114" fill="#53696a">PWM, GPIO 32</text>
    <text x="495" y="186" font-weight="600">OLED SSD1306</text><text x="495" y="204" fill="#53696a">I2C</text>
    <text x="290" y="330" font-weight="600">Wi-Fi radio</text><text x="290" y="348" fill="#53696a">AP + STA</text><text x="290" y="366" fill="#53696a">2.4 GHz</text>
    <text x="495" y="330" font-weight="600">Local web page</text><text x="495" y="348" fill="#53696a">HTTP, port 80</text><text x="495" y="366" fill="#53696a">REST API</text>
    <text x="645" y="186" font-weight="600">Online</text><text x="645" y="204" fill="#53696a">dashboard</text><text x="645" y="222" fill="#53696a">GitHub Pages</text>
    <text x="645" y="330" font-weight="600">MQTT broker</text><text x="645" y="348" fill="#53696a">HiveMQ</text><text x="645" y="366" fill="#53696a">TLS 8883 / WSS</text>
  </g>
  <text x="188" y="72" text-anchor="middle" fill="#53696a" font-size="11">DT, SCK</text>
  <text x="392" y="72" text-anchor="middle" fill="#53696a" font-size="11">command</text>
  <text x="392" y="143" text-anchor="middle" fill="#53696a" font-size="11">state</text>
</svg>"""

# ---------- a command from the online dashboard to the valve ----------
seq = """
<svg dir="ltr" viewBox="0 0 720 360" width="100%" font-family="IBM Plex Sans" font-size="12">
  <defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6e69"/></marker></defs>
  <g text-anchor="middle" font-weight="600" fill="#12302f">
    <rect x="40" y="10" width="160" height="40" rx="8" fill="#eaf3f1" stroke="#0b6e69"/><text x="120" y="35">Browser (dashboard)</text>
    <rect x="280" y="10" width="160" height="40" rx="8" fill="#eaf3f1" stroke="#0b6e69"/><text x="360" y="35">MQTT broker</text>
    <rect x="520" y="10" width="160" height="40" rx="8" fill="#eaf3f1" stroke="#0b6e69"/><text x="600" y="35">ESP32</text>
  </g>
  <g stroke="#9fb3b0" stroke-dasharray="4 4"><line x1="120" y1="50" x2="120" y2="350"/><line x1="360" y1="50" x2="360" y2="350"/><line x1="600" y1="50" x2="600" y2="350"/></g>
  <g stroke="#0b6e69" stroke-width="1.6" marker-end="url(#sa)" fill="none">
    <path d="M120 90 H356"/><path d="M360 125 H596"/><path d="M600 215 H364"/><path d="M360 245 H124"/><path d="M600 290 H364"/><path d="M360 320 H124"/>
  </g>
  <g fill="#12302f" font-family="IBM Plex Mono" font-size="11.5">
    <text x="128" y="82">publish ivmon/&lt;id&gt;/cmd  "ts|close|HMAC"</text>
    <text x="368" y="117">deliver (QoS 1)</text>
    <text x="596" y="148" text-anchor="end">1. verify HMAC-SHA256</text>
    <text x="596" y="166" text-anchor="end">2. reject if older than 120 s</text>
    <text x="596" y="184" text-anchor="end">3. move servo, save state</text>
    <text x="592" y="207" text-anchor="end">publish ivmon/&lt;id&gt;/ack  "ok close"</text>
    <text x="352" y="237" text-anchor="end">deliver</text>
    <text x="592" y="282" text-anchor="end">publish ivmon/&lt;id&gt;/state  (retained)</text>
    <text x="352" y="312" text-anchor="end">deliver: page shows "closed"</text>
  </g>
</svg>"""

pins = [
    ("خلية الحمل", "الأحمر، الأسود، الأخضر، الأبيض", "HX711: E+، E−، A+، A−"),
    ("HX711", "VCC، GND", "3V3، GND"),
    ("HX711", "DT، SCK", "GPIO 18، GPIO 19"),
    ("شاشة OLED", "VCC، GND", "3V3، GND"),
    ("شاشة OLED", "SDA، SCL", "GPIO 21، GPIO 22"),
    ("محرك السيرفو", "الإشارة (البرتقالي)", "GPIO 32"),
    ("محرك السيرفو", "التغذية (الأحمر)، الأرضي (البني)", "5 V من كيبل USB المقصوص، والأرضي المشترك"),
    ("المتحكم ESP32", "micro-USB", "كيبل USB الأول من مصدر التغذية"),
    ("المصباح الأخضر", "الموجب عبر مقاومة 220 Ω، والسالب", "GPIO 26، وGND"),
    ("المصباح الأحمر", "الموجب عبر مقاومة 220 Ω، والسالب", "GPIO 27، وGND"),
    ("الجرس", "الموجب، والسالب", "GPIO 25، وGND"),
]
pins_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td class='l'>{c}</td></tr>" for a, b, c in pins)

parts = [
    ("المتحكم الدقيق", "ESP32 DevKit (ESP-WROOM-32)", "معالجة القياسات، والتحكم بالمحرك، والشبكة، وخادم الويب. ثنائي النواة بتردد 240 MHz، ويدعم Wi-Fi بتردد 2.4 GHz."),
    ("حساس الوزن", "خلية حمل قضيبية (Bar load cell) سعة 3 kg", "تحويل وزن القنينة إلى إشارة كهربائية صغيرة عبر جسر ويتستون من مقاييس الانفعال (Strain gauges)."),
    ("مضخّم ومحوّل", "HX711", "تضخيم إشارة الجسر وتحويلها إلى قيمة رقمية بدقة 24 بت، بمعدل 10 عينات في الثانية."),
    ("المشغّل", "محرك سيرفو MG945", "صمام ضغط (Pinch valve): يضغط ذراعه الأنبوب على قطعة خشبية فيوقف التدفق."),
    ("الشاشة", "OLED 0.96 in، المتحكم SSD1306، دقة 128 × 64", "عرض الكمية المتبقية والوقت والمعدل وحالة الصمام وعنوان الصفحة. مثبتة رأسياً."),
    ("المؤشرات الضوئية", "مصباحا LED، أخضر وأحمر، مع مقاومة 220 Ω لكل منهما", "الأخضر: الحالة طبيعية. الأحمر: الكمية منخفضة أو توقف التدفق."),
    ("الجرس", "جرس نشط (Active buzzer) بطرفين", "تنبيه صوتي متقطع يرافق المصباح الأحمر."),
    ("لوحة التوصيل", "لوحتا Breadboard بسعة 830 نقطة", "توصيل المكونات دون لحام."),
    ("التغذية", "باور بانك أو شاحن USB بمنفذين (5 V)", "منفذ للمتحكم، ومنفذ للمحرك عبر كيبل USB مقصوص."),
    ("الهيكل", "لوح خشبي، وذراع خشبي، وقطعة خشبية للضغط", "تعليق خلية الحمل والقنينة، وتثبيت المحرك والأنبوب."),
]
parts_rows = "".join(f"<tr><td>{a}</td><td class='l'>{b}</td><td>{c}</td></tr>" for a, b, c in parts)

libs = [
    ("Arduino core for ESP32", "3.3.12", "بيئة التشغيل، وWi-Fi، وPWM عبر LEDC، والذاكرة غير المتطايرة"),
    ("HX711 Arduino Library (Bogdan Necula)", "0.7.5", "قراءة HX711"),
    ("WiFiManager (tzapu)", "2.0.17", "بوابة إعداد الشبكة (Captive portal)"),
    ("PubSubClient", "2.8", "عميل MQTT"),
    ("Adafruit SSD1306 وAdafruit GFX", "2.5.17 و1.13.0", "الرسم على الشاشة"),
    ("mbedTLS (ضمن نواة ESP32)", "", "TLS وحساب HMAC-SHA256"),
    ("MQTT.js", "5.10.1", "عميل MQTT في المتصفح عبر WebSocket الآمن"),
]
libs_rows = "".join(f"<tr><td class='l'>{a}</td><td class='l'>{b}</td><td>{c}</td></tr>" for a, b, c in libs)

api = [
    ("GET", "/", "الصفحة المحلية (مضمّنة في البرنامج الثابت)"),
    ("GET", "/api/state", "الحالة كاملة بصيغة JSON"),
    ("POST", "/api/valve", "to=open أو close: فتح الصمام أو إغلاقه"),
    ("POST", "/api/valvestate", "is=open أو closed: تصحيح الحالة المسجلة دون تحريك المحرك"),
    ("POST", "/api/tare", "تصفير الميزان"),
    ("POST", "/api/cal", "g: المعايرة بوزن معروف"),
    ("POST", "/api/servo", "deg: تحريك المحرك إلى زاوية للاختبار"),
    ("POST", "/api/set", "emptyG، lowMl، autoCloseMl، openDeg، closeDeg، alerts"),
    ("POST", "/api/wifisetup", "إعادة التشغيل على بوابة إعداد الشبكة"),
]
api_rows = "".join(f"<tr><td class='l'><code>{a}</code></td><td class='l'><code>{b}</code></td><td>{c}</td></tr>" for a, b, c in api)

topics = [
    ("ivmon/&lt;id&gt;/state", "الجهاز ← اللوحة", "الحالة بصيغة JSON كل ثانيتين، رسالة محفوظة (Retained)"),
    ("ivmon/&lt;id&gt;/status", "الجهاز ← اللوحة", "online عند الاتصال، وoffline رسالة وصية (Last Will) عند الانقطاع"),
    ("ivmon/&lt;id&gt;/cmd", "اللوحة ← الجهاز", "أمر موقّع: الطابع الزمني | الأمر | التوقيع"),
    ("ivmon/&lt;id&gt;/ack", "الجهاز ← اللوحة", "نتيجة تنفيذ الأمر أو سبب رفضه"),
]
topics_rows = "".join(f"<tr><td class='l'><code>{a}</code></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in topics)

tests = [
    ("الاتصال بالراوتر وتشغيل الشبكة الخاصة معاً", "نجح: عنوان على الراوتر، وشبكة IV-Monitor ظاهرة في الوقت نفسه"),
    ("الاتصال بخادم MQTT عبر TLS على المنفذ 8883", "نجح"),
    ("أوامر الفتح والإغلاق وتفعيل التنبيه وإيقافه عبر MQTT", "نجح، مع وصول رسالة التأكيد"),
    ("أمر بتوقيع خاطئ", "رُفض: wrong control key"),
    ("أمر قديم (إعادة إرسال)", "رُفض: command too old"),
    ("واجهة الصفحة المحلية واسم iv-monitor.local", "نجح، وأُعيد الخطأ 400 لمعاملات غير صالحة و404 لمسار غير موجود"),
    ("حفظ حالة الصمام بعد إعادة التشغيل", "نجح"),
    ("لوحة GitHub Pages", "عرضت «الجهاز متصل» مع قراءات حية"),
]
tests_rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in tests)

html = f"""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>{TITLE}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  @page {{ size:A4; margin:0 }}
  :root {{ --ink:#12302f; --muted:#53696a; --line:#d5dfdc; --accent:#0b6e69; --soft:#eef2f1 }}
  * {{ box-sizing:border-box }}
  html, body {{ margin:0; background:#fff; color:var(--ink); font-family:'IBM Plex Sans Arabic',sans-serif; font-size:11.5pt; line-height:1.7 }}
  .page {{ width:210mm; height:297mm; padding:17mm 18mm 16mm; position:relative; overflow:hidden; page-break-after:always }}
  .page:last-child {{ page-break-after:auto }}
  body {{ counter-reset:pg }} .page {{ counter-increment:pg }} .pn::after {{ content:counter(pg) }}
  figure svg {{ direction:ltr }} svg text {{ direction:ltr; unicode-bidi:normal }}
  .foot {{ position:absolute; bottom:8mm; left:18mm; right:18mm; display:flex; justify-content:space-between; font-size:8.5pt; color:var(--muted); border-top:1px solid var(--line); padding-top:2mm }}
  h1 {{ font-size:24pt; line-height:1.3; margin:0 0 3mm; font-weight:700 }}
  h2 {{ font-size:15.5pt; margin:0 0 3.5mm; font-weight:700; display:flex; gap:3mm; align-items:baseline }}
  h2 .no {{ color:var(--accent) }}
  h3 {{ font-size:12.5pt; margin:5mm 0 1.5mm; font-weight:600 }}
  p {{ margin:0 0 2.6mm; text-align:justify }}
  ul, ol {{ margin:0 0 3mm; padding-inline-start:6mm }} li {{ margin-bottom:1.2mm }}
  code, .l {{ direction:ltr; unicode-bidi:isolate }}
  code {{ font-family:'IBM Plex Mono',monospace; font-size:.88em; background:var(--soft); padding:0 1.2mm; border-radius:1mm; white-space:nowrap }}
  td.l {{ text-align:right }}
  table {{ border-collapse:collapse; width:100%; font-size:10pt; line-height:1.5; margin:2mm 0 4mm }}
  th, td {{ border-bottom:1px solid var(--line); padding:1.8mm 2mm; text-align:right; vertical-align:top }}
  th {{ color:var(--muted); font-weight:600; font-size:9.5pt; background:var(--soft) }}
  figure {{ margin:3mm 0 4mm; text-align:center }} figure img {{ max-width:100%; display:block; margin:0 auto }}
  figcaption {{ font-size:9.5pt; color:var(--muted); margin-top:1.5mm }}
  .box {{ background:var(--soft); border-radius:2.5mm; padding:3mm 4.5mm; margin:3mm 0; font-size:10.5pt }}
  .box b {{ display:block }}
  .formula {{ direction:ltr; text-align:center; font-family:'IBM Plex Mono',monospace; font-size:10.5pt; background:var(--soft); border-radius:2mm; padding:2.5mm; margin:2mm 0 3mm }}
  .cover {{ display:flex; flex-direction:column; justify-content:center; height:100% }}
  .cover .sub {{ font-size:13pt; color:var(--muted); margin-bottom:10mm }}
  .toc {{ list-style:none; padding:0; columns:2; column-gap:12mm; font-size:11.5pt }}
  .toc li {{ margin-bottom:2mm }} .toc b {{ color:var(--accent); display:inline-block; width:7mm }}
  .meta {{ margin-top:12mm; font-size:10pt; color:var(--muted) }}
</style></head><body>

<section class="page"><div class="cover">
  <h1>{TITLE}</h1>
  <div class="sub">التقنيات المستخدمة في النموذج الأولي، ووصف الملفات المرفقة معه في الملف المضغوط.</div>
  <ol class="toc">
    <li><b>1</b>نظرة عامة على النظام</li><li><b>2</b>المكونات المادية</li><li><b>3</b>البناء الميكانيكي</li>
    <li><b>4</b>التوصيل الكهربائي</li><li><b>5</b>التغذية الكهربائية</li><li><b>6</b>البرنامج الثابت ومعالجة القياس</li>
    <li><b>7</b>التحكم بالصمام</li><li><b>8</b>الشبكة والصفحة المحلية</li><li><b>9</b>التحكم عن بعد عبر MQTT</li>
    <li><b>10</b>لوحة التحكم على الإنترنت</li><li><b>11</b>الاختبار والتحقق</li><li><b>12</b>الملفات المرفقة</li>
  </ol>
  <div class="meta">النموذج الأولي لمشروع تخرج. الشيفرة المصدرية: <span class="l">github.com/yassin964770/iv-monitor</span></div>
</div>{foot(0)}</section>

<section class="page">
  <h2><span class="no">1</span>نظرة عامة على النظام</h2>
  <p>الجهاز نموذج أولي لمراقبة قنينة المحلول الوريدي. يقيس وزن القنينة باستمرار، ويستنتج منه الكمية المتبقية ومعدل التدفق والزمن المتبقي حتى النفاد، ويتيح فتح خط التسريب وإغلاقه بصمام ضغط يحركه محرك سيرفو. تُعرض النتائج على شاشة الجهاز، وعلى صفحة ويب محلية يخدمها الجهاز نفسه، وعلى لوحة تحكم منشورة على الإنترنت تتصل بالجهاز عبر بروتوكول MQTT.</p>
  <p>يقوم مبدأ القياس على أن كثافة المحلول الملحي بتركيز 0.9% تقارب كثافة الماء، فيُعدّ كل غرام من الوزن الصافي مليلتراً واحداً من المحلول.</p>
  <figure>{arch}<figcaption>الشكل 1. مخطط بنية النظام</figcaption></figure>
  <h3>مسار البيانات</h3>
  <ol>
    <li>تُعلَّق القنينة بخلية الحمل، فيتغير جهد خرج جسر مقاييس الانفعال تبعاً للوزن.</li>
    <li>يضخّم HX711 الإشارة ويحولها إلى قيمة رقمية يقرؤها المتحكم ESP32.</li>
    <li>يرشّح المتحكم القراءات، ويحسب الكمية والمعدل والزمن، ويحدد حالة التسريب.</li>
    <li>تُعرض النتائج على الشاشة، وتُتاح عبر واجهة HTTP المحلية، وتُنشر عبر MQTT.</li>
    <li>تصل أوامر الصمام من الصفحة المحلية أو من لوحة الإنترنت، فيحرك المتحكم محرك السيرفو.</li>
  </ol>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">2</span>المكونات المادية</h2>
  <table><tr><th style="width:17%">الوظيفة</th><th style="width:30%">المكوّن</th><th>الدور</th></tr>{parts_rows}</table>
  <h2 style="margin-top:7mm"><span class="no">3</span>البناء الميكانيكي</h2>
  <p>ثُبّتت المكونات جميعها على لوح خشبي واحد يُعلَّق رأسياً، ليسهل نقل النموذج وعرضه. وروعي في التصميم أن يمر الحمل عبر خلية الحمل وحدها:</p>
  <ul>
    <li><b>تثبيت خلية الحمل:</b> ثُبّت الطرف الثابت لخلية الحمل القضيبية على ذراع خشبي بارز من اللوح، وتُعلَّق القنينة بالطرف الحر، فيقع الحمل على الخلية في اتجاه القياس المحدد عليها.</li>
    <li><b>عزل الأسلاك عن الحمل:</b> ثُبّت كيبل خلية الحمل على اللوح بشريط لاصق، كي لا ينقل أي شد ميكانيكي إلى القراءة.</li>
    <li><b>صمام الضغط:</b> يمر أنبوب المحلول بين ذراع محرك السيرفو وقطعة خشبية مثبتة خلفه. عند الإغلاق يدور الذراع فيضغط الأنبوب على الخشب ويوقف التدفق، دون أن يلامس المحلول أي جزء من الجهاز.</li>
    <li><b>عزل الأنبوب عن الميزان:</b> يُترك الأنبوب بين حجرة التنقيط والصمام مرتخياً، كي لا يحمل جزءاً من وزن القنينة.</li>
  </ul>
{foot(0)}</section>

<section class="page">
  <figure style="margin-top:0"><img src="../report-figures/fig1-board.png" style="width:150mm"><figcaption>الشكل 2. الجهاز كما بُني، وأسماء أجزائه</figcaption></figure>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">4</span>التوصيل الكهربائي</h2>
  <figure style="margin-top:0"><img src="../report-figures/fig2-wiring.png" style="width:172mm"><figcaption>الشكل 3. مخطط التوصيل</figcaption></figure>
  <table><tr><th style="width:18%">المكوّن</th><th style="width:34%">الطرف</th><th>يتصل بـ</th></tr>{pins_rows}</table>
{foot(0)}</section>

<section class="page">
  <p>تعمل الشاشة وHX711 بجهد 3.3 V من منظم الجهد في لوحة ESP32، فتتوافق مستويات الإشارة مع منافذ المتحكم دون محوّل مستويات. ويتصل HX711 بالمتحكم عبر واجهة تسلسلية بسيطة من خطين (DT وSCK)، وتتصل الشاشة بناقل I2C على العنوان 0x3C.</p>
  <h3>المصباحان والجرس</h3>
  <figure style="margin-top:2mm"><img src="../report-figures/fig3-lights-buzzer.png" style="width:172mm"><figcaption>الشكل 4. توصيل المصباحين والجرس</figcaption></figure>
  <p>يتصل كل مصباح بمنفذه عبر مقاومة 220 Ω، فيسحب نحو 5 mA من جهد 3.3 V، وطرفه السالب إلى الأرضي. ويتصل الجرس النشط بالمنفذ GPIO 25 مباشرة دون مقاومة، لأن دائرته الداخلية تحدد تياره وتولّد الصوت بمجرد وصول الجهد.</p>
  <ul>
    <li><b>المصباح الأخضر</b> مضيء ما دام لا يوجد تنبيه.</li>
    <li><b>التنبيه:</b> إذا فُعّل من إعدادات الصفحة، وكانت الحالة «الكمية منخفضة» أو «توقف التدفق» والصمام غير مغلق، ينطفئ الأخضر ويضيء الأحمر، ويعمل الجرس ثانية ويتوقف ثانية، وتعرض الشاشة تحذيراً وامضاً.</li>
    <li><b>حد الكمية المنخفضة</b> قابل للضبط من الإعدادات (50 ml افتراضياً)، وهو الكمية التي يبدأ عندها التنبيه.</li>
    <li>عند إغلاق الصمام يتوقف التنبيه، لأن توقف التدفق حينها مقصود.</li>
  </ul>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">5</span>التغذية الكهربائية</h2>
  <p>يُغذّى الجهاز بكيبلي USB من مصدر واحد بجهد 5 V، باور بانك أو شاحن بمنفذين:</p>
  <ul>
    <li><b>الكيبل الأول</b> يدخل منفذ micro-USB في لوحة ESP32، ويغذي المتحكم والشاشة وHX711.</li>
    <li><b>الكيبل الثاني</b> كيبل USB مقصوص: يُوصل سلكه الأحمر (5 V) بطرف التغذية في محرك السيرفو مباشرة، وسلكه الأسود بالأرضي.</li>
  </ul>
  <p>فُصلت تغذية المحرك عن تغذية المتحكم لأن محرك السيرفو يسحب تياراً عالياً عند الحركة، فلو غُذّي من لوحة ESP32 لهبط جهدها واضطربت قراءات الميزان. ووُصلت الأرضيات كلها في نقطة مشتركة، ليكون لإشارة التحكم في المحرك مرجع جهد واحد مع المتحكم.</p>
  <h3>استقرار التشغيل</h3>
  <ul>
    <li><b>كاشف هبوط الجهد (Brownout detector):</b> يسحب راديو Wi-Fi تياراً لحظياً عالياً عند بدء تشغيله، لذلك يُوقَف الكاشف خلال مرحلة بدء الشبكة وحدها، ثم يُعاد تفعيله فوراً.</li>
    <li><b>مؤقت المراقبة (Task watchdog):</b> إذا توقفت الحلقة الرئيسة 30 ثانية يعيد المتحكم التشغيل تلقائياً.</li>
    <li><b>سبب آخر إعادة تشغيل</b> يُقرأ عند البدء (تشغيل عادي، هبوط جهد، مؤقت المراقبة، انهيار) ويُنشر مع الحالة.</li>
  </ul>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">6</span>البرنامج الثابت ومعالجة القياس</h2>
  <p>كُتب البرنامج الثابت (Firmware) بلغة C++ على إطار Arduino لشريحة ESP32، ويُبنى ويُرفع بأداة Arduino CLI. ويتكون من ثلاثة ملفات: <code>iv_monitor.ino</code> للقياس والتحكم والشبكة، و<code>screen.ino</code> للشاشة، و<code>page.h</code> للصفحة المحلية.</p>
  <table><tr><th>المكتبة</th><th>الإصدار</th><th>الاستخدام</th></tr>{libs_rows}</table>
  <h3>بنية الحلقة الرئيسة</h3>
  <p>صُممت الحلقة الرئيسة دون انتظار حاجب (Non-blocking): تُقرأ عينة من HX711 فقط حين تكون جاهزة، فلا يتأخر خادم الويب ولا عميل MQTT. وفي كل دورة يُصفَّر مؤقت المراقبة، وتُتابَع حالة الشبكة، وتُخدم طلبات DNS وHTTP وMQTT. وتُحدَّث القياسات مرة كل ثانية، والشاشة مرتين في الثانية.</p>
  <h3>ترشيح القراءات</h3>
  <ol>
    <li><b>الوسيط (Median):</b> يُؤخذ وسيط آخر سبع عينات، فلا تؤثر عينة شاذة واحدة في القراءة.</li>
    <li><b>رفض القفزات:</b> التغير المفاجئ بأكثر من 15 g، كلمس القنينة، يُهمَل. فإن استمر 10 ثوانٍ اعتُبر قنينة جديدة، وبدأ حساب المعدل من جديد.</li>
    <li><b>إعادة ضبط النافذة</b> بعد كل حركة للمحرك، لأن الحركة تهز الميزان.</li>
  </ol>
{foot(0)}</section>

<section class="page">
  <h3 style="margin-top:0">الحسابات</h3>
  <p>تُحسب الكمية المتبقية بطرح وزن القنينة الفارغة مع الأنبوب من الوزن المقاس:</p>
  <div class="formula">ml_left = max(0, W − W_empty)</div>
  <p>ويُحسب معدل التدفق من ميل خط المربعات الصغرى (Least squares) لقراءات آخر 5 دقائق، بقراءة واحدة في الثانية. واختيرت نافذة بالدقائق لأن نقص الوزن في الدقيقة الواحدة قريب من مستوى الضجيج، ولا يُعرض المعدل قبل دقيقتين من القراءات:</p>
  <div class="formula">slope = (nΣxy − ΣxΣy) / (nΣx² − (Σx)²)   [g/s]<br>rate = max(0, −slope × 3600)   [ml/h]<br>minutes_left = ml_left / rate × 60</div>
  <h3>حالات التسريب</h3>
  <table><tr><th style="width:24%">الحالة</th><th>الشرط</th></tr>
    <tr><td>جمع القراءات</td><td>أقل من 120 ثانية من القراءات</td></tr>
    <tr><td>طبيعي</td><td>المعدل محسوب، والكمية فوق حد التنبيه</td></tr>
    <tr><td>الكمية منخفضة</td><td>الكمية المتبقية أقل من الحد المضبوط أو تساويه (50 ml افتراضياً)</td></tr>
    <tr><td>توقف التدفق</td><td>المعدل أقل من 3 ml/h، والصمام غير مغلق، والكمية فوق الحد</td></tr>
    <tr><td>الصمام مغلق</td><td>آخر أمر للصمام كان الإغلاق</td></tr>
  </table>
  <p>وإذا ضُبط حد للإغلاق التلقائي، يغلق المتحكم الصمام بنفسه عند بلوغه.</p>
  <h3>المعايرة والتخزين</h3>
  <p>يُحسب الإزاحة (Offset) من متوسط 20 قراءة والخطاف فارغ، ثم يُحسب معامل المعايرة بتعليق وزن معروف:</p>
  <div class="formula">factor = raw_average(20) / known_grams</div>
  <p>تُحفظ المعايرة والإعدادات وحالة الصمام في الذاكرة غير المتطايرة (NVS) عبر مكتبة Preferences، فتبقى بعد انقطاع التيار.</p>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">7</span>التحكم بالصمام</h2>
  <p>يُولَّد نبض التحكم في المحرك مباشرة من وحدة LEDC في ESP32 بتردد 50 Hz ودقة 14 بت، دون مكتبة وسيطة. ويُحوَّل عرض النبض خطياً من 500 µs عند 0° إلى 2400 µs عند 180°:</p>
  <div class="formula">pulse_us = 500 + deg × (2400 − 500) / 180</div>
  <ul>
    <li><b>زمن الدفع:</b> يُرسل النبض 600 ms ثم يُقطع، فيتوقف المحرك عن الدفع. وبذلك لا يجهد نفسه ضد الأنبوب، ولا يسبب ضجيجاً كهربائياً في الميزان وهو ساكن.</li>
    <li><b>حركة واحدة:</b> يبدأ النبض مباشرة بالزاوية المطلوبة، فيتحرك المحرك نحوها حركة واحدة.</li>
    <li><b>زاويتا الفتح والإغلاق</b> قابلتان للضبط من اللوحة. تُضبط زاوية الإغلاق أبعد قليلاً من نقطة التلامس، ليُحكم الضغط على الأنبوب.</li>
    <li><b>الحالة المسجلة</b> تُحفظ مع كل أمر، وتُستعاد عند التشغيل دون تحريك المحرك. ويمكن تصحيحها من الصفحة إذا حُرّك الصمام يدوياً.</li>
  </ul>
  <h2 style="margin-top:7mm"><span class="no">8</span>الشبكة والصفحة المحلية</h2>
  <h3 style="margin-top:0">نمطا الشبكة معاً (AP + STA)</h3>
  <p>يعمل راديو Wi-Fi في النمطين معاً: محطة (Station) متصلة براوتر المكان، ونقطة وصول (Access Point) خاصة باسم <code>IV-Monitor</code> على العنوان <code>192.168.4.1</code>. تبقى نقطة الوصول تعمل دائماً، فيمكن الوصول إلى الجهاز في أي مكان، دون راوتر ولا إنترنت.</p>
  <h3>إعداد الشبكة</h3>
  <p>تتولى مكتبة WiFiManager إعداد الشبكة. إذا لم يجد الجهاز شبكة محفوظة، يفتح بوابة إعداد (Captive portal) على نقطة الوصول مدة 180 ثانية، يختار منها المستخدم الشبكة ويدخل كلمة مرورها. ويعيد خادم DNS داخلي توجيه كل الطلبات إلى صفحة الجهاز.</p>
  <h3>متابعة الاتصال</h3>
  <p>يتابع الجهاز اتصاله بالراوتر باستمرار، ويعيد الاتصال تلقائياً كل 15 ثانية، أو كل 60 ثانية إذا كان مستخدم متصلاً بنقطة الوصول، حفاظاً على اتصال ذلك المستخدم. وإذا لم يعد الراوتر خلال 3 دقائق ولم يكن أحد متصلاً بنقطة الوصول، يعيد الجهاز التشغيل ويبدأ الاتصال من جديد.</p>
{foot(0)}</section>

<section class="page">
  <h3 style="margin-top:0">الصفحة المحلية وواجهة HTTP</h3>
  <p>صفحة HTML واحدة مضمنة في البرنامج الثابت، يخدمها الجهاز على المنفذ 80، ويُعلن عنها باسم <code>iv-monitor.local</code> عبر بروتوكول mDNS. تستعلم الصفحة الحالة كل ثانية، وترسل الأوامر عبر الواجهة التالية:</p>
  <table><tr><th style="width:11%">الطريقة</th><th style="width:26%">المسار</th><th>الوظيفة</th></tr>{api_rows}</table>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">9</span>التحكم عن بعد عبر MQTT</h2>
  <p>يتصل الجهاز بخادم MQTT عام (<code>broker.hivemq.com</code>) عبر اتصال مشفر بـ TLS على المنفذ 8883، ويدعم المنفذ 1883 منفذاً بديلاً يتناوب معه عند إعادة الاتصال. وتتدرج المهلة بين محاولات الاتصال من 10 ثوانٍ حتى دقيقتين، فيستمر عمل الشاشة والميزان دون انقطاع.</p>
  <table><tr><th style="width:27%">الموضوع (Topic)</th><th style="width:18%">الاتجاه</th><th>المحتوى</th></tr>{topics_rows}</table>
  <h3>توقيع الأوامر</h3>
  <p>يُوقَّع كل أمر بخوارزمية HMAC-SHA256 بمفتاح تحكم مشترك بين الجهاز واللوحة. صيغة الأمر:</p>
  <div class="formula">timestamp_ms | command | HMAC-SHA256(key, "timestamp_ms|command")</div>
  <ul>
    <li>يرفض الجهاز الأمر إذا لم يطابق التوقيع.</li>
    <li>يرفض الأمر إذا كان طابعه الزمني أقدم من آخر أمر مقبول، أو يبعد عن ساعة الجهاز أكثر من 120 ثانية، فلا يمكن إعادة إرسال أمر قديم (Replay attack). وتُضبط ساعة الجهاز من خوادم NTP.</li>
    <li>الأوامر المدعومة: <code>open</code>، <code>close</code>، <code>tare</code>، <code>cal</code>، <code>servo</code>، <code>set</code>.</li>
  </ul>
  <figure>{seq}<figcaption>الشكل 5. مسار أمر الإغلاق من لوحة الإنترنت إلى الصمام</figcaption></figure>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">10</span>لوحة التحكم على الإنترنت</h2>
  <p>اللوحة صفحة ويب ثابتة من ملف واحد (HTML وCSS وJavaScript)، دون خادم خلفي. تتصل بخادم MQTT من المتصفح مباشرة عبر WebSocket مشفر (<code>wss://broker.hivemq.com:8884/mqtt</code>) بمكتبة MQTT.js، وتشترك في مواضيع الحالة والتوفر والتأكيد. وتُوقّع الأوامر في المتصفح بواجهة Web Crypto، مع تنفيذ احتياطي لـ SHA-256 بلغة JavaScript للمتصفحات التي لا تتيحها.</p>
  <ul>
    <li><b>التمييز بين البيانات الحية والمحفوظة:</b> تُعرض آخر حالة محفوظة فور فتح اللوحة، لكن الجهاز لا يُعدّ متصلاً إلا عند وصول حالة جديدة. ويُعرض عمر آخر قراءة.</li>
    <li><b>سطر حال الجهاز:</b> مدة التشغيل، واسم الشبكة، وعنوان الصفحة المحلية، وقوة الإشارة، وعدد مرات انقطاع Wi-Fi وسببها، وسبب آخر إعادة تشغيل.</li>
  </ul>
  <h3>النشر</h3>
  <p>تُنشر اللوحة على GitHub Pages عبر سير عمل GitHub Actions (<code>.github/workflows/pages.yml</code>). عند كل دفع (Push) إلى الفرع <code>main</code>، يرفع سير العمل مجلد <code>dashboard</code> وينشره تلقائياً على العنوان:</p>
  <div class="formula">https://yassin964770.github.io/iv-monitor/</div>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">11</span>الاختبار والتحقق</h2>
  <p>اختُبر النظام على النموذج بتاريخ 6 تشرين الثاني 2026. أُرسلت أوامر MQTT من برنامج اختبار يتصل بالخادم بالطريقة نفسها التي تتصل بها اللوحة، واختُبرت الواجهة المحلية بطلبات HTTP مباشرة:</p>
  <table><tr><th style="width:52%">الاختبار</th><th>النتيجة</th></tr>{tests_rows}</table>
{foot(0)}</section>

<section class="page">
  <h2><span class="no">12</span>الملفات المرفقة</h2>
  <p>يحتوي الملف المضغوط المرفق <code>iv-monitor-code.zip</code> على الشيفرة المصدرية بالإصدار المرفوع على الجهاز، وهو الإصدار الذي أُجريت عليه اختبارات القسم 11، وعلى الملفات التالية داخل المجلد <code>iv-monitor</code>:</p>
  <table><tr><th style="width:31%">الملف</th><th>المحتوى</th><th style="width:15%">الحجم</th></tr>{files_rows}</table>
  <h3>الثوابت الرئيسة في <code>iv_monitor.ino</code></h3>
  <table><tr><th style="width:36%">الثابت</th><th>المعنى</th></tr>{consts_rows}</table>
{foot(0)}</section>

<section class="page">
  <h3 style="margin-top:0">بناء البرنامج الثابت ورفعه</h3>
  <ol>
    <li>تُثبَّت حزمة اللوحات <code>esp32 by Espressif</code> بالإصدار 3.3.12، والمكتبات المذكورة في القسم 6 بإصداراتها، من مدير المكتبات في Arduino IDE.</li>
    <li>يُفتح الملف <code>iv_monitor/iv_monitor.ino</code>، فتظهر الملفات الثلاثة في تبويبات المشروع نفسه، وتُبنى معاً.</li>
    <li>تُختار اللوحة <code>ESP32 Dev Module</code> ومنفذ الجهاز، ثم يُرفع البرنامج. وتُقرأ الرسائل على المنفذ التسلسلي بسرعة 115200.</li>
  </ol>
  <p>وبأداة سطر الأوامر Arduino CLI، من داخل المجلد <code>iv_monitor</code>:</p>
  <div class="formula">arduino-cli compile --fqbn esp32:esp32:esp32 .<br>arduino-cli upload -p COM8 --fqbn esp32:esp32:esp32 .</div>
  <p>يشغل البرنامج المبني 1,257,841 بايت، أي 95% من مساحة البرنامج في الشريحة.</p>
  <h3>نشر لوحة التحكم</h3>
  <p>يُرفع المجلد <code>dashboard</code> وسير العمل <code>.github/workflows/pages.yml</code> إلى مستودع على GitHub، وتُفعَّل خدمة GitHub Pages بمصدر GitHub Actions، فتُنشر اللوحة تلقائياً عند كل دفع إلى الفرع <code>main</code>. ويمكن فتح الملف <code>dashboard/index.html</code> كذلك من أي خادم ويب ثابت، لأنه لا يعتمد على خادم خلفي.</p>
  <p>تتطابق قيم اسم الجهاز والخادم ومفتاح التحكم في الثابت <code>DEVICE</code> بملف اللوحة مع قيم الجهاز، ويُشتق اسم الجهاز من رقم الشريحة، وهو في هذا النموذج <code>iv-c83d26</code>.</p>
{foot(0)}</section>
</body></html>"""

(here / "package.html").write_text(html, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto((here / "package.html").as_uri())
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    pg.pdf(path=str(here / PDF_NAME), format="A4", print_background=True, prefer_css_page_size=True)
    (here / "img").mkdir(exist_ok=True)
    for i, el in enumerate(pg.query_selector_all(".page")):
        el.screenshot(path=str(here / "img" / f"_page{i + 1}.png"))
    b.close()
shutil.copy(here / PDF_NAME, stage / PDF_NAME)

out = repo / "iv-monitor-code.zip"
out.unlink(missing_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(stage.rglob("*")):
        if f.is_file():
            z.write(f, "iv-monitor/" + f.relative_to(stage).as_posix())
print(PDF_NAME, "and", out.name, "written")
