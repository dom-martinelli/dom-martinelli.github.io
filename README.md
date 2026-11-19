# dom-martinelli.github.io

Personal site. Static HTML, no build tooling beyond one script.

- `content/*.json` — one file per project, plus `_site.json` for the tabs and home copy.
- `assets/` — stylesheet, tab script, figures.
- `build.py` — reads the JSON and writes `index.html` and `projects/*.html`.

Edit a JSON file, then:

    python3 build.py

Commit the generated HTML along with the content change; GitHub Pages serves the
files as they are.

## Tests

`tests/` holds two layers: contract checks over the content JSON and the
generated HTML (pytest, no browser, under a second) and browser tests
(Playwright, Chrome and mobile Safari). Both run on every push via
`.github/workflows/tests.yml`. The plan, including what is deliberately not
tested and what the first run found, is in [tests/TEST-PLAN.md](tests/TEST-PLAN.md).

    cd tests
    python3 -m pytest checks -q      # 227 contract checks
    npm ci && npx playwright install
    npx playwright test              # 203 browser cases
