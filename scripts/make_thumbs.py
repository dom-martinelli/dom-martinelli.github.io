"""
make_thumbs.py — small WebP copies of every figure the home page shows, so
tiles load in a few KB instead of the full-resolution PNG.

    python3 scripts/make_thumbs.py && python3 build.py

Writes assets/thumb/<same path>.webp. build.py uses a thumbnail when one
exists and falls back to the original. Needs Pillow; build.py does not.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parent.parent
THUMB = SITE / "assets/thumb"
WIDTH = 900  # tiles are at most ~600 css px wide; 900 covers 1.5x screens


def home_figures():
    for f in sorted((SITE / "content").glob("*.json")):
        if f.name.startswith("_"):
            continue
        figs = json.loads(f.read_text()).get("figures") or []
        if figs:
            yield figs[0]["file"]
    pubs = SITE / "content/_publications.json"
    if pubs.exists():
        for p in json.loads(pubs.read_text()).get("published", []):
            if p.get("figure"):
                yield p["figure"]


def main():
    for rel in sorted(set(home_figures())):
        src = SITE / rel
        out = THUMB / Path(rel).with_suffix(".webp")
        if not src.exists() or (out.exists() and out.stat().st_mtime >= src.stat().st_mtime):
            continue
        im = Image.open(src)
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        if im.width > WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "WEBP", quality=82, method=6)
        print(f"{rel}: {src.stat().st_size // 1024} KB -> {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
