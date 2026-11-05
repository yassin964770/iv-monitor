// The page the ESP32 serves at http://192.168.4.1. Self-contained: the phone has no internet on this Wi-Fi.
#pragma once

const char PAGE[] PROGMEM = R"rawliteral(<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>مراقبة المحلول الوريدي</title>
<style>
:root{--bg:#eef2f1;--card:#fff;--ink:#12302f;--muted:#53696a;--line:#d5dfdc;--accent:#0b6e69;--on:#fff;
--ok:#1e7a46;--okbg:#dcefe3;--warn:#8a5200;--warnbg:#fbecd2;--bad:#b3261e;--badbg:#f8dedb;--info:#2c5d8a;--infobg:#dde9f4;
--fill:#3fa9c9;--track:#e2ebe8;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0f1918;--card:#16231f;--ink:#e3eeeb;--muted:#9db3af;--line:#2b3d3a;--accent:#4fc3b8;--on:#0f1918;
--ok:#6fd199;--okbg:#1d3a2a;--warn:#f0b35a;--warnbg:#3d2f17;--bad:#f08a7e;--badbg:#45211d;--info:#8cc0ee;--infobg:#1c2f42;
--fill:#4fb8d6;--track:#22332f;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",Tahoma,"Noto Sans Arabic",system-ui,sans-serif;line-height:1.5;-webkit-tap-highlight-color:transparent}
main{max-width:520px;margin:0 auto;padding:16px;display:grid;gap:12px}
header{display:flex;justify-content:space-between;align-items:center;padding:4px 2px}
h1{font-size:20px;margin:0}
.conn{font-size:13px;color:var(--muted);display:flex;align-items:center;gap:6px}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok)}
.conn.off .dot{background:var(--bad)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.label{font-size:13px;color:var(--muted)}
.num{font-variant-numeric:tabular-nums;direction:ltr;unicode-bidi:isolate}
.hero{display:grid;grid-template-columns:64px 1fr;gap:18px;align-items:center}
.bottle{width:56px;height:124px;border:2px solid var(--line);border-radius:12px 12px 18px 18px;position:relative;overflow:hidden;background:var(--track);margin-inline:auto}
.bottle::before{content:"";position:absolute;top:-2px;left:50%;width:18px;height:8px;margin-left:-9px;background:var(--line);border-radius:0 0 4px 4px;z-index:1}
.bottle i{position:absolute;left:0;right:0;bottom:0;top:0;background:var(--fill);transform:scaleY(0);transform-origin:bottom;transition:transform .6s ease}
.big{font-size:52px;font-weight:700;line-height:1.05}
.big small{font-size:18px;font-weight:500;color:var(--muted)}
.pill{display:inline-block;margin-top:10px;padding:3px 11px;border-radius:99px;font-size:13.5px;font-weight:600}
.pill.ok{background:var(--okbg);color:var(--ok)}.pill.warn{background:var(--warnbg);color:var(--warn)}
.pill.bad{background:var(--badbg);color:var(--bad)}.pill.info{background:var(--infobg);color:var(--info)}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 10px}
.stat b{display:block;font-size:22px;font-weight:700;margin-top:2px}
.stat span{font-size:12px;color:var(--muted)}
canvas{display:block;width:100%;height:96px;margin-top:8px}
.axis{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:4px}
.valve-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.vstate{font-weight:600}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:10px}
button{font:inherit;border-radius:12px;border:1.5px solid var(--accent);padding:14px 10px;font-size:17px;font-weight:600;cursor:pointer;background:transparent;color:var(--accent)}
button.solid{background:var(--accent);color:var(--on)}
button[aria-pressed="true"]{box-shadow:0 0 0 3px var(--infobg)}
button:disabled{opacity:.55;cursor:default}
button:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.small{font-size:14px;padding:9px 12px;border-radius:10px}
.note{font-size:13px;color:var(--muted);margin:10px 0 0}
details summary{cursor:pointer;font-weight:600;list-style:none;display:flex;justify-content:space-between}
details summary::after{content:"+";color:var(--muted)}
details[open] summary::after{content:"−"}
.grid{display:grid;gap:12px;margin-top:14px}
.field{display:grid;grid-template-columns:1fr 92px auto;gap:8px;align-items:center}
.field label{font-size:14px}
input{font:inherit;width:100%;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);text-align:center}
.sep{border-top:1px solid var(--line);margin:4px 0}
#msg{min-height:1.4em;font-size:13.5px;color:var(--muted)}
#msg.err{color:var(--bad)}
</style>
</head>
<body>
<main>
  <header>
    <h1>مراقبة المحلول الوريدي</h1>
    <div class="conn" id="conn"><span class="dot"></span><span id="connText">متصل</span></div>
  </header>

  <section class="card hero">
    <div class="bottle" aria-hidden="true"><i id="level"></i></div>
    <div>
      <div class="label">الكمية المتبقية</div>
      <div class="big"><span class="num" id="ml">--</span> <small>مل</small></div>
      <span class="pill info" id="pill" role="status">جارٍ جمع القراءات</span>
    </div>
  </section>

  <section class="stats">
    <div class="stat"><span>معدل التدفق</span><b class="num" id="rate">--</b><span>مل/ساعة</span></div>
    <div class="stat"><span>الوقت المتبقي</span><b class="num" id="left">--</b><span>ساعة:دقيقة</span></div>
    <div class="stat"><span>الوزن</span><b class="num" id="g">--</b><span>غرام</span></div>
  </section>

  <section class="card">
    <div class="label">الوزن خلال آخر 5 دقائق</div>
    <canvas id="chart" aria-label="مخطط الوزن خلال آخر 5 دقائق"></canvas>
    <div class="axis"><span>الآن</span><span>قبل 5 دقائق</span></div>
  </section>

  <section class="card">
    <div class="valve-head">
      <div><div class="label">الصمام</div><div class="vstate" id="vstate">غير معروف</div></div>
    </div>
    <div class="btns">
      <button type="button" id="bOpen" aria-pressed="false">فتح</button>
      <button type="button" id="bClose" class="solid" aria-pressed="false">إغلاق</button>
    </div>
    <p class="note" id="vnote">للاختبار بالماء فقط، ولا يُستخدم على المرضى.</p>
  </section>

  <section class="card">
    <details id="settings">
      <summary>الإعدادات والمعايرة</summary>
      <div class="grid">
        <p class="note" id="remoteInfo"></p>
        <div class="field">
          <label for="tareBtn">تصفير الميزان (دون حمل على الخطاف)</label><span></span>
          <button type="button" class="small" id="tareBtn">تصفير</button>
        </div>
        <div class="field">
          <label for="calG">معايرة بوزن معروف (غرام)</label>
          <input id="calG" type="number" inputmode="decimal" min="1" placeholder="500">
          <button type="button" class="small" id="calBtn">معايرة</button>
        </div>
        <div class="sep"></div>
        <div class="field"><label for="emptyG">وزن الكيس الفارغ (غرام)</label><input id="emptyG" type="number" inputmode="decimal" min="0"><span></span></div>
        <div class="field"><label for="lowMl">حدّ تنبيه انخفاض الكمية (مل)</label><input id="lowMl" type="number" inputmode="decimal" min="0"><span></span></div>
        <div class="field"><label for="autoCloseMl">الإغلاق التلقائي عند (مل، 0 للتعطيل)</label><input id="autoCloseMl" type="number" inputmode="decimal" min="0"><span></span></div>
        <div class="field"><label for="openDeg">زاوية الفتح</label><input id="openDeg" type="number" inputmode="numeric" min="0" max="180"><button type="button" class="small" data-try="openDeg">اختبار</button></div>
        <div class="field"><label for="closeDeg">زاوية الإغلاق</label><input id="closeDeg" type="number" inputmode="numeric" min="0" max="180"><button type="button" class="small" data-try="closeDeg">اختبار</button></div>
        <button type="button" class="solid" id="saveBtn">حفظ الإعدادات</button>
        <div id="msg" role="status"></div>
      </div>
    </details>
  </section>
