import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { CardState, CardView, SurfaceClass } from "@kinward/schemas";

import { syntheticCardFixtures } from "./fixtures";
import { getCard, listCards, registerCard, resolveCard, SafeCardFallback } from "./registry";
import styles from "../styles.css?raw";
import semanticTokens from "../design-system/tokens/semantic.css?raw";

// Accessibility guarantees now live across the application stylesheet AND the
// token layer (e.g. the 48px target floor and forced-colors handling are
// tokenized, not hardcoded per-selector) — check the whole system, not just
// one file, so this assertion stays true to what actually governs the page.
const allStyles = `${styles}\n${semanticTokens}`;

const states: readonly CardState[] = ["available", "empty", "loading", "degraded", "unavailable", "stale", "error"];

describe("versioned card registry", () => {
  it("contains exactly the eight canonical registrations with complete metadata", () => {
    const cards = listCards();
    expect(cards.map((card) => card.type)).toEqual([
      "assistant-presence", "now", "briefing", "continue", "schedule", "house-status", "approval", "assistant-input",
    ]);
    for (const card of cards) {
      expect(card.version).toBe(1);
      expect(card.supportedSurfaces.length).toBeGreaterThan(0);
      expect(card.capabilities.length).toBeGreaterThan(0);
      expect(card.sizing.minColumns).toBeLessThanOrEqual(card.sizing.preferredColumns);
      expect(card.sizing.preferredColumns).toBeLessThanOrEqual(card.sizing.maxColumns);
      expect(card.schema).toBeDefined();
      expect(card.render).toBeDefined();
    }
  });

  it("renders every card in every truthful state with text status and mock provenance", () => {
    for (const fixture of syntheticCardFixtures) {
      for (const state of states) {
        const view = { ...fixture.view, state, statusMessage: `Synthetic ${state} state` } as CardView;
        const resolved = resolveCard(view.type, view.version, "personal-desktop", view);
        expect(resolved.ok).toBe(true);
        if (!resolved.ok) continue;
        const Renderer = resolved.definition.render;
        const markup = renderToStaticMarkup(<Renderer cardId={fixture.id} title={fixture.title} view={resolved.view} />);
        expect(markup).toContain(`data-state="${state}"`);
        expect(markup).toContain("Synthetic");
        expect(markup).toContain("Mock-backed foundation");
        expect(markup).toContain("role=\"status\"");
      }
    }
  });

  it("fails closed for unknown versions, invalid payloads, and unsupported surfaces", () => {
    const unknown = resolveCard("generated-html", 1, "personal-mobile", { html: "<script>bad()</script>" });
    expect(unknown).toEqual({ ok: false, reason: "unregistered-card" });
    const incompatible = resolveCard("now", 2, "personal-mobile", syntheticCardFixtures[1]?.view);
    expect(incompatible).toEqual({ ok: false, reason: "unregistered-card" });
    const invalid = resolveCard("now", 1, "personal-mobile", { type: "now", version: 1, state: "available", source: "provider-native" });
    expect(invalid).toEqual({ ok: false, reason: "invalid-view-model" });
    const unsupported = resolveCard("assistant-input", 1, "voice" as SurfaceClass, syntheticCardFixtures[7]?.view);
    expect(unsupported).toEqual({ ok: false, reason: "unsupported-surface" });
    const fallback = renderToStaticMarkup(<SafeCardFallback title="Example" reason="invalid-view-model" />);
    expect(fallback).not.toContain("script");
    expect(fallback).toContain("could not be shown safely");
    for (const fixture of syntheticCardFixtures) {
      const invalidFixture = { ...fixture.view, source: "provider-native" };
      expect(resolveCard(fixture.view.type, 1, "personal-desktop", invalidFixture)).toEqual({ ok: false, reason: "invalid-view-model" });
    }
  });

  it("rejects duplicate type and version registrations", () => {
    const first = getCard("now", 1);
    expect(first).toBeDefined();
    if (first) expect(() => registerCard(first)).toThrow("already exists");
  });

  it("keeps Assistant Input text-only and approval outcomes distinct", () => {
    const input = syntheticCardFixtures[7];
    expect(input).toBeDefined();
    if (!input) return;
    const inputResolved = resolveCard(input.view.type, 1, "personal-mobile", input.view);
    expect(inputResolved.ok).toBe(true);
    if (!inputResolved.ok) return;
    const InputRenderer = inputResolved.definition.render;
    const inputMarkup = renderToStaticMarkup(<InputRenderer cardId={input.id} title={input.title} view={inputResolved.view} />).toLowerCase();
    expect(inputMarkup).toContain("type=\"text\"");
    for (const forbidden of ["microphone", "camera", "screenshot", "file", "current-screen", "selection", "ambient", "context target"]) {
      expect(inputMarkup).not.toContain(forbidden);
    }

    const approval = syntheticCardFixtures[6];
    expect(approval).toBeDefined();
    if (!approval || approval.view.type !== "approval") return;
    for (const actionState of ["acting", "submitted", "unknown", "completed", "failed", "cancelled"] as const) {
      const view = { ...approval.view, actionState };
      const resolved = resolveCard("approval", 1, "personal-desktop", view);
      expect(resolved.ok).toBe(true);
      if (!resolved.ok) continue;
      const Renderer = resolved.definition.render;
      const markup = renderToStaticMarkup(<Renderer cardId={approval.id} title={approval.title} view={resolved.view} />);
      if (actionState === "acting" || actionState === "submitted") expect(markup).toContain("completion is not confirmed");
      expect(markup).not.toContain(">Approve<");
    }
  });

  it("uses only obviously synthetic fixture content", () => {
    const serialized = JSON.stringify(syntheticCardFixtures);
    expect(serialized).toContain("synthetic-mock");
    expect(serialized).not.toMatch(/https?:\/\//);
    expect(serialized).not.toMatch(/\b(?:10|127|192)\.\d+\.\d+\.\d+\b/);
    expect(serialized).not.toContain("@");
  });

  it("declares deliberate surface support", () => {
    const surfaces: readonly SurfaceClass[] = ["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"];
    for (const surface of surfaces) expect(listCards().some((card) => card.supportedSurfaces.includes(surface))).toBe(true);
  });

  it("keeps focus, target size, high contrast, reduced motion, and reflow inspectable", () => {
    expect(allStyles).toContain(":focus-visible");
    expect(allStyles).toContain("--kw-target-min: 3rem"); /* 48px minimum interactive target, tokenized */
    expect(allStyles).toContain("prefers-reduced-motion: reduce");
    expect(allStyles).toContain("forced-colors: active");
    expect(allStyles).toContain("flex-wrap: wrap");
    expect(allStyles).toContain("max-width: 100%");
    const interactiveMarkup = renderToStaticMarkup(<>{syntheticCardFixtures.map((fixture) => {
      const resolved = resolveCard(fixture.view.type, 1, "personal-desktop", fixture.view);
      if (!resolved.ok) return null;
      const Renderer = resolved.definition.render;
      return <Renderer key={fixture.id} cardId={fixture.id} title={fixture.title} view={resolved.view} />;
    })}</>);
    expect(interactiveMarkup).toContain("<button");
    expect(interactiveMarkup).toContain("<form");
    expect(interactiveMarkup).toContain("<input");
    expect(interactiveMarkup).not.toContain("tabindex=\"-1\"");
  });
});
