// One generated test per project page.
//
// Data-driven rather than hand-listed: the page list comes off disk at
// collection time, so a project added tomorrow is tested tomorrow without
// anyone editing this file. The failure then names the page, which is what you
// want in a CI log you are reading at speed.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect } from "@playwright/test";

const here = path.dirname(fileURLToPath(import.meta.url));
const projectsDir = path.resolve(here, "../../projects");
const pages = fs
  .readdirSync(projectsDir)
  .filter((f) => f.endsWith(".html"))
  .sort();

/**
 * Navigate, collecting anything the page complains about on the way.
 * Listeners are attached before goto, or the load-time errors are already gone
 * by the time we subscribe.
 */
async function visit(page, url) {
  const problems = [];
  page.on("pageerror", (e) => problems.push(`uncaught: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") problems.push(`console.error: ${m.text()}`);
  });
  page.on("requestfailed", (r) => problems.push(`request failed: ${r.url()}`));
  await page.goto(url);
  return problems;
}

test("the project directory is not empty", () => {
  expect(pages.length).toBeGreaterThan(10);
});

for (const file of pages) {
  test.describe(`projects/${file}`, () => {
    test("has a title, a one-line summary, and a working way back", async ({ page }) => {
      await visit(page, `/projects/${file}`);
      await expect(page.locator("h1")).not.toBeEmpty();
      await expect(page).toHaveTitle(/.+/);

      const back = page.locator("a.back");
      await expect(back, "every project page needs the back link").toHaveCount(1);
      await back.click();
      await expect(page.locator("h1")).toHaveText("Dom Martinelli");
    });

    test("renders no empty definition rows and no leaked placeholders", async ({ page }) => {
      await visit(page, `/projects/${file}`);
      // the spec list is built from optional JSON fields; an empty one should be
      // omitted by build.py, never rendered as a blank row
      const dds = await page.locator("dl.spec dd").allInnerTexts();
      for (const [i, text] of dds.entries()) {
        expect(text.trim(), `spec row ${i} rendered empty`).not.toBe("");
      }
      // whole words only: a substring match here failed on "nan" inside
      // "provenance", and a check that fires on correct prose gets ignored
      const body = await page.locator("main").innerText();
      for (const tell of [/\bundefined\b/, /\bNaN\b/, /\{\{/, /\}\}/, /\bnull\b/]) {
        expect(body.match(tell), `page text contains ${tell}`).toBeNull();
      }
    });

    test("loads clean: no js errors, no failed requests", async ({ page }) => {
      const problems = await visit(page, `/projects/${file}`);
      await page.waitForLoadState("load");
      expect(problems, problems.join("\n  ")).toEqual([]);
    });

    test("every image actually decodes", async ({ page }) => {
      await visit(page, `/projects/${file}`);
      // scroll once: the images are loading="lazy", so a check at the top of a
      // long page would pass on images the browser has not fetched yet
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 600) {
          window.scrollTo(0, y);
          await new Promise((r) => setTimeout(r, 30));
        }
      });
      const imgs = page.locator("main img");
      const n = await imgs.count();
      for (let i = 0; i < n; i++) {
        const img = imgs.nth(i);
        const src = await img.getAttribute("src");
        // naturalWidth 0 means the browser asked and got nothing usable back:
        // a 404, or a file that exists but is not a decodable image. A link
        // check cannot see the second case.
        await expect
          .poll(async () => img.evaluate((el) => el.naturalWidth), {
            message: `image never decoded: ${src}`,
            timeout: 5_000,
          })
          .toBeGreaterThan(0);
      }
    });
  });
}
