import {
  layoutAssignmentSchema,
  surfaceContextSchema,
  surfaceLayoutSchema,
  type CardView,
  type CardSize,
  type LayoutAssignment,
  type LayoutInstance,
  type LayoutScope,
  type SurfaceClass,
  type SurfaceContext,
  type SurfaceLayout,
} from "@kinward/schemas";

export type RegistrySnapshotEntry = {
  type: string;
  version: number;
  supportedSurfaces: readonly SurfaceClass[];
  sizing: CardSize;
};

export class LayoutResolutionError extends Error {
  readonly code: "invalid-surface-context" | "invalid-product-default";

  constructor(code: "invalid-surface-context" | "invalid-product-default") {
    super(code === "invalid-surface-context" ? "Surface context is unavailable." : "Product layout is unavailable.");
    this.code = code;
  }
}

export type LayoutProvenance = LayoutScope | "last-valid";
export type LayoutFallbackReason =
  | "no-assignment"
  | "invalid-layout"
  | "unregistered-card"
  | "incompatible-surface"
  | "upgrade-required";

export type ResolvedLayout = {
  layout: SurfaceLayout;
  context: SurfaceContext;
  provenance: LayoutProvenance;
  assignmentVersion: number | null;
  layoutVersion: number;
  contextVersion: number;
  instances: readonly LayoutInstance[];
  views: ReadonlyMap<string, CardView>;
  fallbackReason?: LayoutFallbackReason;
};

const precedence: readonly LayoutScope[] = [
  "explicit-surface",
  "person-surface",
  "room-surface",
  "household-surface",
  "product-default",
];

function matches(assignment: LayoutAssignment, context: SurfaceContext): boolean {
  if (assignment.surfaceClass !== context.surfaceClass) return false;
  if (assignment.scope === "explicit-surface") return assignment.scopeId === context.surfaceId;
  if (assignment.scope === "person-surface") return Boolean(context.ownerId && assignment.scopeId === context.ownerId);
  if (assignment.scope === "room-surface") return Boolean(context.roomId && assignment.scopeId === context.roomId);
  if (assignment.scope === "household-surface") return assignment.scopeId === undefined;
  return assignment.scope === "product-default";
}

function selectAssignment(candidates: readonly unknown[], context: SurfaceContext): LayoutAssignment | undefined {
  const valid = candidates.flatMap((candidate) => {
    const parsed = layoutAssignmentSchema.safeParse(candidate);
    return parsed.success && matches(parsed.data, context) ? [parsed.data] : [];
  });
  valid.sort((left, right) => {
    const scopeOrder = precedence.indexOf(left.scope) - precedence.indexOf(right.scope);
    if (scopeOrder !== 0) return scopeOrder;
    if (left.assignmentVersion !== right.assignmentVersion) return right.assignmentVersion - left.assignmentVersion;
    return left.id.localeCompare(right.id);
  });
  return valid[0];
}

function compatibilityReason(candidate: unknown): LayoutFallbackReason {
  if (typeof candidate === "object" && candidate !== null && "schemaMajor" in candidate) {
    const major = (candidate as { schemaMajor?: unknown }).schemaMajor;
    if (typeof major === "number" && major !== 1) return "upgrade-required";
  }
  return "invalid-layout";
}

function validateLayout(
  candidate: unknown,
  context: SurfaceContext,
  registry: readonly RegistrySnapshotEntry[],
): { layout?: SurfaceLayout; reason?: LayoutFallbackReason } {
  const parsed = surfaceLayoutSchema.safeParse(candidate);
  if (!parsed.success) return { reason: compatibilityReason(candidate) };
  const layout = parsed.data;
  if (layout.surfaceClass !== context.surfaceClass || layout.contextVersion > context.contextVersion) {
    return { reason: "incompatible-surface" };
  }
  for (const instance of layout.instances) {
    const registration = registry.find((entry) => entry.type === instance.type && entry.version === instance.version);
    if (!registration) return { reason: "unregistered-card" };
    if (!registration.supportedSurfaces.includes(context.surfaceClass)) return { reason: "incompatible-surface" };
    if (
      instance.columns < registration.sizing.minColumns
      || instance.columns > registration.sizing.maxColumns
      || instance.rows < registration.sizing.minRows
    ) return { reason: "invalid-layout" };
  }
  return { layout };
}

function narrowInstances(
  layout: SurfaceLayout,
  context: SurfaceContext,
  authorizedViews: ReadonlyMap<string, CardView>,
): { instances: readonly LayoutInstance[]; views: ReadonlyMap<string, CardView> } {
  const instances = layout.instances.filter((instance) => {
    if (!authorizedViews.has(instance.id)) return false;
    if (instance.narrowWhen?.requiresTouch === true && !context.touch) return false;
    if (instance.narrowWhen?.requiresKeyboard === true && !context.keyboard) return false;
    return true;
  });
  const allowed = new Map<string, CardView>();
  for (const instance of instances) {
    const view = authorizedViews.get(instance.id);
    if (view) allowed.set(instance.id, view);
  }
  return { instances, views: allowed };
}

export function resolveLayout(input: {
  context: unknown;
  assignments: readonly unknown[];
  registry: readonly RegistrySnapshotEntry[];
  authorizedViews: ReadonlyMap<string, CardView>;
  productDefault: unknown;
  lastValid?: unknown;
}): ResolvedLayout {
  const parsedContext = surfaceContextSchema.safeParse(input.context);
  if (!parsedContext.success) throw new LayoutResolutionError("invalid-surface-context");
  const context = parsedContext.data;
  const assignment = selectAssignment(input.assignments, context);
  const selected = assignment ? validateLayout(assignment.layout, context, input.registry) : { reason: "no-assignment" as const };
  let layout = selected.layout;
  let provenance: LayoutProvenance = assignment?.scope ?? "product-default";
  let fallbackReason = selected.reason;

  if (!layout && input.lastValid !== undefined) {
    const last = validateLayout(input.lastValid, context, input.registry);
    if (last.layout) {
      layout = last.layout;
      provenance = "last-valid";
    }
  }
  if (!layout) {
    const fallback = validateLayout(input.productDefault, context, input.registry);
    if (!fallback.layout) throw new LayoutResolutionError("invalid-product-default");
    layout = fallback.layout;
    provenance = "product-default";
  }
  const narrowed = narrowInstances(layout, context, input.authorizedViews);
  return {
    layout,
    context,
    provenance,
    assignmentVersion: provenance === assignment?.scope ? assignment.assignmentVersion : null,
    layoutVersion: layout.version,
    contextVersion: context.contextVersion,
    instances: narrowed.instances,
    views: narrowed.views,
    ...(fallbackReason === undefined ? {} : { fallbackReason }),
  };
}
