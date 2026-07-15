# Story 2.3: Persist Authorized Topics and Personal Context

Status: ready-for-dev

## Story

As an authenticated household member,
I want my assistant conversation to create or update a durable private topic,
so that useful context remains available without depending on an external provider or crossing another person's privacy boundary.

## Acceptance Criteria

1. Accepting a request without a topic creates one Kinward-local topic bound to the authenticated person, their owned primary assistant, originating surface, current authorization/policy versions, `private-person` class, and initial version through an application command/unit of work; exact duplicates are idempotent.
2. Persisting accepted conversation content or assistant output advances the topic version atomically with permitted conversation records and surface provenance. Optimistic concurrency rejects stale updates and failed transactions preserve the prior version.
3. Topic/conversation repositories require `AccessContext` and constrain queries by current person, assistant ownership, topic ownership, lifecycle, class/audience, purpose, and policy/source versions before protected rows are read. Authorization repeats before serialization; unauthorized topics are absent without existence metadata.
4. For separate adults and assistants, records, memory references, counts, recent/search results, facets, and empty states are influenced only by the authorized adult's data. Administrator role does not broaden access and the fallback assistant cannot query private-person indexes.
5. Each optional memory/knowledge reference records owner, creating assistant/authority, source identity/version, canonical data class, purpose, authorization/policy reference, provider capability/freshness, and lifecycle. Kinward SQL remains authoritative; a provider is never the sole topic/conversation copy.
6. On cancelled, failed, or uncertain requests, only policy-permitted content accepted before the terminal boundary is retained. Post-cancellation output is neither persisted nor rendered, and terminal request truth remains separate from conversation content.
7. Local topic create/read/update continues if model, memory, or knowledge providers are unavailable. Missing provider context is explicit; projection/retrieval failure does not roll back a valid local commit.
8. Topic, conversation, and memory-reference metadata explicitly defines backup inclusion, restore quarantine, ownership/class, retention/deletion, import eligibility, and provider-reference treatment. Personal records remain unavailable after restore until same-owner reauthentication/disposition; no credential or provider-native payload is stored.
9. Operational output omits prompts, conversation bodies, topic titles, memory bodies, and provider payloads, using only opaque correlations and bounded categories; fixtures are obviously fictional.

This story addresses `FR-014`, `FR-018`, `FR-020`, `FR-021`, `FR-027`, `FR-030`, `FR-033`, `NFR-001`, `NFR-005`, `NFR-006`, `NFR-008`, `NFR-010`, `NFR-029`, `NFR-030`, `NFR-032`, `UX-DR13`, and `AD-04–AD-07`, `AD-19`, `AD-25`.

## Tasks / Subtasks

- [ ] Define topic, conversation, protected-reference, and lifecycle contracts (AC: 1-9)
  - [ ] Add framework-free topic/conversation aggregates with UUID identity, owner person, owned assistant, class, audience/policy reference, lifecycle, version, UTC timestamps, and surface provenance.
  - [ ] Use canonical data classes (`private-person`, `private-child`, `selected-share`, `household-shared`, `surface-ephemeral`, `system-operational`); this story creates private-person topics only and must not invent sharing behavior.
  - [ ] Define repository/query ports that require `AccessContext`, expected versions, purpose, and current authorization; no unscoped list/count/search method is permitted.
  - [ ] Define optional projection/reference ports and capability/freshness results without provider-native types.
- [ ] Add authoritative local persistence through a forward migration (AC: 1-8)
  - [ ] Create topic, conversation entry, and external memory/knowledge reference tables with database ownership/class/version/lifecycle constraints and useful scoped indexes.
  - [ ] Enforce idempotent topic creation/content append, monotonic per-topic ordering, optimistic version compare-and-set, and atomic request/topic/content transitions.
  - [ ] Store private bodies in protected fields/tables separate from bounded operational metadata; do not overload `MemoryIndexRecord`'s legacy `privacy/source/external_id` shape without migrating it to the canonical contract.
  - [ ] Add exact source IDs/versions/classes, transformation version, and expiry only where a derived item is actually introduced; do not silently reclassify a source.
