import { z } from "zod";

export const surfaceClassSchema = z.enum([
  "personal-mobile",
  "personal-tablet",
  "personal-desktop",
  "shared-kitchen",
  "shared-living-room",
]);

export const cardStateSchema = z.enum([
  "available",
  "empty",
  "loading",
  "degraded",
  "unavailable",
  "stale",
  "error",
]);

export const cardTypeSchema = z.enum([
  "assistant-presence",
  "now",
  "briefing",
  "continue",
  "schedule",
  "house-status",
  "approval",
  "assistant-input",
]);

export const cardVersionSchema = z.literal(1);
export const cardCapabilitySchema = z.enum(["display", "navigate", "decide", "text-input"]);

const common = {
  version: cardVersionSchema,
  state: cardStateSchema,
  statusMessage: z.string().min(1).max(240),
  source: z.literal("synthetic-mock"),
};

export const assistantPresenceViewSchema = z.object({
  ...common,
  type: z.literal("assistant-presence"),
  name: z.string().min(1).max(80).optional(),
  message: z.string().min(1).max(240).optional(),
});

export const nowViewSchema = z.object({
  ...common,
  type: z.literal("now"),
  headline: z.string().min(1).max(160).optional(),
  detail: z.string().min(1).max(320).optional(),
  actionLabel: z.string().min(1).max(80).optional(),
  actionIntent: z.string().min(1).max(80).optional(),
}).superRefine((value, context) => {
  if (value.state === "available" && !value.headline) {
    context.addIssue({ code: "custom", message: "Available Now cards require one headline" });
  }
  if (Boolean(value.actionLabel) !== Boolean(value.actionIntent)) {
    context.addIssue({ code: "custom", message: "Now action label and intent must be paired" });
  }
});

const conciseItemSchema = z.object({
  id: z.string().min(1).max(80),
  label: z.string().min(1).max(200),
  detail: z.string().min(1).max(320).optional(),
});

export const briefingViewSchema = z.object({
  ...common,
  type: z.literal("briefing"),
  items: z.array(conciseItemSchema).max(5).default([]),
});

export const continueViewSchema = z.object({
  ...common,
  type: z.literal("continue"),
  topics: z.array(conciseItemSchema).max(6).default([]),
});

export const scheduleViewSchema = z.object({
  ...common,
  type: z.literal("schedule"),
  entries: z.array(z.object({
    id: z.string().min(1).max(80),
    timeLabel: z.string().min(1).max(80),
    title: z.string().min(1).max(160),
  })).max(8).default([]),
});

export const houseStatusViewSchema = z.object({
  ...common,
  type: z.literal("house-status"),
  summary: z.string().min(1).max(160).optional(),
  facts: z.array(z.string().min(1).max(160)).max(8).default([]),
});

export const approvalActionStateSchema = z.enum([
  "decision-required",
  "acting",
  "submitted",
  "unknown",
  "completed",
  "failed",
  "cancelled",
]);

export const approvalViewSchema = z.object({
  ...common,
  type: z.literal("approval"),
  target: z.string().min(1).max(160).optional(),
  effect: z.string().min(1).max(240).optional(),
  consequence: z.string().min(1).max(320).optional(),
  expires: z.string().min(1).max(120).optional(),
  reversible: z.boolean().optional(),
  actionState: approvalActionStateSchema,
  decisionPrompt: z.string().min(1).max(160).optional(),
});

export const assistantInputViewSchema = z.object({
  ...common,
  type: z.literal("assistant-input"),
  placeholder: z.string().min(1).max(160),
  disabled: z.boolean().default(false),
});

export const cardViewSchema = z.discriminatedUnion("type", [
  assistantPresenceViewSchema,
  briefingViewSchema,
  continueViewSchema,
  scheduleViewSchema,
  houseStatusViewSchema,
  approvalViewSchema,
  assistantInputViewSchema,
]).or(nowViewSchema);

export const cardSizeSchema = z.object({
  minColumns: z.number().int().min(1).max(12),
  preferredColumns: z.number().int().min(1).max(12),
  maxColumns: z.number().int().min(1).max(12),
  minRows: z.number().int().min(1).max(12),
}).refine((value) => value.minColumns <= value.preferredColumns && value.preferredColumns <= value.maxColumns, {
  message: "Card column sizing must be ordered",
});

export const cardInstanceSchema = z.object({
  id: z.string().min(1).max(80),
  type: cardTypeSchema,
  version: cardVersionSchema,
  title: z.string().min(1).max(120),
  config: z.object({}).strict().default({}),
});

