# mdlinkcheck

A tiny, offline checker for local links in markdown files. Pure Python 3
standard library, a single file, no network access.

## Why

Renamed files and edited headings silently break relative links and
`#anchor` links. Most link checkers are heavy or hit the network. This one
only checks what can be verified locally, so it is fast and safe for CI.

## What it checks

- Relative file links whose target does not exist.
- Anchors (same file, or in another markdown file) that match no heading,
  using GitHub-style slugs, including the `-1`, `-2` suffix for duplicates.

It ignores http(s), mailto and other URL-scheme links, and anything inside
fenced code blocks or inline code. Only ATX headings (`# Title`) are
recognised as anchor targets.

## Install

Copy `mdlinkcheck.py` anywhere, or run it from a clone. Needs Python 3.8+.

## Usage

```
python3 mdlinkcheck.py README.md docs/
```

Directories are searched recursively for `.md` and `.markdown` files
(skipping `.git`, `node_modules`, `.venv`). Output looks like:

```
docs/guide.md:12: broken link: file not found: setup.md
docs/guide.md:30: broken anchor: #install not found in this file
```

Exit code is 1 if any problem was found, otherwise 0.

## Tests

```
python3 -m unittest
```

(`pytest` also works if installed.)

## License

MIT, see the LICENSE file.
