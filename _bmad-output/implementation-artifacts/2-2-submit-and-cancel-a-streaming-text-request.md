# Story 2.2: Submit and Cancel a Streaming Text Request

Status: ready-for-dev

## Story

As an authenticated household member,
I want to submit a text request and see truthful incremental progress with cancellation,
so that I know what my assistant is doing and can stop work before anything unsubmitted proceeds.

## Acceptance Criteria

1. An authenticated personal mobile/desktop user submits text through persistent Assistant Input to a versioned `/api/v1` command using the server-authorized assistant and surface, optional authorized topic context, correlation ID, and idempotency key. No microphone, camera, screenshot, file, screen, selected-object, application, or ambient-device context is sent or advertised.
2. Acceptance creates one canonical request identity, exposes `accepted` within 500 ms p95, and uses only `accepted`, `understanding`, `responding`, `awaiting-approval`, `acting`, `completed`, `cancelled`, `uncertain`, or `failed`.
3. Incremental generation produces ordered versioned SSE events with request ID, sequence, UTC time, correlation ID, event type, and policy-filtered payload; first visible content is within 3 seconds p95 outside provider outages and exactly one truthful terminal event is emitted.
4. Immutable `AccessContext` authorizes actor, account, owned assistant, surface/audience, optional topic, capability, permitted context, action authority, freshness, and policy versions before every protected query/provider call and again before event serialization. Only minimum permitted data reaches a model provider.
5. Provider/model output is untrusted. It cannot select identity, authority, policy, sources, or mutation targets. Only registered, backend-authorized, input/output-validated Milestone B read capabilities may execute; external mutation capabilities remain unavailable.
6. Cancellation winning serialization from accepted/understanding/responding/awaiting-approval stops or discards later output, prevents all unsubmitted side effects, emits exactly one `cancelled` terminal result, and delivers/persists no later content or completion.
7. The first valid terminal transition wins and is immutable. Exact duplicate cancellation is idempotent; cancellation after terminal returns current state without reopening.
8. Timeout, disconnect, malformed output, or provider failure produces `uncertain` or `failed` based on known truth, never false completion, plus a household-safe retryability/next-step result.
9. SSE reconnect resumes retained ordered events from a supported cursor without duplication or queries current state when replay is unavailable. Stream closure alone never implies completion.
10. Older clients ignore optional fields safely and may handle unknown non-terminal events only by preserving sequence and querying state. Unknown major versions, required enums, or terminal semantics fail closed as upgrade-required.
11. Logs/traces/metrics/errors/fixtures contain no full prompt, conversation body, provider-native payload, credential, or protected high-cardinality label. Tests prove ordering, cancellation races, reconnect, timeout, malformed/provider failure, one terminal event, authorization order, and minimization with fictional data.

This story addresses `FR-013`, `FR-017`, `FR-021`, `FR-030`, `FR-033`, `NFR-001`, `NFR-005`, `NFR-006`, `NFR-008`, `NFR-011`, `NFR-018`, `NFR-019`, `NFR-029`, `NFR-030`, `NFR-032`, `UX-DR14`, `UX-DR20`, `UX-DR25`, `UX-DR27`, and `AD-02`, `AD-03`, `AD-05`, `AD-19`, `AD-21`.

## Tasks / Subtasks

- [ ] Define the request lifecycle and orchestration ports (AC: 1-8, 10)
  - [ ] Implement a framework-free state machine with allowed transitions, immutable terminal states, expected-version compare-and-set, and exactly-one-terminal invariant.
  - [ ] Define versioned submit/cancel/query commands, request/event envelopes, provider-neutral orchestration/context ports, registered read-capability contracts, clocks, IDs, and cancellation signals.
  - [ ] Treat `awaiting-approval` and `acting` as representable lifecycle states only; do not enable external mutation or approval execution in Milestone B.
  - [ ] Specify `uncertain` versus `failed` based on whether the result is unknowable versus known not to have completed.
