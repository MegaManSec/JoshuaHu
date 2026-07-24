#!/usr/bin/env python3
"""Validate social/structured metadata in the built site (_site/).

Complements validate_posts.py (which checks source frontmatter): this script
checks what actually ships -- Open Graph and Twitter tags, JSON-LD, canonical
URLs, image existence and dimensions, and cross-page uniqueness.

Run after `bundle exec jekyll build`:

    python3 .github/scripts/validate_metadata.py [path/to/_site]

Exits non-zero (and emits GitHub Actions error annotations) if any page fails.
Runs with the stdlib only -- no pip install required.
"""

from __future__ import annotations

import json
import os
import struct
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_URL = "https://joshua.hu"
SOCIAL_CARD = "/assets/img/social-card.png"
SOCIAL_CARD_DIMS = (1200, 630)
# Directories in _site that contain artifacts, not pages.
SKIP_DIRS = {"files", "assets", "vendor"}
# Pages that must carry a Person JSON-LD entity.
PERSON_PAGES = {"index.html", "about.html"}
REQUIRED_SITE_FILES = ["sitemap.xml", "feed.xml", "rss-feed.xml", "llms.txt", "llms-full.txt", "site.webmanifest"]


class Head(HTMLParser):
    """Collects <title>, meta tags, canonical link, and JSON-LD blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.titles: list[str] = []
        self.meta: dict[str, list[str]] = defaultdict(list)
        self.canonical: list[str] = []
        self.json_ld: list[str] = []
        self._in_title = False
        self._in_json_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
            self.titles.append("")
        elif tag == "meta":
            # jekyll-seo-tag emits merged tags like
            # <meta name="twitter:description" property="og:description" ...>,
            # so record the tag under both keys.
            for key in {a.get("property"), a.get("name")}:
                if key:
                    self.meta[key].append(a.get("content") or "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical.append(a.get("href") or "")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_json_ld = True
            self.json_ld.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.titles[-1] += data
        elif self._in_json_ld:
            self.json_ld[-1] += data


def png_dims(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as fh:
            header = fh.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def local_path_for(url: str, site_dir: Path) -> Path | None:
    """Map an absolute joshua.hu URL (or site-root path) to a file in _site."""
    if url.startswith(SITE_URL):
        url = url[len(SITE_URL):]
    if not url.startswith("/"):
        return None
    return site_dir / url.lstrip("/")


def check_page(page: Path, site_dir: Path) -> tuple[list[str], Head]:
    errors: list[str] = []
    head = Head()
    head.feed(page.read_text(encoding="utf-8", errors="replace"))

    titles = [t.strip() for t in head.titles]
    if len(titles) != 1:
        errors.append(f"expected exactly one <title>, found {len(titles)}")
    elif not titles[0]:
        errors.append("<title> is empty")

    for key in ("description", "twitter:card", "twitter:description", "twitter:image"):
        values = head.meta.get(key, [])
        if not values or not values[0].strip():
            errors.append(f"missing or empty meta `{key}`")

    for key in ("og:title", "og:description", "og:url", "og:site_name", "og:type"):
        if not any(v.strip() for v in head.meta.get(key, [])):
            errors.append(f"missing or empty meta `{key}`")

    og_images = head.meta.get("og:image", [])
    if len(og_images) != 1:
        errors.append(f"expected exactly one og:image, found {len(og_images)}")
    else:
        img_url = og_images[0]
        local = local_path_for(img_url, site_dir)
        if local is None:
            errors.append(f"og:image is not a joshua.hu URL: {img_url}")
        elif not local.is_file():
            errors.append(f"og:image points at a missing file: {img_url}")
        else:
            dims = png_dims(local) if local.suffix == ".png" else None
            if img_url.endswith(SOCIAL_CARD) and dims != SOCIAL_CARD_DIMS:
                errors.append(f"social card is {dims}, expected {SOCIAL_CARD_DIMS}")
            declared_w = (head.meta.get("og:image:width") or [None])[0]
            declared_h = (head.meta.get("og:image:height") or [None])[0]
            if dims and declared_w and declared_h and (str(dims[0]), str(dims[1])) != (declared_w, declared_h):
                errors.append(
                    f"og:image:width/height ({declared_w}x{declared_h}) disagree with actual image ({dims[0]}x{dims[1]})"
                )

    if not head.canonical:
        errors.append("missing <link rel=\"canonical\">")

    parsed_ld: list[object] = []
    for i, block in enumerate(head.json_ld, 1):
        try:
            parsed_ld.append(json.loads(block))
        except json.JSONDecodeError as exc:
            errors.append(f"JSON-LD block #{i} does not parse: {exc}")

    ld_types = {doc.get("@type") for doc in parsed_ld if isinstance(doc, dict)}

    og_type = (head.meta.get("og:type") or [""])[0]
    if og_type == "article":
        if not any(v.strip() for v in head.meta.get("article:published_time", [])):
            errors.append("article page is missing `article:published_time`")
        if not any(v.strip() for v in head.meta.get("article:author", [])):
            errors.append("article page is missing `article:author`")
        if "BlogPosting" not in ld_types:
            errors.append("article page is missing BlogPosting JSON-LD")

    rel = page.relative_to(site_dir).as_posix()
    if rel in PERSON_PAGES and "Person" not in ld_types:
        errors.append("expected a Person JSON-LD entity on this page")

    return errors, head


def emit(page: Path, message: str) -> None:
    print(f"  - {page}: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", " ").replace("\r", " ")
        print(f"::error file={page}::{safe}")


def main() -> int:
    site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "_site"
    if not site_dir.is_dir():
        print(f"error: built site not found: {site_dir} (run `bundle exec jekyll build` first)", file=sys.stderr)
        return 2

    pages = [
        p for p in sorted(site_dir.rglob("*.html"))
        if not (set(p.relative_to(site_dir).parts[:-1]) & SKIP_DIRS)
    ]
    if not pages:
        print(f"error: no HTML pages found in {site_dir}", file=sys.stderr)
        return 2

    failed: list[tuple[Path, list[str]]] = []
    article_titles: dict[str, list[str]] = defaultdict(list)
    article_descriptions: dict[str, list[str]] = defaultdict(list)

    for page in pages:
        rel = page.relative_to(site_dir)
        errs, head = check_page(page, site_dir)
        if errs:
            failed.append((rel, errs))
        if (head.meta.get("og:type") or [""])[0] == "article":
            title = (head.meta.get("og:title") or [""])[0].strip()
            desc = (head.meta.get("og:description") or [""])[0].strip()
            if title:
                article_titles[title].append(rel.as_posix())
            if desc:
                article_descriptions[desc].append(rel.as_posix())

    global_errors: list[str] = []
    for title, where in article_titles.items():
        if len(where) > 1:
            global_errors.append(f"duplicate article og:title `{title}` on: {', '.join(where)}")
    for desc, where in article_descriptions.items():
        if len(where) > 1:
            global_errors.append(f"duplicate article og:description on: {', '.join(where)}")
    for name in REQUIRED_SITE_FILES:
        if not (site_dir / name).is_file():
            global_errors.append(f"expected site file missing from build: {name}")
    card = site_dir / SOCIAL_CARD.lstrip("/")
    if not card.is_file():
        global_errors.append(f"social card missing: {SOCIAL_CARD}")
    elif png_dims(card) != SOCIAL_CARD_DIMS:
        global_errors.append(f"social card is {png_dims(card)}, expected {SOCIAL_CARD_DIMS}")

    if failed or global_errors:
        total = sum(len(errs) for _, errs in failed) + len(global_errors)
        print(f"Metadata validation failed: {total} issue(s) across {len(failed)} of {len(pages)} page(s).\n")
        for page, errs in failed:
            for err in errs:
                emit(page, err)
        for err in global_errors:
            print(f"  - {err}")
            if os.environ.get("GITHUB_ACTIONS") == "true":
                print(f"::error::{err}")
        return 1

    articles = sum(1 for _ in article_titles)
    print(f"OK: {len(pages)} pages validated ({articles} articles); social metadata, JSON-LD, and images look good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
