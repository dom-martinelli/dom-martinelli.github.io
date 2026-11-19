// Phone layout, checked by measurement rather than by eye.
//
// The failure this catches is horizontal overflow: one wide table, one long
// unbroken URL, or one image without a max-width, and the whole page scrolls
// sideways on a phone. It is invisible on a laptop and obvious to every reader
// on a phone, which is the worst combination a bug can have.
import { test, expect } from "@playwright/test";

const PAGES = ["/index.html", "/gallery.html", "/projects/patient-innovation-index.html"];

test.describe("narrow screens", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  for (const url of PAGES) {
    test(`${url} does not scroll sideways at 375px`, async ({ page }) => {
      await page.goto(url);
      const { scrollWidth, clientWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      // 1px of slack for subpixel rounding, no more
      expect(
        scrollWidth,
        `${url} is ${scrollWidth - clientWidth}px wider than the viewport`
      ).toBeLessThanOrEqual(clientWidth + 1);
    });

    test(`${url} keeps every element inside the viewport`, async ({ page }) => {
      await page.goto(url);
      // name the culprit, rather than only reporting that the page is too wide
      const offenders = await page.evaluate(() => {
        const w = document.documentElement.clientWidth;
        const out = [];
        for (const el of document.querySelectorAll("body *")) {
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) continue;
          if (r.right > w + 1) {
            out.push(
              `${el.tagName.toLowerCase()}${el.className ? "." + String(el.className).split(" ")[0] : ""}` +
                ` overflows by ${Math.round(r.right - w)}px`
            );
          }
        }
        return [...new Set(out)].slice(0, 10);
      });
      expect(offenders, offenders.join("\n  ")).toEqual([]);
    });
  }
});

test("tap targets in the header are big enough to hit", async ({ page }) => {
  // WCAG 2.2 success criterion 2.5.8 (Target Size, Minimum) asks for 24x24 css
  // px, and names an exception for targets "in a sentence or block of text".
  //
  // Applying the rule without its exception produced a finding that is not a
  // defect: the subject jump row renders as "Papers · Projects", two inline
  // links in a line of text, measured at 44x22 and 51x22. Flagging those is how
  // an accessibility check loses the argument with the person who has to fix
  // it. So the check covers the standalone nav links and states the exception
  // rather than quietly lowering the threshold.
  //
  // https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/index.html");

  const small = await page.locator("nav:not(.jump) a").evaluateAll((as) =>
    as
      .map((a) => ({ text: a.textContent.trim(), r: a.getBoundingClientRect() }))
      .filter(({ r }) => r.height > 0 && (r.height < 24 || r.width < 24))
      .map(({ text, r }) => `${text}: ${Math.round(r.width)}x${Math.round(r.height)}`)
  );
  expect(small, `standalone nav links under 24x24:\n  ${small.join("\n  ")}`).toEqual([]);
});

test("the inline jump links are still wide enough to hit, even under the exception", async ({ page }) => {
  // the exception covers height, not reach: a 10px-wide link in a dense row is
  // unusable on a phone whether or not the standard excuses its height
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/index.html");
  const tiny = await page.locator("nav.jump a").evaluateAll((as) =>
    as
      .map((a) => ({ text: a.textContent.trim(), r: a.getBoundingClientRect() }))
      .filter(({ r }) => r.width < 32 || r.height < 16)
      .map(({ text, r }) => `${text}: ${Math.round(r.width)}x${Math.round(r.height)}`)
  );
  expect(tiny, tiny.join("\n  ")).toEqual([]);
});