- [ ] Persist request identity, lifecycle, idempotency, and replayable event metadata (AC: 2, 3, 6-10)
  - [ ] Add a forward migration and SQLAlchemy records for requests and retained ordered events with UUIDs, UTC timestamps, sequence uniqueness, expected versions, terminal uniqueness, and idempotency conflict detection.
  - [ ] Keep private prompt/event bodies in appropriately classified storage, separate from bounded operational metadata; define retention and backup/quarantine treatment.
  - [ ] Serialize submit, cancel, provider completion, timeout, and failure transitions transactionally so races cannot emit two terminal states.
  - [ ] Define bounded SSE retention and cursor-expiry behavior; current-state query remains authoritative when replay is unavailable.
- [ ] Implement assistant request application services (AC: 1-8, 11)
  - [ ] Require Story 2.1 `AccessContext`; resolve assistant/surface/topic authority server-side and reject client attempts to broaden it.
  - [ ] Accept duplicate-equal submissions idempotently and reject conflicting key reuse without starting another provider request.
  - [ ] Assemble minimum policy-filtered context and invoke a provider-neutral model adapter with explicit timeout/cancellation handling.
  - [ ] Validate typed content/read-capability proposals; reject provider-native or mutation proposals and prevent adapters from committing state.
  - [ ] On cancellation, signal cooperative provider cancellation and independently discard any subsequent output before persistence or serialization.
- [ ] Add REST/SSE adapters and generated contracts (AC: 1-3, 6-10)
  - [ ] Add `/api/v1` submit, request-state, cancel, and SSE endpoints with CSRF on state changes and cookie authentication from Story 2.1.
  - [ ] Use monotonic per-request sequence numbers and a documented cursor/`Last-Event-ID` contract; heartbeat/transport frames must not masquerade as lifecycle events.
  - [ ] Generate TypeScript contracts from Pydantic/OpenAPI and add compatibility fixtures for optional fields, unknown non-terminal events, and fail-closed major/terminal changes.
- [ ] Connect persistent Assistant Input and truthful response UI (AC: 1-3, 6-10)
  - [ ] Replace the current no-op form with typed submission, visible accepted/progress/content/terminal states, cancel control, reconnect/state recovery, and safe retry guidance.
  - [ ] Keep text-only scope explicit; remove or withhold every uncommitted context affordance.
  - [ ] Ensure keyboard operation, visible focus, screen-reader live-region semantics without duplicate announcements, reduced-motion behavior, and non-color status.
  - [ ] Clear/discard event payloads immediately when session/access authorization fails or narrows.
- [ ] Add provider-null/degraded and security behavior (AC: 4, 5, 8, 11)
  - [ ] A missing model adapter returns a truthful unavailable/failed outcome without fabricated content and without blocking local authenticated capabilities.
  - [ ] Bound provider calls with explicit timeout and no unsafe automatic retry; minimize provider payload and sanitize adapter exceptions by construction.
  - [ ] Reject prompt/tool attempts to override authority and assert forbidden repositories/capabilities are never invoked.
- [ ] Verify lifecycle, contracts, UX, and performance (AC: 1-11)
  - [ ] Property/race tests cover submit duplication, cancel-vs-output/terminal, disconnect/reconnect, sequence gaps/duplicates, cursor expiry, malformed events, timeouts, provider failure, and terminal immutability.
  - [ ] API tests cover auth/CSRF first, pre-query and pre-serialization policy, byte/field absence, minimum provider payload, and generated-client compatibility.
  - [ ] Playwright covers mobile/desktop text submit, accepted feedback, streaming, cancellation, reconnect, provider outage, keyboard/screen reader semantics, and no private browser persistence.
  - [ ] Capture 500 ms acceptance and 3 second first-content p95 evidence on the defined reference profile; run all four Make gates and repository-safety scans.

## Dev Notes

### Dependencies and Scope

- Story 2.1 must provide a stable authenticated `AccessContext`, CSRF/session validation, and owned-assistant resolution. Do not invent a parallel auth context in this story.
- Story 2.3 will make topics/conversation authoritative. This story may persist request/event truth required for cancellation and reconnect, but must expose application ports so Story 2.3 can atomically retain authorized content without making the model provider authoritative.
- No external mutation, approval execution, specialist assistant, voice/multimodal input, arbitrary tool, WebSocket, or provider-specific UI contract is in scope.

