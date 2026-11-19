// Every internal link resolves.
//
// This is the test that earns its keep on a generated static site. The pages
// are written by build.py from content/*.json, and a link in that JSON is just
// a string: nothing in the generator checks that the file on the other end
// exists, or that the path is relative to the right directory. Two conventions
// live side by side in the content files ("growth-medqa.html", meaning a
// sibling page, and "../tools/x.html", meaning up one level), so a path written
// in the wrong frame renders fine, looks fine, and 404s on click.
//
// It found two live ones on first run:
//   projects/growth-medqa-explorer.html -> projects/growth-medqa.html
//   projects/wakespace.html             -> projects/bupropion-market.html
// Both resolved to projects/projects/*.html.
//
// It crawls rather than taking a list, so a page added next month is covered
// without anyone remembering to add it here.
import { test, expect } from "@playwright/test";

const ENTRY = ["/index.html", "/gallery.html", "/archive.html"];

/**
 * Internal hrefs and srcs on one page, resolved against that page's URL.
 *
 * Script and style blocks are removed first. The interactive tools build their
 * tables from javascript template literals, so the raw text of those pages
 * contains things like `href="${link}"` — correct code that a regex over the
 * whole file reads as a link to a file named `${link}`. The first version of
 * this crawler reported exactly that as a broken link on
 * tools/fda-ai-devices.html, which is a false positive, and a false positive in
 * a link checker is expensive: it sends you looking for a bug that is not there
 * and it teaches you to skim the output.
 */
async function refsOn(request, baseURL, path) {
  const res = await request.get(path);
  if (!res.ok()) return { status: res.status(), refs: [] };
  const html = (await res.text())
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");
  const refs = [];
  for (const m of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const raw = m[1];
    if (/^(https?:|mailto:|tel:|data:|#|\/\/)/.test(raw)) continue;
    // anything still carrying a template marker is unrendered markup, which is
    // a different defect from a broken link; it is asserted on separately below
    if (/[$]\{|\{\{/.test(raw)) continue;
    const abs = new URL(raw, new URL(path, baseURL)).pathname;
    refs.push({ raw, abs });
  }
  return { status: res.status(), refs };
}

test.describe("internal links", () => {
  // one browser project is enough: this is a question about the server's file
  // tree, not about rendering, so running it twice buys nothing
  test.skip(({ browserName }) => browserName !== "chromium");

  test("no internal link or asset 404s anywhere on the site", async ({ request, baseURL }) => {
    const seen = new Set();
    const queue = [...ENTRY];
    const broken = [];
    const statuses = new Map();

    while (queue.length) {
      const path = queue.shift();
      if (seen.has(path)) continue;
      seen.add(path);

      const { status, refs } = await refsOn(request, baseURL, path);
      statuses.set(path, status);
      // archive.html is optional; a missing entry point is not a broken link
      if (!ENTRY.includes(path) && status >= 400) continue;

      for (const { raw, abs } of refs) {
        if (statuses.has(abs)) {
          if (statuses.get(abs) >= 400) broken.push(`${path} -> ${raw}`);
          continue;
        }
        const r = await request.get(abs);
        statuses.set(abs, r.status());
        if (r.status() >= 400) {
          broken.push(`${path} -> ${raw}  (${r.status()} at ${abs})`);
        } else if (abs.endsWith(".html")) {
          queue.push(abs);
        }
      }
    }

    // the failure message is the bug report: every broken pair, not just the first
    expect(broken, `broken internal references:\n  ${broken.join("\n  ")}`).toEqual([]);
    // guard against the crawler silently finding nothing and "passing"
    expect(seen.size, "crawler should reach more than the entry pages").toBeGreaterThan(5);
  });

  test("no link points into a directory that is already in the path", async ({ request, baseURL }) => {
    // the shape of the bug above, caught directly: a page inside /projects/
    // linking to "projects/..." . This fails even if the stray file happens to
    // exist, which a 404 check would miss.
    const res = await request.get("/index.html");
    const html = await res.text();
    const pages = [...html.matchAll(/href="(projects\/[^"#?]+\.html)"/g)].map((m) => "/" + m[1]);
    expect(pages.length, "index should link to project pages").toBeGreaterThan(5);

    const offenders = [];
    for (const p of pages) {
      const { refs } = await refsOn(request, baseURL, p);
      for (const { raw } of refs) {
        if (raw.startsWith("projects/")) offenders.push(`${p} -> ${raw}`);
      }
    }
    expect(offenders, `links written in the wrong directory frame:\n  ${offenders.join("\n  ")}`).toEqual([]);
  });

  test("no unrendered template marker reaches a link in the markup", async ({ request }) => {
    // the other half of the split above: `${...}` is fine inside a script, and
    // a defect in the markup the browser is handed. Checked against the page
    // with script and style blocks removed, so the tools' own javascript does
    // not count against it.
    const pages = ["/index.html", "/gallery.html", "/tools/fda-ai-devices.html", "/tools/stroke-belt-flows.html"];
    const offenders = [];
    for (const p of pages) {
      const res = await request.get(p);
      if (!res.ok()) continue;
      const markup = (await res.text())
        .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
        .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");
      for (const m of markup.matchAll(/(?:href|src)="([^"]*(?:[$]\{|\{\{)[^"]*)"/g)) {
        offenders.push(`${p} -> ${m[1]}`);
      }
    }
    expect(offenders, `unrendered markers in markup:\n  ${offenders.join("\n  ")}`).toEqual([]);
  });
});
