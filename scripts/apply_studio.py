#!/usr/bin/env python3
"""Apply the Portfolio Studio's state to content/*.json.

The Studio keeps its state in the artifact's own database. Claude reads that
database and dumps it to a JSON file of {slug: {public, rank, thumb, title}};
this applies it. Run build.py afterwards.

    python3 scripts/apply_studio.py /tmp/studio-state.json
"""
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"


def main(state_file: str) -> None:
    state = json.loads(pathlib.Path(state_file).read_text())
    site_path = CONTENT / "_site.json"
    site = json.loads(site_path.read_text(), object_pairs_hook=collections.OrderedDict)
    ranked, changed, missing = {}, [], []

    for slug, s in state.items():
        f = CONTENT / f"{slug}.json"
        if not f.exists():
            missing.append(slug)
            continue
        d = json.loads(f.read_text(), object_pairs_hook=collections.OrderedDict)
        before = json.dumps(d, sort_keys=True)

        if "public" in s:
            d["public"] = bool(s["public"])
        if s.get("title"):
            d["title"] = s["title"]
        # A chosen thumbnail is just that figure moved to the front of the list.
        if s.get("thumb"):
            figs = d.get("figures", [])
            i = next((n for n, g in enumerate(figs) if g["file"] == s["thumb"]), None)
            if i is None:
                print(f"  ! {slug}: thumb not among its figures: {s['thumb']}")
            elif i:
                d["figures"] = [figs[i]] + figs[:i] + figs[i + 1:]
        if "rank" in s:
            ranked[slug] = s["rank"]

        if json.dumps(d, sort_keys=True) != before:
            f.write_text(json.dumps(d, indent=1) + "\n")
            changed.append(slug)

    # Studio ranks drive the order list; unranked cards keep their relative order after.
    if ranked:
        order = [s for s in site.get("order", [])]
        rest = [s for s in order if s not in ranked]
        site["order"] = sorted(ranked, key=lambda s: ranked[s]) + rest
        site_path.write_text(json.dumps(site, indent=1) + "\n")

    pub = sum(1 for s in state.values() if s.get("public"))
    print(f"applied {len(state)} cards: {pub} public, {len(changed)} files changed")
    if missing:
        print(f"  ! not found in content/: {missing}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/studio-state.json")