### Current Repository State and Required Changes

| Area | Current state | Required change | Preserve |
| --- | --- | --- | --- |
| `apps/web/src/App.tsx` | Assistant Input form only prevents default; content is static. | Bind to generated API/SSE client, lifecycle state, cancellation, reconnect, and accessible feedback. | Persistent bottom input and personal mobile/desktop responsive shell. |
| `services/kinward/src/kinward/app.py` | Only versioned health plus legacy setup. | Register thin request/cancel/state/SSE routes under `/api/v1`. | App factory and truthful health behavior. |
| `persistence/models.py` | No request/event/topic/conversation state; outbox is only a readiness seam. | Add request/event persistence through a forward migration; do not overload generic outbox payloads as conversation truth. | Typed SQLAlchemy mappings, UTC/UUID conventions. |
| `integrations/protocols.py` | Provider-specific-looking calendar/mail/voice protocols; no model orchestration port and voice is out of scope. | Add provider-neutral model/orchestration ports in architecture-compliant namespaces; do not reuse voice/mail protocols. | Adapter isolation concept only. |
| `packages/contracts/src/index.ts` | Hand-authored summaries, not generated API types. | Generate request/event/client contracts from Pydantic/OpenAPI. | `packages/schemas` only for card/layout/config schemas. |

### Architecture Guardrails

- REST commands/queries plus SSE are fixed. Do not introduce WebSocket. Every envelope is versioned and correlation-bearing; exactly one terminal event is durable truth.
- Routes parse/dispatch only. The application service owns policy, state transitions, provider invocation, cancellation, and unit-of-work. Provider adapters emit typed proposals and never write household state.
- Authorization precedes every protected query/provider assembly and event serialization. Client-supplied assistant/topic/surface IDs are requested context, never authority.
- Provider output is hostile/untrusted input. Validate sizes, schemas, event ordering, and capability names; never execute generated HTML/React/code or direct provider tool calls.
- Do not log prompt/content bodies, SSE payloads, provider exceptions/payloads, topic IDs, or request IDs as metric labels. Opaque correlation IDs may be structured log fields.

### Persistence, Recovery, and Retention

- Request state and retained events are Kinward-local. Define backup inclusion, personal quarantine, retention, deletion, and import exclusion for each introduced record.
- A cancelled/failed/uncertain request remains distinguishable from its accepted content. Unknown provider output after cancellation is discarded, not hidden in provider projection.
- Provider request state must recover truthfully after process restart. Do not automatically retry a generation whose outcome cannot be established.

### File Structure Guidance

- Expected additions: assistant domain/application/ports, persistence repositories, model/null adapters, versioned API/SSE modules, migration, generated web client, SSE hook/store, and focused test suites.
- Expected updates: `app.py`, web App/input styling, manifests/locks if a generated-client/SSE helper is justified. Prefer platform `EventSource`/fetch-compatible primitives where cookie and cancellation requirements allow; do not add a library without need.

### Testing and Evidence Ownership

- BE owns lifecycle/state-machine, policy ordering, provider minimization, cancellation, SSE replay, and performance evidence. FE owns accessible live state, reconnect, clearing, and text-only scope. QA owns race/property, compatibility, end-to-end, and leakage evidence. OPS owns ingress buffering/timeouts required for SSE.

### Previous Story and Git Intelligence

- Story 2.1 establishes the only authentication and `AccessContext` seam this story may use.
- Story 1.1/commit `2492dc8` established same-origin Nginx, API/worker separation, SQL outbox readiness, frozen locks, and optional-provider-safe health. Update ingress for SSE without breaking `/api/v1/health`, legacy setup compatibility, or no-provider startup.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.2: Submit and Cancel a Streaming Text Request`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-02 — Versioned REST and SSE request contract`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-03 — Provider-neutral assistant orchestration`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Assistant orchestration flow`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#API and contract design`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Personal Mobile`]
- [Source: `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md#Architecture Compliance`]
- [Source: `AGENTS.md#Public repository safety`]

## Dev Agent Record

### Agent Model Used

OpenAI GPT-5

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List
