import type { ComponentType, ReactNode } from "react";
import type { ZodType } from "zod";
import {
  approvalViewSchema,
  assistantInputViewSchema,
  assistantPresenceViewSchema,
  briefingViewSchema,
  cardSizeSchema,
  continueViewSchema,
  houseStatusViewSchema,
  nowViewSchema,
  scheduleViewSchema,
  type CardCapability,
  type CardSize,
  type CardState,
  type CardType,
  type CardView,
  type SurfaceClass,
} from "@kinward/schemas";

export type CardIntent = {
  cardId: string;
  kind: "navigate" | "decide" | "submit-text";
  value: string;
};

export type CardRenderProps = {
  cardId: string;
  title: string;
  view: CardView;
  onIntent?: (intent: CardIntent) => void;
};

export type CardDefinition = {
  type: CardType;
  version: 1;
  supportedSurfaces: readonly SurfaceClass[];
  schema: ZodType<CardView>;
  sizing: CardSize;
  capabilities: readonly CardCapability[];
  render: ComponentType<CardRenderProps>;
};

const stateLabels: Record<CardState, string> = {
  available: "Available",
  empty: "Nothing to show",
  loading: "Loading",
  degraded: "Limited",
  unavailable: "Unavailable",
  stale: "May be out of date",
  error: "Could not load",
};

