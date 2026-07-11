---
title: "Kinward Single-Household Pivot and Rebuild Plan"
type: "BMAD-aligned implementation strategy"
status: "final"
created: "2026-07-11"
---

# Kinward Single-Household Pivot and Rebuild Plan

## Executive Decision

Create a new clean repository for the single-household Kinward product.

Keep the legacy Homefront repository as a source archive. Move only explicitly approved backend capabilities, tests, contracts, and infrastructure. Rebuild the frontend from the new product brief and UX specification. Do not migrate the old frontend screen by screen.

Build web/PWA first. Native Android remains late backlog work for capabilities that genuinely require it.

## Why a New Repository Is Cleaner

- Legacy SaaS files do not pollute search or AI-agent context.
- The new product vocabulary is authoritative from the first commit.
- Database migrations restart cleanly.
- CI and Compose reflect one household only.
- Obsolete control-plane and routine assumptions cannot survive accidentally.
- The old repository remains available for reference and salvage.

## Repository Strategy

Freeze and tag the legacy Homefront repository, then rename it later to `Homefront-legacy` or `Homefront-saas-archive`.

The new repository uses `Kinward` as the active project.

Nothing moves automatically. Every candidate must be classified as move unchanged, move after refactor, rewrite, or retire.

## Likely Salvage

- Household people and roles.
- Per-user and per-assistant memory.
- Multiple assistants per user.
- Assistant personality/configuration.
- Calendar and email integrations.
- Home Assistant integration.
- Voice STT/TTS seams.
- Permissions, approvals, and activity concepts that still fit one household.
- Health checks and local observability.
- Optional Honcho and LLM-Wiki adapters.
- Generic API, test, Docker, React, Vite, TypeScript, Vitest, and Playwright infrastructure.

## Do Not Move

- Control-plane service.
- Multi-tenant identity.
- SaaS registration and provisioning.
- Billing and commercial entitlements.
- Support-operator access.
- Managed deployment logic.
- Cloud-region metadata.
- Zitadel/OIDC stubs without a current requirement.
- Marketplace and package-tier architecture.
- Kubernetes/EKS/Helm production plans.
- Old morning-routine UI and onboarding.
- Legacy epics, stories, tests, and documents protecting obsolete behavior.
- Old migration history.

## New Repository Shape

```text
Kinward/
  apps/
    web/
    android/             # later
  services/
    kinward/
  packages/
    contracts/
    schemas/
    assistant-core/
    card-sdk/
    layout-sdk/
    integration-sdk/
    test-support/
  infra/
    compose/
    docker/
    observability/
  docs/
    product/
    ux/
    architecture/
    adr/
    integrations/
    operations/
  _bmad/
  _bmad-output/
  scripts/
  compose.yaml
  Makefile
  README.md
```

## Architecture Direction

Start with one household backend unless a real boundary requires another service. It owns household members, assistants, memory routing, permissions, identity context, calendar, email, Home Assistant, approvals, activity, coordination, surface configuration, and health.

Honcho and LLM-Wiki remain optional peers. Kinward must boot without them and report degraded capability clearly.

Create a new single-household schema and a new baseline migration. Do not copy the old migration chain.

Rebuild `apps/web` around design system, surface context, card registry, layout registry and resolver, privacy and visibility rules, assistant presence and input, mock adapters, one cross-surface vertical slice, Kinward Control, layout editing, and live backend integrations.

The initial product is web/PWA. Android comes later for background wake word, foreground services, widgets, share targets, proximity, biometrics, Android Auto, and other OS-level capabilities.

## Pivot Workstreams

### Product and planning reset

Create authoritative current documents: product brief, PRD, UX specification, architecture, ADRs, epics, stories, and README. Do not copy the full legacy BMAD corpus into the active repo.

### Backend salvage audit

Produce a subsystem matrix covering household and users, assistants, memory and knowledge, auth and permissions, policy and approvals, activity ledger, calendar and email, Home Assistant, voice, notifications, background work, database, health, observability, and tests.

### Infrastructure simplification

The default stack should start with `docker compose up`. Remove tenant IDs, control-plane services, support access, managed deployment variables, billing, and SaaS entitlements. Keep optional profiles for memory, knowledge, observability, and development.

### Database reset

Preserve only useful household data through explicit export/import: people, assistants, personality settings, useful memories, integration settings, and Home Assistant mappings.

### Contract reset

Use household language and define current contracts for household, person, assistant, memory, topic, surface, card, layout, approval, activity, coordination request, integration, voice handoff, and emergency state.

### Frontend replacement

Do not keep a permanent legacy frontend directory. Use Git history or the archived repository when reference is needed.

The first vertical slice should render the same capabilities across personal mobile, tablet, desktop, shared kitchen display, and shared living-room display.

### Documentation cleanup

The new repository contains only current documentation. Historical SaaS and routine-centric material remains in the archived repository.

### Testing reset

Rebuild tests around current schemas, privacy, permissions, layout resolution, card registry, cross-surface states, onboarding, assistant creation, shared-display privacy, approvals, layout editing, emergency mode, and integrations.

## Execution Order

### Phase 0 — Freeze

- Stop feature work in the old repo.
- Tag it.
- Create the new repo.
- Add final planning documents.

### Phase 1 — Skeleton

- Create monorepo structure.
- Add backend, web app, shared contracts, Compose, CI, BMAD, and Ringer.

### Phase 2 — Salvage

- Audit old subsystems.
- Copy only approved capabilities.
- Rewrite terminology and contracts.
- Recreate tests.

### Phase 3 — Frontend foundation

- Build design system, cards, layouts, surfaces, privacy, mocks, and one cross-surface slice.

### Phase 4 — Household foundation

- Household setup.
- Accounts and invitations.
- Assistant creation.
- Personality interview.
- Memory.

### Phase 5 — Integrations

- Calendar.
- Email.
- Home Assistant.
- Voice endpoints.
- Optional Honcho and LLM-Wiki.

### Phase 6 — Advanced experience

- Layout editor.
- Declarative editor.
- Coordination requests.
- Emergency mode.
- Maintenance recall.
- Progressive school, work, and personal onboarding.

### Phase 7 — Native evaluation

- Measure actual PWA limitations.
- Build only justified Android modules.
- Sideload first.
- Consider Play Store or iOS later.

## BMAD and Ringer

Use BMAD to produce the authoritative product brief, PRD, UX, architecture, epics, stories, and readiness review.

Use Ringer for salvage audits, parallel cleanup, card batches, tests, contract conversion, and verification-heavy work. Every Ringer task should have an executable or inspectable check.

## Final Recommendation

Treat the legacy Homefront repository as an archive and salvage source, not a codebase that must be cleaned indefinitely.

Kinward should be single-household from its first commit, web/PWA first, modular from the first frontend milestone, and free of SaaS and morning-routine assumptions.
