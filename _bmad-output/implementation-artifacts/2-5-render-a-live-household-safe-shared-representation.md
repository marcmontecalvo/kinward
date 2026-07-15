# Story 2.5: Render a Live Household-Safe Shared Representation

Status: ready-for-dev

<!-- Ultimate context engine analysis completed - comprehensive developer guide created. -->

## Story

As a household member,
I want an explicitly shared topic to appear safely on a live shared display,
so that the household can see useful coordination context without learning private details or that unshared private work exists.

## Acceptance Criteria

1. Persist one fictional `household-shared` topic and one fictional unshared `private-person` topic through the real authorized backend path, with no static-only fixtures or hard-coded person IDs.
2. At least one kitchen or living-room live shared context uses a server-built shared-surface `AccessContext`; policy applies before repository query and serialization; the explicitly shared topic produces a registered-card view model. The other context may remain mock-backed but cannot be described as live.
3. A shared topic containing private preferences, costs, messages, sources, and household-safe coordination fields serializes only allowed household-safe fields; forbidden details are absent from API, SSE, DOM, caches, logs, and fallback context. The client performs no privacy filtering.
4. The unshared topic is absent from shared queries, cards, counts, summaries, activity, empty states, source categories, and assistant context, with no ID, count delta, placeholder, timestamp, correlation, or “private item” existence hint.
5. A separately approved derived coordination statement is eligible only as a separately reviewable record with exact source IDs/versions/classes, transformation version, household-shared class, purpose, and expiry; its private source remains absent.
6. Narrowing, revocation, expiry, deletion, or source-version invalidation immediately revokes further backend authorization and removes the item from shared/fallback context and stale rendered/cache state.
7. Shared explanation reveals only permitted information class and household-safe reason; it exposes no private source, hidden reasoning, prompt, or protected existence, and does not offer full private correction on the shared display.
8. Shared browser storage/service worker/cache/IndexedDB/local storage/error reporting contains no private topic or private-derived source payload; only current household-safe view models may be retained.
9. Automated field and byte assertions cover API, SSE, DOM, browser storage, fallback context, counts, and errors, proving zero forbidden-field disclosure and zero existence disclosure.
10. The Milestone B demonstration exercises authenticated mobile submission, incremental response, persistence, desktop continuation, safe shared representation, and shared-safe explanation while preserving five-context mock tests and fictional evidence.

## Tasks / Subtasks

- [ ] Define the shared projection and lineage contracts (AC: 1-7)
  - [ ] Extend Story 2.3 protected-topic metadata and Story 2.4 view-query seams; do not add a second topic store or client-side sharing model.
  - [ ] Define a minimal Pydantic household-safe card view model. Either direct `household-shared` data or a separately approved derived statement is eligible; `private-person` records never enter the candidate result set.
  - [ ] For derived statements, persist exact source IDs/versions/classes, transformation version, purpose, audience policy/grant, expiry, and independent item version. Never reclassify the private source.
- [ ] Implement shared-surface policy before query and serialization (AC: 2-6)
  - [ ] Derive the registered shared surface and household audience server-side; do not accept person/assistant/topic authority from the browser.
  - [ ] Constrain repository queries to currently authorized household-safe candidates so forbidden topics cannot affect rows, counts, sort order, pagination, empty state, or provider/fallback context.
  - [ ] Reauthorize fields/lineage/current source versions at serialization; fail closed on missing/stale ownership, policy, grant, expiry, or lineage.
- [ ] Connect one live shared surface through registered cards (AC: 2, 3, 6-8)
  - [ ] Select exactly one existing kitchen/living-room context as the Milestone B live surface; preserve the other contexts' mock status visibly and in tests.
  - [ ] Render only backend-produced policy-filtered view models through the completed Story 1.x card/layout registry. Add revocation/update signaling or bounded refetch so stale shared content disappears.
  - [ ] Prevent private payload persistence in browser/application caches. Scope service-worker behavior and error reporting to household-safe payloads and clear invalidated view models.
- [ ] Add household-safe explanation entry point (AC: 7, 10)
  - [ ] Reuse Story 2.6's explanation contract if implemented concurrently; otherwise expose the narrow shared-safe seam that 2.6 can extend without leaking source cardinality or private correction links.
  - [ ] State the allowed class/reason/recency only; full correction routes to an authorized private surface in a later owning story, not a shared-display disclosure.
- [ ] Prove private absence end to end (AC: 1-10)
  - [ ] Use canary strings in forbidden fictional fields and assert byte absence in serialized responses/events, DOM, storage, caches, logs, fallback/model context, and errors.
  - [ ] Compare runs with and without the private topic and assert shared counts/order/empty states/telemetry do not reveal its existence.
  - [ ] Test source change, narrowing, revocation, expiry, deletion, reconnect, offline/cache behavior, and current-source-version recovery.
  - [ ] Preserve the five-context mock foundation and execute the complete Milestone B mobile -> desktop -> shared demonstration.

