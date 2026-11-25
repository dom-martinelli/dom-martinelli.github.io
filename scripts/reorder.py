#!/usr/bin/env python3
"""A compact, draggable view of the cards, for deciding what goes where.

    python3 scripts/reorder.py

Writes `_preview/reorder.html`: one small tile per card, thumbnails shrunk so a
whole shelf fits on a phone screen at once. Drag a tile to move it, then press
Copy and paste the line back into the chat. Claude rewrites the `featured`
numbers and rebuilds.

The page stores nothing. It is generated from `content/` every run, so it can
never show a stale order the way the old Portfolio Studio did, and dragging a
tile changes nothing on disk until you send the order back.

Needs Pillow for small thumbnails; without it the images go in full size and
the file is simply larger.
"""
from __future__ import annotations

import base64
import html
import io
import json
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import build  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
THUMB_W = 260

try:
    from PIL import Image
except ImportError:
    Image = None


def thumb(rel: str) -> str | None:
    p = (ROOT / rel).resolve()
    if not p.exists():
        return None
    if Image is None:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    im = Image.open(p).convert("RGB")
    im.thumbnail((THUMB_W, THUMB_W * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=72, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    site, projects = build.load()
    shelves = []
    for gid, label in build.GROUPS:
        items = sorted((p for p in projects if build.group(p) == gid),
                       key=lambda p: (p.get("featured", 99), not p.get("figures")))
        if items:
            shelves.append((gid, label, items))

    # Hidden cards never reach build.load()'s output, so read them straight off disk.
    # Without this there is no way to see, let alone unhide, a card that is off.
    import glob
    live = {p["slug"] for p in projects}
    hidden = []
    for f in sorted(glob.glob(str(ROOT / "content" / "*.json"))):
        c = json.load(open(f))
        if isinstance(c, dict) and c.get("slug") and c["slug"] not in live:
            hidden.append(c)
    hidden.sort(key=lambda c: (c.get("status", "zz"), c["slug"]))
    if hidden:
        shelves.append(("hidden", "Hidden (not on the site)", hidden))

    data = []
    for gid, label, items in shelves:
        cards = []
        for p in items:
            figs = p.get("figures") or []
            cards.append({
                "slug": p["slug"],
                "title": p.get("title", ""),
                "line": (p.get("line") or "")[:110],
                "status": p.get("status", ""),
                "public": bool(p.get("public")),
                "featured": p.get("featured"),
                "nfig": len(figs),
                "thumb": thumb(figs[0]["file"]) if figs else None,
                "hidden": gid == "hidden",
            })
        data.append({"id": gid, "label": label, "cards": cards})

    stamp = datetime.now().strftime("%-d %b %Y, %H:%M")
    page = TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__STAMP__", html.escape(stamp))
    out = ROOT / "_preview"
    out.mkdir(exist_ok=True)
    (out / "reorder.html").write_text(page)
    n = sum(len(s["cards"]) for s in data)
    print(f"{n} cards across {len(data)} shelf/shelves, "
          f"{len(page)/1e6:.2f} MB -> {out / 'reorder.html'}")
    if Image is None:
        print("  (no Pillow: thumbnails are full size. "
              "uv run --no-project --with pillow python scripts/reorder.py)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reorder cards</title>
<style>
  :root{
    --bg:#0E1113; --panel:#171B1E; --panel-2:#1E2327; --line:#2A3034;
    --ink:#E8EAE9; --soft:#9AA3A6; --faint:#6B7478; --accent:#B87C14; --live:#00918A;
  }
  @media (prefers-color-scheme: light){
    :root:not([data-theme="dark"]){
      --bg:#FBFAF8; --panel:#fff; --panel-2:#F2F1ED; --line:#E4E7E4;
      --ink:#1A1D1C; --soft:#5A6160; --faint:#8A918D;
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;
    padding:0 16px 120px}
  header{max-width:980px;margin:0 auto;padding:26px 0 8px}
  h1{font-size:21px;margin:0 0 6px;font-weight:650}
  .sub{color:var(--soft);font-size:13.5px;margin:0}
  h2{font-size:13px;letter-spacing:.07em;text-transform:uppercase;color:var(--faint);
    margin:30px 0 10px;font-weight:600}
  .wrap{max-width:980px;margin:0 auto}
  ol{list-style:none;margin:0;padding:0;display:grid;gap:8px;
     grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
  li{display:flex;gap:11px;align-items:flex-start;background:var(--panel);
     border:1px solid var(--line);border-radius:10px;padding:9px 11px 9px 9px;
     cursor:grab;touch-action:none;user-select:none}
  li.drag{opacity:.35}
  li.over{outline:2px solid var(--accent);outline-offset:1px}
  .pos{flex:0 0 22px;text-align:right;color:var(--faint);font-variant-numeric:tabular-nums;
    font-size:13px;padding-top:2px}
  .thumb{flex:0 0 58px;height:46px;border-radius:5px;background:var(--panel-2);
    object-fit:cover;object-position:top center}
  .noimg{flex:0 0 58px;height:46px;border-radius:5px;background:var(--panel-2);
    display:grid;place-items:center;color:var(--faint);font-size:10px}
  .meta{min-width:0;flex:1}
  .t{font-weight:600;font-size:13.5px;line-height:1.3;margin:0 0 2px;
     overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
  .l{color:var(--soft);font-size:11.5px;line-height:1.35;margin:0 0 4px;
     overflow:hidden;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical}
  .chips{display:flex;gap:4px;flex-wrap:wrap}
  .c{font-size:10px;padding:1px 6px;border-radius:99px;border:1px solid var(--line);
     color:var(--faint)}
  .nudge{flex:0 0 26px;display:flex;flex-direction:column;gap:3px;padding-top:1px}
  .nudge button{padding:0;width:26px;height:22px;font-size:11px;line-height:1;
     border-radius:5px;font-weight:400;color:var(--soft)}
  .nudge button:disabled{opacity:.25}
  .c.live{color:var(--live);border-color:var(--live)}
  .c.hidden{color:var(--accent);border-color:var(--accent)}
  .c.off{cursor:pointer;color:var(--faint);border-style:dashed;padding:2px 8px}
  .c.off[data-show="1"]{color:var(--live);border-color:var(--live);border-style:solid}
  li.willshow{border-color:var(--live)}
  .bar{position:fixed;left:0;right:0;bottom:0;background:var(--panel);
    border-top:1px solid var(--line);padding:11px 16px;display:flex;gap:10px;
    align-items:center;justify-content:center;flex-wrap:wrap}
  button{font:inherit;font-size:14px;font-weight:600;padding:9px 18px;border-radius:8px;
    border:1px solid var(--line);background:var(--panel-2);color:var(--ink);cursor:pointer}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
  #said{color:var(--soft);font-size:13px;min-height:18px;text-align:center;width:100%}
  textarea{position:absolute;left:-9999px}
</style></head><body>
<header class="wrap">
  <h1>Reorder cards</h1>
  <p class="sub">Generated from the repo on __STAMP__. Drag a tile, then press Copy
  and paste the line into the chat. Nothing changes on disk until you send it back.</p>
</header>
<div class="wrap" id="root"></div>
<div class="bar">
  <button class="primary" id="copy">Copy the new order</button>
  <button id="reset">Reset</button>
  <div id="said"></div>
</div>
<textarea id="sink"></textarea>
<script>
const DATA = __DATA__;
const root = document.getElementById('root');
const said = document.getElementById('said');
const original = JSON.stringify(DATA.map(s => s.cards.map(c => c.slug)));

function renumber(ol){
  const kids = [...ol.children];
  kids.forEach((li,i) => {
    li.querySelector('.pos').textContent = i+1;
    li.querySelector('.up').disabled = (i === 0);
    li.querySelector('.down').disabled = (i === kids.length-1);
  });
}

function render(){
  root.innerHTML = '';
  for (const shelf of DATA){
    const h = document.createElement('h2'); h.textContent = shelf.label; root.appendChild(h);
    const ol = document.createElement('ol'); ol.dataset.shelf = shelf.id;
    for (const c of shelf.cards){
      const li = document.createElement('li');
      li.draggable = true; li.dataset.slug = c.slug;
      const chips = [];
      if (c.status) chips.push(`<span class="c${c.status==='live'?' live':''}">${c.status}</span>`);
      if (!c.public) chips.push('<span class="c hidden">not public</span>');
      if (c.hidden) chips.push('<span class="c off" data-show="0">off &#183; tap to turn on</span>');
      chips.push(`<span class="c">${c.nfig} fig${c.nfig===1?'':'s'}</span>`);
      li.innerHTML =
        `<div class="pos"></div>` +
        (c.thumb ? `<img class="thumb" src="${c.thumb}" alt="">`
                 : `<div class="noimg">none</div>`) +
        `<div class="meta"><p class="t">${c.title}</p>` +
        (c.line ? `<p class="l">${c.line}</p>` : '') +
        `<div class="chips">${chips.join('')}</div></div>` +
        `<div class="nudge"><button class="up" title="move up">&#9650;</button>` +
        `<button class="down" title="move down">&#9660;</button></div>`;
      ol.appendChild(li);
    }
    renumber(ol); root.appendChild(ol);
  }
}

// Arrows, because HTML5 drag does not fire on a touch screen and this page is
// meant to be usable on a phone.
root.addEventListener('click', e => {
  const tog = e.target.closest('.c.off');
  if (tog){
    const on = tog.dataset.show === '1';
    tog.dataset.show = on ? '0' : '1';
    tog.innerHTML = on ? 'off &#183; tap to turn on' : 'turn ON &#183; tap to undo';
    tog.closest('li').classList.toggle('willshow', !on);
    said.textContent = 'press Copy to send the change.';
    return;
  }
  const btn = e.target.closest('.up, .down'); if (!btn) return;
  const li = btn.closest('li'), ol = li.parentElement;
  if (btn.classList.contains('up')) { const prev = li.previousElementSibling;
    if (prev) prev.before(li); }
  else { const next = li.nextElementSibling; if (next) next.after(li); }
  renumber(ol);
  li.scrollIntoView({block:'nearest', behavior:'smooth'});
  said.textContent = 'moved. press Copy when the order looks right.';
});

let dragged = null;
root.addEventListener('dragstart', e => {
  if (e.target.closest('.nudge')) { e.preventDefault(); return; }
  const li = e.target.closest('li'); if (!li) return;
  dragged = li; li.classList.add('drag'); e.dataTransfer.effectAllowed = 'move';
});
root.addEventListener('dragend', e => {
  if (dragged) dragged.classList.remove('drag');
  root.querySelectorAll('.over').forEach(n => n.classList.remove('over'));
  dragged = null;
});
root.addEventListener('dragover', e => {
  const li = e.target.closest('li');
  if (!li || !dragged || li === dragged) return;
  if (li.parentElement !== dragged.parentElement) return;   // same shelf only
  e.preventDefault();
  root.querySelectorAll('.over').forEach(n => n.classList.remove('over'));
  li.classList.add('over');
});
root.addEventListener('drop', e => {
  const li = e.target.closest('li');
  if (!li || !dragged || li.parentElement !== dragged.parentElement) return;
  e.preventDefault();
  const ol = li.parentElement, kids = [...ol.children];
  kids.indexOf(dragged) < kids.indexOf(li) ? li.after(dragged) : li.before(dragged);
  li.classList.remove('over');
  renumber(ol);
  said.textContent = 'moved. press Copy when the order looks right.';
});

function currentOrder(){
  return [...root.querySelectorAll('ol')].map(ol => ({
    shelf: ol.dataset.shelf,
    slugs: [...ol.children].map(li => li.dataset.slug)
  }));
}

document.getElementById('copy').onclick = async () => {
  const cur = currentOrder();
  const same = JSON.stringify(cur.map(s => s.slugs)) === original;
  const turnOn = [...root.querySelectorAll('.c.off[data-show="1"]')]
                   .map(t => t.closest('li').dataset.slug);
  const parts = [];
  if (!same) parts.push('set the card order to: ' + cur.filter(s => s.shelf !== 'hidden')
      .map(s => `${s.shelf} = ${s.slugs.join(', ')}`).join('  |  '));
  if (turnOn.length) parts.push('turn these cards ON: ' + turnOn.join(', '));
  const text = parts.length ? parts.join('\n') : 'nothing changed';
  try { await navigator.clipboard.writeText(text); }
  catch { const t = document.getElementById('sink');
          t.value = text; t.select(); document.execCommand('copy'); }
  said.textContent = (same && !turnOn.length) ? 'nothing changed, so nothing to send.'
                                              : 'copied. paste it into the chat.';
};
document.getElementById('reset').onclick = () => {
  render(); said.textContent = 'back to the order on disk.';
};
render();
</script></body></html>
"""


if __name__ == "__main__":
    main()
