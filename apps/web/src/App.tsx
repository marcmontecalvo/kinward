import { useState } from "react";
import type { SurfaceClass } from "@kinward/schemas";

import { listCards, resolveCard, SafeCardFallback, type CardIntent } from "./cards/registry";
import { buildPolicyFilteredPayload, type SharedIdentityState } from "./foundation/policy";
import { productLayouts } from "./layouts/defaults";
import { resolveLayout } from "./layouts/resolver";

const surfaces: readonly SurfaceClass[] = ["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"];
const identityStates: readonly SharedIdentityState[] = ["unknown", "candidate", "group", "verified-selected", "expired", "authorization-loss"];

function initialSurface(): SurfaceClass {
  if (typeof window === "undefined") return "personal-desktop";
  const candidate = new URLSearchParams(window.location.search).get("surface");
  return surfaces.find((surface) => surface === candidate) ?? "personal-desktop";
}

function initialIdentity(): SharedIdentityState {
  if (typeof window === "undefined") return "unknown";
  const candidate = new URLSearchParams(window.location.search).get("identity");
  return identityStates.find((state) => state === candidate) ?? "unknown";
}

function simulateInvalidLayout(): boolean {
  return typeof window !== "undefined" && new URLSearchParams(window.location.search).get("invalidLayout") === "1";
}

const registrySnapshot = listCards().map(({ type, version, supportedSurfaces, sizing }) => ({ type, version, supportedSurfaces, sizing }));

export function App() {
  const [surface] = useState(initialSurface);
  const [identityState, setIdentityState] = useState(initialIdentity);
  const payload = buildPolicyFilteredPayload(surface, identityState);
  const context = payload.context;
  const handleIntent = (intent: CardIntent) => {
    document.dispatchEvent(new CustomEvent("kinward:card-intent", { detail: intent }));
  };
  const resolvedLayout = resolveLayout({
    context,
    assignments: simulateInvalidLayout() ? [{ id: "synthetic-invalid-assignment", scope: "explicit-surface", scopeId: context.surfaceId, surfaceClass: context.surfaceClass, assignmentVersion: 1, layout: { schemaMajor: 2 } }] : [],
    registry: registrySnapshot,
    authorizedViews: payload.views,
    productDefault: productLayouts[context.surfaceClass],
  });
  const shared = context.privacy === "household-shared";

  return (
    <main className={`shell surface-shell surface-${surface}`} data-surface={surface} data-privacy={context.privacy} data-interaction={`${context.touch ? "touch" : "no-touch"}-${context.keyboard ? "keyboard" : "no-keyboard"}`} data-viewing-distance={context.viewingDistance} data-layout-id={resolvedLayout.layout.id} data-layout-version={resolvedLayout.layoutVersion} data-context-version={resolvedLayout.contextVersion} data-layout-provenance={resolvedLayout.provenance} data-fallback-reason={resolvedLayout.fallbackReason ?? "none"}>
      <header className="assistant-header">
        <div>
          <p className="eyebrow">Kinward Assistant · {payload.mockLabel}</p>
          <h1>{payload.greeting}</h1>
          <p className="muted">Synthetic examples only. No provider data is live.</p>
          <p className="surface-description">{surface === "personal-mobile" ? "Focused mobile view" : surface === "personal-tablet" ? "Touch-and-keyboard tablet workspace" : surface === "personal-desktop" ? "Desktop planning workspace" : surface === "shared-kitchen" ? "Kitchen glance view" : "Living-room distance view"}</p>
        </div>
        <span className="presence-mark header-mark" aria-hidden="true">✦</span>
      </header>
      {!shared ? <nav className="primary-nav" aria-label="Primary assistant navigation"><a href="#now-example">Now</a><a href="#briefing-example">Briefing</a><a href="#continue-example">Continue</a></nav> : null}
      {shared ? <nav className="identity-controls" aria-label="Synthetic shared identity state"><span>Shared preview: {identityState}</span><button onClick={() => setIdentityState("candidate")}>Simulate candidate</button><button onClick={() => setIdentityState("verified-selected")}>Show selected share</button><button onClick={() => setIdentityState("authorization-loss")}>End private preview</button></nav> : null}
      <section className="grid resolved-grid" aria-label="Synthetic assistant overview" style={{ gridTemplateColumns: `repeat(${resolvedLayout.layout.grid.columns}, minmax(0, 1fr))`, gap: resolvedLayout.layout.grid.gapPx }}>
        {resolvedLayout.instances.map((instance) => {
          const view = resolvedLayout.views.get(instance.id);
          const resolved = resolveCard(instance.type, instance.version, context.surfaceClass, view);
          return <div id={instance.id} className="layout-instance" key={instance.id} data-instance-id={instance.id} style={{ gridColumn: `${instance.column} / span ${instance.columns}`, gridRow: `${instance.row} / span ${instance.rows}` }}>{resolved.ok ? (() => { const Renderer = resolved.definition.render; return <Renderer cardId={instance.id} title={instance.title} view={resolved.view} onIntent={handleIntent} />; })() : <SafeCardFallback title={instance.title} reason={resolved.reason} />}</div>;
        })}
      </section>
      {shared ? <p className="privacy-cue" role="status">{identityState === "authorization-loss" || identityState === "expired" ? "Private preview ended · household-safe view restored." : identityState === "verified-selected" ? "Selected shared preview · end it to clear selected details." : "Shared surface · household-safe information only."}</p> : <p className="privacy-cue" role="status">Private session · visible only in this synthetic personal context.</p>}
    </main>
  );
}
