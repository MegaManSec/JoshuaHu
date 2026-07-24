#!/usr/bin/env python3
"""Generate assets/img/social-card.png (1200x630 Open Graph / Twitter card).

Renders an HTML template with the site's own fonts (base64-inlined from
assets/fonts/) and the site icon as a watermark, then screenshots it with
headless Chrome. Stdlib only; requires Chrome or Chromium on the machine.

Usage: python3 .github/social-card/generate.py
"""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PNG = REPO_ROOT / "assets" / "img" / "social-card.png"

# Latin 400-weight subsets already shipped by the site (see assets/css/google-fonts.css).
FONT_SANS = REPO_ROOT / "assets" / "fonts" / "va9c4lja2NVIDdIAAoMR5MfuElaRB0zJt08.woff2"
FONT_MONO = REPO_ROOT / "assets" / "fonts" / "HI_diYsKILxRpg3hIP6sJ7fM7PqPMcMnZFqUwX28DMyQtMlrTA.woff2"
WATERMARK = REPO_ROOT / "web-app-manifest-512x512.png"

CHROME_CANDIDATES = [
    os.environ.get("CHROME"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome"),
    shutil.which("chromium-browser"),
    shutil.which("chromium"),
]

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'Quattrocento Sans';
    font-style: normal;
    font-weight: 400;
    src: url(data:font/woff2;base64,{sans_b64}) format('woff2');
  }}
  @font-face {{
    font-family: 'Source Code Pro';
    font-style: normal;
    font-weight: 400;
    src: url(data:font/woff2;base64,{mono_b64}) format('woff2');
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1200px; height: 630px; overflow: hidden; }}
  body {{
    position: relative;
    font-family: 'Quattrocento Sans', sans-serif;
    background: linear-gradient(160deg, #0d1219 0%, #0a0e14 55%, #0b1018 100%);
    color: #f2f5f7;
  }}
  .accent {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 8px;
    background: #0065a3;
  }}
  .watermark {{
    position: absolute;
    right: -110px;
    bottom: -150px;
    width: 560px;
    opacity: 0.13;
  }}
  .frame {{
    position: absolute;
    inset: 0;
    padding: 74px 84px 64px 84px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .prompt {{
    font-family: 'Source Code Pro', monospace;
    font-size: 26px;
    color: #5b7285;
    letter-spacing: 0.2px;
  }}
  .prompt .host {{ color: #7d97ab; }}
  .cursor {{
    display: inline-block;
    width: 15px;
    height: 30px;
    margin-left: 10px;
    vertical-align: text-bottom;
    background: #3f9dd8;
  }}
  .title {{
    font-size: 84px;
    line-height: 1.12;
    letter-spacing: -0.5px;
    color: #f2f5f7;
  }}
  .subtitle {{
    margin-top: 26px;
    font-size: 35px;
    line-height: 1.4;
    color: #93a4b3;
    max-width: 900px;
  }}
  .domain {{
    font-family: 'Source Code Pro', monospace;
    font-size: 30px;
    color: #3f9dd8;
  }}
</style>
</head>
<body>
  <div class="accent"></div>
  <img class="watermark" src="data:image/png;base64,{mark_b64}" alt="">
  <div class="frame">
    <div class="prompt"><span class="host">jrogers@joshua.hu</span>:~$ cat scribbles.md<span class="cursor"></span></div>
    <div>
      <div class="title">Joshua Rogers&rsquo; Scribbles</div>
      <div class="subtitle">Security research, systems engineering, and long-form writeups by Joshua Rogers.</div>
    </div>
    <div class="domain">https://joshua.hu</div>
  </div>
</body>
</html>
"""


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def find_chrome() -> str:
    for cand in CHROME_CANDIDATES:
        if cand and Path(cand).exists():
            return cand
    sys.exit("error: no Chrome/Chromium found (set CHROME=/path/to/chrome)")


def main() -> int:
    html = HTML.format(sans_b64=b64(FONT_SANS), mono_b64=b64(FONT_MONO), mark_b64=b64(WATERMARK))
    chrome = find_chrome()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--window-size=1200,630",
                f"--screenshot={OUT_PNG}",
                f"--user-data-dir={tmp}/profile",
                page.as_uri(),
            ],
            check=True,
            capture_output=True,
        )

    print(f"wrote {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
