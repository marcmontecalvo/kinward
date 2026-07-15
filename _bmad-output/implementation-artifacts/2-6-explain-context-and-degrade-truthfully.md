# Story 2.6: Explain Context and Degrade Truthfully

Status: ready-for-dev

<!-- Ultimate context engine analysis completed - comprehensive developer guide created. -->

## Story

As a household member,
I want Kinward to explain the context it used and clearly identify unavailable capabilities,
so that I can trust what the assistant knows without mistaking missing providers or stale information for current facts.

## Acceptance Criteria

1. An authorized personal item, response, topic representation, or result explanation shows why it appeared, what changed when applicable, permitted source categories, recency, confidence/uncertainty, sharing class, and available correction, but no chain-of-thought, raw prompt, credential, provider payload, or unauthorized source.
2. For multiple protected sources, authorization runs before source retrieval and serialization; only minimum permitted metadata appears, with no omitted-source count, gap, placeholder, timestamp, or existence leak.
3. With no/unavailable model provider, authentication, personal surfaces, local topic reads/writes, and continuation remain available; assistant capability reports a truthful canonical state and next step; no fabricated response is generated.
4. Memory and knowledge failures report independently with health/freshness; local authoritative topic/conversation context remains available; unavailable external memory is not presented as remembered fact, inferred confidence, or proof of no memory.
5. One or more optional-provider failures do not make healthy core application/database/auth/bootstrap/local-topic/continuation capabilities unhealthy; each affected capability has its own state and safe actionable reason.
6. Stale, malformed, timed-out, or freshness-unknown provider data is labeled stale/unavailable and excluded from current claims; lower confidence reduces capability; transport acknowledgement/timeout is never called completed.
7. On recovery, only a successfully checked/refreshed capability returns available; stale data is not silently current, and authorization is reevaluated before provider data reenters context.
8. Mobile, desktop, and shared degraded states use text/semantics, ordinary language, and an action/no-action message; shared display reveals no private provider ownership, configuration, error, or protected source metadata.
9. Automated outage/recovery evidence covers single and multiple failures for every Milestone B capability, with bounded categories/opaque correlations and no private body, provider payload, person ID, or high-cardinality protected metric label.

## Tasks / Subtasks

- [ ] Define one policy-filtered explanation contract (AC: 1, 2, 8)
  - [ ] Create an application query/view model for explanation target, household-safe reason, permitted source categories, recency/freshness, confidence/uncertainty, sharing class, changed-when-known, and allowed correction action.
  - [ ] Authorize the target and every source before retrieval; query only permitted metadata and reauthorize fields before serialization. Do not compute total source counts before filtering.
  - [ ] Define separate personal and shared serialization policies. Shared mode must not expose provider account ownership/configuration, private correction, source cardinality, or protected existence.
- [ ] Normalize capability and freshness status end to end (AC: 3-8)
  - [ ] Reuse the canonical states `available`, `degraded`, `unavailable`, `intentionally-disabled`, `stale`, and `reauthorization-required` from Story 1.1 health; do not add UI-only synonyms or collapse disabled into unavailable.
  - [ ] Make model, memory, and knowledge adapters expose independent bounded capability/freshness results through provider-neutral ports. Integrate Story 2.2 orchestration and Story 2.3/2.4 local-topic paths.
  - [ ] Ensure malformed output, timeout, transport success, and unknown freshness cannot yield a completed/current claim. Recovery requires a current successful check/refresh and renewed authorization.
- [ ] Add accessible explanation and degraded UI states (AC: 1, 3-8)
  - [ ] Render reusable registered explanation/status cards or disclosure panels on mobile and desktop; use the narrow household-safe variant supplied to Story 2.5 shared representation.
  - [ ] Convey state with text, semantics, and non-color indicators; support keyboard and screen readers; provide a safe next step or “no action needed.”
  - [ ] Preserve local topic content independently from assistant/provider status. Never replace known local content with an empty provider state or synthetic assistant prose.
- [ ] Harden observability and recovery behavior (AC: 5-9)
  - [ ] Emit bounded component/capability/state/reason categories and opaque correlations only. No prompt, message/topic title, provider payload/object ID, person ID, or target ID in metrics.
  - [ ] Test single/multiple outages, stale/malformed/timeout states, partial recovery, reauthorization-required, disabled-by-configuration, and failure during explanation assembly.
  - [ ] Assert unrelated capabilities remain healthy and only the refreshed capability recovers; verify stale cached context remains excluded until refresh evidence exists.
- [ ] Validate the complete Milestone B trust path (AC: 1-9)
  - [ ] Exercise personal explanations for topic/result data and the Story 2.5 household-safe shared explanation.
  - [ ] Exercise no-model local read/write/continuation, independent memory/knowledge failure, and recovery with fictional data.
  - [ ] Run privacy byte/field checks, accessibility journeys, generated-contract compilation, and all repository gates.

## Dev Notes

### Implementation Boundaries and Dependencies

