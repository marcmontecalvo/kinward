import { describe, expect, it } from "vitest";
import type { CardView, LayoutScope, SurfaceContext, SurfaceLayout } from "@kinward/schemas";

import { syntheticCardFixtures } from "../cards/fixtures";
import { listCards } from "../cards/registry";
import { productLayouts } from "./defaults";
import { resolveLayout } from "./resolver";

const context: SurfaceContext = {
  schemaMajor: 1,
  contextVersion: 3,
  surfaceId: "surface-example-desktop",
  surfaceClass: "personal-desktop",
  ownerId: "00000000-0000-4000-8000-000000000001",
  privacy: "personal",
  roomId: "room-example-study",
  touch: false,
  keyboard: true,
  viewingDistance: "desk",
  authorityDerived: true,
};
const registry = listCards().map(({ type, version, supportedSurfaces, sizing }) => ({ type, version, supportedSurfaces, sizing }));
const authorizedViews = new Map<string, CardView>(syntheticCardFixtures.map((fixture) => [fixture.id, fixture.view]));
const base = productLayouts["personal-desktop"];

const scopeIds: Record<LayoutScope, string | undefined> = {
  "explicit-surface": context.surfaceId,
  "person-surface": context.ownerId,
  "room-surface": context.roomId,
  "household-surface": undefined,
  "product-default": undefined,
};

function assignment(scope: LayoutScope, version = 1, id = `assignment-${scope}`, layout: unknown = { ...base, id: `layout-${scope}` }) {
  return { id, scope, ...(scopeIds[scope] === undefined ? {} : { scopeId: scopeIds[scope] }), surfaceClass: context.surfaceClass, assignmentVersion: version, layout };
}

function resolve(assignments: readonly unknown[], options: { lastValid?: unknown; authorized?: ReadonlyMap<string, CardView> } = {}) {
  return resolveLayout({ context, assignments, registry, authorizedViews: options.authorized ?? authorizedViews, productDefault: base, ...(options.lastValid === undefined ? {} : { lastValid: options.lastValid }) });
}

describe("deterministic layout resolution", () => {
  it("uses the exact five-level precedence independent of input order", () => {
    const assignments = [assignment("explicit-surface"), assignment("person-surface"), assignment("room-surface"), assignment("household-surface"), assignment("product-default")];
    expect(resolve(assignments).provenance).toBe("explicit-surface");
    expect(resolve(assignments.slice(1)).provenance).toBe("person-surface");
    expect(resolve(assignments.slice(2)).provenance).toBe("room-surface");
    expect(resolve(assignments.slice(3)).provenance).toBe("household-surface");
    expect(resolve(assignments.slice(4)).provenance).toBe("product-default");
    expect(resolve([]).provenance).toBe("product-default");
  });

  it("breaks same-scope conflicts by newest assignment version then lexical id", () => {
    const older = assignment("explicit-surface", 1, "assignment-z", { ...base, id: "older" });
    const newerB = assignment("explicit-surface", 2, "assignment-b", { ...base, id: "newer-b" });
    const newerA = assignment("explicit-surface", 2, "assignment-a", { ...base, id: "newer-a" });
    const result = resolve([older, newerB, newerA]);
    expect(result.layout.id).toBe("newer-a");
    expect(result.assignmentVersion).toBe(2);
    expect(result.layoutVersion).toBe(1);
    expect(result.contextVersion).toBe(3);
  });

  it("retains the last valid layout or immutable default after invalid activation", () => {
    const invalid = assignment("explicit-surface", 2, "bad", { ...base, schemaMajor: 2 });
    const lastValid: SurfaceLayout = { ...base, id: "last-valid-layout" };
    const retained = resolve([invalid], { lastValid });
    expect(retained.provenance).toBe("last-valid");
    expect(retained.layout.id).toBe("last-valid-layout");
    expect(retained.fallbackReason).toBe("upgrade-required");
    const fallback = resolve([invalid]);
    expect(fallback.provenance).toBe("product-default");
    expect(fallback.layout.id).toBe(base.id);
  });

  it("fails closed for unknown cards, incompatible surfaces, executable fields, and future context", () => {
    const unknownCard = { ...base, instances: [{ ...base.instances[0], type: "unknown-card" }] };
    expect(resolve([assignment("explicit-surface", 1, "unknown", unknownCard)]).fallbackReason).toBe("invalid-layout");
    const executable = { ...base, instances: [{ ...base.instances[0], renderer: "alert(1)" }] };
    expect(resolve([assignment("explicit-surface", 1, "code", executable)]).fallbackReason).toBe("invalid-layout");
    const wrongSurface = { ...base, surfaceClass: "personal-mobile" };
    expect(resolve([assignment("explicit-surface", 1, "surface", wrongSurface)]).fallbackReason).toBe("incompatible-surface");
    const futureContext = { ...base, contextVersion: 99 };
    expect(resolve([assignment("explicit-surface", 1, "future", futureContext)]).fallbackReason).toBe("incompatible-surface");
    const undersized = { ...base, instances: base.instances.map((instance, index) => index === 0 ? { ...instance, columns: 1 } : instance) };
    expect(resolve([assignment("explicit-surface", 1, "size", undersized)]).fallbackReason).toBe("invalid-layout");
  });

  it("tolerates additive top-level fields but rejects unknown required semantics", () => {
    const additive = { ...base, additiveFutureHint: "ignored safely" };
    expect(resolve([assignment("explicit-surface", 1, "additive", additive)]).layout.id).toBe(base.id);
    const unknownEnum = { ...base, surfaceClass: "personal-hologram" };
    expect(resolve([assignment("explicit-surface", 1, "enum", unknownEnum)]).fallbackReason).toBe("invalid-layout");
  });

  it("only narrows pre-authorized view models and never manufactures forbidden data", () => {
    const oneAuthorized = new Map([["now-example", authorizedViews.get("now-example")!]]);
    const result = resolve([], { authorized: oneAuthorized });
    expect(result.instances.map((instance) => instance.id)).toEqual(["now-example"]);
    expect([...result.views.keys()]).toEqual(["now-example"]);
    expect(result.views.size).toBe(1);
  });

  it("applies touch and keyboard conditions only as narrowing", () => {
    const conditional = { ...base, instances: base.instances.map((instance, index) => index === 0 ? { ...instance, narrowWhen: { requiresTouch: true } } : instance) };
    const result = resolve([assignment("explicit-surface", 1, "narrow", conditional)]);
    expect(result.instances.some((instance) => instance.id === base.instances[0]?.id)).toBe(false);
  });

  it("rejects missing or client-derived context with a fixed safe error", () => {
    expect(() => resolveLayout({ context: {}, assignments: [], registry, authorizedViews, productDefault: base })).toThrow("Surface context is unavailable");
    expect(() => resolveLayout({ context: { ...context, authorityDerived: false }, assignments: [], registry, authorizedViews, productDefault: base })).toThrow("Surface context is unavailable");
  });
});
