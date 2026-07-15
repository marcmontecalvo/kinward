import { cardViewSchema, surfaceContextSchema, type CardView, type SurfaceClass, type SurfaceContext } from "@kinward/schemas";

export type DataClassification =
  | "private-person"
  | "private-child"
  | "selected-share"
  | "household-shared"
  | "surface-ephemeral"
  | "system-operational";

export type SharedIdentityState =
  | "unknown"
  | "candidate"
  | "group"
  | "verified-selected"
  | "expired"
  | "authorization-loss";

export type FoundationSurface = SurfaceClass;

const ownerId = "00000000-0000-4000-8000-000000000001";

export const foundationContexts: Readonly<Record<FoundationSurface, SurfaceContext>> = {
  "personal-mobile": surfaceContextSchema.parse({ schemaMajor: 1, contextVersion: 1, surfaceId: "surface-example-mobile", surfaceClass: "personal-mobile", ownerId, privacy: "personal", roomId: "room-example-pocket", touch: true, keyboard: false, viewingDistance: "near", authorityDerived: true }),
  "personal-tablet": surfaceContextSchema.parse({ schemaMajor: 1, contextVersion: 1, surfaceId: "surface-example-tablet", surfaceClass: "personal-tablet", ownerId, privacy: "personal", roomId: "room-example-den", touch: true, keyboard: true, viewingDistance: "near", authorityDerived: true }),
  "personal-desktop": surfaceContextSchema.parse({ schemaMajor: 1, contextVersion: 1, surfaceId: "surface-example-desktop", surfaceClass: "personal-desktop", ownerId, privacy: "personal", roomId: "room-example-study", touch: false, keyboard: true, viewingDistance: "desk", authorityDerived: true }),
  "shared-kitchen": surfaceContextSchema.parse({ schemaMajor: 1, contextVersion: 1, surfaceId: "surface-example-kitchen", surfaceClass: "shared-kitchen", privacy: "household-shared", roomId: "room-example-kitchen", touch: true, keyboard: false, viewingDistance: "room", authorityDerived: true }),
  "shared-living-room": surfaceContextSchema.parse({ schemaMajor: 1, contextVersion: 1, surfaceId: "surface-example-living", surfaceClass: "shared-living-room", privacy: "household-shared", roomId: "room-example-living", touch: false, keyboard: false, viewingDistance: "room", authorityDerived: true }),
};

type ClassifiedView = { classification: DataClassification; view: CardView };

const classifiedViews: readonly ClassifiedView[] = [
  { classification: "surface-ephemeral", view: { type: "assistant-presence", version: 1, state: "available", statusMessage: "Synthetic assistant presence", source: "synthetic-mock", name: "Kinward Example", message: "Mock-backed and ready." } },
  { classification: "household-shared", view: { type: "now", version: 1, state: "available", statusMessage: "One household-safe example", source: "synthetic-mock", headline: "The example household is quiet.", detail: "A fictional shared delivery window begins later.", actionLabel: "Continue on a personal device", actionIntent: "synthetic-handoff" } },
  { classification: "selected-share", view: { type: "briefing", version: 1, state: "available", statusMessage: "Explicitly selected example", source: "synthetic-mock", items: [{ id: "selected-share-example", label: "SELECTED_SHARE_EXAMPLE_ITEM", detail: "Shared only after explicit fictional selection." }] } },
  { classification: "private-person", view: { type: "continue", version: 1, state: "available", statusMessage: "Private fictional topic", source: "synthetic-mock", topics: [{ id: "private-person-example", label: "PRIVATE_PERSON_EXAMPLE_TOPIC" }] } },
  { classification: "private-child", view: { type: "schedule", version: 1, state: "available", statusMessage: "Private child example", source: "synthetic-mock", entries: [{ id: "private-child-example", timeLabel: "Later", title: "PRIVATE_CHILD_EXAMPLE_EVENT" }] } },
  { classification: "household-shared", view: { type: "house-status", version: 1, state: "unavailable", statusMessage: "House status is intentionally unavailable in this mock", source: "synthetic-mock", facts: [] } },
  { classification: "household-shared", view: { type: "approval", version: 1, state: "available", statusMessage: "Fictional decision waiting", source: "synthetic-mock", target: "Example shared calendar entry", effect: "Move the fictional entry", consequence: "The example reminder also moves", expires: "End of this preview", reversible: true, actionState: "decision-required", decisionPrompt: "Approve this fictional change?" } },
  { classification: "private-person", view: { type: "assistant-input", version: 1, state: "available", statusMessage: "Text input ready", source: "synthetic-mock", placeholder: "Ask Kinward with text…", disabled: false } },
];