- [ ] Implement scoped topic commands and queries (AC: 1-7)
  - [ ] Create/open/update/list/search/recent/count services only to the extent needed for durable continuation; all use Story 2.1 `AccessContext` and Story 2.2 request identities/terminal boundaries.
  - [ ] Resolve owner/assistant from server state, authorize before SQL construction, and reauthorize candidate fields immediately before Pydantic view-model serialization.
  - [ ] Make duplicate-equal commands return prior results, conflicting idempotency reuse fail, and stale expected versions return a safe conflict/current-refresh path.
  - [ ] Ensure fallback and cross-person contexts cannot construct private topic/memory queries, including counts, empty states, and error branches.
- [ ] Integrate Story 2.2 lifecycle atomically (AC: 1, 2, 6)
  - [ ] Persist only accepted user content and policy-filtered assistant content at defined lifecycle boundaries.
  - [ ] Serialize topic append against cancellation/terminal transitions so output after cancellation cannot commit even if the provider emits late.
  - [ ] Keep request terminal state separate and link by opaque identity; never infer request completion from the presence of a conversation entry.
- [ ] Add optional provider projection/retrieval behavior (AC: 5, 7)
  - [ ] Commit authoritative SQL first with a durable outbox intent for optional projection; provider failure cannot roll back or hide the local topic.
  - [ ] Require `AccessContext` and minimum-purpose filtering for retrieval/projection. Fallback assistant access to private-person references is impossible by contract.
  - [ ] Report unavailable/stale provider context separately and never convert absence/failure into a claim that no memory exists.
  - [ ] External deletion mechanics remain governed by AD-25; record blocked/deletion-pending references if introduced, but do not build Epic 4 fact-management UX.
- [ ] Add versioned topic API/view models and generated client contracts (AC: 1-9)
  - [ ] Add only thin `/api/v1` topic endpoints needed by this and Story 2.4; responses are policy-filtered view models, not ORM/provider objects.
  - [ ] Generate TypeScript contracts from Pydantic/OpenAPI; keep card/layout/config schemas in `packages/schemas` and remove any duplicated topic authority.
  - [ ] Prevent private titles/bodies/source metadata from entering errors, denial payloads, caches, metrics, or shared/fallback response shapes.
- [ ] Define backup, restore, retention, deletion, and import metadata (AC: 8)
  - [ ] Include authoritative topic/conversation records in protected backups; quarantine personal records after restore until same-owner reauthentication and explicit disposition.
  - [ ] Exclude provider credentials/native payloads; classify external references as rebuildable, externally retained, deletion-pending, or reauthorization-required as applicable.
  - [ ] Mark private topic/conversation data ineligible for the current controlled import unless a later explicit allowlist authorizes it; define user deletion/body-erasure and minimal permitted tombstone behavior.
- [ ] Verify authorization, concurrency, degradation, and safety (AC: 1-9)
  - [ ] Test two adults/admin, owned/fallback/cross-owner assistants, lifecycle/class/purpose variants, and assert forbidden SQL/provider calls and all existence channels are absent.
  - [ ] Test duplicate and concurrent create/append, stale versions, transaction rollback, cancellation races, process restart, outbox projection failure/recovery, and model/memory/knowledge outage independence.
  - [ ] Run SQLite persistence tests and the same contract suite against PostgreSQL where available; PostgreSQL remains unadvertised until the complete suite passes.
  - [ ] Inspect API/SSE bytes, logs, metrics, errors, caches, and fixtures for protected strings; run all four Make gates and public-safety scan.

## Dev Notes

### Dependencies and Scope

- Story 2.1 supplies authenticated `AccessContext`; Story 2.2 supplies canonical request lifecycle, cancellation boundary, and accepted content events. Do not duplicate either contract.
- This story makes local private topics durable. Story 2.4 owns cross-surface continuation UI/metrics; Story 2.5 owns household-safe sharing; Epic 4 owns topic management, reclassification, facts, inferred observations, lineage workflows, and deletion UX.
- Do not expose fallback/shared display access, household sharing, specialist assistants, arbitrary provider memory, or provider-only continuity.

### Current Repository State and Required Changes