export const surfacePrivacySchema = z.enum(["personal", "household-shared"]);
export const viewingDistanceSchema = z.enum(["near", "desk", "room"]);
export const surfaceContextSchema = z.object({
  schemaMajor: z.literal(1),
  contextVersion: z.number().int().positive(),
  surfaceId: z.string().min(1).max(120),
  surfaceClass: surfaceClassSchema,
  ownerId: z.string().uuid().optional(),
  privacy: surfacePrivacySchema,
  roomId: z.string().min(1).max(120).optional(),
  touch: z.boolean(),
  keyboard: z.boolean(),
  viewingDistance: viewingDistanceSchema,
  authorityDerived: z.literal(true),
}).superRefine((value, context) => {
  const personal = value.surfaceClass.startsWith("personal-");
  if (personal && (!value.ownerId || value.privacy !== "personal")) {
    context.addIssue({ code: "custom", message: "Personal surfaces require a server-derived owner and personal privacy" });
  }
  if (!personal && (value.ownerId || value.privacy !== "household-shared" || !value.roomId)) {
    context.addIssue({ code: "custom", message: "Shared surfaces require household privacy and a server-derived room" });
  }
});

export const layoutGridSchema = z.object({
  columns: z.number().int().min(1).max(24),
  gapPx: z.number().int().min(8).max(64),
});

export const layoutInstanceSchema = cardInstanceSchema.extend({
  column: z.number().int().min(1).max(24),
  row: z.number().int().min(1).max(100),
  columns: z.number().int().min(1).max(24),
  rows: z.number().int().min(1).max(24),
  narrowWhen: z.object({
    requiresTouch: z.boolean().optional(),
    requiresKeyboard: z.boolean().optional(),
  }).strict().optional(),
}).strict();

export const surfaceLayoutSchema = z.object({
  schemaMajor: z.literal(1),
  id: z.string().min(1).max(120),
  version: z.number().int().positive(),
  contextVersion: z.number().int().positive(),
  surfaceClass: surfaceClassSchema,
  grid: layoutGridSchema,
  instances: z.array(layoutInstanceSchema).min(1).max(40),
}).superRefine((value, context) => {
  const ids = new Set<string>();
  for (const instance of value.instances) {
    if (ids.has(instance.id)) context.addIssue({ code: "custom", message: `Duplicate card instance: ${instance.id}` });
    ids.add(instance.id);
    if (instance.column + instance.columns - 1 > value.grid.columns) {
      context.addIssue({ code: "custom", message: `Card instance exceeds grid: ${instance.id}` });
    }
  }
});

export const layoutScopeSchema = z.enum([
  "explicit-surface",
  "person-surface",
  "room-surface",
  "household-surface",
  "product-default",
]);

export const layoutAssignmentSchema = z.object({
  id: z.string().min(1).max(120),
  scope: layoutScopeSchema,
  scopeId: z.string().min(1).max(120).optional(),
  surfaceClass: surfaceClassSchema,
  assignmentVersion: z.number().int().positive(),
  layout: z.unknown(),
});

export type SurfaceClass = z.infer<typeof surfaceClassSchema>;
export type CardState = z.infer<typeof cardStateSchema>;
export type CardType = z.infer<typeof cardTypeSchema>;
export type CardCapability = z.infer<typeof cardCapabilitySchema>;
export type CardSize = z.infer<typeof cardSizeSchema>;
export type CardInstance = z.infer<typeof cardInstanceSchema>;
export type CardView = z.infer<typeof cardViewSchema>;
export type AssistantPresenceView = z.infer<typeof assistantPresenceViewSchema>;
export type NowView = z.infer<typeof nowViewSchema>;
export type BriefingView = z.infer<typeof briefingViewSchema>;
export type ContinueView = z.infer<typeof continueViewSchema>;
export type ScheduleView = z.infer<typeof scheduleViewSchema>;
export type HouseStatusView = z.infer<typeof houseStatusViewSchema>;
export type ApprovalView = z.infer<typeof approvalViewSchema>;
export type AssistantInputView = z.infer<typeof assistantInputViewSchema>;
export type SurfacePrivacy = z.infer<typeof surfacePrivacySchema>;
export type ViewingDistance = z.infer<typeof viewingDistanceSchema>;
export type SurfaceContext = z.infer<typeof surfaceContextSchema>;
export type LayoutGrid = z.infer<typeof layoutGridSchema>;
export type LayoutInstance = z.infer<typeof layoutInstanceSchema>;
export type SurfaceLayout = z.infer<typeof surfaceLayoutSchema>;
export type LayoutScope = z.infer<typeof layoutScopeSchema>;
export type LayoutAssignment = z.infer<typeof layoutAssignmentSchema>;
