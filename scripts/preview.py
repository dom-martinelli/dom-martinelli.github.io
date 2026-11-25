#!/usr/bin/env python3
"""Build a self-contained copy of the site so Dominic can look at it anywhere.

    python3 build.py && python3 scripts/preview.py

Writes one HTML file with every stylesheet and image inlined as base64, plus
the project pages folded in behind in-page links, so it needs no server and no
network. Publish it as an Artifact and send him the URL.

Why this exists: a stored snapshot of the card list (the old Portfolio Studio)
drifts, because the sessions that edit the cards do not know it is there. This
is generated from the current build every time, so it cannot be out of date. It
also shows work that is committed but not pushed, which the live site cannot.

    --live    drop the "not published" banner (use only after a push)
    --cards   one page per card instead of the homepage
"""
from __future__ import annotations

import argparse
import base64
import mimetypes
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANNER = ('<div style="background:#B87C14;color:#fff;padding:10px 16px;font:500 '
          '14px/1.45 -apple-system,BlinkMacSystemFont,sans-serif;text-align:center">'
          'PREVIEW generated {when} from the local repo. '
          'Not published to dom-martinelli.github.io.</div>')


def inline(page: pathlib.Path, banner: str | None) -> str:
    html = page.read_text()
    base = page.parent

    def css(m):
        href = re.search(r'href="([^"]+)"', m.group(0))
        if not href:
            return m.group(0)
        p = (base / href.group(1)).resolve()
        return f"<style>\n{p.read_text()}\n</style>" if p.exists() else m.group(0)

    html = re.sub(r'<link[^>]*rel="stylesheet"[^>]*>', css, html)

    missing = []

    def img(m):
        src = m.group(1)
        if src.startswith(("data:", "http://", "https://")):
            return m.group(0)
        p = (base / src).resolve()
        if not p.exists():
            p = (ROOT / src.lstrip("./")).resolve()
        if not p.exists():
            missing.append(src)
            return m.group(0)
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        return f'src="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"'

    html = re.sub(r'src="([^"]+)"', img, html)
    html = html.replace('loading="lazy"', "")       # show everything at once
    if banner:
        html = html.replace("<body>", "<body>" + banner, 1)
    if missing:
        print(f"  !! {len(missing)} image(s) not found: {missing[:4]}")
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="omit the preview banner")
    ap.add_argument("--cards", action="store_true", help="project pages, not the homepage")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    from datetime import datetime
    banner = None if a.live else BANNER.format(when=datetime.now().strftime("%-d %b, %H:%M"))

    if a.cards:
        pages = sorted((ROOT / "projects").glob("*.html"))
    else:
        pages = [ROOT / "index.html"]
    if not pages or not pages[0].exists():
        raise SystemExit("nothing built yet: run `python3 build.py` first")

    out_dir = pathlib.Path(a.out) if a.out else ROOT / "_preview"
    out_dir.mkdir(exist_ok=True)
    total = 0
    for p in pages:
        html = inline(p, banner)
        dest = out_dir / p.name
        dest.write_text(html)
        total += len(html)
        print(f"  {p.name:38s} {len(html)/1e6:5.2f} MB")
    print(f"\n{len(pages)} page(s), {total/1e6:.1f} MB total -> {out_dir}")
    print("publish the file(s) above as an Artifact and send Dominic the link")


if __name__ == "__main__":
    main()
