#!/usr/bin/env python3
"""mdlinkcheck - offline checker for local links in markdown files."""
import os
import re
import sys
from urllib.parse import unquote

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}
MD_EXTS = (".md", ".markdown")

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
INLINE_LINK_RE = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*(<[^>]*>|[^()\s]*(?:\([^()\s]*\)[^()\s]*)*)[^)]*\)")
REF_DEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")


def slugify(text):
    """GitHub-style heading slug (without duplicate suffix)."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
    text = re.sub(r"<[^>]+>", "", text)  # html tags
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def iter_lines(text):
    """Yield (lineno, line) for lines outside fenced code blocks."""
    fence = None
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE_RE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and not m.group(2).strip():
                fence = None
            continue
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = m.group(1)
            continue
        yield n, line


def heading_slugs(text):
    """Set of valid anchors for a markdown document."""
    seen = {}
    slugs = set()
    for _, line in iter_lines(text):
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = slugify(m.group(1) or "")
        count = seen.get(base, 0)
        seen[base] = count + 1
        slugs.add(base if count == 0 else "%s-%d" % (base, count))
    return slugs


def extract_links(text):
    """Yield (lineno, target) for links outside code."""
    for n, line in iter_lines(text):
        m = REF_DEF_RE.match(line)
        if m:
            yield n, m.group(1)
            continue
        clean = CODE_SPAN_RE.sub(lambda s: " " * len(s.group(0)), line)
        for m in INLINE_LINK_RE.finditer(clean):
            yield n, m.group(1)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def check_file(path, _cache=None):
    """Return list of (lineno, message) problems for one markdown file."""
    cache = {} if _cache is None else _cache

    def slugs_of(p):
        if p not in cache:
            try:
                cache[p] = heading_slugs(read(p))
            except OSError:
                cache[p] = set()
        return cache[p]

    text = read(path)
    problems = []
    base = os.path.dirname(os.path.abspath(path))
    for n, target in extract_links(text):
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        target = target.strip()
        if not target or SCHEME_RE.match(target) or target.startswith("/"):
            continue
        file_part, _, anchor = target.partition("#")
        file_part = unquote(file_part.split("?", 1)[0])
        anchor = unquote(anchor).lower()
        if file_part:
            dest = os.path.normpath(os.path.join(base, file_part))
            if not os.path.exists(dest):
                problems.append((n, "broken link: file not found: %s" % file_part))
                continue
        else:
            dest = os.path.abspath(path)
        if anchor and os.path.isfile(dest) and dest.lower().endswith(MD_EXTS):
            if anchor not in slugs_of(dest):
                where = file_part or "this file"
                problems.append((n, "broken anchor: #%s not found in %s" % (anchor, where)))
    return problems


def collect(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for f in sorted(files):
                    if f.lower().endswith(MD_EXTS):
                        yield os.path.join(root, f)
        else:
            yield p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: mdlinkcheck.py PATH... (markdown files or directories)")
        return 0 if argv else 2
    cache = {}
    bad = 0
    for f in collect(argv):
        try:
            problems = check_file(f, cache)
        except OSError as e:
            print("%s:0: cannot read: %s" % (f, e.strerror))
            bad += 1
            continue
        for n, msg in problems:
            print("%s:%d: %s" % (f, n, msg))
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
