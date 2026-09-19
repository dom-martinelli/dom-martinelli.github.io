"""
build.py — generates the site from content/*.json.

    python3 build.py

Writes index.html and projects/<slug>.html. No dependencies. Edit the JSON,
rerun, push. Tab order and the home copy live in content/_site.json.

Per-project fields the pages use:
  title, tab, status, line        plain title + one fragment, no sentence
  skills, tools, data             lists, shown first on tile and page
  question                        one sentence, the only full sentence up top
  calls                           judgment calls, notes voice: "x over y. why"
  broke                           what failed or had to be redone
  tried                           one rejected approach, only if documented
  figures [{file, note, dark}]    note sits in the margin beside the figure
  links [{label, url}]
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT_PROJECTS = ROOT / "projects"
OUT_TOOLS = ROOT / "tools"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def load():
    site = json.loads((CONTENT / "_site.json").read_text())
    projects = []
    for p in sorted(CONTENT.glob("*.json")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text())
        if not d.get("hidden"):
            projects.append(d)
    order = {s: i for i, s in enumerate(site.get("order", []))}
    projects.sort(key=lambda d: (order.get(d["slug"], 999), d["title"]))
    return site, projects


def head(title: str, desc: str, depth: int) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
"""


def site_header(site, depth: int) -> str:
    up = "../" * depth
    links = "".join(
        f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in site.get("elsewhere", []))
    return f"""<header class="top wrap">
  <a class="name" href="{up}index.html">{esc(site["name"])}</a>
  <nav class="elsewhere">{links}</nav>
</header>
"""


def status_label(status: str) -> str:
    if not status:
        return ""
    return f'<span class="status status-{esc(status.replace(" ", "-"))}">{esc(status)}</span>'


def figure_panel(fig, depth: int, cls="panel") -> str:
    up = "../" * depth
    if fig.get("dark"):
        cls += " panel-dark"   # a screenshot of a dark UI, not a figure on paper
    return (f'<div class="{cls}"><img src="{up}{esc(fig["file"])}" '
            f'alt="{esc(fig.get("note", ""))}" loading="lazy"></div>')


def chips(items, cls="tags"):
    return f'<ul class="{cls}">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"


def tile(p, wide: bool) -> str:
    figs = p.get("figures") or []
    # no figure, no empty picture frame: the tile becomes text only
    art = figure_panel(figs[0], 0) if figs else ""
    cls = "tile" + (" tile-wide" if wide and figs else "") + ("" if figs else " tile-text")
    skills = " · ".join(esc(s) for s in (p.get("skills") or [])[:4])
    return f"""<a class="{cls}" href="projects/{esc(p['slug'])}.html">
  {art}
  <div class="tile-body">
    <div class="tile-top"><h3>{esc(p['title'])}</h3>{status_label(p.get('status', ''))}</div>
    <p class="line">{esc(p.get('line', ''))}</p>
    <p class="skills">{skills}</p>
    {chips((p.get('tools') or [])[:5])}
  </div>
</a>"""


def build_index(site, projects):
    tabs = [t for t in site["tabs"] if any(p["tab"] == t["id"] for p in projects)]
    tab_buttons = "".join(
        f'<button role="tab" id="tab-{esc(t["id"])}" aria-controls="panel-{esc(t["id"])}" '
        f'data-tab="{esc(t["id"])}">{esc(t["label"])}'
        f'<span class="count">{sum(p["tab"] == t["id"] for p in projects)}</span></button>'
        for t in tabs)
    panels = []
    for t in tabs:
        items = [p for p in projects if p["tab"] == t["id"]]
        tiles = "".join(tile(p, wide=(i == 0)) for i, p in enumerate(items))
        panels.append(
            f'<section class="tabpanel" role="tabpanel" id="panel-{esc(t["id"])}" '
            f'aria-labelledby="tab-{esc(t["id"])}"><div class="grid">{tiles}</div></section>')
    works = "".join(f"<li>{esc(w)}</li>" for w in site.get("works_with", []))
    body = f"""{site_header(site, 0)}
<main class="wrap">
  <section class="hero">
    <h1>{esc(site['name'])}</h1>
    <p class="affil">{esc(site['affiliation'])}</p>
    <div class="works"><span class="margin-note">works with</span><ul>{works}</ul></div>
  </section>
  <div class="tabs" role="tablist" aria-label="Subjects">{tab_buttons}</div>
  {''.join(panels)}
</main>
<footer class="wrap foot">{esc(site.get('footer', ''))}</footer>
<script src="assets/tabs.js"></script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(head(site["title"], site["affiliation"], 0) + body)


def row(label, inner):
    """One annotated row: a lowercase serif note in the margin, content beside it."""
    if not inner:
        return ""
    return f'<div class="row"><div class="margin-note">{esc(label)}</div><div class="row-body">{inner}</div></div>'


def ul(items):
    items = [i for i in (items or []) if i]
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>" if items else ""


def build_project(site, p, tab_label):
    depth = 1
    links = list(p.get("links") or [])
    if p.get("host_file"):
        src = ROOT / p["host_file"]
        if src.exists():
            links.insert(0, {"label": "open it", "url": f"../{p['host_file']}"})
    link_html = "".join(
        f'<a class="btn{" btn-primary" if i == 0 else ""}" href="{esc(l["url"])}">{esc(l["label"])}</a>'
        for i, l in enumerate(links))
    spec = "".join(
        f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in (
            ("skills", " · ".join(esc(s) for s in p.get("skills") or [])),
            ("tools", chips(p.get("tools") or [])),
            ("data", " · ".join(esc(s) for s in p.get("data") or [])),
            ("status", status_label(p.get("status", ""))),
        ) if v)
    figs = "".join(
        f'<figure class="fig">{figure_panel(f, depth)}'
        f'<figcaption class="margin-note">{esc(f.get("note", ""))}</figcaption></figure>'
        for f in (p.get("figures") or []))
    body = f"""{site_header(site, depth)}
<main class="wrap article">
  <a class="back" href="../index.html#{esc(p['tab'])}">&larr; {esc(tab_label)}</a>
  <h1>{esc(p['title'])}</h1>
  <p class="line">{esc(p.get('line', ''))}</p>
  <dl class="spec">{spec}</dl>
  {f'<div class="actions">{link_html}</div>' if link_html else ''}
  {row('question', f"<p>{esc(p['question'])}</p>" if p.get('question') else '')}
  {f'<div class="figs">{figs}</div>' if figs else ''}
  {row('calls made', ul(p.get('calls')))}
  {row('what broke', ul(p.get('broke')))}
  {row('what i tried', f"<p>{esc(p['tried'])}</p>" if p.get('tried') else '')}
  {row('not shown', ul(p.get('not_shown')))}
</main>
<footer class="wrap foot">{esc(site.get('footer', ''))}</footer>
</body>
</html>
"""
    OUT_PROJECTS.mkdir(exist_ok=True)
    (OUT_PROJECTS / f"{p['slug']}.html").write_text(
        head(f"{p['title']} · {site['name']}", p.get("line", ""), depth) + body)


def main():
    site, projects = load()
    labels = {t["id"]: t["label"] for t in site["tabs"]}
    unknown = [p["slug"] for p in projects if p["tab"] not in labels]
    if unknown:
        raise SystemExit(f"projects with an unknown tab: {unknown}")
    build_index(site, projects)
    for p in projects:
        build_project(site, p, labels[p["tab"]])
    print(f"built index + {len(projects)} project pages")


if __name__ == "__main__":
    main()
