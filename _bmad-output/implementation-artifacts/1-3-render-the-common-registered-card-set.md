---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
---

# Story 1.3: Render the Common Registered Card Set

Status: review

## Story

As a household member,
I want Kinward's common assistant capabilities to render through consistent registered cards,
so that every supported surface can present familiar information without arbitrary generated UI or provider-specific behavior.

## Acceptance Criteria

1. One registry contains versioned Assistant Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Assistant Input registrations. Each declares type/version, supported surfaces, Zod view-model schema, renderer, sizing, and capabilities.
2. Renderers consume only validated, policy-filtered view models; they never query providers/persistence/protected APIs or decide authorization/classification.
3. Every card truthfully renders synthetic available, empty, loading, degraded, unavailable, stale, and error states in direct household language with non-color status.
4. Assistant Input exposes text only and does not advertise microphone, camera, screenshot, file, current-screen, selection, app, ambient-device, or context-targeted input.
5. Approval represents target, effect, consequence, expiry, reversibility, required decision and distinct `acting`, `submitted`, `unknown`, `completed`, `failed`, and `cancelled` states without implementing action execution.
6. All renderers provide semantics, focus, reduced motion, contrast, keyboard operation, and no lost function at 200% text scale.
7. Unknown/unregistered type or incompatible/invalid view model fails closed; no arbitrary JavaScript, React, HTML, generated code, or provider-native payload renders.
8. `packages/schemas` owns shared card/config schemas; backend Pydantic/OpenAPI remains API authority and generated `packages/contracts` types are not hand-duplicated domain models.
9. Fixtures/evidence are synthetic and contain no secrets, internal endpoints, deployment identifiers, or real household data.

Addresses `FR-035`, `FR-040`, `NFR-023`, `NFR-026`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR1`, `UX-DR3`, `UX-DR14`, `UX-DR15`, `UX-DR20`, `UX-DR21`, `UX-DR25-UX-DR27`, `AD-21`, and `AD-22`.

## Tasks / Subtasks

- [x] Define shared versioned card contracts (AC: 1-4, 7-8)
  - [x] Replace generic `Record<string, unknown>` data with discriminated, Zod-validated view models and a canonical capability/state vocabulary.
  - [x] Define registration validation, duplicate type+version behavior, supported-surface declarations, sizing constraints, and safe unknown/incompatible fallback behavior.
  - [x] Keep API-derived view models in generated contracts; put only intentionally shared client card/config schemas in `packages/schemas`.
- [x] Implement the eight registered cards (AC: 1-6)
  - [x] Build dedicated renderers and state presentations for Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and text-only Assistant Input.
  - [x] Use shared accessible primitives/tokens; assistant presence must avoid a default humanoid avatar and motion must be functional and suppressible.
  - [x] Ensure Now has at most one dominant item/action and Briefing defaults to concise prioritized meaning rather than a notification feed.
- [x] Replace hard-coded app composition with registry consumption (AC: 1-3, 7)
  - [x] Remove the current generic `now`/`list`/`topics` shortcut and static private-looking examples; render validated synthetic fixtures through registrations.
  - [x] Keep policy/provider/API work outside cards. Card callbacks emit typed UI intent only; they do not mutate household state.
- [x] Add exhaustive component/contract/accessibility tests (AC: 1-9)
  - [x] Test each card x each required state, invalid data, unknown type/version, surface support, keyboard/focus/semantics, reduced motion, non-color status, 200% scaling, and fictional-data safety.
  - [x] Run `make lint`, `make typecheck`, `make test`, and `make build`.

## Dev Notes

### Current State and Required Changes

- `apps/web/src/cards/registry.tsx` currently registers only generic `now`, `list`, and `topics`; definitions lack version, schema, sizing, and capabilities, and render arbitrary `Record<string, unknown>` coercions. Replace this contract; do not preserve it as a parallel registry.
- `apps/web/src/App.tsx` hard-codes four cards and renders Assistant Input outside the registry. Move all eight capabilities behind the registry while leaving layout selection for Story 1.4.
- `packages/schemas/src/index.ts` has partial card/layout schemas with broad config/visibility concepts and legacy assistant kinds. Narrow this story to explicit card/view/config contracts; do not expose specialists, layout editing, or authority-bearing client rules.
- `packages/contracts/src/index.ts` is handwritten and stale. Do not expand it as a second backend authority; introduce generated-contract direction only where this story needs API-shaped types.
- Preserve Story 1.1's TypeScript strictness (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`) and current dependency policy. Add no UI framework unless clearly necessary and locked.

### Architecture and Scope Guardrails

- Server produces policy-filtered view models. Synthetic mock adapters stand in for that boundary in Milestone A; label mocks and never present them as live.
- Visibility and layout precedence belong to Story 1.4. Five-context orchestration/evidence belongs to Story 1.5. This story supplies reusable contracts/renderers and focused fixtures.
- Text input only. Voice/multimodal/context targeting, richer cards, arbitrary generated views, layout editing, and live providers are non-committed.
- Approval is representational only here. Never equate acting/submitted with completed.
- Do not create a Home Assistant dashboard clone or expose provider names/entities in everyday cards.

### Testing and Evidence Ownership

- FE: registry/contracts/renderers/component tests and visual states.
- QA: accessibility modes, schema-negative cases, public-fixture inspection.
- BE: review that API/domain authority is not duplicated and mock view models are policy-shaped.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.3: Render the Common Registered Card Set`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Card Registry`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Initial Cross-Surface Vertical Slice`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-21 - Authoritative API and shared-schema ownership`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-22 - Registry-driven policy-filtered frontend`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Frontend design`]
- [Source: `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md#Dependency and Language Requirements`]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `make lint && make typecheck && make test && make build` (2026-07-14): all repository gates passed; 39 backend tests and 9 web tests passed.
- Registry matrix renders eight cards across seven canonical states and rejects invalid data for every registration.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Replaced permissive generic card data with versioned Zod contracts, canonical states/capabilities, validated sizing, surface support, and safe resolution failures.
- Registered dedicated Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and text-only Assistant Input renderers.
- Replaced private-looking hard-coded composition with validated, explicitly mock-backed fictional fixtures and typed UI intents.
- Added non-color state semantics, native keyboard controls, focus/target/reflow rules, reduced-motion and forced-color support, and exhaustive registry tests.
- Removed stale handwritten API response mirrors; backend OpenAPI remains the declared API contract authority.

### File List

- `apps/web/package.json`
- `apps/web/src/App.tsx`
- `apps/web/src/cards/fixtures.ts`
- `apps/web/src/cards/registry.test.tsx`
- `apps/web/src/cards/registry.tsx`
- `apps/web/src/styles.css`
- `apps/web/vite.config.ts`
- `packages/contracts/src/index.ts`
- `packages/schemas/src/index.ts`
- `pnpm-lock.yaml`

## Change Log

- 2026-07-14: Implemented and verified the common versioned card registry; status moved to review.
