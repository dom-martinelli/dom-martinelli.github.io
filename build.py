"""
build.py — generates the site from content/*.json.

    python3 build.py

Writes index.html and projects/<slug>.html. No dependencies. Edit the JSON,
rerun, push. Tab order and the home copy live in content/_site.json.
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
        if d.get("hidden"):
            continue
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
    cls = status.replace(" ", "-")
    return f'<span class="status status-{esc(cls)}">{esc(status)}</span>'


def figure_panel(fig, depth: int, cls="panel") -> str:
    up = "../" * depth
    if fig.get("dark"):
        cls += " panel-dark"   # a screenshot of a dark UI, not a figure on paper
    return (f'<div class="{cls}"><img src="{up}{esc(fig["file"])}" '
            f'alt="{esc(fig.get("caption", ""))}" loading="lazy"></div>')


def tile(p, wide: bool) -> str:
    figs = p.get("figures") or []
    art = figure_panel(figs[0], 0) if figs else '<div class="panel panel-empty"></div>'
    tags = "".join(f"<li>{esc(t)}</li>" for t in (p.get("tools") or [])[:4])
    return f"""<a class="tile{' tile-wide' if wide else ''}" href="projects/{esc(p['slug'])}.html">
  {art}
  <div class="tile-body">
    <div class="tile-meta">{status_label(p.get('status', ''))}</div>
    <h3>{esc(p['title'])}</h3>
    <p>{esc(p['hook'])}</p>
    <ul class="tags">{tags}</ul>
    <span class="more">Read more <span aria-hidden="true">&rarr;</span></span>
  </div>
</a>"""


def build_index(site, projects):
    tabs = site["tabs"]
    tab_buttons = "".join(
        f'<button role="tab" id="tab-{esc(t["id"])}" aria-controls="panel-{esc(t["id"])}" '
        f'data-tab="{esc(t["id"])}">{esc(t["label"])}</button>' for t in tabs)
    panels = []
    for t in tabs:
        items = [p for p in projects if p["tab"] == t["id"]]
        if not items:
            continue
        tiles = "".join(tile(p, wide=(i == 0)) for i, p in enumerate(items))
        panels.append(f"""<section class="tabpanel" role="tabpanel" id="panel-{esc(t['id'])}" aria-labelledby="tab-{esc(t['id'])}">
  <div class="panel-head"><h2>{esc(t['label'])}</h2><p>{esc(t.get('blurb', ''))}</p></div>
  <div class="grid">{tiles}</div>
</section>""")
    body = f"""{site_header(site, 0)}
<main class="wrap">
  <section class="hero">
    <h1>{esc(site['headline'])}</h1>
    <p class="lede">{esc(site['intro'])}</p>
  </section>
  <div class="tabs" role="tablist" aria-label="Subjects">{tab_buttons}</div>
  {''.join(panels)}
</main>
<footer class="wrap foot">{esc(site.get('footer', ''))}</footer>
<script src="assets/tabs.js"></script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(head(site["title"], site["intro"], 0) + body)


def bullets(title, items):
    items = [i for i in (items or []) if i]
    if not items:
        return ""
    lis = "".join(f"<li>{esc(i)}</li>" for i in items)
    return f'<section class="block"><h2>{esc(title)}</h2><ul>{lis}</ul></section>'


def para(title, text):
    if not text:
        return ""
    return f'<section class="block"><h2>{esc(title)}</h2><p>{esc(text)}</p></section>'


def build_project(site, p, tab_label):
    depth = 1
    links = list(p.get("links") or [])
    if p.get("host_file"):
        src = Path(p["host_file"])
        if src.exists():
            OUT_TOOLS.mkdir(exist_ok=True)
            shutil.copy(src, OUT_TOOLS / f"{p['slug']}.html")
            links.insert(0, {"label": "Open it", "url": f"../tools/{p['slug']}.html"})
    link_html = "".join(
        f'<a class="btn{" btn-primary" if i == 0 else ""}" href="{esc(l["url"])}">{esc(l["label"])}</a>'
        for i, l in enumerate(links))
    figs = "".join(
        f'<figure>{figure_panel(f, depth)}<figcaption>{esc(f.get("caption", ""))}</figcaption></figure>'
        for f in (p.get("figures") or []))
    tags = "".join(f"<li>{esc(t)}</li>" for t in (p.get("tools") or []))
    body = f"""{site_header(site, depth)}
<main class="wrap article">
  <a class="back" href="../index.html#{esc(p['tab'])}">&larr; {esc(tab_label)}</a>
  <div class="tile-meta">{status_label(p.get('status', ''))}</div>
  <h1>{esc(p['title'])}</h1>
  <p class="lede">{esc(p['hook'])}</p>
  {f'<div class="actions">{link_html}</div>' if link_html else ''}
  {para('The question', p.get('question'))}
  {para('Why it matters', p.get('why_it_matters'))}
  {f'<div class="figs">{figs}</div>' if figs else ''}
  {bullets('What I did', p.get('what_i_did'))}
  {bullets('What I found', p.get('what_i_found'))}
  {bullets('Limits', p.get('limits'))}
  {f'<section class="block"><h2>Tools</h2><ul class="tags">{tags}</ul></section>' if tags else ''}
</main>
<footer class="wrap foot">{esc(site.get('footer', ''))}</footer>
</body>
</html>
"""
    OUT_PROJECTS.mkdir(exist_ok=True)
    (OUT_PROJECTS / f"{p['slug']}.html").write_text(
        head(f"{p['title']} · {site['name']}", p["hook"], depth) + body)


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
