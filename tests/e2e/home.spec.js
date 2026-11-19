// The home page's own promises.
//
// Each test here encodes something that is true on purpose, so that breaking it
// turns red instead of quietly shipping. The interesting ones are not "does the
// h1 exist" but the two invariants the generator can violate: the count badge
// on a shelf heading has to match the tiles under it, and there is exactly one
// Projects shelf (that one is a decision, not an accident, and it has been
// undone by hand before).
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/index.html");
});

test("loads with the name and a document title", async ({ page }) => {
  await expect(page.locator("h1")).toHaveText("Dom Martinelli");
  await expect(page).toHaveTitle(/Dom Martinelli/);
});

test("each shelf's count badge matches the number of cards under it", async ({ page }) => {
  // build.py writes the badge from len(items); if the committed HTML is stale
  // relative to content/*.json, or the two ever drift, this is where it shows.
  //
  // The selector is `.tile`, not `a.tile`. A project with a live tool is built
  // as a div.tile holding two links (the picture opens the tool, the text opens
  // the write-up), so an anchor-only selector silently misses those five and
  // reports a mismatch that is not there. A test that is wrong in the same
  // direction every time is worse than no test, because it gets believed once
  // and then disbelieved forever.
  const shelves = [
    { id: "papers", card: "article.paper" },
    { id: "analyses", card: ".tile" },
  ];
  for (const { id, card } of shelves) {
    const shelf = page.locator(`section.shelf#${id}`);
    await expect(shelf, `shelf #${id} should exist`).toHaveCount(1);
    const badge = Number(await shelf.locator("h2 span.count").innerText());
    const cards = await shelf.locator(card).count();
    expect(cards, `#${id}: badge says ${badge}, ${cards} cards rendered`).toBe(badge);
    expect(cards, `#${id} should not be empty`).toBeGreaterThan(0);
  }
});

test("there is one Projects shelf, not a tools/analyses split", async ({ page }) => {
  // a locked decision, asserted so a later edit cannot quietly reverse it
  await expect(page.locator("section.shelf")).toHaveCount(2);
  await expect(page.locator("section.shelf > h2")).toHaveText([/^Papers/, /^Projects/]);
});

test("every project tile has a readable title, an image with alt text, and a target", async ({ page }) => {
  const tiles = page.locator("section#analyses .tile");
  const n = await tiles.count();
  expect(n).toBeGreaterThan(5);

  for (let i = 0; i < n; i++) {
    const tile = tiles.nth(i);

    // two shapes: a plain tile is itself the link; a tile with a live tool is a
    // div holding the tool link and the write-up link. Either way the reader
    // has to be able to reach the write-up from the tile.
    const own = await tile.getAttribute("href");
    const inner = await tile.locator("a.tile-body").count();
    const href = own ?? (inner ? await tile.locator("a.tile-body").getAttribute("href") : null);
    expect(href, `tile ${i} offers no link to its project page`).toBeTruthy();
    expect(href, `tile ${i} links somewhere unexpected: ${href}`).toMatch(/^projects\/.+\.html$/);

    const heading = (await tile.locator("h3").first().innerText()).trim();
    expect(heading, `tile ${i} (${href}) has an empty heading`).not.toBe("");

    // alt text is the caption a screen reader gets. empty alt on a content
    // image is a real accessibility defect, not a nit.
    const img = tile.locator("img").first();
    if (await img.count()) {
      const alt = (await img.getAttribute("alt")) ?? "";
      expect(alt.trim(), `tile ${i} (${href}) has an image with no alt text`).not.toBe("");
    }
  }
});

test("a tile with a live tool offers both links, and they go to different places", async ({ page }) => {
  // the shape that broke the count test above, pinned down so the intent is
  // recorded: the picture opens the tool, the text opens the write-up
  const live = page.locator("section#analyses div.tile");
  const n = await live.count();
  expect(n, "the home page should have at least one live-tool tile").toBeGreaterThan(0);

  for (let i = 0; i < n; i++) {
    const tile = live.nth(i);
    const tool = await tile.locator(".panel-live a, a:not(.tile-body)").first().getAttribute("href");
    const writeup = await tile.locator("a.tile-body").getAttribute("href");
    expect(writeup, `live tile ${i} has no write-up link`).toBeTruthy();
    expect(tool, `live tile ${i} has no tool link`).toBeTruthy();
    expect(tool, `live tile ${i} sends both links to the same place`).not.toBe(writeup);
  }
});

test("the subject jump links point at sections that exist", async ({ page }) => {
  const anchors = await page.locator("nav.jump a").evaluateAll((as) =>
    as.map((a) => a.getAttribute("href"))
  );
  expect(anchors.length).toBeGreaterThan(0);
  for (const a of anchors) {
    expect(a.startsWith("#"), `jump link ${a} is not an anchor`).toBe(true);
    await expect(page.locator(a), `no section for jump link ${a}`).toHaveCount(1);
  }
});

test("no template or placeholder text leaked into the page", async ({ page }) => {
  // the generator interpolates strings; a missing key shows up as one of these.
  //
  // Whole words only. The first version of this test matched substrings and
  // failed on "nan" inside "provenance" — a check that cries wolf on correct
  // prose gets switched off, and then it is not checking anything. "None" and
  // "nan" on their own are gone for the same reason: they are too collision-
  // prone in English to be worth their recall. The python-side type checks in
  // tests/checks catch that class at its source instead.
  const body = await page.locator("body").innerText();
  const tells = [/\bundefined\b/, /\bNaN\b/, /\{\{/, /\}\}/, /\bTODO\b/, /\bFIXME\b/, /\bnull\b/];
  for (const tell of tells) {
    const hit = body.match(tell);
    expect(hit, `page text contains ${tell}: "${hit?.input?.slice(Math.max(0, hit.index - 50), hit.index + 50)}"`).toBeNull();
  }
});
