#!/usr/bin/env python3
"""Render every built page at phone and desktop widths and fail on overflow.

Checks, at each width in WIDTHS:
  - nothing makes the page wider than the screen (sideways scrolling);
  - nothing in a post sticks out past the text column.
Content inside its own scroll area (code blocks, wide tables) is exempt.

Serves _site/ on localhost and drives headless Chrome over the DevTools pipe
(the same client as .github/social-card/generate.py). Run after
`bundle exec jekyll build`:

    python3 .github/scripts/validate_layout.py [path/to/_site]

Exits non-zero (and emits GitHub Actions error annotations) on any overflow.
Runs with the stdlib only -- no pip install required; needs Chrome/Chromium.
"""

from __future__ import annotations

import functools
import json
import os
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT / ".github" / "social-card"))
from generate import Chrome, find_chrome  # noqa: E402

WIDTHS = (320, 375, 1280)
# Directories in _site that contain artifacts, not pages.
SKIP_DIRS = {"files", "assets", "vendor"}

PROBE = """
(async (width) => {
  await document.fonts.ready;
  const scrollers = new Set([...document.body.querySelectorAll('*')].filter(el => getComputedStyle(el).overflowX !== 'visible'));
  const scrolls = el => {
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      if (scrollers.has(a)) return true;
    }
    return false;
  };
  const describe = el => {
    const text = (el.textContent || el.getAttribute('src') || '').replace(/\\s+/g, ' ').trim();
    const cls = el.classList.length ? '.' + [...el.classList].join('.') : '';
    return `<${el.tagName.toLowerCase()}${cls}> "${text.slice(0, 50)}"`;
  };
  const outermost = els => [...els].filter(el => !els.has(el.parentElement));
  const problems = [];
  const all = [...document.body.querySelectorAll('*')].filter(el => !scrolls(el));
  const wide = new Set(all.filter(el => el.getBoundingClientRect().right > width + 0.5));
  for (const el of outermost(wide)) {
    const by = el.getBoundingClientRect().right - width;
    problems.push(`${describe(el)} makes the page ${Math.round(by)}px wider than the screen`);
  }
  const article = document.querySelector('article');
  if (article) {
    const style = getComputedStyle(article);
    const column = article.getBoundingClientRect().right - parseFloat(style.paddingRight) - parseFloat(style.borderRightWidth);
    const past = new Set([...article.querySelectorAll('*')].filter(el => !scrolls(el) && !wide.has(el)
      && [...el.getClientRects()].some(r => r.width && r.right > column + 0.5)));
    for (const el of outermost(past)) {
      const by = Math.max(...[...el.getClientRects()].map(r => r.right)) - column;
      problems.push(`${describe(el)} sticks out ${by.toFixed(1)}px past the text column`);
    }
  }
  return problems;
})
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def emit(path: Path, message: str) -> None:
    print(f"  - {path}: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", " ").replace("\r", " ")
        print(f"::error file={path}::{safe}")


def main() -> int:
    site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "_site"
    if not site_dir.is_dir():
        print(f"error: built site not found: {site_dir} (run `bundle exec jekyll build` first)", file=sys.stderr)
        return 2

    pages = [
        p.relative_to(site_dir) for p in sorted(site_dir.rglob("*.html"))
        if not (set(p.relative_to(site_dir).parts[:-1]) & SKIP_DIRS)
    ]
    if not pages:
        print(f"error: no HTML pages found in {site_dir}", file=sys.stderr)
        return 2

    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(site_dir)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"

    failed: list[tuple[Path, list[str]]] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        chrome = Chrome(find_chrome(), f"{tmp}/profile")
        try:
            target = chrome.send("Target.createTarget", {"url": "about:blank"})["targetId"]
            session = chrome.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
            chrome.send("Page.enable", session=session)
            results: dict[Path, list[str]] = {}
            for width in WIDTHS:
                chrome.send(
                    "Emulation.setDeviceMetricsOverride",
                    {"width": width, "height": 800, "deviceScaleFactor": 1, "mobile": width < 768},
                    session,
                )
                for page in pages:
                    chrome.send("Page.navigate", {"url": f"{base}/{page.as_posix()}"}, session)
                    chrome.wait_for("Page.loadEventFired", session)
                    reply = chrome.send(
                        "Runtime.evaluate",
                        {"expression": f"{PROBE}({width})", "awaitPromise": True, "returnByValue": True},
                        session,
                    )
                    for problem in reply["result"]["value"]:
                        results.setdefault(page, []).append(f"at {width}px: {problem}")
            failed = sorted(results.items())
        finally:
            chrome.close()
            server.shutdown()

    if failed:
        total = sum(len(p) for _, p in failed)
        print(f"Layout check failed: {total} overflow(s) across {len(failed)} of {len(pages)} page(s).\n")
        for page, problems in failed:
            for problem in problems:
                emit(page, problem)
        return 1

    print(f"OK: {len(pages)} pages fit the screen and the text column at {', '.join(f'{w}px' for w in WIDTHS)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
