#!/usr/bin/env python3
"""Generate the 1200x630 (rendered at 2x) Open Graph / Twitter cards.

Renders an HTML template with the site's own fonts (base64-inlined from
assets/fonts/) and the site icon as a watermark, then screenshots each card
with a single headless Chrome driven over the DevTools pipe. Stdlib only;
requires Chrome or Chromium on the machine.

Usage:
  python3 .github/social-card/generate.py          # assets/img/social-card.png
  python3 .github/social-card/generate.py --posts  # assets/img/social/<slug>.png per post
"""

from __future__ import annotations

import base64
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_CARD = REPO_ROOT / "assets" / "img" / "social-card.png"
POST_CARD_DIR = REPO_ROOT / "assets" / "img" / "social"
POSTS_DIR = REPO_ROOT / "_posts"
SCALE = 2
TIMEOUT = 30

# 400-weight subsets already shipped by the site (see assets/css/google-fonts.css).
FONT_SANS = REPO_ROOT / "assets" / "fonts" / "va9c4lja2NVIDdIAAoMR5MfuElaRB0zJt08.woff2"
FONT_SANS_EXT = REPO_ROOT / "assets" / "fonts" / "va9c4lja2NVIDdIAAoMR5MfuElaRB0zHt0_uHA.woff2"
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
    src: url(data:font/woff2;base64,{sans_ext_b64}) format('woff2');
    unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
  }}
  @font-face {{
    font-family: 'Quattrocento Sans';
    font-style: normal;
    font-weight: 400;
    src: url(data:font/woff2;base64,{sans_b64}) format('woff2');
    unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
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
    background: linear-gradient(180deg, #0d1219 0%, #0a0e14 55%, #0b1018 100%);
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
    display: flex;
    align-items: center;
    font-family: 'Source Code Pro', monospace;
    font-size: 26px;
    color: #5b7285;
    letter-spacing: 0.2px;
  }}
  .prompt .cmd {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .prompt .host {{ color: #7d97ab; }}
  .cursor {{
    flex: none;
    width: 15px;
    height: 30px;
    margin-left: 10px;
    background: #3f9dd8;
  }}
  .title {{
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
    <div class="prompt"><span class="cmd"><span class="host">jrogers@joshua.hu</span>:~$ cat <span id="file"></span></span><span class="cursor"></span></div>
    <div>
      <div class="title" id="title"></div>
      <div class="subtitle" id="subtitle"></div>
    </div>
    <div class="domain">https://joshua.hu</div>
  </div>
<script>
  async function render(card) {{
    document.getElementById('file').textContent = card.file;
    document.getElementById('subtitle').textContent = card.subtitle;
    const title = document.getElementById('title');
    title.textContent = card.title;
    title.style.fontSize = card.titlePx + 'px';
    await Promise.all([
      document.fonts.load(card.titlePx + "px 'Quattrocento Sans'", card.title + card.subtitle),
      document.fonts.load("26px 'Source Code Pro'", 'jrogers@joshua.hu:~$ cat ' + card.file + 'https://joshua.hu'),
      document.querySelector('.watermark').decode(),
    ]);
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  }}
</script>
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


def title_px(title: str) -> int:
    n = len(title)
    return 80 if n <= 30 else 68 if n <= 60 else 58 if n <= 95 else 50 if n <= 140 else 42


def post_title(path: Path) -> str:
    front = path.read_text(encoding="utf-8").split("\n---", 1)[0]
    match = re.search(r"^title:[ \t]*(.+?)[ \t]*$", front, re.M)
    if not match:
        sys.exit(f"error: no title in {path}")
    value = match.group(1)
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def post_slug(path: Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)


class Chrome:
    """Minimal DevTools protocol client over --remote-debugging-pipe (fds 3 and 4)."""

    def __init__(self, binary: str, profile: str) -> None:
        cmd_r, self._cmd_w = os.pipe()
        self._res_r, res_w = os.pipe()
        args = [
            binary,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--remote-debugging-pipe",
            f"--user-data-dir={profile}",
            "about:blank",
        ]
        if os.environ.get("GITHUB_ACTIONS"):
            args.append("--no-sandbox")
        self._proc = subprocess.Popen(
            ["/bin/sh", "-c", f'exec "$@" 3<&{cmd_r} 4>&{res_w}', "sh", *args],
            pass_fds=(cmd_r, res_w),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        os.close(cmd_r)
        os.close(res_w)
        self._buf = b""
        self._next_id = 0
        self._events: list[dict] = []

    def _read(self, deadline: float) -> dict:
        while b"\0" not in self._buf:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self._res_r], [], [], left)[0]:
                raise TimeoutError("Chrome stopped responding")
            chunk = os.read(self._res_r, 1 << 20)
            if not chunk:
                raise RuntimeError("Chrome exited unexpectedly")
            self._buf += chunk
        raw, self._buf = self._buf.split(b"\0", 1)
        return json.loads(raw)

    def send(self, method: str, params: dict | None = None, session: str | None = None) -> dict:
        self._next_id += 1
        msg = {"id": self._next_id, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        os.write(self._cmd_w, json.dumps(msg).encode() + b"\0")
        deadline = time.monotonic() + TIMEOUT
        while True:
            reply = self._read(deadline)
            if reply.get("id") == self._next_id:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                result = reply["result"]
                if "exceptionDetails" in result:
                    raise RuntimeError(f"{method}: {result['exceptionDetails']}")
                return result
            if "method" in reply:
                self._events.append(reply)

    def wait_for(self, method: str, session: str) -> None:
        deadline = time.monotonic() + TIMEOUT
        while True:
            for event in self._events:
                if event.get("method") == method and event.get("sessionId") == session:
                    self._events.remove(event)
                    return
            self._events.append(self._read(deadline))

    def close(self) -> None:
        try:
            os.killpg(self._proc.pid, signal.SIGKILL)
        except OSError:
            pass
        self._proc.wait()
        os.close(self._cmd_w)
        os.close(self._res_r)


def render(page_html: str, cards: list[tuple[dict, Path]]) -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(page_html, encoding="utf-8")
        chrome = Chrome(find_chrome(), f"{tmp}/profile")
        try:
            target = chrome.send("Target.createTarget", {"url": "about:blank"})["targetId"]
            session = chrome.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
            chrome.send("Page.enable", session=session)
            chrome.send(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1200, "height": 630, "deviceScaleFactor": SCALE, "mobile": False},
                session,
            )
            chrome.send("Page.navigate", {"url": page.as_uri()}, session)
            chrome.wait_for("Page.loadEventFired", session)
            for card, out in cards:
                chrome.send("Runtime.evaluate", {"expression": f"render({json.dumps(card)})", "awaitPromise": True}, session)
                shot = chrome.send("Page.captureScreenshot", {"format": "png"}, session)
                out.write_bytes(base64.b64decode(shot["data"]))
                print(f"wrote {out.relative_to(REPO_ROOT)} ({out.stat().st_size} bytes)")
        finally:
            chrome.close()


def main() -> int:
    page_html = HTML.format(
        sans_b64=b64(FONT_SANS), sans_ext_b64=b64(FONT_SANS_EXT), mono_b64=b64(FONT_MONO), mark_b64=b64(WATERMARK)
    )

    if sys.argv[1:] == ["--posts"]:
        POST_CARD_DIR.mkdir(parents=True, exist_ok=True)
        cards = []
        for path in sorted(POSTS_DIR.glob("*.md")):
            title, slug = post_title(path), post_slug(path)
            card = {"title": title, "titlePx": title_px(title), "subtitle": "Joshua Rogers\u2019 Scribbles", "file": f"{slug}.md"}
            cards.append((card, POST_CARD_DIR / f"{slug}.png"))
    elif not sys.argv[1:]:
        card = {
            "title": "Joshua Rogers\u2019 Scribbles",
            "titlePx": 84,
            "subtitle": "Security research, systems engineering, and long-form writeups by Joshua Rogers.",
            "file": "scribbles.md",
        }
        cards = [(card, SITE_CARD)]
    else:
        sys.exit(__doc__)

    render(page_html, cards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
