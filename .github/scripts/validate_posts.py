#!/usr/bin/env python3
"""Validate every post in _posts/ has tags + description in its frontmatter,
and is linked from menu/topics.md.

Exits non-zero (and emits GitHub Actions error annotations) if any post fails.
Runs with the stdlib only -- no pip install required.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTS_DIR = REPO_ROOT / "_posts"
TOPICS_FILE = REPO_ROOT / "menu" / "topics.md"

DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
TAGS_LINE = re.compile(r"^tags:\s*(.*\S)?\s*$", re.MULTILINE)
DESC_LINE = re.compile(r"^description:\s*(.*\S)?\s*$", re.MULTILINE)
EMPTY_LIST = re.compile(r"^\[\s*\]$")
TOPIC_URL = re.compile(r"https?://joshua\.hu/([^\s)>#?\"']+)", re.IGNORECASE)


def collect_topic_paths(text: str) -> set[str]:
    return {m.group(1).rstrip("/") for m in TOPIC_URL.finditer(text)}


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1].strip()
    return value


def check_post(post: Path, topic_paths: set[str]) -> list[str]:
    errors: list[str] = []
    text = post.read_text(encoding="utf-8")

    fm_match = FRONTMATTER.match(text)
    if not fm_match:
        errors.append("missing YAML frontmatter block (expected `---` ... `---` at top of file)")
    else:
        fm = fm_match.group(1)

        tags_match = TAGS_LINE.search(fm)
        if not tags_match:
            errors.append("frontmatter is missing a `tags:` field (e.g. `tags: [security, fuzzing]`)")
        else:
            value = (tags_match.group(1) or "").strip()
            if not value or EMPTY_LIST.match(value):
                errors.append("frontmatter `tags:` is empty -- add at least one tag")

        desc_match = DESC_LINE.search(fm)
        if not desc_match:
            errors.append("frontmatter is missing a `description:` field")
        else:
            value = strip_quotes(desc_match.group(1) or "")
            if not value:
                errors.append("frontmatter `description:` is empty")

    stem = post.stem
    slug = DATE_PREFIX.sub("", stem)
    if slug not in topic_paths and stem not in topic_paths:
        errors.append(
            f"slug `{slug}` is not linked from menu/topics.md -- "
            f"add `[<title>](https://joshua.hu/{slug})` under a topic heading"
        )

    return errors


def emit(post: Path, message: str) -> None:
    rel = post.relative_to(REPO_ROOT).as_posix()
    print(f"  - {rel}: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", " ").replace("\r", " ")
        print(f"::error file={rel}::{safe}")


def main() -> int:
    if not POSTS_DIR.is_dir():
        print(f"error: posts directory not found: {POSTS_DIR}", file=sys.stderr)
        return 2
    if not TOPICS_FILE.is_file():
        print(f"error: topics file not found: {TOPICS_FILE}", file=sys.stderr)
        return 2

    topic_paths = collect_topic_paths(TOPICS_FILE.read_text(encoding="utf-8"))
    posts = sorted(POSTS_DIR.glob("*.md"))
    if not posts:
        print(f"error: no posts found in {POSTS_DIR}", file=sys.stderr)
        return 2

    failed: list[tuple[Path, list[str]]] = []
    for post in posts:
        errs = check_post(post, topic_paths)
        if errs:
            failed.append((post, errs))

    if failed:
        total = sum(len(errs) for _, errs in failed)
        print(f"Validation failed: {total} issue(s) across {len(failed)} of {len(posts)} post(s).\n")
        for post, errs in failed:
            for err in errs:
                emit(post, err)
        print(
            "\nEvery post in _posts/ must have non-empty `tags:` and `description:` "
            "in its YAML frontmatter, and must be linked from menu/topics.md."
        )
        return 1

    print(f"OK: all {len(posts)} posts have tags + description and are linked from menu/topics.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
