#!/usr/bin/env python3
"""Fail if the built site (_site/) loads anything from another origin.

Every image, video, script, stylesheet, font, icon and iframe must be served
from joshua.hu itself (relative URLs, https://joshua.hu/..., or data: URIs).
Links to other sites are fine; only things the browser fetches on its own are
checked: src/srcset/poster/data attributes, fetching <link> rels, url() and
@import in <style>, style="" and the site's CSS files.

Run after `bundle exec jekyll build`:

    python3 .github/scripts/validate_resources.py [path/to/_site]

Exits non-zero (and emits GitHub Actions error annotations) on any hit.
Runs with the stdlib only -- no pip install required.
"""

from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_HOSTS = {"joshua.hu", "www.joshua.hu"}
# Directories in _site that contain artifacts, not pages.
SKIP_DIRS = {"files", "vendor"}

URL_ATTRS = {
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "iframe": ("src",),
    "embed": ("src",),
    "object": ("data",),
    "script": ("src",),
    "input": ("src",),
    "image": ("href", "xlink:href"),
    "use": ("href", "xlink:href"),
}
FETCHING_RELS = {
    "stylesheet", "icon", "apple-touch-icon", "mask-icon", "manifest",
    "preload", "modulepreload", "prefetch", "prerender", "preconnect", "dns-prefetch",
}
CSS_URL = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)|@import\s+(['"])(.*?)\3""", re.IGNORECASE)


def is_external(url: str) -> bool:
    url = url.strip()
    if not url or url.lower().startswith("data:"):
        return False
    parts = urlsplit(url)
    if parts.scheme and parts.scheme.lower() not in ("http", "https"):
        return parts.scheme.lower() not in ("about", "blob")
    return bool(parts.netloc) and parts.hostname not in SITE_HOSTS


def srcset_urls(value: str) -> list[str]:
    return [c.strip().split()[0] for c in value.split(",") if c.strip()]


def css_urls(css: str) -> list[str]:
    return [m.group(2) or m.group(4) or "" for m in CSS_URL.finditer(css)]


class Resources(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hits: list[str] = []
        self._in_style = False

    def _check(self, where: str, url: str) -> None:
        if is_external(url):
            self.hits.append(f"{where} loads {url.strip()}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        for attr in URL_ATTRS.get(tag, ()):
            if attr in a:
                urls = srcset_urls(a[attr]) if attr == "srcset" else [a[attr]]
                for url in urls:
                    self._check(f"<{tag} {attr}>", url)
        if tag == "link" and FETCHING_RELS & set(a.get("rel", "").lower().split()):
            self._check(f"<link rel=\"{a.get('rel')}\">", a.get("href", ""))
        if "style" in a:
            for url in css_urls(a["style"]):
                self._check(f"<{tag} style>", url)
        if tag == "style":
            self._in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            for url in css_urls(data):
                self._check("<style>", url)


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

    files = [
        p for p in sorted(site_dir.rglob("*"))
        if p.suffix in (".html", ".css") and p.is_file()
        and not (set(p.relative_to(site_dir).parts[:-1]) & SKIP_DIRS)
    ]
    if not any(p.suffix == ".html" for p in files):
        print(f"error: no HTML pages found in {site_dir}", file=sys.stderr)
        return 2

    failed: list[tuple[Path, list[str]]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".css":
            hits = [f"CSS loads {u.strip()}" for u in css_urls(text) if is_external(u)]
        else:
            parser = Resources()
            parser.feed(text)
            hits = parser.hits
        if hits:
            failed.append((path.relative_to(site_dir), hits))

    if failed:
        total = sum(len(h) for _, h in failed)
        print(f"External resource check failed: {total} resource(s) from other origins across {len(failed)} file(s).")
        print("Self-host them under files/ (images) or assets/ (fonts, scripts, styles).\n")
        for path, hits in failed:
            for hit in hits:
                emit(path, hit)
        return 1

    print(f"OK: {len(files)} pages and stylesheets load nothing from other origins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