## Dev Notes

### Implementation Boundaries and Dependencies

- Stories 2.1–2.4 are prerequisites even when authored concurrently. Use their session/CSRF, `AccessContext`, request/SSE, topic persistence/versioning, and continuation contracts. Reconcile with their implemented names before development.
- Story 2.5 owns one live shared-display representation and privacy-absence evidence. It does not implement passive identity, verified private shared sessions, handoff redemption, broad shared assistant memory, layout editing, or the second live shared context.
- A `household-shared` source and a privacy-filtered derived statement are different cases. Direct sharing changes only the explicitly authored item; transformation creates a new separately governed record and never changes source classification.

### Architecture Compliance

- AD-05: protected data is filtered before SQL/provider query and again before serialization. Post-fetch client filtering is forbidden.
- AD-07: every protected/derived item carries ownership, class, versions, audience policy/grant; derived items add exact lineage, transformation, and expiry. Any stale dependency invalidates downstream use/cache/rendering.
- AD-10 safe baseline: shared display is household-only unless a short-lived server grant was explicitly approved on a registered personal destination. Passive sensing cannot grant private access. This story needs no private shared session.
- AD-22: shared cards render only server-produced policy-filtered view models through the common registry/layout system.
- The fallback assistant must not receive personal topic or source context. Shared-safe projection is an application query/view, not new memory in a combined family brain.
- Operational evidence is sanitized by construction; do not collect unrestricted objects and redact afterward.

### Current Repository State and Change Guidance

| Area | Current state | Change | Preserve |
| --- | --- | --- | --- |
| `apps/web/src/App.tsx` | Static personal-looking page with hard-coded household data. | Use the Story 1.5 surface shell and choose one shared context for live backend data. | Distinct surface layouts and ordinary household language. |
| `apps/web/src/cards/registry.tsx` | Registry currently excludes `topics` from shared display. | Add/reuse a specifically household-safe coordination representation; do not make the private topics card shared-capable. | Card registry is rendering only, never policy. |
| `packages/schemas/src/index.ts` | Surface/layout schemas exist; privacy enum does not match canonical architecture classes. | Do not use this enum as domain authorization. Add only client-owned view/layout validation if needed. | Backend Pydantic/OpenAPI is wire authority. |
| `services/kinward/src/kinward/persistence/models.py` | No current topic/lineage records in baseline. | Extend Story 2.3's forward migration/models for explicit sharing and derived lineage only where not already supplied. | SQL authority, UUID/UTC/version constraints. |
| `services/kinward/src/kinward/domain/permissions.py` | Narrow child-setting helper, not a general policy engine. | Do not overload it casually; use the policy/AccessContext module established in 2.1–2.3. | Existing child-setting behavior. |

### Testing Requirements

- Domain/application: class eligibility, deny-overrides, current lineage, revocation/expiry/source-version invalidation, fallback exclusion.
- Persistence/API: pre-query constraints, no count/order/pagination leakage, generated contracts, byte-level canary absence, stable safe errors.
- Web: one live shared surface; forbidden canaries absent from DOM and every browser storage/cache mechanism; stale content clears on invalidation.
- E2E: full Milestone B demonstration plus five existing mock contexts. Test both direct household-shared and separately approved derived-statement paths.
- Run `make lint`, `make typecheck`, `make test`, and `make build`, the relevant Playwright suite, and a repository-safety scan using fictional data only.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.5: Render a Live Household-Safe Shared Representation`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-05 - AccessContext before query and before serialization`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-07 - Protected-data class and lineage`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-10 - Audience-scoped shared-display grants`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-22 - Registry-driven policy-filtered frontend`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Protected data`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Shared Displays`]
- [Source: `docs/pivot/salvage-matrix.md#Acceptance rule`]

## Previous Story Intelligence

- Story 2.4 establishes explicit destination opens, policy-filtered topic view models, current-version behavior, and cache clearing. Reuse its query/cache conventions but do not expose the personal workspace model to shared surfaces.
- Story 1.1 repository precedent requires small retained seams, explicit public-safety checks, and truthful provider absence. The current static frontend is migration input, not evidence that privacy is implemented.

## Git Intelligence Summary

- Commit `2492dc8` established same-origin production ingress and truthful capability health. The live shared query should use that origin and existing health semantics without adding cross-origin credentials or mandatory providers.
- The current registry test explicitly keeps `topics` off shared displays. Preserve that privacy invariant by introducing a separate safe representation rather than broadening the private card.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

