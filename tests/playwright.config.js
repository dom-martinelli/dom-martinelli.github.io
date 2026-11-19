// Playwright config for the portfolio site.
//
// The site is plain static files, so the "server" is python's own http.server
// pointed at the repo root. Playwright starts it, waits for it, and kills it
// when the run ends, which means `npm test` works the same on a laptop and in
// CI with no setup step in between.
import { defineConfig, devices } from "@playwright/test";

const PORT = process.env.PORT || 4173;

export default defineConfig({
  testDir: "./e2e",

  // A test that only passes sometimes is worse than no test: it trains you to
  // ignore red. So: no retries locally, one retry in CI (to absorb a genuinely
  // flaky network/boot race, not a flaky assertion), and any test that needs
  // more than that gets fixed instead of retried.
  retries: process.env.CI ? 1 : 0,
  forbidOnly: !!process.env.CI,
  fullyParallel: true,

  // fail fast on the thing most likely to be wrong in a static site: a hang
  timeout: 15_000,
  expect: { timeout: 5_000 },

  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }], ["list"]]
    : [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: process.env.BASE_URL || `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },

  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    // the site is read on phones more than laptops; layout regressions there
    // are the ones that actually cost a reader
    { name: "mobile-safari", use: { ...devices["iPhone 13"] } },
  ],

  webServer: {
    command: `python3 -m http.server ${PORT} --bind 127.0.0.1 --directory ..`,
    url: `http://127.0.0.1:${PORT}/index.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 20_000,
  },
});
