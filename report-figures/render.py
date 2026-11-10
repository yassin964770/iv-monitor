# Renders each figure's HTML to a high-resolution PNG (3x, about 300 dpi at report width).
import sys, pathlib
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
names = sys.argv[1:] or ["fig1-board", "fig2-wiring"]
with sync_playwright() as p:
    b = p.chromium.launch()
    for n in names:
        page = b.new_page(device_scale_factor=3)
        page.goto((here / f"{n}.html").as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        el = page.query_selector(".page")
        el.screenshot(path=str(here / f"{n}.png"))
        print("wrote", n + ".png")
    b.close()