| Area | Current state | Required change | Preserve |
| --- | --- | --- | --- |
| `persistence/models.py` | No topic/conversation tables. `MemoryIndexRecord` has only person, assistant, global external ID, legacy privacy/source/confidence. | Add canonical topic/conversation/reference persistence and migrate/refactor the legacy reference shape behind scoped repositories. | SQL authority, UUID/UTC typed mapping conventions. |
| `memory/contracts.py` | Provider-oriented messages/hits/facts use legacy roles/status/privacy and arbitrary metadata; no `AccessContext`. | Treat as migration input; introduce provider-neutral application ports and canonical ownership/class/source metadata. | Optional adapter concept, not these domain types as authority. |
| `memory/providers.py`, `honcho.py`, `llm_wiki.py` | Optional provider factories/adapters can become projections/retrieval adapters. | Require scoped ports/context, normalize capability/freshness, and ensure providers are never sole copy. | Safe optional degradation and no-provider startup. |
| `outbox_messages` | Generic durable hand-off seam with no delivery semantics. | Reuse through a typed application outbox contract for optional projection; do not store private bodies in observable generic payloads without classification/protection. | SQL durable dispatch and worker readiness. |
| `apps/web` | Static topics card and fictional list; no live topic API. | Story 2.3 needs generated API types and minimal live private view model; Story 2.4 owns full continuation UX. | Registered-card-only rendering and surface distinctions. |

### Architecture and Privacy Guardrails

- Kinward SQL owns topic/conversation continuity. Optional providers are outbound projections/retrieval only. Provider deletion or outage cannot erase local truth or fabricate knowledge.
- Every protected item carries owner principal, canonical class, item version, and versioned audience policy/grant reference. Missing/stale ownership or policy fails closed.
- Query authorization must change SQL/provider predicates, not filter a broad result after loading. Reauthorize before serialization and test counts, recent/search, empty states, errors, caches, and events for existence leakage.
- Administrator role is not ownership. The household fallback has no personal owner and cannot query private-person topic/conversation/memory indexes.
- Application commands are the only mutation path. Route, ORM adapter, provider adapter, worker callback, and card renderer may not independently commit topic state.

### Persistence and Lifecycle Guidance

- Use short transactions and compare-and-set versions compatible with SQLite and PostgreSQL. Database constraints must backstop ordering/idempotency/ownership, not rely only on Python checks.
- Define conversation entry kinds narrowly (accepted person input and policy-filtered assistant output). Do not store hidden prompts, chain-of-thought, raw provider payloads, or credentials.
- Separate topic lifecycle from request lifecycle. A failed/uncertain/cancelled request may leave accepted prior content while remaining visibly non-completed.
- Personal topic records are protected backup content and restore quarantined. Derived shares are not created by this story.

### File Structure Guidance

- Expected additions: topic domain/application/ports, scoped SQL repositories, migration, Pydantic API/view models, generated TS contracts, provider projection adapter seam, and privacy/concurrency contract tests.
- Expected updates: persistence models/session exports, worker outbox dispatch if projections are enabled, memory adapters/contracts, app router registration, and the minimal personal topic card/data adapter.
- Do not put topic domain models in `packages/schemas` or return ORM models from FastAPI.

### Testing and Evidence Ownership

- BE owns atomicity, optimistic concurrency, scoped repositories, provider projection, lifecycle/recovery, and backup classification. FE owns safe view-model use and private cache/storage behavior. QA owns cross-person/existence matrices, cancellation races, outage/restart, dual-adapter contracts, and protected-string scans.

### Previous Story and Git Intelligence

- Story 2.2's terminal event and cancellation serialization are authoritative; topic writes must participate in or coordinate with that unit of work so late output cannot persist.
- Story 2.1's server-derived actor/assistant/surface context is the only authorization source.
- Story 1.1/commit `2492dc8` provides frozen `001`, SQL outbox/worker, optional memory/knowledge capability health, SQLite default, and no-provider startup. Add a forward migration and preserve all those gates.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.3: Persist Authorized Topics and Personal Context`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-04 — Kinward-local topic and conversation authority`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-07 — Protected-data class and lineage`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Data ownership and persistence`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Read and serialization flow`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Personal Mobile`]
- [Source: `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md#Completion Notes List`]
- [Source: `docs/pivot/salvage-matrix.md#Acceptance rule`]
- [Source: `AGENTS.md#Public repository safety`]

## Dev Agent Record

### Agent Model Used

OpenAI GPT-5

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List
