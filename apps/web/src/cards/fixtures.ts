import type { CardView } from "@kinward/schemas";

export type SyntheticCardFixture = { id: string; title: string; view: CardView };

export const syntheticCardFixtures: readonly SyntheticCardFixture[] = [
  { id: "presence-example", title: "Assistant presence", view: { type: "assistant-presence", version: 1, state: "available", statusMessage: "Ready for this fictional preview", source: "synthetic-mock", name: "Kinward Example", message: "Nothing urgent needs attention." } },
  { id: "now-example", title: "Now", view: { type: "now", version: 1, state: "available", statusMessage: "One fictional priority", source: "synthetic-mock", headline: "The example household is quiet.", detail: "A synthetic delivery window begins later.", actionLabel: "Review example", actionIntent: "review-example" } },
  { id: "briefing-example", title: "Briefing", view: { type: "briefing", version: 1, state: "available", statusMessage: "Two fictional changes", source: "synthetic-mock", items: [{ id: "brief-example-1", label: "Example calendar changed", detail: "A fictional event moved by thirty minutes." }, { id: "brief-example-2", label: "No example approvals are overdue" }] } },
  { id: "continue-example", title: "Continue", view: { type: "continue", version: 1, state: "available", statusMessage: "Fictional topics ready", source: "synthetic-mock", topics: [{ id: "topic-example-1", label: "Example garden plan" }, { id: "topic-example-2", label: "Fictional weekend idea" }] } },
  { id: "schedule-example", title: "Schedule", view: { type: "schedule", version: 1, state: "available", statusMessage: "Synthetic schedule", source: "synthetic-mock", entries: [{ id: "schedule-example-1", timeLabel: "Later", title: "Example appointment" }] } },
  { id: "house-example", title: "House status", view: { type: "house-status", version: 1, state: "available", statusMessage: "Synthetic status only", source: "synthetic-mock", summary: "Example house is all normal", facts: ["Example entry is secure", "No fictional alerts"] } },
  { id: "approval-example", title: "Approval", view: { type: "approval", version: 1, state: "available", statusMessage: "Fictional decision waiting", source: "synthetic-mock", target: "Example calendar entry", effect: "Move the fictional entry", consequence: "The example reminder also moves", expires: "End of this preview", reversible: true, actionState: "decision-required", decisionPrompt: "Approve this fictional change?" } },
  { id: "input-example", title: "Assistant input", view: { type: "assistant-input", version: 1, state: "available", statusMessage: "Text input ready", source: "synthetic-mock", placeholder: "Ask Kinward with text…", disabled: false } },
];
