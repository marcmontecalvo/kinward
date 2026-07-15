# Story 2.4: Continue a Topic Across Mobile and Desktop

Status: ready-for-dev

<!-- Ultimate context engine analysis completed - comprehensive developer guide created. -->

## Story

As an authenticated household member,
I want to resume an authorized topic on desktop after starting it on mobile,
so that I can continue useful work without repeating my original request or losing stored context.

## Acceptance Criteria

1. **Given** a person submits a text request on an authenticated personal mobile surface, **when** the request is accepted and creates or updates a topic, **then** mobile shows truthful incremental response state and the resulting topic and permitted conversation context are durably available from Kinward-local persistence.
2. **Given** that topic has prior mobile activity, **when** the same person explicitly opens it on an authenticated personal desktop surface, **then** the server reauthorizes person, account state, owned assistant, topic, sharing class, source versions, and destination surface before querying, and desktop renders current permitted context without restatement.
3. **Given** a valid continuation, **when** the desktop workspace loads, **then** it presents topic identity, permitted conversation, decisions, unresolved questions, assistant progress, and truthful terminal/in-progress states at that version, without fabricating missing context or exposing hidden prompts, provider payloads, or chain-of-thought.
4. **Given** the topic changed after mobile last rendered it, **when** desktop opens it, **then** desktop receives the current authorized server version, stale state cannot overwrite it, and stale mutation returns a household-safe conflict plus current-state refresh path.
5. **Given** authorization narrowed, was revoked, expired, or became ambiguous, **when** continuation is attempted, **then** the backend denies affected topic/fields before query and serialization, returns no forbidden field, count, title, source, or existence signal, and clears cached/rendered no-longer-authorized state.
6. **Given** duplicate tabs, reconnects, or rerenders, **when** continuation evidence is recorded, **then** one canonical `continuation_id` identifies that explicit destination open; a later explicit open after closure gets a new ID; passive rerenders do not inflate evidence.
7. **Given** keyboard-only mobile and desktop use, **when** the person opens Continue, selects a topic, inspects context, submits follow-up text, and cancels or completes it, **then** the journey has visible focus and screen-reader semantics, and distinct mobile/desktop layouts use the same registered cards and generated API contracts.
8. **Given** the reference deployment and selected evidence population, **when** performance is measured, **then** cached personal home is interactive within 2 seconds p95, cold load within 4 seconds p95, local continuation reads within 500 ms p95, and evidence distinguishes continuation without restatement, restatement, cancellation, and visible failure.
9. **Given** the model or optional memory provider is unavailable, **when** the persisted topic opens, **then** authorized local context still renders, dependent generation is separately marked unavailable/degraded, and unavailable provider memory is not presented as known.

## Tasks / Subtasks

- [ ] Define the continuation application query and generated wire contracts (AC: 2-6, 9)
  - [ ] Build on Stories 2.1–2.3 `AccessContext`, session, topic, conversation, request-state, SSE, and generated OpenAPI client contracts; do not create parallel identity, topic, event, or handwritten TypeScript domain contracts.
  - [ ] Return a policy-filtered workspace view model containing topic/version, permitted messages, explicit decisions/unresolved questions when locally represented, request lifecycle state, surface provenance, capability status, and an opaque continuation identity.
  - [ ] Define stable not-found/denied semantics that reveal neither topic existence nor ownership; define an optimistic-concurrency conflict with safe refresh metadata.
- [ ] Implement explicit destination-open continuation semantics (AC: 2, 4-6)
  - [ ] Add a `/api/v1` query/command handler that derives desktop surface and authority server-side, authorizes before repository query, and reauthorizes fields immediately before serialization.
  - [ ] Create/reuse one canonical continuation record or bounded evidence identity per explicit destination open; make duplicate delivery/idempotent reopen behavior precise and prevent passive fetch/rerender from creating adoption events.
  - [ ] Read current server versions; never let browser state choose authority or overwrite a newer topic. Clear client query/cache state on denial, revocation, or account/session loss.
- [ ] Build mobile Continue and desktop topic workspace on registered cards (AC: 1-3, 7)
  - [ ] Replace relevant static topic examples with server-produced policy-filtered view models while preserving the Story 1.3–1.5 registry/layout resolver and all five mock-foundation tests.
  - [ ] Keep personal mobile glance/Continue compact; give desktop a distinct deeper workspace. Reuse the same card definitions and generated API types, not duplicate surface-specific feature models.
  - [ ] Integrate Story 2.2 streaming/follow-up/cancellation state rather than implementing another request lifecycle.
- [ ] Preserve local continuity under provider failure (AC: 3, 9)
  - [ ] Load topic/conversation truth solely from Kinward SQL as established by Story 2.3; optional model/memory/knowledge adapters may enrich only through authorized ports.
  - [ ] Render missing/stale external capability separately from local content; never infer “no memory” from an unavailable provider or synthesize decisions/questions not persisted locally.
- [ ] Add focused privacy, concurrency, accessibility, and performance evidence (AC: 1-9)
  - [ ] Test same-owner mobile-to-desktop success, other-adult/admin/fallback denial, narrowed/revoked authorization, no-existence leakage, duplicate tabs/reconnect/rerender identity, stale expected version, and provider absence.
  - [ ] Add React/Vitest and Playwright journeys for keyboard/focus/screen-reader semantics, cache clearing, follow-up streaming, cancellation, and distinct mobile/desktop layouts.
  - [ ] Use fictional fixtures and bounded metrics only; measure the adopted reference deployment and categorize continuation outcomes without person/topic IDs as metric labels.