</main>

<script>
const $ = id => document.getElementById(id);
let full = 0, busy = false, filled = false, tareArmed = false, last = null;

async function api(path, body) {
  const r = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams(body) } : { cache: 'no-store' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
const fmt = (v, d = 0) => v == null ? '--' : Number(v).toFixed(d);
const say = (t, err) => { $('msg').textContent = t; $('msg').className = err ? 'err' : ''; };

const STATES = {
  ok: ['طبيعي', 'ok'], low: ['الكمية منخفضة', 'warn'], stopped: ['توقف التدفق', 'bad'],
  closed: ['الصمام مغلق', 'info'], warming: ['جارٍ جمع القراءات', 'info']
};

function render(s) {
  last = s;
  $('ml').textContent = fmt(s.ml);
  if (s.ml != null) full = Math.max(full, s.ml);
  $('level').style.transform = 'scaleY(' + (full > 0 && s.ml != null ? Math.min(1, s.ml / full) : 0) + ')';
  $('g').textContent = fmt(s.g, 1);
  $('rate').textContent = fmt(s.rate, 0);
  $('left').textContent = s.mins == null ? '--' : Math.floor(s.mins / 60) + ':' + String(s.mins % 60).padStart(2, '0');

  const st = STATES[s.state] || STATES.warming;
  $('pill').className = 'pill ' + st[1];
  $('pill').textContent = s.state === 'warming' && s.rateIn > 0 ? 'جارٍ جمع القراءات، يظهر المعدل خلال ' + s.rateIn + ' ثانية' : st[0];

  const v = { open: 'مفتوح', closed: 'مغلق', unknown: 'غير معروف' }[s.valve];
  $('vstate').textContent = v + (s.autoClosed ? ' (أُغلق تلقائياً عند انخفاض الكمية)' : '');
  $('bOpen').setAttribute('aria-pressed', String(s.valve === 'open'));
  $('bClose').setAttribute('aria-pressed', String(s.valve === 'closed'));

  if (!filled) {
    ['emptyG', 'lowMl', 'autoCloseMl', 'openDeg', 'closeDeg'].forEach(k => $(k).value = fmt(s[k]));
    filled = true;
  }
  draw(s.chart || []);
}

function draw(pts) {
  const c = $('chart'), dpr = window.devicePixelRatio || 1, w = c.clientWidth, h = c.clientHeight;
  c.width = w * dpr; c.height = h * dpr;
  const x = c.getContext('2d'); x.scale(dpr, dpr); x.clearRect(0, 0, w, h);
  const css = getComputedStyle(document.documentElement);
  if (pts.length < 2) {
    x.fillStyle = css.getPropertyValue('--muted'); x.font = '13px sans-serif'; x.textAlign = 'center';
    x.fillText('يظهر المخطط بعد دقيقة تقريباً', w / 2, h / 2); return;
  }
  let lo = Math.min(...pts), hi = Math.max(...pts);
  if (hi - lo < 4) { const m = (hi + lo) / 2; lo = m - 2; hi = m + 2; }
  const px = i => i / (pts.length - 1) * w, py = v => 6 + (hi - v) / (hi - lo) * (h - 12);
  x.beginPath(); pts.forEach((v, i) => i ? x.lineTo(px(i), py(v)) : x.moveTo(px(i), py(v)));
  x.lineWidth = 2.5; x.strokeStyle = css.getPropertyValue('--accent'); x.lineJoin = 'round'; x.stroke();
  x.lineTo(px(pts.length - 1), h); x.lineTo(px(0), h); x.closePath();
  x.globalAlpha = .12; x.fillStyle = css.getPropertyValue('--accent'); x.fill(); x.globalAlpha = 1;
  const lv = pts[pts.length - 1];
  x.beginPath(); x.arc(px(pts.length - 1), py(lv), 4, 0, 7); x.fillStyle = css.getPropertyValue('--accent'); x.fill();
}

function setConn(ok) {
  $('conn').className = ok ? 'conn' : 'conn off';
  $('connText').textContent = ok ? (last && last.mqtt ? 'متصل، والسحابة متصلة' : 'متصل') : 'انقطع الاتصال';
}

async function poll() {
  try { render(await api('/api/state')); setConn(true); }
  catch (e) { setConn(false); }
  finally { setTimeout(poll, 1000); }
}

async function act(path, body, okText) {
  if (busy) return;
  busy = true; document.querySelectorAll('button').forEach(b => b.disabled = true);
  try { render(await api(path, body)); if (okText) say(okText); }
  catch (e) { say('تعذّر التنفيذ: ' + (e.message || 'انقطع الاتصال'), true); }
  finally { busy = false; document.querySelectorAll('button').forEach(b => b.disabled = false); }
}

$('bOpen').onclick = () => act('/api/valve', { to: 'open' });
$('bClose').onclick = () => act('/api/valve', { to: 'close' });
$('tareBtn').onclick = () => {
  if (!tareArmed) { tareArmed = true; $('tareBtn').textContent = 'تأكيد'; say('أزل الكيس عن الخطاف، ثم اضغط "تأكيد" خلال 5 ثوانٍ.'); setTimeout(() => { tareArmed = false; $('tareBtn').textContent = 'تصفير'; }, 5000); return; }
  tareArmed = false; $('tareBtn').textContent = 'تصفير';
  act('/api/tare', {}, 'تم تصفير الميزان.');
};
$('calBtn').onclick = () => {
  const g = parseFloat($('calG').value);
  if (!(g > 0)) { say('أدخل الوزن المعروف بالغرام، مثلاً 500.', true); return; }
  act('/api/cal', { g }, 'تمت المعايرة على ' + g + ' غرام.');
};
document.querySelectorAll('[data-try]').forEach(b => b.onclick = () => {
  const d = parseInt($(b.dataset.try).value, 10);
  if (!(d >= 0 && d <= 180)) { say('يجب أن تكون الزاوية بين 0 و180.', true); return; }
  act('/api/servo', { deg: d }, 'تم تحريك المحرك إلى ' + d + ' درجة.');
});
$('saveBtn').onclick = () => {
  const body = {};
  for (const k of ['emptyG', 'lowMl', 'autoCloseMl', 'openDeg', 'closeDeg']) {
    const v = parseFloat($(k).value);
    if (isNaN(v) || v < 0) { say('تحقق من قيمة "' + $(k).labels[0].textContent + '".', true); return; }
    body[k] = v;
  }
  act('/api/set', body, 'تم حفظ الإعدادات.');
};
fetch('/api/info').then(r => r.json()).then(i => {
  $('remoteInfo').textContent = 'للدخول من لوحة التحكم عن بعد: اسم الجهاز ' + i.id + '، ورمز التحكم ' + i.key + '.';
}).catch(() => {});
poll();
</script>
</body>
</html>)rawliteral";
