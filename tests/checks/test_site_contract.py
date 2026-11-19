"""Contract checks for the site generator. No browser, no network, ~1 second.

The browser tests in ../e2e answer "does the page work for a reader". These
answer "is the repo internally consistent", which is a cheaper question with a
faster answer, so it belongs first in CI: when the content JSON and the
committed HTML disagree, this fails in a second and names the file, instead of
a Playwright run failing in a minute and naming a selector.

Run from tests/:   python3 -m pytest checks -q
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
PROJECTS = ROOT / "projects"

PROJECT_FILES = sorted(p for p in CONTENT.glob("*.json") if not p.stem.startswith("_"))
BUILT_PAGES = sorted(PROJECTS.glob("*.html"))


def load(p: Path) -> dict:
    return json.loads(p.read_text())


SITE = load(CONTENT / "_site.json")


# --------------------------------------------------------------------------
# the content files themselves
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", PROJECT_FILES, ids=lambda p: p.stem)
def test_project_json_has_the_fields_the_pages_read(path: Path):
    """build.py indexes these without a default, so a missing one is a crash or
    a blank page, depending on which. Checking here means the error message
    says which file and which field."""
    d = load(path)
    for field in ("slug", "title", "tab"):
        assert d.get(field), f"{path.name}: missing or empty {field!r}"
    assert d["slug"] == path.stem, f"{path.name}: slug {d['slug']!r} does not match the filename"
    assert isinstance(d["title"], str) and d["title"].strip()


@pytest.mark.parametrize("path", PROJECT_FILES, ids=lambda p: p.stem)
def test_list_fields_are_lists_of_strings(path: Path):
    """A string where a list belongs renders as one character per bullet. It is
    the kind of mistake that looks like a styling problem and is not."""
    d = load(path)
    for field in ("skills", "tools", "data", "did", "found", "so_what", "items", "planned", "calls", "broke"):
        v = d.get(field)
        if v is None:
            continue
        assert isinstance(v, list), f"{path.name}: {field!r} is {type(v).__name__}, expected a list"
        for i, item in enumerate(v):
            assert isinstance(item, str), f"{path.name}: {field}[{i}] is {type(item).__name__}"
            assert item.strip(), f"{path.name}: {field}[{i}] is blank"


@pytest.mark.parametrize("path", PROJECT_FILES, ids=lambda p: p.stem)
def test_tab_is_one_the_site_declares(path: Path):
    d = load(path)
    tabs = {t["label"] if isinstance(t, dict) else t for t in SITE["tabs"]}
    tabs |= {t.get("id") for t in SITE["tabs"] if isinstance(t, dict)}
    assert d["tab"] in tabs, f"{path.name}: tab {d['tab']!r} is not in _site.json tabs ({sorted(tabs)})"


def test_order_is_unique_and_only_names_real_projects():
    order = SITE["order"]
    dupes = {s for s in order if order.count(s) > 1}
    assert not dupes, f"_site.json order lists these twice: {sorted(dupes)}"
    known = {p.stem for p in PROJECT_FILES}
    assert not (set(order) - known), f"order names projects with no content file: {sorted(set(order) - known)}"


# --------------------------------------------------------------------------
# the bug class that shipped: local links written in the wrong directory frame
# --------------------------------------------------------------------------


def _local(url: str) -> bool:
    return not re.match(r"^(https?:|mailto:|tel:|#|data:|//)", url)


@pytest.mark.parametrize("path", PROJECT_FILES, ids=lambda p: p.stem)
def test_local_links_resolve_from_the_page_that_will_host_them(path: Path):
    """A links[].url is pasted straight into a project page, so it is relative
    to /projects/, not to the site root. Writing "projects/x.html" there — the
    form the home page needs — renders a link to /projects/projects/x.html.

    Two of those were live when this test was written, and a third was latent
    in a project whose page had not been generated yet. The generator cannot
    catch it, because both forms are valid strings.
    """
    d = load(path)
    for link in d.get("links") or []:
        url = link["url"]
        if not _local(url):
            continue
        assert not url.startswith("projects/"), (
            f"{path.name}: link {url!r} is written relative to the site root, but it is "
            f"rendered inside projects/. Use {url.removeprefix('projects/')!r}."
        )
        target = (PROJECTS / url.split("#")[0]).resolve()
        assert target.exists(), f"{path.name}: link {url!r} points at a file that does not exist ({target})"


@pytest.mark.parametrize("path", PROJECT_FILES, ids=lambda p: p.stem)
def test_every_figure_file_exists(path: Path):
    """Figure paths are site-root-relative and build.py prefixes the depth, so
    these resolve from the repo root."""
    d = load(path)
    for i, fig in enumerate(d.get("figures") or []):
        f = fig.get("file")
        assert f, f"{path.name}: figures[{i}] has no file"
        assert (ROOT / f).exists(), f"{path.name}: figures[{i}] file missing: {f}"
        if fig.get("interactive") and _local(fig["interactive"]):
            t = ROOT / fig["interactive"]
            assert t.exists(), f"{path.name}: figures[{i}].interactive missing: {fig['interactive']}"


# --------------------------------------------------------------------------
# generated output matches its source
# --------------------------------------------------------------------------


def test_committed_html_matches_a_fresh_build(tmp_path: Path):
    """The repo commits generated HTML alongside the JSON it came from, so the
    two can disagree: edit the JSON and forget `python3 build.py`, or hand-edit
    an HTML file that the next build will overwrite. Either way the site a
    reader sees stops matching the source of truth.

    The build runs in a throwaway directory, so the test never writes to the
    working tree — a check that mutates the thing it is checking is not a check.
    """
    for name in ("build.py", "content"):
        src = ROOT / name
        dst = tmp_path / name
        if src.is_dir():
            dst.mkdir()
            for f in src.rglob("*"):
                rel = f.relative_to(src)
                if f.is_dir():
                    (dst / rel).mkdir(parents=True, exist_ok=True)
                else:
                    (dst / rel).write_bytes(f.read_bytes())
        else:
            dst.write_bytes(src.read_bytes())
    # assets are only read for existence (thumbnails), so a link is enough and
    # keeps the test off 26 MB of copying
    (tmp_path / "assets").symlink_to(ROOT / "assets")
    (tmp_path / "tools").symlink_to(ROOT / "tools")

    proc = subprocess.run(
        [sys.executable, "build.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert proc.returncode == 0, f"build.py failed:\n{proc.stdout}\n{proc.stderr}"

    stale = []
    for rel in ["index.html", "gallery.html", "archive.html"] + [
        f"projects/{p.name}" for p in BUILT_PAGES
    ]:
        fresh, committed = tmp_path / rel, ROOT / rel
        if not fresh.exists() and not committed.exists():
            continue
        if not committed.exists():
            stale.append(f"{rel}: build.py produces it, but it is not committed")
        elif not fresh.exists():
            stale.append(f"{rel}: committed, but no longer produced by build.py")
        elif fresh.read_bytes() != committed.read_bytes():
            stale.append(f"{rel}: committed HTML differs from a fresh build")

    assert not stale, "run `python3 build.py` and commit the result:\n  " + "\n  ".join(stale)


@pytest.mark.parametrize("page", BUILT_PAGES, ids=lambda p: p.stem)
def test_every_built_page_is_reachable_from_the_home_page_or_gallery(page: Path):
    """A page nobody links to is a page nobody reads. This has happened twice:
    a project got a page and never got added to the order list."""
    index = (ROOT / "index.html").read_text()
    gallery = (ROOT / "gallery.html").read_text() if (ROOT / "gallery.html").exists() else ""
    direct = f"projects/{page.name}" in index or f"projects/{page.name}" in gallery
    if direct:
        return
    # or linked from a page that is itself reachable (one hop is enough here)
    for other in BUILT_PAGES:
        if other == page:
            continue
        if f"projects/{other.name}" in index and page.name in other.read_text():
            return
    pytest.fail(f"projects/{page.name} is not linked from index.html, gallery.html, or any linked project page")
