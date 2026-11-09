#!/usr/bin/env python3
"""Enforce code-fence conventions in _posts/.

Deterministic, low-false-positive rules (stdlib only, no pip):

  1. A fenced block whose language is the Rouge console lexer or one of its
     aliases (console, terminal, shell_session, shell-session) must be written
     exactly as `console?prompt=$,#`.

  2. A block tagged bash/shell/sh/zsh, or left unlabelled, that contains an
     interactive prompt line (a line starting with `$ ` or a `user@host...$ `
     prompt) is an interactive session and must use `console?prompt=$,#`
     instead. Shebang (`#!`) blocks are treated as scripts and skipped.

A block is exempt if the line directly above its opening fence is
`<!-- fence-lint-ignore -->` (optionally followed by a reason). Use it for the
rare real case, e.g. a shell script whose heredoc body literally starts `$ `,
or a console block that needs a different prompt set.

Exits non-zero (and emits GitHub Actions error annotations) on any violation.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTS_DIR = REPO_ROOT / "_posts"

FENCE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})\s*(\S*)\s*$")
IGNORE = re.compile(r"^\s*<!--\s*fence-lint-ignore\b")

CONSOLE_ALIASES = {"console", "terminal", "shell_session", "shell-session"}
SHELL_LANGS = {"bash", "shell", "sh", "zsh", ""}
CANONICAL = "console?prompt=$,#"

# High-signal interactive-prompt lines. A shell script line never starts `$ `,
# and never looks like `user@host:...$ `.
USER_PROMPT = re.compile(r"^(\$ |\$$|[\w.-]+@[\w.-]+:[^\n]*\$ )")


def iter_blocks(lines: list[str]):
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m or (m.group(3) and not re.match(r"^[\w+\-.]*(\?\S*)?$", m.group(3))):
            i += 1
            continue
        fence, info = m.group(2), m.group(3)
        j = i + 1
        while j < len(lines):
            mm = FENCE.match(lines[j])
            if mm and mm.group(2)[0] == fence[0] and len(mm.group(2)) >= len(fence) and not mm.group(3):
                break
            j += 1
        prev = lines[i - 1] if i > 0 else ""
        yield {"line": i + 1, "info": info, "lang": info.split("?")[0].lower(),
               "body": lines[i + 1:j], "exempt": bool(IGNORE.match(prev))}
        i = j + 1


def check_post(post: Path) -> list[tuple[int, str]]:
    errors: list[tuple[int, str]] = []
    lines = post.read_text(encoding="utf-8").split("\n")
    for b in iter_blocks(lines):
        if b["exempt"]:
            continue
        if b["lang"] in CONSOLE_ALIASES:
            if b["info"] != CANONICAL:
                errors.append((b["line"],
                    f"console block must be written `{CANONICAL}` (found `{b['info']}`)"))
            continue
        if b["lang"] in SHELL_LANGS and not any(l.lstrip().startswith("#!") for l in b["body"]):
            if any(USER_PROMPT.match(l) for l in b["body"]):
                found = b["info"] or "(no language)"
                errors.append((b["line"],
                    f"interactive session (has a `$ ` prompt) must use `{CANONICAL}`, not `{found}`"))
    return errors


def emit(post: Path, line: int, message: str) -> None:
    rel = post.relative_to(REPO_ROOT).as_posix()
    print(f"  - {rel}:{line}: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", " ").replace("\r", " ")
        print(f"::error file={rel},line={line}::{safe}")


def main() -> int:
    if not POSTS_DIR.is_dir():
        print(f"error: posts directory not found: {POSTS_DIR}", file=sys.stderr)
        return 2
    posts = sorted(POSTS_DIR.glob("*.md"))
    failed = [(p, errs) for p in posts if (errs := check_post(p))]
    if failed:
        total = sum(len(e) for _, e in failed)
        print(f"Fence validation failed: {total} issue(s) across {len(failed)} of {len(posts)} post(s).\n")
        for post, errs in failed:
            for line, msg in errs:
                emit(post, line, msg)
        print("\nInteractive shell sessions use `console?prompt=$,#`; console/terminal "
              "blocks must be written that way too. Add `<!-- fence-lint-ignore -->` "
              "on the line above a fence to exempt a deliberate exception.")
        return 1
    print(f"OK: all {len(posts)} posts follow the code-fence conventions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
