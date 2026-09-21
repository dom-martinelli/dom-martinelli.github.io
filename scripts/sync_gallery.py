"""
sync_gallery.py — copy every matplotlib figure into gallery/ under a stable
name, so a regeneration overwrites the same file and the site updates with it.

    python3 scripts/sync_gallery.py && python3 build.py

Add a row to FIGURES when a new figure exists. Source paths point at the repo
that produces the figure; nothing is generated here, only copied. Writes
content/_gallery.json for build.py.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
GH = HOME / "Documents/GitHub"
SITE = Path(__file__).resolve().parent.parent
OUT = SITE / "gallery"
# the same figures, mirrored to iCloud Drive so they open in Finder and Quick
# Look at full size, one subfolder per project. Overwritten each revision.
ICLOUD = HOME / "Library/Mobile Documents/com~apple~CloudDocs/Figure Gallery"

# gallery name, source path, project slug, one-line note
FIGURES = [
    ("odor-structure-topography.png", GH / "sweetspace/figures/fig-odor-structure-topography.png",
     "sweetspace", "three odour words on the same map of 3,522 molecules"),
    ("odor-descriptor-cooccurrence.png", GH / "sweetspace/figures/fig-odor-descriptor-cooccurrence.png",
     "sweetspace", "which odour words land on the same molecule"),
    ("sweetener-anchoring.png", GH / "sweetspace/src/fig-sweetspace-anchoring.png",
     "sweetspace", "flavours by how much of their identity one molecule carries"),
    ("drug-property-space.png", GH / "wakespace/figures/01-property-space.png",
     "wakespace", "wakefulness drugs by lipophilicity and polar surface area"),
    ("drug-class-radar.png", GH / "wakespace/figures/02-class-radar.png",
     "wakespace", "one radar per compound, grouped by licensed use"),
    ("drug-property-topography.png", GH / "wakespace/figures/03-property-topography.png",
     "wakespace", "density of the same property space"),
    ("criteria-over-time.png", GH / "advocacy-and-accrual/outputs/figures/01_criteria_over_time.png",
     "advocacy-accrual", "eligibility criteria per trial, by year"),
    ("biomarker-divergence.png", GH / "advocacy-and-accrual/outputs/figures/02_biomarker_divergence.png",
     "advocacy-accrual", "biomarker requirements diverging between fields"),
    ("depression-vs-cancer.png", GH / "advocacy-and-accrual/outputs/figures/03_depression_vs_cancer.png",
     "advocacy-accrual", "two fields, two different trial cultures"),
    ("revival-confound.png", GH / "advocacy-and-accrual/outputs/figures/04_revival_confound.png",
     "advocacy-accrual", "what else moves with a compound being revived"),
    ("revival-by-reason.png", GH / "advocacy-and-accrual/outputs/figures/05_revival_by_reason.png",
     "advocacy-accrual", "revival rate by why the first trial stopped"),
    ("revival-model.png", GH / "advocacy-and-accrual/outputs/figures/06_revival_model.png",
     "advocacy-accrual", "model estimates for revival"),
    ("abandoned-by-reason.png", GH / "advocacy-and-accrual/outputs/figures/07_abandoned_by_reason.png",
     "advocacy-accrual", "abandoned compounds by stop reason"),
    ("glp1-cascade.png", GH / "advocacy-and-accrual/outputs/figures/08_glp1_cascade.png",
     "evidence-lag", "the GLP-1 weight signal moving through the record"),
    ("glp1-lag-shrinking.png", GH / "advocacy-and-accrual/outputs/figures/09_glp1_lag_shrinking.png",
     "evidence-lag", "the lag from signal to label, narrowing"),
    ("glp1-faers-share.png", GH / "advocacy-and-accrual/outputs/figures/10_glp1_faers_share.png",
     "evidence-lag", "weight reports as a share of each drug's own reports"),
    ("glp1-signal-vs-approval.png", GH / "advocacy-and-accrual/outputs/figures/10_glp1_signal_vs_approval.png",
     "evidence-lag", "first safety report, first approval, weight indication"),
    ("eds-terminology-lag.png", GH / "advocacy-and-accrual/outputs/figures/11_eds_terminology_lag.png",
     "evidence-lag", "old and new naming for the same diagnosis"),
    ("cfs-get-pacing.png", GH / "advocacy-and-accrual/outputs/figures/12_cfs_get_pacing.png",
     "evidence-lag", "graded exercise against pacing, with the 2021 guideline reversal"),
    ("mi-sex-framing.png", GH / "advocacy-and-accrual/outputs/figures/13_mi_sex_framing.png",
     "evidence-lag", "how papers frame heart attacks in women"),
]


def figstyle_version() -> str:
    for p in (GH / "sweetspace/src/figstyle.py", GH / "wakespace/src/figstyle.py"):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("FIGSTYLE_VERSION"):
                    return line.split('"')[1]
    return "unknown"


def main():
    OUT.mkdir(exist_ok=True)
    rows, missing = [], []
    for name, src, slug, note in FIGURES:
        if not src.exists():
            missing.append(str(src))
            continue
        dest = OUT / name
        shutil.copy2(src, dest)          # same name every time: revisions overwrite
        mirror = ICLOUD / slug
        mirror.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, mirror / name)
        rows.append({
            "file": f"gallery/{name}", "slug": slug, "note": note,
            "source": str(src).replace(str(HOME), "~"),
            "rebuilt": datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d"),
        })
    # every other figure a project page shows (lab figures, screenshots) gets
    # mirrored and listed too, so the folder and the page are complete
    seen = {r["file"] for r in rows}
    for pj in sorted((SITE / "content").glob("*.json")):
        if pj.name.startswith("_"):
            continue
        proj = json.loads(pj.read_text())
        for fig in proj.get("figures") or []:
            rel = fig["file"]
            if rel in seen or not (SITE / rel).exists():
                continue
            seen.add(rel)
            src = SITE / rel
            mirror = ICLOUD / proj["slug"]
            mirror.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, mirror / src.name)
            rows.append({
                "file": rel, "slug": proj["slug"], "note": fig.get("note", ""),
                "source": rel,
                "rebuilt": datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d"),
            })

    data = {"version": figstyle_version(),
            "synced": datetime.now().strftime("%Y-%m-%d"), "figures": rows}
    (SITE / "content" / "_gallery.json").write_text(json.dumps(data, indent=1))
    print(f"{len(rows)} figures -> {OUT}  (figstyle {data['version']})")
    print(f"mirrored to {ICLOUD}")
    for m in missing:
        print("  missing:", m)
    changed = subprocess.run(["git", "-C", str(SITE), "status", "--short", "gallery"],
                             capture_output=True, text=True).stdout.strip()
    print("changed in gallery/:", len(changed.splitlines()))


if __name__ == "__main__":
    main()
