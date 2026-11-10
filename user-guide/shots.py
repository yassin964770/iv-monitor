# Phone-sized screenshots of the device's local page and the online dashboard, for the user guide.
# The device is not needed: its page (from page.h) is served here with a sample reading like the board's in testing,
# and the online dashboard is opened with the same sample reading injected in place of the broker.
import json, pathlib, re, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).parent
out = root / "img"
out.mkdir(exist_ok=True)
page_h = (root.parent / "iv_monitor" / "page.h").read_text(encoding="utf-8")
PAGE = re.search(r'R"rawliteral\((.*)\)rawliteral"', page_h, re.S).group(1)

chart = [round(322.4 - i * 0.045, 1) for i in range(60)]
STATE = {"g": 319.8, "ml": 290, "rate": 32, "mins": 544, "emptyG": 30, "lowMl": 50, "autoCloseMl": 0, "alerts": False,
         "openDeg": 120, "closeDeg": 70, "rateIn": 0, "state": "ok", "valve": "open", "autoClosed": False, "mqtt": True,
         "id": "iv-c83d26", "ssid": "Yassin", "ip": "192.168.100.184", "rssi": -52, "drops": 0, "why": 0, "up": 2460,
         "boot": "power on", "chart": chart}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body, kind = (json.dumps(STATE), "application/json") if self.path.startswith("/api/state") else (PAGE, "text/html; charset=utf-8")
        self.send_response(200); self.send_header("Content-Type", kind); self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *a): pass


srv = HTTPServer(("127.0.0.1", 8765), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as p:
    b = p.chromium.launch()

    def shoot(name, url, prep=None):
        page = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True)
        page.goto(url)
        page.wait_for_timeout(2500)
        if prep: prep(page)
        page.screenshot(path=str(out / f"{name}-top.png"))
        page.evaluate("document.querySelector('details') && (document.querySelector('details').open = true)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(out / f"{name}-full.png"), full_page=True)
        # where each control sits on the full screenshot, for the numbered markers in the guide
        ids = ["ml", "pill", "rate", "left", "g", "chart", "bOpen", "bClose", "tareBtn", "calBtn", "emptyG", "alerts",
               "lowMl", "autoCloseMl", "openDeg", "closeDeg", "saveBtn", "vReal", "netInfo", "wifiBtn", "conn", "health"]
        boxes = page.evaluate("""ids => Object.fromEntries(ids.map(i => [i, document.getElementById(i)])
            .filter(([, e]) => e).map(([i, e]) => { const r = e.getBoundingClientRect();
            return [i, [r.left + scrollX, r.top + scrollY, r.width, r.height]]; }))""", ids)
        size = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
        (out / f"{name}-boxes.json").write_text(json.dumps({"size": size, "boxes": boxes}))
        print(name, page.evaluate("document.body.scrollHeight"))

    shoot("local", "http://127.0.0.1:8765/")

    def online(page):
        # The dashboard would wait for the real device; give it the same sample reading through its own render path.
        page.wait_for_timeout(3000)   # its connection to the broker is up and the stored messages are in
        page.evaluate("""s => { deviceOnline = true; lastSeen = Date.now(); render(s); setConn(); }""", STATE)
        page.wait_for_timeout(300)
    shoot("online", "https://yassin964770.github.io/iv-monitor/", online)
    b.close()
srv.shutdown()
