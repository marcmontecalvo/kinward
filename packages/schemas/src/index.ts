import { z } from "zod";

export const surfaceClassSchema = z.enum([
  "personal-mobile",
  "personal-tablet",
  "personal-desktop",
  "shared-display",
  "voice",
]);

export const privacyLevelSchema = z.enum([
  "public",
  "household",
  "personal",
  "sensitive",
]);

export const assistantKindSchema = z.enum([
  "primary",
  "specialist",
  "temporary",
  "shared-fallback",
]);

export const personRoleSchema = z.enum([
  "admin",
  "adult",
  "teen",
  "child",
]);

export const cardSizeSchema = z.object({
  columns: z.number().int().min(1).max(12),
  rows: z.number().int().min(1).max(12),
});

export const visibilityRuleSchema = z.object({
  surfaces: z.array(surfaceClassSchema).optional(),
  people: z.array(z.string().uuid()).optional(),
  rooms: z.array(z.string()).optional(),
  minimumPrivacy: privacyLevelSchema.optional(),
  requiresData: z.array(z.string()).optional(),
});

export const cardInstanceSchema = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  version: z.number().int().positive().default(1),
  title: z.string().optional(),
  config: z.record(z.string(), z.unknown()).default({}),
  visibility: visibilityRuleSchema.optional(),
  layout: z.object({
    mobile: cardSizeSchema.optional(),
    tablet: cardSizeSchema.optional(),
    desktop: cardSizeSchema.optional(),
    shared: cardSizeSchema.optional(),
  }).default({}),
});

export const surfaceLayoutSchema = z.object({
  id: z.string().min(1),
  version: z.number().int().positive(),
  surface: surfaceClassSchema,
  ownerId: z.string().uuid().optional(),
  roomId: z.string().optional(),
  columns: z.number().int().min(1).max(24).default(12),
  cards: z.array(cardInstanceSchema),
});

export const coordinationRequestSchema = z.object({
  id: z.string().uuid(),
  requestingPersonId: z.string().uuid(),
  receivingPersonId: z.string().uuid(),
  summary: z.string().min(1),
  detail: z.string().optional(),
  expiresAt: z.string().datetime().optional(),
  actions: z.array(z.enum(["accept", "decline", "counter", "delegate"])),
});

export type SurfaceClass = z.infer<typeof surfaceClassSchema>;
export type PrivacyLevel = z.infer<typeof privacyLevelSchema>;
export type CardInstance = z.infer<typeof cardInstanceSchema>;
export type SurfaceLayout = z.infer<typeof surfaceLayoutSchema>;
export type CoordinationRequest = z.infer<typeof coordinationRequestSchema>;