const instanceIds: Record<CardView["type"], string> = {
  "assistant-presence": "presence-example",
  now: "now-example",
  briefing: "briefing-example",
  continue: "continue-example",
  schedule: "schedule-example",
  "house-status": "house-example",
  approval: "approval-example",
  "assistant-input": "input-example",
};

function allowedClasses(context: SurfaceContext, identity: SharedIdentityState): ReadonlySet<DataClassification> {
  if (context.privacy === "personal") {
    return new Set(["private-person", "private-child", "selected-share", "household-shared", "surface-ephemeral", "system-operational"]);
  }
  if (identity === "verified-selected") return new Set(["selected-share", "household-shared", "surface-ephemeral", "system-operational"]);
  return new Set(["household-shared", "surface-ephemeral", "system-operational"]);
}

function greeting(context: SurfaceContext, identity: SharedIdentityState): string {
  if (context.privacy === "personal") return "Good afternoon, Example Adult.";
  if (identity === "candidate") return "Hello.";
  if (identity === "group") return "Hello, everyone.";
  if (identity === "verified-selected") return "Shared preview selected.";
  if (identity === "expired") return "Private preview expired.";
  if (identity === "authorization-loss") return "Private preview ended.";
  return "Good afternoon.";
}

export type PolicyFilteredPayload = {
  contractVersion: 1;
  context: SurfaceContext;
  identityState: SharedIdentityState;
  greeting: string;
  mockLabel: "mock-backed foundation";
  operationalStatus: "synthetic-adapter-active";
  views: ReadonlyMap<string, CardView>;
};

export function buildPolicyFilteredPayload(
  surface: FoundationSurface,
  identityState: SharedIdentityState = "unknown",
): PolicyFilteredPayload {
  const context = foundationContexts[surface];
  const allowed = allowedClasses(context, identityState);
  const views = new Map<string, CardView>();
  for (const item of classifiedViews) {
    if (!allowed.has(item.classification)) continue;
    const validated = cardViewSchema.parse(item.view);
    views.set(instanceIds[validated.type], validated);
  }
  if (context.privacy === "household-shared") {
    const safeFallbacks: readonly CardView[] = [
      { type: "briefing", version: 1, state: "empty", statusMessage: "No household-shared briefing items", source: "synthetic-mock", items: [] },
      { type: "continue", version: 1, state: "unavailable", statusMessage: "Continue is unavailable on this shared surface", source: "synthetic-mock", topics: [] },
      { type: "schedule", version: 1, state: "unavailable", statusMessage: "No household-shared schedule is available", source: "synthetic-mock", entries: [] },
      { type: "assistant-input", version: 1, state: "unavailable", statusMessage: "Text input is unavailable on this shared preview", source: "synthetic-mock", placeholder: "Text input unavailable", disabled: true },
    ];
    for (const fallback of safeFallbacks) {
      const id = instanceIds[fallback.type];
      if (!views.has(id)) views.set(id, cardViewSchema.parse(fallback));
    }
  }
  return {
    contractVersion: 1,
    context,
    identityState,
    greeting: greeting(context, identityState),
    mockLabel: "mock-backed foundation",
    operationalStatus: "synthetic-adapter-active",
    views,
  };
}

export function serializePolicyPayload(payload: PolicyFilteredPayload): string {
  return JSON.stringify({ ...payload, views: Object.fromEntries(payload.views) });
}
