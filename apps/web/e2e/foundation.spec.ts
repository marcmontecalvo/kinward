import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const surfaces = ["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"] as const;
const privateMarkers = ["PRIVATE_PERSON_EXAMPLE_TOPIC", "PRIVATE_CHILD_EXAMPLE_EVENT"];

test.describe("five-surface mock-backed foundation", () => {
  for (const surface of surfaces) {
    test(`${surface} resolves through the shared registries`, async ({ page }) => {
      await page.goto(`/?surface=${surface}`);
      const shell = page.locator("main.surface-shell");
      await expect(shell).toHaveAttribute("data-surface", surface);
      await expect(shell).toHaveAttribute("data-layout-provenance", "product-default");
      await expect(shell).toHaveAttribute("data-layout-version", "1");
      await expect(shell).toHaveAttribute("data-context-version", "1");
      await expect(page.getByText("mock-backed foundation", { exact: false }).first()).toBeVisible();
      const cards = page.locator("[data-card-type]");
      expect(await cards.count()).toBe(8);
      for (const card of await cards.all()) {
        await expect(card).toHaveAttribute("data-card-version", "1");
      }
      const body = await page.locator("body").innerText();
      if (surface.startsWith("shared-")) for (const marker of privateMarkers) expect(body).not.toContain(marker);
    });
  }

  test("surface contexts are visibly distinct rather than enlarged mobile", async ({ page }) => {
    const snapshots = new Map<string, string>();
    for (const surface of surfaces) {
      await page.goto(`/?surface=${surface}`);
      const shell = page.locator("main.surface-shell");
      const descriptor = [
        await shell.getAttribute("data-interaction"),
        await shell.getAttribute("data-viewing-distance"),
        await shell.getAttribute("data-privacy"),
        await shell.getAttribute("data-layout-id"),
        await page.locator(".surface-description").innerText(),
      ].join("|");
      snapshots.set(surface, descriptor);
    }
    expect(new Set(snapshots.values()).size).toBe(5);
  });

  test("invalid layout activation falls back to the immutable product default", async ({ page }) => {
    await page.goto("/?surface=personal-desktop&invalidLayout=1");
    const shell = page.locator("main.surface-shell");
    await expect(shell).toHaveAttribute("data-layout-provenance", "product-default");
    await expect(shell).toHaveAttribute("data-fallback-reason", "upgrade-required");
    await expect(shell).toHaveAttribute("data-layout-id", "product-personal-desktop");
    await expect(page.getByRole("heading", { name: "Now" })).toBeVisible();
  });

  test("shared uncertainty and authorization loss remove forbidden DOM state", async ({ page }) => {
    await page.goto("/?surface=shared-kitchen&identity=candidate");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Hello.");
    let body = await page.locator("body").innerText();
    expect(body).not.toContain("SELECTED_SHARE_EXAMPLE_ITEM");
    for (const marker of privateMarkers) expect(body).not.toContain(marker);
    await page.getByRole("button", { name: "Show selected share" }).click();
    await expect(page.getByText("SELECTED_SHARE_EXAMPLE_ITEM")).toBeVisible();
    await page.getByRole("button", { name: "End private preview" }).click();
    await expect(page.getByText("SELECTED_SHARE_EXAMPLE_ITEM")).toHaveCount(0);
    body = await page.locator("body").innerText();
    expect(body).toContain("Private preview ended.");
    for (const marker of [...privateMarkers, "SELECTED_SHARE_EXAMPLE_ITEM"]) expect(body).not.toContain(marker);
    const storage = await page.evaluate(async () => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      indexed: await indexedDB.databases(),
      caches: "caches" in window ? await caches.keys() : [],
    }));
    expect(storage).toEqual({ local: [], session: [], indexed: [], caches: [] });
  });

  test("mobile and desktop preserve essential hierarchy without horizontal loss", async ({ page }) => {
    for (const surface of ["personal-mobile", "personal-desktop"] as const) {
      await page.setViewportSize(surface === "personal-mobile" ? { width: 360, height: 800 } : { width: 1440, height: 900 });
      await page.goto(`/?surface=${surface}`);
      for (const name of ["Now", "Briefing", "Continue", "Assistant input"]) await expect(page.getByRole("heading", { name })).toBeVisible();
      await expect(page.getByRole("navigation", { name: "Primary assistant navigation" })).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow).toBeLessThanOrEqual(1);
      expect(await page.locator("[data-card-type=\"now\"] button").count()).toBeLessThanOrEqual(1);
      expect(await page.locator(".dominant-decision").count()).toBe(1);
    }
  });

  test("reference shared fixture passes semantics, scaling, targets, contrast, and room typography", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium-desktop", "Reference evidence uses the desktop Chromium profile");
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/?surface=shared-living-room&identity=verified-selected");
    for (const name of ["Now", "Briefing", "Approval", "House status"]) await expect(page.getByRole("heading", { name })).toBeVisible();
    await expect(page.getByText("House status is intentionally unavailable in this mock", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Continue on a personal device" })).toBeVisible();
    const violations = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag22aa"]).analyze();
    expect(violations.violations).toEqual([]);
    const targets = await page.locator("button, input").evaluateAll((elements) => elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }));
    for (const target of targets) expect(Math.min(target.width, target.height)).toBeGreaterThanOrEqual(48);
    const geometry = await page.locator(".layout-instance").evaluateAll((elements) => elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, clippedX: element.scrollWidth > element.clientWidth + 1, clippedY: element.scrollHeight > element.clientHeight + 1 };
    }));
    for (const item of geometry) {
      expect(item.clippedX).toBe(false);
      expect(item.clippedY).toBe(false);
    }
    for (let left = 0; left < geometry.length; left += 1) for (let right = left + 1; right < geometry.length; right += 1) {
      const a = geometry[left];
      const b = geometry[right];
      if (!a || !b) continue;
      const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      expect(overlapWidth > 1 && overlapHeight > 1).toBe(false);
    }
    const decisionSpacing = await page.locator(".decision-actions button").evaluateAll((elements) => {
      const [first, second] = elements.map((element) => element.getBoundingClientRect());
      return first && second ? Math.max(second.left - first.right, first.left - second.right, second.top - first.bottom, first.top - second.bottom) : 0;
    });
    expect(decisionSpacing).toBeGreaterThanOrEqual(8);
    const headingSize = await page.getByRole("heading", { level: 1 }).evaluate((element) => Number.parseFloat(getComputedStyle(element).fontSize));
    expect(headingSize).toBeGreaterThanOrEqual(48);
    await page.screenshot({ path: testInfo.outputPath("shared-reference-100-percent.png"), fullPage: true });
    await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    await expect(page.getByRole("heading", { name: "Approval" })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("shared-reference-200-percent.png"), fullPage: true });
  });

  test("keyboard, focus, reduced motion, and forced colors retain plain cues", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce", forcedColors: "active" });
    await page.goto("/?surface=shared-kitchen");
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    await expect(focused).toBeVisible();
    const outline = await focused.evaluate((element) => getComputedStyle(element).outlineStyle);
    expect(outline).not.toBe("none");
    await expect(page.getByText("Shared surface · household-safe information only.")).toBeVisible();
    const reduced = await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
    const contrast = await page.evaluate(() => matchMedia("(forced-colors: active)").matches);
    expect(reduced).toBe(true);
    expect(contrast).toBe(true);
  });
});
