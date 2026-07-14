import type { ComponentType, ReactNode } from "react";

export type CardRenderProps = {
  title: string;
  data: Record<string, unknown>;
  className?: string;
};

export type CardDefinition = {
  type: string;
  supportedSurfaces: Array<"personal-mobile" | "personal-tablet" | "personal-desktop" | "shared-display">;
  render: ComponentType<CardRenderProps>;
};

function Shell({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`.trim()}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

const registry = new Map<string, CardDefinition>();

export function registerCard(definition: CardDefinition): void {
  if (registry.has(definition.type)) {
    throw new Error(`Card type already registered: ${definition.type}`);
  }
  registry.set(definition.type, definition);
}

export function getCard(type: string): CardDefinition {
  const definition = registry.get(type);
  if (!definition) {
    throw new Error(`Unknown card type: ${type}`);
  }
  return definition;
}

registerCard({
  type: "now",
  supportedSurfaces: ["personal-mobile", "personal-tablet", "personal-desktop", "shared-display"],
  render: ({ title, data, className }) => (
    <Shell title={title} {...(className === undefined ? {} : { className })}>
      <p className="headline">{String(data.headline ?? "Nothing needs attention.")}</p>
      <p className="muted">{String(data.detail ?? "")}</p>
      {data.action ? <button>{String(data.action)}</button> : null}
    </Shell>
  ),
});

registerCard({
  type: "list",
  supportedSurfaces: ["personal-mobile", "personal-tablet", "personal-desktop", "shared-display"],
  render: ({ title, data, className }) => (
    <Shell title={title} {...(className === undefined ? {} : { className })}>
      <ul>{Array.isArray(data.items) ? data.items.map((item) => <li key={String(item)}>{String(item)}</li>) : null}</ul>
    </Shell>
  ),
});

registerCard({
  type: "topics",
  supportedSurfaces: ["personal-mobile", "personal-tablet", "personal-desktop"],
  render: ({ title, data, className }) => (
    <Shell title={title} {...(className === undefined ? {} : { className })}>
      <div className="topic-list">
        {Array.isArray(data.items) ? data.items.map((item) => <button key={String(item)}>{String(item)}</button>) : null}
      </div>
    </Shell>
  ),
});
