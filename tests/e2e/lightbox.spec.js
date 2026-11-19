// The one piece of real behaviour on the site: the figure lightbox.
//
// assets/lightbox.js intercepts clicks on a.zoom, builds a dialog, locks page
// scroll, and restores it on close. Scroll locking is the part that breaks
// silently: if close() ever stops restoring overflow, the page looks fine and
// then cannot be scrolled, and nothing about that shows up in a screenshot.
// The progressive-enhancement promise is tested too: with JS off the same link
// still has to open the file.
import { test, expect } from "@playwright/test";

const PAGE = "/projects/growth-medqa.html";

async function firstZoom(page) {
  await page.goto(PAGE);
  const zoom = page.locator("a.zoom").first();
  await expect(zoom, `${PAGE} should contain a zoomable figure`).toHaveCount(1);
  await zoom.scrollIntoViewIfNeeded();
  return zoom;
}

test("clicking a figure opens it, and the dialog announces itself", async ({ page }) => {
  const zoom = await firstZoom(page);
  const href = await zoom.getAttribute("href");

  await zoom.click();

  const box = page.locator(".lightbox.on");
  await expect(box).toBeVisible();
  await expect(box).toHaveAttribute("role", "dialog");
  await expect(box).toHaveAttribute("aria-modal", "true");

  // it shows the file that was clicked, not a cached previous one
  await expect(box.locator("img")).toHaveAttribute("src", new RegExp(href.split("/").pop()));

  // keyboard users land on the control that gets them out
  await expect(box.locator(".lb-close")).toBeFocused();
});

test("escape closes it and gives scrolling back", async ({ page }) => {
  const zoom = await firstZoom(page);
  await zoom.click();
  await expect(page.locator(".lightbox.on")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.style.overflow)).toBe("hidden");

  await page.keyboard.press("Escape");

  await expect(page.locator(".lightbox.on")).toHaveCount(0);
  // the assertion that matters: the page is usable again
  expect(
    await page.evaluate(() => document.documentElement.style.overflow),
    "page scroll was not restored on close"
  ).toBe("");
});

test("clicking the backdrop closes it, clicking the image does not", async ({ page }) => {
  const zoom = await firstZoom(page);
  await zoom.click();
  const box = page.locator(".lightbox.on");

  await box.locator("img").click();
  await expect(box, "clicking the figure itself should not dismiss it").toBeVisible();

  await box.click({ position: { x: 4, y: 4 } });
  await expect(page.locator(".lightbox.on")).toHaveCount(0);
});

test("without javascript the figure link still opens the file", async ({ browser }) => {
  // the stated design promise of lightbox.js, and the reason the markup is a
  // plain <a href> rather than a button with a handler
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const page = await ctx.newPage();
  await page.goto(PAGE);
  const zoom = page.locator("a.zoom").first();
  const href = await zoom.getAttribute("href");
  expect(href, "zoom link must carry a real href").toMatch(/\.(png|jpg|jpeg|webp|svg|gif)$/i);

  const res = await page.request.get(new URL(href, page.url()).toString());
  expect(res.status(), `figure file not served: ${href}`).toBe(200);
  await ctx.close();
});
