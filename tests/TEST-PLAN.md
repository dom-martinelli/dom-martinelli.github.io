# Test plan — dom-martinelli.github.io

One page. What is tested, how, what counts as passing, and what is deliberately
not tested.

## What this site is, in testing terms

A static site with one moving part. `content/*.json` is the source of truth;
`build.py` generates `index.html`, `gallery.html` and `projects/*.html`; GitHub
Pages serves the files as committed. There is no server, no database and no user
input, so the whole risk surface is three things:

1. **Generated output drifting from its source.** The HTML is committed next to
   the JSON it came from, so the two can disagree.
2. **References that do not resolve.** Links and images are strings in JSON;
   nothing checks them before they reach a reader.
3. **Behaviour on a real device.** One script (the figure lightbox) and a
   responsive layout read mostly on phones.

Everything below exists because of one of those three.

## Risk, and where each risk is covered

| # | What could go wrong | Reader's experience | Covered by |
|---|---|---|---|
| 1 | JSON edited, `build.py` not re-run | the site shows last week's text | `checks/test_site_contract.py::test_committed_html_matches_a_fresh_build`, and the CI rebuild-and-diff step |
| 2 | A link written relative to the wrong directory | a project link 404s | `checks` link resolution, `e2e/links.spec.js` |
| 3 | A figure file renamed or missing | a broken image frame | `checks` figure existence, `e2e/project-pages.spec.js` image decode |
| 4 | A content field given as a string where a list belongs | one bullet per character | `checks/test_list_fields_are_lists_of_strings` |
| 5 | A shelf heading's count going stale | the page contradicts itself | `e2e/home.spec.js` badge vs cards |
| 6 | A project page nobody links to | work that cannot be found | `checks` reachability |
| 7 | The lightbox failing to restore page scroll | the page freezes after closing a figure | `e2e/lightbox.spec.js` |
| 8 | Something overflowing the viewport | the page scrolls sideways on a phone | `e2e/responsive.spec.js` |
| 9 | A missing template value rendering as `undefined` | visible placeholder text | both layers |
| 10 | The Projects shelf being split back into two | a decision quietly reversed | `e2e/home.spec.js` |

## Two layers, cheapest first

**Layer 1, contract checks** (`tests/checks`, pytest, no browser, ~0.2 s).
Questions about files and JSON: does this field have the right type, does this
path exist, does the committed HTML match a fresh build. 227 cases, mostly
generated one-per-content-file so a new project is covered without editing a
test.

**Layer 2, browser tests** (`tests/e2e`, Playwright, ~25 s).
Questions that need a browser: does the image decode, does the dialog trap
focus, does the page fit a 375px viewport, does the back link land where it
says. 203 cases across Desktop Chrome and iPhone 13 Safari.

CI runs layer 1 first and only starts layer 2 if it passes. A wrong field type
should fail in twenty seconds naming the file, not in two minutes naming a CSS
selector.

## How to run it

```bash
cd tests
python3 -m pytest checks -q          # layer 1
npm ci && npx playwright install     # once
npx playwright test                  # layer 2
npx playwright test --headed         # watch it
npx playwright show-report           # after a failure: traces and screenshots
```

## Passing

- Both layers green on Chrome and on mobile Safari.
- No test skipped without a printed reason.
- Two consecutive runs agree. A test that passes intermittently is treated as a
  failure and fixed, not retried: CI allows one retry to absorb a server boot
  race, and anything needing more gets fixed.
- A failure message names the file or the page and the value, so it can be acted
  on without reproducing it locally.

## Not tested, on purpose

- **External links.** They rot for reasons outside this repo, and a build that
  goes red because someone else's site is down trains everyone to ignore red.
  Worth a monthly scheduled job that opens an issue, not a gate on a push.
- **Visual appearance.** No screenshot diffing. Font rendering differs between
  machines, so the failures would mostly be noise; layout is checked by
  measurement (overflow, target size) instead, which is what actually breaks.
- **The interactive tools' internals** (`tools/*.html`). They load clean and
  their links resolve; their filtering logic is not covered here. That is the
  largest real gap in this plan.
- **Lighthouse or full WCAG audits.** Specific accessibility invariants are
  asserted — image alt text, dialog roles, focus on open, target size with its
  inline exception — rather than a score that moves on its own.

## What the first run found

Three defects, all live on the published site, all in the class "nothing checked
the content files":

1. `projects/growth-medqa-explorer.html` linked to `projects/growth-medqa.html`
   from inside `projects/`, resolving to `projects/projects/growth-medqa.html`.
2. The same mistake in `projects/wakespace.html`, and a third in
   `content/pediatric-index-filter.json` that had not shipped yet because that
   page is not generated.
3. `patient-led-science.json` gave `so_what` as a string instead of a list, so
   the published page rendered one bullet per character, 160 of them.

Fixed in the content, with `ul()` in `build.py` made to coerce a string so the
class cannot reach a reader again.

Two findings that turned out to be **bugs in the tests, not the site**, which is
the other half of an honest report:

- The crawler read `href="${link}"` out of a javascript template literal inside
  a `<script>` block and called it a broken link. Script and style blocks are
  now stripped before parsing.
- The home-page count test used `a.tile`, missing the five live-tool tiles,
  which are `div.tile` holding two links by design. The badge was right.
- A placeholder check matched substrings and failed on `nan` inside
  "provenance". Whole words only now.
