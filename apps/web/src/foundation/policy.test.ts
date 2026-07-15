import { describe, expect, it } from "vitest";

import { buildPolicyFilteredPayload, foundationContexts, serializePolicyPayload, type SharedIdentityState } from "./policy";

const privateMarkers = ["PRIVATE_PERSON_EXAMPLE_TOPIC", "PRIVATE_CHILD_EXAMPLE_EVENT"];

describe("synthetic policy harness", () => {
  it("defines five complete, server-derived surface contexts", () => {
    expect(Object.keys(foundationContexts)).toEqual(["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"]);
    for (const context of Object.values(foundationContexts)) {
      expect(context.authorityDerived).toBe(true);
      expect(context.contextVersion).toBe(1);
      expect(context.viewingDistance).toMatch(/near|desk|room/);
    }
  });

  it("allows private classes only on personal surfaces before serialization", () => {
    for (const surface of ["personal-mobile", "personal-tablet", "personal-desktop"] as const) {
      const serialized = serializePolicyPayload(buildPolicyFilteredPayload(surface));
      for (const marker of privateMarkers) expect(serialized).toContain(marker);
    }
    for (const surface of ["shared-kitchen", "shared-living-room"] as const) {
      const serialized = serializePolicyPayload(buildPolicyFilteredPayload(surface));
      for (const marker of privateMarkers) expect(serialized).not.toContain(marker);
    }
  });

  it("gives every uncertain shared identity state only its exact safe fields", () => {
    const states: readonly SharedIdentityState[] = ["unknown", "candidate", "group", "expired", "authorization-loss"];
    for (const state of states) {
      const serialized = serializePolicyPayload(buildPolicyFilteredPayload("shared-kitchen", state));
      for (const marker of [...privateMarkers, "SELECTED_SHARE_EXAMPLE_ITEM"]) expect(serialized).not.toContain(marker);
      expect(serialized).not.toContain("confidence");
      expect(serialized).not.toContain("ownerId");
    }
    const candidate = buildPolicyFilteredPayload("shared-kitchen", "candidate");
    expect(candidate.greeting).toBe("Hello.");
    expect(serializePolicyPayload(candidate)).not.toMatch(/identity confidence|private exists|possible identity|matched person/i);
  });

  it("reveals only explicitly selected data and clears it on downgrade", () => {
    const selected = serializePolicyPayload(buildPolicyFilteredPayload("shared-living-room", "verified-selected"));
    expect(selected).toContain("SELECTED_SHARE_EXAMPLE_ITEM");
    for (const marker of privateMarkers) expect(selected).not.toContain(marker);
    const downgraded = serializePolicyPayload(buildPolicyFilteredPayload("shared-living-room", "authorization-loss"));
    expect(downgraded).not.toContain("SELECTED_SHARE_EXAMPLE_ITEM");
    for (const marker of privateMarkers) expect(downgraded).not.toContain(marker);
  });

  it("is entirely fictional and provider-independent", () => {
    const serialized = Object.keys(foundationContexts).map((surface) => serializePolicyPayload(buildPolicyFilteredPayload(surface as keyof typeof foundationContexts))).join("\n");
    expect(serialized).toContain("mock-backed foundation");
    expect(serialized).not.toMatch(/https?:\/\//);
    expect(serialized).not.toContain("@");
    expect(serialized).not.toMatch(/home.?assistant|provider payload|api[_-]?key|token/i);
  });
});
