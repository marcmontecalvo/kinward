---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
---

# Story 1.4: Resolve Validated Layouts Safely

Status: review

## Story

As a household member,
I want Kinward to choose a valid layout for my current surface and context,
so that information appears appropriately without invalid configuration breaking the experience or broadening access.

## Acceptance Criteria

1. Versioned shared schemas validate layout identity/version, surface class, grid, instances, sizing, configuration, and every registered card type/version; executable client code is rejected.
2. Resolution is deterministic in this exact order: explicit surface, person+surface, room+surface, household surface profile, immutable product default. The result records layout and context versions.
3. Server-derived surface context includes class, owner, privacy, optional room, touch/keyboard capability, and viewing distance; client-supplied identifiers never create authority.
4. Visibility only narrows already-authorized view-model availability using safe surface capabilities. Layout, room, presence, or configuration cannot broaden authorization or request forbidden fields.
5. Invalid/unknown/incompatible/unregistered activation never replaces active state; last valid remains, or immutable product default renders if none exists. Sanitized errors contain no private/provider data.
6. Persisted assignment/config mutations use application commands/UoW and store scope, ownership, version, expected prior version, and idempotency where replay matters, with backup/restore/retention/import disposition. No editor is added.
7. Additive optional fields are tolerated by supported older clients; unknown major/required enum/card semantic/incompatible schema fails closed with upgrade-required behavior.
8. Fictional product defaults prioritize Presence, Now, Briefing, Continue and persistent text input on personal contexts; shared defaults remain ambient/household-safe and everyday navigation contains no routine builder, HA dashboard, or technical configuration.

