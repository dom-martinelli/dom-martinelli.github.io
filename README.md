# dom-martinelli.github.io

Personal site. Static HTML, no build tooling beyond one script.

- `content/*.json` — one file per project, plus `_site.json` for the tabs and home copy.
- `assets/` — stylesheet, tab script, figures.
- `build.py` — reads the JSON and writes `index.html` and `projects/*.html`.

Edit a JSON file, then:

    python3 build.py

Commit the generated HTML along with the content change; GitHub Pages serves the
files as they are.
