"""
inventory_notebooks.py — walk the machine for notebooks and scripts, bucket
them by subject, and guess whether each one is Dominic's own work or something
downloaded. Writes content/_archive.json, which build.py renders as the archive
page.

    python3 scripts/inventory_notebooks.py

Nothing is copied or moved. Only paths, dates and counts are recorded, plus the
libraries a file imports. Notebook contents never leave the machine.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
ROOTS = [
    HOME / "Projects", HOME / "bioinfo", HOME / "Documents", HOME / "Downloads",
    HOME / "Desktop", HOME / "cs1110", HOME / "Library/CloudStorage",
]
SKIP_PARTS = {
    "node_modules", ".git", "__pycache__", ".ipynb_checkpoints", "Library/Caches",
    "site-packages", ".venv", "venv", "anaconda3", ".Trash",
}

# subject buckets, tested in order: first hit wins
BUCKETS = [
    ("molecular dynamics", r"gromacs|gmx |charmm|\.mdp|namd|openmm|mdtraj"),
    ("cheminformatics", r"rdkit|chembl|pubchem|smiles|morgan|chemception|drugbank|pyrfume"),
    ("omics and sequencing", r"deseq|scanpy|anndata|rnaseq|rna-seq|kegg|proteomic|metabolomic|synapse|single.cell|fastq|bioconductor|limma|edger"),
    ("clinical and health data", r"fhir|icd|rxnorm|namcs|n2c2|clinicaltrials|aact|pubmed|icite|cdc |nhanes|mesh|meddra|faers"),
    ("geospatial", r"geopandas|folium|shapefile|geojson|choropleth|census|tiger|tract"),
    ("machine learning", r"sklearn|scikit-learn|keras|tensorflow|torch|xgboost|shap|random.?forest|classifier|neural"),
    ("statistics and dataframes", r"statsmodels|scipy\.stats|regression|anova|pandas"),
    ("intro programming", r"cs1110|assert_equals|introcs|planetoid|def test_"),
    ("visualisation", r"matplotlib|seaborn|plotly|altair|bokeh"),
]

# a file is third-party if any of these matches its path or its text
THIRD_PARTY_PATH = re.compile(
    r"cs1110|Ex_Files|LinkedIn|demos|helper-notebooks|tutorial|vignette|course|"
    r"lecture|lab\d|week\d|homework|hw\d|exercise|PUBPOL-2130 notebooks|"
    r"NLP-Tutorials|keras-molecules|chembl_webresource", re.I)
THIRD_PARTY_TEXT = re.compile(
    r"in this tutorial|this notebook will teach|exercise \d|solution:|"
    r"©\s*\d{4}|copyright \d{4}|we have downloaded all|instructor", re.I)
MINE_TEXT = re.compile(r"dominiero|/Users/dominiero|martinelli|my own|todo:", re.I)


def git_remote(path: Path) -> str:
    d = path
    for _ in range(6):
        if (d / ".git").exists():
            try:
                out = subprocess.run(["git", "-C", str(d), "remote", "get-url", "origin"],
                                     capture_output=True, text=True, timeout=10)
                return out.stdout.strip()
            except Exception:
                return ""
        d = d.parent
    return ""


def read_notebook(p: Path):
    try:
        nb = json.loads(p.read_text(errors="ignore"))
    except Exception:
        return None
    cells = nb.get("cells", [])
    src = []
    outs = 0
    for c in cells:
        src.append("".join(c.get("source", [])))
        outs += 1 if c.get("outputs") else 0
    return {"cells": len(cells), "with_output": outs, "text": "\n".join(src)}


def bucket_of(text: str, path: str) -> str:
    hay = (text[:20000] + " " + path).lower()
    for name, pat in BUCKETS:
        if re.search(pat, hay, re.I):
            return name
    return "unsorted"


def provenance(path: str, text: str, remote: str) -> str:
    if remote and "dom-martinelli" not in remote:
        return "third party"
    if THIRD_PARTY_PATH.search(path):
        return "third party"
    if THIRD_PARTY_TEXT.search(text[:20000]):
        return "third party"
    if MINE_TEXT.search(text[:20000]) or (remote and "dom-martinelli" in remote):
        return "mine"
    return "unclear"


def walk_tree(root: Path):
    """rglob, but a cloud folder that goes stale mid-walk does not kill the run."""
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except OSError:
            continue  # stale cloud handle, permission, or a folder that vanished
        for e in entries:
            try:
                if e.is_dir():
                    if not any(part in str(e) for part in SKIP_PARTS):
                        stack.append(e)
                elif e.suffix == ".ipynb":
                    yield e
            except OSError:
                continue


def walk():
    rows = []
    for root in ROOTS:
        if not root.exists():
            continue
        for p in walk_tree(root):
            s = str(p)
            if any(part in s for part in SKIP_PARTS):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            nb = read_notebook(p)
            if nb is None:
                rows.append(dict(path=s, name=p.name, bytes=st.st_size, cells=0,
                                 date=datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m"),
                                 bucket="unreadable", provenance="unclear", note="could not parse"))
                continue
            remote = git_remote(p.parent)
            rows.append(dict(
                path=s.replace(str(HOME), "~"), name=p.name, bytes=st.st_size,
                cells=nb["cells"], with_output=nb["with_output"],
                date=datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m"),
                bucket=bucket_of(nb["text"], s),
                provenance=provenance(s, nb["text"], remote),
                stub=st.st_size < 2000,
            ))
    return rows


def main():
    rows = walk()
    rows.sort(key=lambda r: (r["provenance"] != "mine", r["bucket"], r["date"]), reverse=False)
    out = Path(__file__).resolve().parent.parent / "content" / "_archive.json"
    counts = {}
    for r in rows:
        counts.setdefault(r["bucket"], {"mine": 0, "third party": 0, "unclear": 0})
        counts[r["bucket"]][r["provenance"]] += 1
    out.write_text(json.dumps({"generated": datetime.now().strftime("%Y-%m-%d"),
                               "rows": rows, "counts": counts}, indent=1))
    print(f"{len(rows)} notebooks -> {out}")
    for b, c in sorted(counts.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {b:28} mine {c['mine']:3}  third party {c['third party']:3}  unclear {c['unclear']:3}")


if __name__ == "__main__":
    main()
