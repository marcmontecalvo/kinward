import { describe, expect, it } from "vitest";

import { getCard } from "./registry";

describe("card registry", () => {
  it("contains the initial cross-surface cards", () => {
    expect(getCard("now").supportedSurfaces).toContain("personal-mobile");
    expect(getCard("list").supportedSurfaces).toContain("shared-display");
    expect(getCard("topics").supportedSurfaces).not.toContain("shared-display");
  });

  it("rejects unknown card types", () => {
    expect(() => getCard("missing")).toThrow("Unknown card type");
  });
});