## Dev Notes

### Implementation Boundaries and Dependencies

- This story depends on the contracts created by Stories 2.1–2.3 even if those files are authored concurrently: 2.1 owns authentication/session/CSRF and server-derived `AccessContext`; 2.2 owns request identity, SSE lifecycle, cancellation, reconnect, and terminal truth; 2.3 owns local topic/conversation persistence, ownership filters, versions, and provider references.
- Reconcile against the actual implemented 2.1–2.3 APIs before coding. Extend their application ports; do not guess at or fork their contracts.
- Story 2.4 owns personal mobile-to-desktop continuation only. Story 2.5 owns live shared representation and absence proofs. Story 2.6 owns reusable explanation view models and capability-degradation presentation.
- No voice, personal-tablet live workspace, multimodal/context-targeted input, specialist assistant, layout editor, or native client is authorized.

### Architecture Compliance

- Follow the hexagonal modular monolith: thin FastAPI adapter -> application query/service -> policy -> repository/provider ports. SQLAlchemy, FastAPI, and provider SDK types stay out of domain/application contracts.
- Apply AD-05 twice: authorize/scoped-filter before query construction and authorize each serialized field afterward. Empty states, counts, metrics, cached data, and SSE are protected outputs too.
- Kinward SQL is authoritative for topics, conversations, lifecycle, sharing, versions, surface provenance, and required continuity (AD-04/AD-06). Optional providers cannot be the only copy.
- All mutations, including a follow-up or continuation evidence record when persisted, use application commands, idempotency/expected versions as appropriate, and one unit of work (AD-19).
- Backend Pydantic/OpenAPI owns wire contracts; generate TypeScript into `packages/contracts`. `packages/schemas` remains for card/layout/client configuration only (AD-21).
- Registered cards accept only server-filtered view models. Authorization must never move into card renderers (AD-22).

### Current Repository State and Change Guidance

| Area | Current state | Change | Preserve |
| --- | --- | --- | --- |
| `apps/web/src/App.tsx` | One static shell with hard-coded Now/briefing/topics/house data and composer. | Route/render personal mobile and desktop continuation using live query state and Story 2.2 composer lifecycle. | Everyday assistant shell, persistent input, no Kinward Control density. |
| `apps/web/src/cards/registry.tsx` | Small registry with `now`, `list`, and personal-only `topics`; props are unvalidated `Record<string, unknown>`. | Extend the Story 1.x completed registry with typed continuation cards/view models; use its actual post-story state. | Registry-only rendering and per-surface support; no arbitrary generated components. |
| `packages/contracts/src/index.ts` | Handwritten summaries that include out-of-scope specialist/temporary assistant kinds and stale health enums. | Do not extend these by hand; consume generated Story 2.1–2.3 API types and add generated continuation responses. | Build/package boundary only. |
| `packages/schemas/src/index.ts` | Client card/layout schemas plus broader legacy-like privacy vocabulary. | Touch only if a continuation card/layout configuration schema is genuinely client-owned. | Domain and API authority remain backend-owned. |
| `services/kinward/src/kinward/persistence/models.py` | Household foundation only; no topics/conversations in current baseline. | Use Story 2.3 models/repositories and forward migration; add only continuation-specific persistence that is truly required. | UUIDs, UTC, typed SQLAlchemy mappings, single-household schema. |
| `services/kinward/src/kinward/app.py` | Health plus retained setup route; no topic router. | Register the shared `/api/v1` route modules delivered by 2.1–2.3 and the continuation endpoint. | App factory and truthful health. |

### Testing Requirements

- Unit/application: authorization ordering, field-level reauthorization, current-version reads, expected-version conflict, continuation ID idempotency/lifecycle, no-provider behavior.
- Persistence: run topic/version/continuation semantics on SQLite; keep repository contract portable for the eventual PostgreSQL evidence gate.
- API/contracts: generated client compiles; stable errors contain only safe code/message/correlation; unknown optional fields remain compatible.
- Web/E2E: mobile start -> stream -> persisted topic -> desktop explicit open -> follow-up/cancel; keyboard-only and assistive semantics; revoked state disappears from memory/cache/DOM.
- Run `make lint`, `make typecheck`, `make test`, and `make build` plus the relevant Playwright/performance subset.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.4: Continue a Topic Across Mobile and Desktop`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Stories 2.1-2.3`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-04 - Kinward-local topic and conversation authority`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-05 - AccessContext before query and before serialization`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-21 - Authoritative API and shared-schema ownership`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-22 - Registry-driven policy-filtered frontend`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Assistant orchestration flow`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Information Architecture`]
- [Source: `_bmad-output/project-context.md#Technology Stack & Versions`]

## Previous Story Intelligence

- Story 2.3 is the immediate implementation dependency but may not yet exist as a file. Its epic contract requires SQL-authoritative topics/conversations, pre-query ownership constraints, optimistic versions, local operation without providers, and no protected operational output.
- Repository precedent from Story 1.1 favors explicit scope boundaries, a current-state/change/preserve table, synthetic fixtures, and completing all four Make gates before handoff.

## Git Intelligence Summary

- Recent commit `2492dc8` established the current healthy deployment, generated lockfiles, one-shot migration/API/worker split, typed health contract, and same-origin web ingress. Extend those seams; do not reintroduce migration-on-start, Redis, or optional-provider startup coupling.
- The working baseline is intentionally sparse. New topic modules should follow the target architecture directories rather than putting business logic in `app.py` or current setup adapters.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