- Stories 2.1–2.5 supply auth/`AccessContext`, request lifecycle, local topic authority, continuation, and shared-safe projection. Use their real contracts after they land; do not create parallel status, explanation target, policy, or source models.
- This story explains permitted evidence and capability state. It must never expose chain-of-thought or attempt to summarize hidden reasoning. “Why” means product-visible policy/source/recency/change metadata.
- Do not turn provider diagnostics into household UI. Household language is bounded (“Memory is unavailable right now; your saved topic is still here”), while internal details remain sanitized operational categories.
- This story covers Milestone B model/memory/knowledge/local-topic capability behavior. Calendar, Home Assistant, email, voice, backup, and broader Control diagnostics belong to later owning stories even though the health contract reserves categories.

### Architecture Compliance

- AD-03: provider-neutral orchestration; provider content is untrusted; a no-model local path remains useful.
- AD-05/AD-07: authorize before source retrieval and before serialization; minimum metadata only; omissions cannot leak through counts/order/gaps; stale lineage invalidates use.
- AD-06: SQL-authoritative local topics remain available independently. Providers return Kinward view/domain types with capability, health, and freshness.
- AD-14: diagnostics are allowlisted and sanitized by construction. Health and user-facing explanation share bounded semantics, not raw objects.
- AD-21: explanation/status API is Pydantic/OpenAPI-owned and generated for TypeScript. Do not revive the stale handwritten health types in `packages/contracts/src/index.ts`.
- AD-22: reusable registered UI consumes only filtered view models and keeps Kinward Control/admin density out of everyday surfaces.

### Current Repository State and Change Guidance

| Area | Current state | Change | Preserve |
| --- | --- | --- | --- |
| `services/kinward/src/kinward/health.py` | Canonical core/capability states exist; configured providers remain `unavailable` pending checks. | Reuse/centralize state vocabulary and add bounded real capability/freshness seams needed by Milestone B. | Core status independence, safe reason codes, provider absence as non-core failure. |
| `services/kinward/src/kinward/integrations/base.py` | Resilient HTTP helper tracks process-local success/error and returns provider-oriented detail. | Adapt behind capability ports; do not use process-local flags as durable/current truth or expose raw details to UI. | Bounded timeout/circuit behavior where appropriate. |
| `services/kinward/src/kinward/memory/contracts.py` | Provider methods expose content-oriented types but lack `AccessContext`, capability, and freshness. | Extend/replace via the Story 2.x application ports so protected provider calls require authorized minimal context and report normalized freshness. | Provider neutrality and optional null implementations. |
| `services/kinward/src/kinward/memory/factory.py` | Selects Honcho/LLM-Wiki or null providers. | Keep optional selection; make null/unavailable semantics explicit without pretending empty results prove absence. | Core boot without providers. |
| `apps/web/src/App.tsx` | Static copy says everything is normal; no live degraded/explanation state. | Consume generated status/explanation views in the surface shells established by prior stories. | Calm, brief, ordinary household language. |
| `packages/contracts/src/index.ts` | Handwritten health states are only `available/degraded/disabled` and omit core/model/calendar. | Replace through generated OpenAPI contract; do not patch another competing enum. | Package as generated-client destination. |

### Library and Framework Requirements

- Add no dependency solely for explanation/status rendering. Use existing Pydantic 2/FastAPI, React 19, TypeScript strict mode, and the completed card registry/query client stack.
- Project context governs dependency currency and supersedes architecture's older fixed table. Resolve any needed package at implementation time through committed pnpm/uv lockfiles and document a hold only under the project policy.
- Preserve `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, Pydantic validation at boundaries, native typed SQLAlchemy mappings, UUIDs, and UTC timestamps.

### Testing Requirements

- Application/policy: target/source preauthorization, field reauthorization, zero cardinality/existence leaks, personal vs shared explanation.
- Provider contracts: none/disabled, timeout, malformed, stale, unavailable, degraded, reauthorization-required, successful refresh, partial and multiple failures.
- API/client: exact canonical enums, safe bounded reasons, generated TypeScript compilation, additive compatibility, no provider-native payload.
- Web/E2E/accessibility: mobile/desktop/shared semantic status, keyboard disclosure, non-color indication, safe next action, no-model local continuation.
- Observability: scan logs/metrics/errors for fictional canaries and forbidden IDs/payloads; metric labels remain bounded.
- Run `make lint`, `make typecheck`, `make test`, and `make build` plus relevant Playwright/provider-failure suites.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.6: Explain Context and Degrade Truthfully`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-03 - Provider-neutral assistant orchestration`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-05 - AccessContext before query and before serialization`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-14 - Sanitized observability and diagnostics`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Observability and operations`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Content Design`]
- [Source: `docs/architecture/memory-and-knowledge.md#Provider selection`]
- [Source: `_bmad-output/project-context.md#Dependency Currency and Compatibility`]

## Previous Story Intelligence

- Story 2.5 needs a deliberately narrower shared explanation that cannot expose private source existence or correction. Keep the explanation service policy-driven so the shared serializer is a restricted view, not client redaction.
- Story 1.1 already established the canonical health vocabulary and truthful core-vs-capability split. Extend that work rather than creating another status taxonomy.

## Git Intelligence Summary

- Commit `2492dc8` added `health.py`, optional-provider configuration, current lockfiles, and focused health tests. Its `intentionally-disabled` behavior and sanitized reason codes are the repository's strongest precedent.
- Current memory ports predate `AccessContext`; treating them as directly safe would violate the adopted architecture. Place authorization/minimization in application ports before adapters are invoked.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