function CardShell({ title, view, children, className = "" }: {
  title: string;
  view: CardView;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card registered-card ${className}`.trim()} aria-labelledby={`${view.type}-title`} data-card-type={view.type} data-card-version={view.version} data-state={view.state}>
      <div className="card-heading">
        <h2 id={`${view.type}-title`}>{title}</h2>
        <span className={`state state-${view.state}`} role="status">{stateLabels[view.state]}: {view.statusMessage}</span>
      </div>
      <span className="mock-label">Mock-backed foundation</span>
      {view.state === "available" ? children : <p>{view.statusMessage}</p>}
    </section>
  );
}

function PresenceCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view} className="presence-card">
    {view.type === "assistant-presence" ? <div className="presence-content"><span className="presence-mark" aria-hidden="true">✦</span><div><strong>{view.name}</strong><p>{view.message}</p></div></div> : null}
  </CardShell>;
}

function NowCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view} className="now-card">
    {view.type === "now" ? <><p className="headline">{view.headline}</p>{view.detail ? <p>{view.detail}</p> : null}{view.actionLabel && view.actionIntent ? <button className="secondary-action" onClick={() => props.onIntent?.({ cardId: props.cardId, kind: "navigate", value: view.actionIntent ?? "" })}>{view.actionLabel}</button> : null}</> : null}
  </CardShell>;
}

function BriefingCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view}>{view.type === "briefing" ? <ol className="meaning-list">{view.items.map((item) => <li key={item.id}><strong>{item.label}</strong>{item.detail ? <span>{item.detail}</span> : null}</li>)}</ol> : null}</CardShell>;
}

function ContinueCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view}>{view.type === "continue" ? <div className="topic-list">{view.topics.map((topic) => <button key={topic.id} onClick={() => props.onIntent?.({ cardId: props.cardId, kind: "navigate", value: topic.id })}>{topic.label}</button>)}</div> : null}</CardShell>;
}

function ScheduleCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view}>{view.type === "schedule" ? <ul className="schedule-list">{view.entries.map((entry) => <li key={entry.id}><time>{entry.timeLabel}</time><span>{entry.title}</span></li>)}</ul> : null}</CardShell>;
}

function HouseStatusCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view}>{view.type === "house-status" ? <><p className="headline">{view.summary}</p><ul>{view.facts.map((fact) => <li key={fact}>{fact}</li>)}</ul></> : null}</CardShell>;
}

const approvalStateLabels = {
  "decision-required": "Decision required",
  acting: "Kinward is acting; completion is not confirmed",
  submitted: "Submitted; completion is not confirmed",
  unknown: "Outcome unknown",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
} as const;

function ApprovalCard(props: CardRenderProps) {
  const view = props.view;
  return <CardShell title={props.title} view={view}>{view.type === "approval" ? <div className="approval-content"><p><strong>{approvalStateLabels[view.actionState]}</strong></p><dl><dt>Target</dt><dd>{view.target ?? "Not provided"}</dd><dt>Effect</dt><dd>{view.effect ?? "Not provided"}</dd><dt>Consequence</dt><dd>{view.consequence ?? "Not provided"}</dd><dt>Expires</dt><dd>{view.expires ?? "No expiry provided"}</dd><dt>Reversible</dt><dd>{view.reversible === undefined ? "Unknown" : view.reversible ? "Yes" : "No"}</dd></dl>{view.actionState === "decision-required" ? <div className="decision-actions dominant-decision" role="group" aria-label={view.decisionPrompt ?? "Approval decision"}><button onClick={() => props.onIntent?.({ cardId: props.cardId, kind: "decide", value: "approve" })}>Approve</button><button onClick={() => props.onIntent?.({ cardId: props.cardId, kind: "decide", value: "decline" })}>Decline</button></div> : null}</div> : null}</CardShell>;
}

function AssistantInputCard(props: CardRenderProps) {
  const view = props.view;
  if (view.type !== "assistant-input") return <CardShell title={props.title} view={view} />;
  return <CardShell title={props.title} view={view} className="input-card"><form className="composer" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); props.onIntent?.({ cardId: props.cardId, kind: "submit-text", value: String(form.get("message") ?? "") }); }}><label className="sr-only" htmlFor={`${props.cardId}-input`}>Message Kinward</label><input id={`${props.cardId}-input`} name="message" type="text" disabled={view.disabled} placeholder={view.placeholder} autoComplete="off" /><button type="submit" disabled={view.disabled}>Send</button></form></CardShell>;
}

const allSurfaces: readonly SurfaceClass[] = ["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"];
const size = (minColumns: number, preferredColumns: number, maxColumns: number, minRows: number): CardSize => cardSizeSchema.parse({ minColumns, preferredColumns, maxColumns, minRows });

const definitions: CardDefinition[] = [
  { type: "assistant-presence", version: 1, supportedSurfaces: allSurfaces, schema: assistantPresenceViewSchema as ZodType<CardView>, sizing: size(2, 4, 12, 1), capabilities: ["display"], render: PresenceCard },
  { type: "now", version: 1, supportedSurfaces: allSurfaces, schema: nowViewSchema as ZodType<CardView>, sizing: size(4, 7, 12, 2), capabilities: ["display", "navigate"], render: NowCard },
  { type: "briefing", version: 1, supportedSurfaces: allSurfaces, schema: briefingViewSchema as ZodType<CardView>, sizing: size(3, 5, 12, 2), capabilities: ["display"], render: BriefingCard },
  { type: "continue", version: 1, supportedSurfaces: allSurfaces, schema: continueViewSchema as ZodType<CardView>, sizing: size(3, 5, 12, 2), capabilities: ["display", "navigate"], render: ContinueCard },
  { type: "schedule", version: 1, supportedSurfaces: allSurfaces, schema: scheduleViewSchema as ZodType<CardView>, sizing: size(3, 6, 12, 2), capabilities: ["display"], render: ScheduleCard },
  { type: "house-status", version: 1, supportedSurfaces: allSurfaces, schema: houseStatusViewSchema as ZodType<CardView>, sizing: size(3, 5, 12, 2), capabilities: ["display"], render: HouseStatusCard },
  { type: "approval", version: 1, supportedSurfaces: allSurfaces, schema: approvalViewSchema as ZodType<CardView>, sizing: size(4, 6, 12, 3), capabilities: ["display", "decide"], render: ApprovalCard },
  { type: "assistant-input", version: 1, supportedSurfaces: allSurfaces, schema: assistantInputViewSchema as ZodType<CardView>, sizing: size(4, 12, 12, 1), capabilities: ["text-input"], render: AssistantInputCard },
];

const registry = new Map<string, CardDefinition>();

export function registrationKey(type: CardType, version: number): string {
  return `${type}@${version}`;
}

export function registerCard(definition: CardDefinition): void {
  const key = registrationKey(definition.type, definition.version);
  if (registry.has(key)) throw new Error(`Card registration already exists: ${key}`);
  cardSizeSchema.parse(definition.sizing);
  if (definition.supportedSurfaces.length === 0) throw new Error(`Card registration has no surfaces: ${key}`);
  registry.set(key, Object.freeze(definition));
}

definitions.forEach(registerCard);

export function getCard(type: string, version: number): CardDefinition | undefined {
  return registry.get(`${type}@${version}`);
}

export function listCards(): readonly CardDefinition[] {
  return [...registry.values()];
}

export type ResolvedCard =
  | { ok: true; definition: CardDefinition; view: CardView }
  | { ok: false; reason: "unregistered-card" | "invalid-view-model" | "unsupported-surface" };
export type CardFailureReason = Extract<ResolvedCard, { ok: false }>["reason"];

export function resolveCard(type: string, version: number, surface: SurfaceClass, candidate: unknown): ResolvedCard {
  const definition = getCard(type, version);
  if (!definition) return { ok: false, reason: "unregistered-card" };
  if (!definition.supportedSurfaces.includes(surface)) return { ok: false, reason: "unsupported-surface" };
  const parsed = definition.schema.safeParse(candidate);
  if (!parsed.success || parsed.data.type !== definition.type || parsed.data.version !== definition.version) return { ok: false, reason: "invalid-view-model" };
  return { ok: true, definition, view: parsed.data };
}

export function SafeCardFallback({ title, reason }: { title: string; reason: CardFailureReason }) {
  return <section className="card registered-card" role="status" data-state="unavailable"><h2>{title}</h2><strong>Unavailable</strong><p>{reason === "unsupported-surface" ? "This card is not available on this surface." : "This card could not be shown safely."}</p></section>;
}