Addresses `FR-035`, `FR-036`, `FR-040`, `FR-041`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR2`, `UX-DR4`, `UX-DR5`, `UX-DR8`, `UX-DR15-UX-DR17`, `UX-DR29`, `AD-19`, `AD-21`, and `AD-22`.

## Tasks / Subtasks

- [x] Finalize versioned layout and surface-context schemas (AC: 1, 3, 7)
  - [x] Define stable major-version handling, grid/gap/instance/sizing constraints, card type+version references, and server-derived ownership/privacy/room/interaction/distance context.
  - [x] Remove authority-like client visibility fields (`people`, `minimumPrivacy`) or constrain them to non-authoritative narrowing inputs; never infer access from IDs.
- [x] Implement pure deterministic resolution (AC: 2-5, 7)
  - [x] Add a testable resolver accepting validated assignments/context/registry snapshot and returning selected layout, provenance, versions, and sanitized fallback reason.
  - [x] Implement the exact five-level precedence, deterministic tie/conflict handling, last-valid retention, immutable defaults, and fail-closed compatibility behavior.
  - [x] Filter instances only after authorized view-model availability is known; never query extra data because a card is present.
- [x] Add product defaults and app integration (AC: 5, 8)
  - [x] Define distinct personal mobile/tablet/desktop and shared kitchen/living-room defaults using Story 1.3 registrations and fictional mock view models.
  - [x] Replace `App.tsx`'s hard-coded tree with resolved layout instances without building the Story 1.5 test matrix or a layout editor.
- [x] Implement persisted assignment activation behind backend seams (AC: 5-6)
  - [x] Define Pydantic/OpenAPI command/query contracts and application/UoW behavior; routes do not write `SurfaceLayoutRecord` directly.
  - [x] Preserve last-valid state atomically under invalid, stale-version, replay, and concurrent activation; record classified activity/outbox intent as required.
  - [x] Define layout backup inclusion, same-household restore validation/quarantine behavior, retention/deletion, and controlled-import eligibility.
- [x] Verify resolver and compatibility contracts (AC: 1-8)
  - [x] Unit-test every precedence level/tie, missing context, invalid schema/card/config, last-valid/default fallback, additive optional fields, unknown major/required semantics, and forbidden-field non-request.
  - [x] Test SQLite concurrency/idempotency and sanitized errors; run `make lint`, `make typecheck`, `make test`, and `make build`.

## Dev Notes

### Current State and Required Changes

- `packages/schemas/src/index.ts` has one partial `surfaceLayoutSchema`; it lacks schema major, context version, grid gap, assignment provenance, immutable-default/last-valid semantics, and registry-aware validation. Its `visibility.people` and `minimumPrivacy` can be mistaken for client authority: redesign them as narrowing-only or remove them.
- `SurfaceLayoutRecord` stores one JSON configuration and `active` flag with a scope uniqueness rule, but has no expected-version/idempotency/last-valid activation model. Evolve it through the application command path and keep migration/model parity.
- `App.tsx` currently contains a hard-coded card tree and CSS breakpoint layout. Preserve reusable styling, but resolved declarative layouts must own composition.
- Story 1.3 is the prerequisite card registry contract. Do not duplicate card metadata or accept an unregistered type in layout code.

### Architecture and Scope Guardrails

- Resolver is pure application/client-domain logic; persistence and HTTP are adapters. Backend mutations follow AD-19.
- The client never authorizes. A layout can hide an available authorized model, never request or reveal a forbidden field.
- Product defaults are immutable code assets and always available. “Last valid” means last successfully validated/activated version, not last submitted JSON.
- No visual/declarative editor, generated views, live shared identity, presence inference, or Kinward Control surface manager in this story.
- Tablet is mock-foundation only; do not imply live tablet support.

### Testing and Evidence Ownership

- FE: schemas, resolver, defaults, client compatibility and integration.
- BE: assignment commands/UoW, persistence concurrency, sanitized results.
- QA: precedence matrix, invalid activation, fallback, authorization-narrowing inspection.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.4: Resolve Validated Layouts Safely`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Layout Registry`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#13.5 Surfaces, cards, and layouts`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-19 - Application commands are the only mutation path`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-22 - Registry-driven policy-filtered frontend`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Frontend design`]
- [Source: `_bmad-output/implementation-artifacts/1-3-render-the-common-registered-card-set.md#Dev Notes`]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `make lint && make typecheck && make test && make build` (2026-07-14): all gates passed; 44 backend tests and 17 web tests passed.
- Resolver matrix covers every precedence level, deterministic ties, compatibility failure, last-valid/default fallback, and authorization narrowing.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added versioned server-derived surface context and declarative layout schemas with strict card instances, safe additive compatibility, sizing/grid constraints, and no authority-bearing visibility rules.
- Implemented the pure five-level resolver with deterministic conflict handling, registry compatibility, last-valid retention, immutable fallback, fixed sanitized reasons, and post-authorization narrowing.
- Added distinct immutable product defaults for personal mobile/tablet/desktop and shared kitchen/living-room, and moved app composition to resolved instances.
- Added versioned backend activation/query contracts through an application unit of work with optimistic concurrency, idempotency, classified activity/outbox evidence, and client-identifier authority denial.
- Defined and tested backup, same-household restore/quarantine, retention/deletion, and controlled-import policy.

### File List

- `apps/web/src/App.tsx`
- `apps/web/src/layouts/defaults.ts`
- `apps/web/src/layouts/resolver.test.ts`
- `apps/web/src/layouts/resolver.ts`
- `apps/web/src/styles.css`
- `packages/schemas/src/index.ts`
- `services/kinward/migrations/versions/001_initial_single_household.py`
- `services/kinward/src/kinward/api/layouts.py`
- `services/kinward/src/kinward/app.py`
- `services/kinward/src/kinward/application/layouts.py`
- `services/kinward/src/kinward/domain/layout_lifecycle.py`
- `services/kinward/src/kinward/domain/lifecycle.py`
- `services/kinward/src/kinward/persistence/models.py`
- `services/kinward/tests/test_layout_lifecycle.py`
- `services/kinward/tests/test_layouts_api.py`
- `services/kinward/tests/test_lifecycle.py`
- `services/kinward/tests/test_migrations.py`

## Change Log

- 2026-07-14: Implemented and verified safe versioned layout resolution and activation; status moved to review.
