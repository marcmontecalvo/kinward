---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
inputDocuments:
  - _bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md
  - _bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md
  - _bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md
  - docs/pivot/single-household-pivot-and-rebuild-plan.md
  - docs/pivot/salvage-matrix.md
---

# kinward - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for kinward, decomposing the requirements from the PRD, UX design specification, architecture contract, rebuild plan, and salvage matrix into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-001: Support exactly one household per deployment.

FR-002: Bootstrap the household, initial administrator and account binding, primary personal assistant, household fallback assistant, and all selected adult, child, and pet profiles in one duplicate-safe transactional operation.

FR-003: Allow administrators to create adult and minor profiles before those people have accounts, during bootstrap or later profile management.

FR-004: Complete initial onboarding without requiring integrations, rooms, devices, routines, detailed schedules, notification rules, or layout editing.

FR-005: Bind an accepted invitation to its intended existing profile without creating a duplicate profile.

FR-006: Make invitations single-use, expiring, revocable, and invalid after the target profile is bound.

FR-007: Separately model and enforce household role, account state, privacy class, assistant ownership, action authority, account-state transitions, retained ownership, reactivation, and fail-closed invalidation.

FR-008: Let people review their identity and relationship data and make only the authorized atomic, versioned corrections defined by the PRD; reject stale, ambiguous, unauthorized, cross-profile, or incompletely evaluated changes.

FR-009: Give each account-bearing person exactly one primary personal assistant in the first usable release; keep additional and specialist assistants unavailable.

FR-010: Give every primary personal or future specialist assistant exactly one owner.

FR-011: Provision and manage one household-owned fallback assistant with no personal owner and the strict household-safe boundary.

FR-012: During adult onboarding, collect and persist the assistant name and supported personality and interaction preferences without allowing preferences to alter authority or privacy.

FR-013: Expose the complete truthful assistant request lifecycle from accepted through terminal completion, cancellation, uncertainty, or failure.

FR-014: Bind conversation continuity to the person, assistant, topic, surface, and current authorization.

FR-015: Allow an authorized topic to continue across personal mobile and desktop without restating stored context.

FR-016: Let authorized users create, rename, archive, reopen, reclassify, inspect, and delete topics with immediate narrowing and dependency invalidation.

FR-017: Ensure cancellation stops further model output, prevents every unsubmitted action, and visibly marks the request cancelled.

FR-018: Bind personal memory to its owning person and creation permissions.

FR-019: Store or label household-shared facts separately from private memory.

FR-020: Prevent the household fallback assistant from querying private personal memory indexes.

FR-021: Assemble only context permitted for the current person, assistant, topic, surface, audience, action, capability, and external-state freshness.

FR-022: Store and expose knowledge state and sharing class as independent classifications and explain both without exposing protected sources.

FR-023: Require authorized explicit confirmation before a pending inferred observation becomes a durable fact or influences future assistance as one.

FR-024: Let users inspect, correct, reclassify, and delete durable facts about themselves while retaining only permitted sanitized deletion evidence.

FR-025: Record source category, timestamp, sharing class, confirmation state, and confidence for every durable fact.

FR-026: Enforce sharing narrowing, revocation, expiry, derived lineage and source-version invalidation, mixed-owner authorization, downstream clearing, and external deletion-pending behavior.

FR-027: Degrade safely when optional memory or knowledge providers fail and never claim unavailable memory as known.

FR-028: Require authentication before a personal surface exposes private assistant content.

FR-029: Implement every deterministic shared-surface identity state, exact allowed payload, transition, downgrade, expiry, and private-content clearing outcome.

FR-030: Enforce authorization in backend services and provider-query construction, not only in client rendering.

FR-031: Prevent administrators from receiving another adult's private data solely because of role.

FR-032: Enforce adult, teen, and child policy, including unconditional denial of private teen disclosure outside exact owner-authorized privacy-filtered sharing and fail-closed policy transitions.

FR-033: Scope every API response containing personal information to authenticated identity and effective surface policy.

FR-034: Record denied private-resource access without recording protected content.

FR-035: Render the common capability set from one card and layout registry across five mock surface contexts, then support live mobile, desktop, and at least one shared display.

FR-036: Supply every surface with ownership, privacy, room where applicable, interaction capability, and viewing-distance context.

FR-037: Include assistant presence, Now, briefing, topics, and persistent text input in the personal default experience.

FR-038: Implement Now and Briefing as prioritized, explainable, correctable experiences rather than a raw notification feed.

FR-039: Make shared displays household-safe by default and return them to that state after personal-session expiry.

FR-040: Render only registered cards from validated layouts.

FR-041: Reject invalid configuration safely and retain the last valid layout.

FR-042: Build generated temporary views only from registered components and enforce ephemeral, topic, and pinned persistence lifecycles.

FR-043: Let users inspect why an item appeared, its source categories, confidence, sharing class, and corrections without exposing hidden reasoning or secrets.

FR-044: Ensure shared-display responses and payloads never receive private card data forbidden by effective policy.

FR-045: Support the defined proactive delivery levels while limiting Milestone C to calendar-change ambient or briefing delivery and keeping all later levels and categories disabled until authorized.

FR-046: Select the least disruptive permitted proactive level using versioned review opportunities, timezone-safe boundary rules, lower-confidence fallback, and privacy suppression.

FR-047: Enforce the Milestone D default cap for non-critical interruptions.

FR-048: Detect specified calendar changes and create an exception only when a supported overlap, transportation, attendee, or response-obligation predicate is satisfied.

FR-049: Explain a proactive item's category and level safely and provide correction on an authorized private surface, using handoff from shared displays.

FR-050: Limit Milestone D coordination requests to minimum-necessary data backed by complete, valid delegation metadata.

FR-051: Implement the deterministic coordination lifecycle, exact terminal states, revocation and expiry precedence, idempotency, concurrency rules, linked counters, and matching authorized views.

FR-052: Enforce the complete meaningful external-action policy for adult and minor principals, exact approval, delegation, expiry, unknown results, restart, and same-target concurrency.

FR-053: Produce the complete mandatory, correctly classified record sequence for every meaningful action attempt and every required principal, including blocked, cancelled, failed, timed-out, and unknown attempts.

FR-054: Filter activity only after record and view authorization, without leaking unauthorized records through counts, facets, empty states, or metadata.

FR-055: Let a person connect and disconnect a private person-owned calendar credential independently of assistant lifecycle.

FR-056: Read calendar events only within the connected account's granted scope.

FR-057: Detect calendar additions, removals, time, location, attendee, and cancellation changes.

FR-058: Retain provider event identity, observed version, observed time, and affected account for detected calendar changes.

FR-059: Keep private calendar details off shared surfaces and out of fallback context unless explicitly shared.

FR-060: Run calendar mutations through exact approval and activity, consume approval at submission, preserve unknown state, reconcile before retry, and reapprove changed proposals.

FR-061: Preserve local calendar configuration through reconnect while making stale or unavailable data visibly non-current and unusable for mutation.

FR-062: Keep Home Assistant authoritative for physical areas, devices, entities, services, and current state.

FR-063: Present Home Assistant state and actions in ordinary household language outside authorized technical views in Kinward Control.

FR-064: Distinguish observed device state, requested action, submitted action, and confirmed resulting state.

FR-065: Require a fresh matching Home Assistant observation before marking a mutation completed; otherwise report unknown.

FR-066: Apply identity, permission, freshness, approval, activity, and household-resource authority policy to Home Assistant actions.

FR-067: Degrade Home Assistant-dependent cards safely without blocking core use and preserve unconfirmed submitted actions as unknown until reconciliation.

FR-068: Keep Kinward Control separate from everyday assistant navigation.

FR-069: Let authorized administrators manage household people, invitations, assistants, child policy, household integrations, shared surfaces, proactive defaults, backup, and health with safe disablement semantics.

FR-070: Let adults manage their own integrations, memory, assistant preferences, and sharing without unrelated administrative access.

FR-071: Keep credentials, hidden prompts, unrestricted private adult content, and hidden reasoning out of administrative views.

FR-072: Distinguish core failure, optional degradation, intentional disablement, stale data, reauthorization need, and configuration error in health views.

FR-073: Give every degraded state an actionable next step or explicitly state that no action is needed.

FR-074: Create backups with a versioned manifest and complete included, excluded, protected, external, rebuildable, pending-observation, deletion, and unresolved-action blocking metadata.

FR-075: Restore to a clean same or compatible deployment only after presenting the point-in-time archive warning.

FR-076: Complete restore atomically or leave the existing valid household state unchanged.

FR-077: Verify the complete restored household graph, quarantine, ownership, account, observation, deletion, provider-reference, and unresolved-action contracts before activation.

FR-078: List every excluded integration credential as a required reauthorization task and keep account-recovery material separately classified.

FR-079: Use `001_initial_single_household` as the sole new schema origin with no executable legacy migration dependency; move legacy data only through controlled import.

FR-080: Require a restorable pre-upgrade backup and stop with actionable instructions when compatibility checks fail.

FR-081: Record backup and restore activity without secret material.

FR-082: Document and enforce retention for the named durable classes while deleting ephemeral, invalidated, expired security, and user-deleted content as specified.

FR-083: Implement the complete deletion-pending person lifecycle, including immediate authority shutdown, reconciliation-only access, persistent blockers, atomic final disposition, and sole-administrator protection.

FR-084: Classify authentication and recovery artifacts as portable or excluded, exclude integration credentials under the safe interim, and import only portable account-access material.

FR-085: Let an administrator securely recover access to the same restored administrator profile without database editing.

FR-086: Verify post-restore same-profile access recovery, owner reauthorization, quarantine, token invalidation, deletion restrictions, and unresolved-action blocking without unauthorized release.

FR-087: Apply requester-independent minor action policy, exact named-adult quorum, notice, minimum disclosure, serialized approval, and teen-owned sharing authorization to every action representing, targeting, or materially affecting a minor.

FR-088: Keep a minor's private conversation, prompt, and prepared message body out of adult memory and approval by default; permit only the narrowly noticed and authorized future exception defined by policy.

FR-089: Deliver and verify the inspectable delegation-record prerequisite and deny invalid exchanges before any future specialist invocation or inter-assistant delegation can be enabled.

FR-090: Implement the full pending inferred-observation lifecycle: ownership, inspection-only use, correction, confirmation, rejection, fixed expiry, dependency invalidation, recurrence suppression, backup, and restore.

FR-091: Support optional no-account pet profiles with only explicit household-shared care and relationship facts and no assistant, credentials, private memory, approval, delegation, or authority.

FR-092: Require inspectable purpose-specific calendar and transportation recipient assignments and fail closed with a safe configuration-gap notice when no valid recipient exists.

FR-093: Enforce owner-controlled primary-assistant disablement, deletion, same-owner replacement, content and work disposition, grant revocation, credential preservation, and no cross-person transfer.

FR-094: Pass the complete authenticated-minor UJ-7 flow and its approval, expiry, cancellation, quorum, privacy, activity, and unconditional teen-denial branches.

FR-095: Apply versioned category policy and general multi-principal authority to direct household-owned actions, including Home Assistant, without role-derived request or approval authority.

FR-096: Pass the complete Milestone D UJ-10 coordination, generated-view, proactive correction, and bounded autonomous-action fixture without enabling specialist assistants.

FR-097: Implement current-administrator joint management and fail-closed conflict resolution for direct household-authored content in active and restored states.

FR-098: Atomically import the documented five-class minimum household data set through a versioned allowlist, with complete graph validation, duplicate handling, quarantine, disallowed-state rejection, safe reporting, and rollback.

FR-099: Implement intended-person, single-use private-device handoff with the exact neutral pre-auth payload, current authorization re-evaluation, fixed terminal outcomes, and no private existence leakage.

FR-100: Implement the general multi-principal approval object, explicit quorum, affected-principal approvals, serialized responses, deterministic precedence, invalidation, and exactly-once transition to acting.

### NonFunctional Requirements

NFR-001: Enforce server-side authorization for every private resource and provider query.

NFR-002: Protect secrets and credentials at rest and exclude them from normal responses and logs.

NFR-003: Automate tests for every shared-surface identity state and transition.

NFR-004: Automate adult, teen, child, administrator, personal-assistant, and fallback boundaries, plus the specialist ownership/delegation prerequisite before specialist enablement.

NFR-005: Treat external content as untrusted and unable to override authorization, system policy, or action authority.

NFR-006: Minimize data sent to external providers to the permitted task.

NFR-007: Make authentication, invitation, approval, and handoff tokens expiring and replay-resistant; make handoff references single-use and terminally invalidated.

NFR-008: Exclude full private prompts, conversation bodies, credentials, and unrestricted integration payloads from normal logs and telemetry.

NFR-009: Produce append-protected records for every security-sensitive configuration change and mandatory activity or deletion disposition, with complete-population integrity evidence.

NFR-010: Degrade each unavailable optional capability separately without representing stale data as current or blocking milestone-available core behavior.

NFR-011: Apply explicit timeouts, bounded retries, and failure isolation to external calls.

NFR-012: Use provider idempotency controls where available; otherwise block retries and same-target execution until an unconfirmed attempt is reconciled.

NFR-013: Pass the complete clean-deployment restore and quarantine contract before the first usable release.

NFR-014: Demonstrate zero known loss of included backup data and zero unauthorized release of restored quarantined data.

NFR-015: Preserve in-progress and unknown action, deletion overlay, and reconciliation blockers truthfully across restart, backup, restore, abandonment, and resumption.

NFR-016: Make background jobs observable, retry-bounded, recoverable, and free of duplicate user-visible outcomes.

NFR-017: Make cached personal-home content interactive within 2 seconds p95 and cold loads within 4 seconds p95 on the reference deployment.

NFR-018: Show accepted or responding state within 500 ms p95 after assistant request submission.

NFR-019: Show first visible streamed response content within 3 seconds p95 outside documented provider outages.

NFR-020: Invalidate private fetch authorization immediately on identity downgrade and clear shared-display private content within the specified 250 ms/1 second fail-closed bounds.

NFR-021: Complete local-only API reads and writes within 500 ms p95 under reference load.

NFR-022: Return shared displays to household-safe state within 1 second of session-expiry detection.

NFR-023: Meet applicable WCAG 2.2 AA requirements in core web/PWA experiences.

NFR-024: Meet the fixed shared-display size, viewing-distance, target-size, spacing, contrast, text-size, scaling, and inspection requirements at 100% and 200% text scale.

NFR-025: Support keyboard-only completion of onboarding, conversation, topic continuation, approval, and basic Kinward Control.

NFR-026: Never rely on color alone to communicate status.

NFR-027: Use household language and require no infrastructure or provider terminology in ordinary workflows.

NFR-028: Explain consequences before destructive actions, privacy-sharing changes, and external mutations are confirmed.

NFR-029: Keep model, memory, knowledge, calendar, email, and smart-home capability interfaces provider-neutral.

NFR-030: Version cards, layouts, policies, schemas, provider references, and backup manifests for migration.

NFR-031: Require automated or inspectable validation gates for Milestone A foundation and Milestone B/C requirements.

NFR-032: Use only fictional or synthetic data in public repository fixtures and examples.

NFR-033: Keep current documentation separate from archived Homefront SaaS and routine-centric artifacts.

NFR-034: Report health separately for application, database, model, memory, knowledge, calendar, Home Assistant, background work, and backup capabilities.

NFR-035: Correlate a visible failed action with sanitized activity and operational events without exposing private content.

NFR-036: Measure request/provider latency, provider failure, action result, job backlog, privacy denial, and backup result without high-cardinality private labels.

NFR-037: Produce an allowlisted sanitized diagnostic bundle with health, versions, capability states, and opaque correlations only.

NFR-038: Export or restore private/recovery-bearing backups only after confidentiality and integrity protection is established and verified, with scoped consequence notices.

NFR-039: Gate Milestones C and D on the frozen, versioned, hashed evidence catalog and complete signed defect/evidence pack, without waiver of automatic blockers.

NFR-040: From a clean checkout, make the unmodified default `docker compose up` start a healthy core stack without optional providers while reporting dependent capabilities safely degraded or disabled.

### Additional Requirements

- Use a hexagonal modular monolith: framework-free domain modules and application ports inward; API, persistence, worker, crypto, archive, and provider adapters depend inward.
- One deployable backend owns all household state and policy; do not introduce internal microservices or distributed policy ownership.
- Preserve the existing brownfield repository as the starter substrate rather than adopting a new starter template; Milestone A must make the current skeleton compliant.
- Use one single-household domain model with no tenant identifier or global cross-household query path; use UUID entity IDs, UTC persistence, and one configured IANA household timezone.
- Use `001_initial_single_household` as the baseline schema origin; complete it before the Milestone A evidence freeze, then use forward-only migrations.
- Make SQLite 3 the required default and PostgreSQL 17 an optional profile that cannot be advertised until the same transaction and behavior suite passes on both.
- Remove Redis from required topology and implement durable SQL jobs/outbox with bounded leases, retries, idempotent handlers, and preserved unknown mutations.
- Route every mutation through handler, application service, policy, unit of work, domain/persistence, and transactional outbox/activity; routes, renderers, models, workers, and adapters must not write directly.
- Require an immutable `AccessContext` on protected application, repository, and provider ports and authorize before query construction and again before serialization.
- Use canonical protected-data metadata for owner, data class, item version, audience policy/grant, and exact lineage for every derived item.
- Keep Kinward SQL authoritative for topics, conversations, policies, actions, activity, jobs, layouts, and backup metadata; optional memory/knowledge services are projections or retrieval adapters only.
- Provide versioned REST JSON under `/api/v1` and ordered typed SSE progress with exactly one truthful terminal event; cancellation is an application command.
- Make backend Pydantic/OpenAPI the API authority and generate TypeScript client contracts; reserve `packages/schemas` for explicitly shared client layout/card/configuration schemas.
- Keep API/SSE evolution additive within a major version; fail closed on unknown major versions, required enums, or terminal semantics and cover compatibility with fixtures.
- Use provider-neutral assistant orchestration that receives minimized policy-filtered context and treats model/tool output as untrusted typed proposals.
- Support a no-model local path for authentication, topics, configuration, Kinward Control, backup, and truthful capability health.
- Use local Argon2id-equivalent password authentication, opaque server-side sessions in secure cookies, explicit CSRF defense, and one-time hashed revocable invitation/recovery capabilities.
- Keep external OIDC unavailable in current scope.
- Implement one persisted meaningful-action state machine with immutable attempts, optimistic versions, canonical namespaced conflict keys, database-enforced same-target locking, exact approval, and reconciliation.
- Preserve unknown action attempts across restart, backup, restore, account transition, assistant lifecycle, and deletion; never retry automatically or unblock same-target work before reconciliation.
- Keep Home Assistant authoritative for physical state; service-call success is only submitted, and completion requires a fresh matching observation.
- Normalize calendar identity, version, observed UTC time, capability, and freshness behind an outbound port; stale state blocks current-change claims and mutations.
- Encrypt provider credentials with application envelope encryption using a deployment key outside the database; exclude secrets from images and source.
- Implement backup with a coordinated mutation/worker barrier or transactionally consistent checkpoint and store archives outside the live database volume.
- Stage restore as a whole-authority replacement, validate it in isolation, quarantine protected content, and activate atomically rather than merging into live state.
- Make activity envelopes append-protected, transactionally coupled to state/outbox, separately classify protected details, and integrity-chain envelopes with a key outside the database.
- Sanitize logs, traces, metrics, health, and diagnostic bundles by construction; prohibit prompts, protected bodies, secrets, provider payloads, and protected high-cardinality labels.
- Use audience-scoped, short-lived shared-display grants; passive sensing cannot create verified authority, and private payloads must never persist in shared-browser storage.
- Implement private-device handoff as a separate opaque, expiring, one-use reference with destination reauthorization and only the five specified terminal outcomes.
- Use registered cards with server-produced policy-filtered view models and versioned declarative layouts resolved in the fixed order: surface, person+surface, room+surface, household profile, product default.
- Keep Assistant Experience and Kinward Control in separate route shells and navigation families, while allowing shared tokens and primitives.
- Serve production web and API same-origin behind one ingress; run one one-shot migration container before API/worker readiness; use the same backend image for API and worker.
- Keep model, memory, knowledge, calendar, and Home Assistant providers optional, with explicit capability, health, freshness, timeout, and safe-retry contracts.
- Apply the salvage rule to every retained subsystem: document current behavior, remove SaaS/multi-tenant assumptions, define Kinward contracts, move the smallest implementation, rewrite focused tests, and pass public-repository safety review.
- Align manifests and lockfiles to the adopted compatibility lines without silently upgrading: Node 22, pnpm 10.13.1, React 19.x, TypeScript 5.7.x, Vite 6.1.x, Zod 4.4.3, Python 3.12, FastAPI 0.115.x, SQLAlchemy 2.0.x, Alembic 1.x, SQLite 3, and optional PostgreSQL 17.
- Validate domain state machines, application policy/order, adapter contracts, dual-database semantics, privacy matrices, API compatibility, five-context Playwright flows, backup/import, WCAG 2.2 AA, performance, and public-repository safety.
- Freeze the exact Milestone C reference host, browser, display, load, and network evidence catalog before performance/accessibility acceptance.
- Carry open decisions into stories by ID with their safe interim behavior; stories must not silently decide deferred mechanisms or broaden product scope.
- Keep all PRD Section 4.3 horizons out of epics and stories until a future PRD and architecture amendment explicitly authorizes decomposition.

### UX Design Requirements

UX-DR1: Implement a calm, warm, restrained visual foundation with assistant presence that avoids default humanoid avatars and uses functional, interruptible, reduced-motion-aware state cues.

UX-DR2: Keep Assistant Experience and Kinward Control visually, navigationally, and informationally distinct.

UX-DR3: Implement the common registered capability set: Assistant Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Assistant Input.

UX-DR4: Render the common capability set through one card registry and one layout registry across personal mobile, personal tablet, personal desktop, shared kitchen, and shared living-room mock contexts.

UX-DR5: Adapt layouts, density, type scale, touch targets, visibility, and navigation from explicit surface ownership, privacy, room, interaction capability, and viewing distance.

UX-DR6: Make personal mobile prioritize assistant presence, one dominant Now item, a quiet three-item default briefing, Continue topics, persistent text input, and minimal navigation.

UX-DR7: Make personal desktop support persistent navigation, an adaptive canvas, persistent assistant input, topic/workspace continuity, and authorized Kinward Control access.

UX-DR8: Make shared displays ambient and household-safe by default, readable at room distance, shallow in navigation, and automatically returning to ambient state.

UX-DR9: Ensure private shared-display content disappears promptly on identity downgrade, uncertainty, disconnection, or session expiry and is never persisted in browser storage or caches.

UX-DR10: Offer a neutral, single-use private-device handoff when shared-display privacy blocks disclosure, without exposing a person, topic, source, or private-record existence before authentication.

UX-DR11: Implement Now with at most one dominant useful item, a concise reason it matters, and one primary action; allow it to disappear when nothing is useful.

UX-DR12: Implement Briefing as prioritized meaning rather than a notification feed, with source category, recency, scope, required action, correction/dismissal, grouping, and visible uncertainty.

UX-DR13: Represent continuing work as durable topics rather than raw chat sessions and preserve current decisions, unresolved questions, progress, and authorized context across surfaces.

UX-DR14: Keep persistent assistant input text-only in committed scope and never imply microphone, camera, screenshot, file, current-screen, selection, app, or ambient-device context.

UX-DR15: Provide registered cards with declared type/version, supported surfaces, view-model schema, renderer, sizing, and capabilities; never execute arbitrary generated client code.

UX-DR16: Validate versioned declarative layouts, reject unknown/invalid active configuration safely, preserve the last valid version, and keep built-in defaults available.

UX-DR17: Resolve layouts deterministically in the architecture-defined precedence order and allow card visibility only to narrow already-authorized server view models.

UX-DR18: Implement generated-view ephemeral, topic, and pinned dispositions using registered components only, including deletion of ephemeral state on normal or abnormal session end.

UX-DR19: Provide explainability showing why an item appeared, what changed, source categories, confidence/uncertainty, sharing class, relevant permission, and corrections without revealing chain-of-thought, prompts, credentials, or secrets.

UX-DR20: Present request and action progress with visibly distinct accepted, understanding, responding, awaiting approval, acting, submitted, completed, cancelled, uncertain/unknown, and failed states; never equate acting or submission with completion.

UX-DR21: Present exact approval consequences, affected principals, expiry, reversibility, and minimum-necessary decision fields before confirmation.

UX-DR22: Present Home Assistant resources in ordinary room/device/state/action language on everyday surfaces and confine raw entities, services, mappings, and provider syntax to authorized Kinward Control views.

UX-DR23: Provide a plain-language, authorization-filtered Activity experience that explains what happened, who requested/acted where authorized, why it was allowed, service category, result, and undo availability.

UX-DR24: Provide Kinward Control views for people, assistants, privacy/policy, integrations, shared surfaces, activity, backup, capability health, and sanitized diagnostics without exposing private bodies or secrets.

UX-DR25: Show every degraded or stale capability distinctly with an actionable next step or an explicit statement that none is required, while keeping unaffected core workflows usable.

UX-DR26: Meet WCAG 2.2 AA with keyboard operation, screen-reader semantics, large touch targets, reduced motion, contrast, 200% text scaling, non-color states, clear focus, timeout warning, and shared-display distance readability.

UX-DR27: Use direct, calm, brief, ordinary household language; avoid infrastructure/provider terminology, surveillance framing, infantilizing teen language, false certainty, and nagging.

UX-DR28: Keep one dominant decision at a time, limit notification density, preserve context, and let users request simpler explanations.

UX-DR29: Provide polished defaults and useful initial surfaces without requiring routines, card/layout configuration, Home Assistant, or technical administration.

UX-DR30: In Milestone D, present coordination requests with minimum-necessary context and Accept, Decline, and Counter actions plus accurate terminal closure for both authorized participants.

### FR Coverage Map

FR-001: Epic 1 - One household per deployment.
FR-002: Epic 1 - Atomic initial household bootstrap.
FR-003: Epic 3 - Pre-account adult and minor profiles.
FR-004: Epic 3 - Non-technical initial onboarding.
FR-005: Epic 3 - Invitation binding to existing profiles.
FR-006: Epic 3 - Single-use invitation lifecycle.
FR-007: Epic 3 (lead), Epic 6 (action-state closure) - Account, role, privacy, ownership, and authority transitions.
FR-008: Epic 3 - Authorized profile corrections and binding safety.
FR-009: Epic 2 - Exactly one primary personal assistant.
FR-010: Epic 2 - Single-owner assistant boundary.
FR-011: Epic 1 - Household fallback assistant foundation.
FR-012: Epic 3 - Assistant personality and interaction interview.
FR-013: Epic 2 - Truthful assistant request lifecycle.
FR-014: Epic 2 - Authorization-bound conversation continuity.
FR-015: Epic 2 - Mobile-to-desktop topic continuation.
FR-016: Epic 4 - Topic lifecycle and sharing management.
FR-017: Epic 2 - Cancellation and unsubmitted-action prevention.
FR-018: Epic 2 - Person-owned personal memory.
FR-019: Epic 4 - Separate household-shared facts.
FR-020: Epic 4 - Fallback exclusion from private memory.
FR-021: Epic 2 - Permission-bound context assembly.
FR-022: Epic 4 - Knowledge-state and sharing-class inspection.
FR-023: Epic 4 - Confirmation before durable-fact promotion.
FR-024: Epic 4 - Personal durable-fact management.
FR-025: Epic 4 - Durable-fact metadata.
FR-026: Epic 4 - Sharing, lineage, invalidation, and external deletion.
FR-027: Epic 2 - Safe optional-memory degradation.
FR-028: Epic 2 - Personal-surface authentication.
FR-029: Epic 5 - Deterministic shared-surface identity policy.
FR-030: Epic 2 - Backend and provider-query authorization.
FR-031: Epic 3 - No role-derived adult private access.
FR-032: Epic 4 - Teen and child privacy policy.
FR-033: Epic 2 - Identity- and surface-scoped API responses.
FR-034: Epic 8 - Sanitized denied-access records.
FR-035: Epic 1 - Five-context mock foundation and live-surface baseline.
FR-036: Epic 1 - Complete surface context.
FR-037: Epic 2 - Personal default assistant experience.
FR-038: Epic 6 - Now and Briefing behavior.
FR-039: Epic 2 - Household-safe shared-display default.
FR-040: Epic 1 - Registered cards and validated layouts.
FR-041: Epic 1 - Last-valid layout fallback.
FR-042: Epic 10 - Generated-view persistence dispositions.
FR-043: Epic 2 - Safe item explanation and correction.
FR-044: Epic 2 - Private-data absence from shared payloads.
FR-045: Epic 6 - Milestone-scoped proactive levels.
FR-046: Epic 6 - Least-disruptive review-opportunity selection.
FR-047: Epic 10 - Non-critical interruption cap.
FR-048: Epic 6 - Calendar-change exception predicates.
FR-049: Epic 6 - Proactive explanation and correction.
FR-050: Epic 10 - Minimum-necessary coordination requests.
FR-051: Epic 10 - Deterministic coordination closure.
FR-052: Epic 6 - Complete meaningful-action policy.
FR-053: Epic 6 - Mandatory classified action records.
FR-054: Epic 6 - Authorization-safe activity filtering.
FR-055: Epic 6 - Person-owned calendar credentials.
FR-056: Epic 6 - Granted-scope calendar reads.
FR-057: Epic 6 - Calendar change detection.
FR-058: Epic 6 - Calendar identity and freshness evidence.
FR-059: Epic 6 - Calendar privacy on shared surfaces.
FR-060: Epic 6 - Exact calendar mutation and reconciliation.
FR-061: Epic 6 - Calendar reconnect and stale-state behavior.
FR-062: Epic 7 - Home Assistant physical-state authority.
FR-063: Epic 7 - Household-language smart-home UX.
FR-064: Epic 7 - Observed/requested/submitted/confirmed states.
FR-065: Epic 7 - Observation-confirmed mutation outcomes.
FR-066: Epic 7 - Authorized Home Assistant actions.
FR-067: Epic 7 - Home Assistant degradation and reconciliation.
FR-068: Epic 8 - Separate Kinward Control experience.
FR-069: Epic 8 - Authorized household administration.
FR-070: Epic 8 - Adult self-management without unrelated admin access.
FR-071: Epic 8 - Private-data exclusion from administration.
FR-072: Epic 8 - Granular health states.
FR-073: Epic 8 - Actionable degraded-state guidance.
FR-074: Epic 9 - Complete versioned backup manifest.
FR-075: Epic 9 - Compatible clean restore with warning.
FR-076: Epic 9 - Atomic restore activation.
FR-077: Epic 9 - Complete post-restore verification.
FR-078: Epic 9 - Credential reauthorization tasks.
FR-079: Epic 1 - New baseline migration origin.
FR-080: Epic 9 - Pre-upgrade backup and compatibility stop.
FR-081: Epic 9 - Secret-free backup/restore activity.
FR-082: Epic 4 - Explicit retention and deletion contract.
FR-083: Epic 3 (lead), Epic 6 (action-state closure), Epic 9 (backup/restore closure) - Person deletion-pending lifecycle.
FR-084: Epic 9 - Portable and excluded recovery artifacts.
FR-085: Epic 9 - Same-profile administrator recovery.
FR-086: Epic 9 - Secure restored-member re-access and quarantine.
FR-087: Epic 6 - Requester-independent minor approval policy.
FR-088: Epic 6 - Minor conversation and body privacy.
FR-089: Epic 10 - Specialist delegation prerequisite boundary.
FR-090: Epic 4 - Pending inferred-observation lifecycle.
FR-091: Epic 3 - Bounded optional pet profiles.
FR-092: Epic 6 - Calendar and transportation recipient assignment.
FR-093: Epic 3 (lead), Epic 6 (action-state closure) - Owner-controlled assistant lifecycle.
FR-094: Epic 6 - Authenticated-minor end-to-end acceptance.
FR-095: Epic 7 - Household-resource multi-principal authority.
FR-096: Epic 10 - Milestone D journey closure.
FR-097: Epic 4 - Direct household-authored content lifecycle.
FR-098: Epic 9 - Controlled atomic household-data import.
FR-099: Epic 5 - Single-use private-device handoff.
FR-100: Epic 6 - General multi-principal approval lifecycle.

## Epic Execution Guardrails

- Each epic must be complete and usable against all capabilities delivered through that epic. Later epics may add explicitly mapped integration closure but must not repair an omitted earlier acceptance condition.
- Every story must identify its applicable FRs, NFRs, UX-DRs, architecture constraints, open AD/PD safe interims, milestone, verification methods, and evidence owners.
- Every NFR and UX-DR must map to at least one story, and cross-cutting requirements must map to every story whose behavior they constrain.
- Open AD/PD records retain their documented safe interim. A story may implement the interim but must not silently resolve or broaden the decision.
- Epic 1 bootstrap must have a one-time, fail-closed setup boundary, become unavailable after successful commit, and remain usable without optional providers. Full ongoing account and session behavior remains in Epic 2.
- Epic 6 must be decomposed into vertical user outcomes. No story may deliver only an action framework, generic policy layer, database schema, or provider adapter without an independently testable user-visible outcome.
- Changes to the draft PRD or architecture require checking stable requirement IDs, affected epic mappings, cross-epic closure, and story acceptance criteria before implementation continues.
- Epic numbering expresses capability dependency, not mandatory team serialization. Stories may proceed in parallel only when their required predecessor contracts are stable and they do not depend on unfinished future behavior.
- Every story introducing persisted state must define backup inclusion or exclusion, restore and quarantine behavior, retention and deletion disposition, import eligibility, ownership and classification, and unresolved-action implications as applicable. Epic 9 delivers household-facing recovery workflows and end-to-end verification rather than retrofitting recovery semantics.
- A cross-epic FR is complete only after its lead capability and every named closure have passed their mapped verification. Status reporting must distinguish lead completion from final requirement completion.
- Accessibility, privacy, performance, observability, dual-database, degraded-mode, and public-repository safety evidence must be collected incrementally in applicable stories. Milestone gates aggregate this evidence and do not defer its creation.
- Epic 6 must expose independently demonstrable vertical checkpoints so Calendar read value, change awareness, approval, mutation, reconciliation, activity, and lifecycle closure can be validated before the entire epic closes.

## Epic List

### Epic 1: A Reliable Kinward Home

Household owners can start a clean, single-household Kinward deployment and see polished, adaptive foundations across all five mock surface contexts.

**FRs covered:** FR-001, FR-002, FR-011, FR-035, FR-036, FR-040, FR-041, FR-079

### Epic 2: A Private Assistant That Continues Across Surfaces

A person can authenticate, ask by text, receive truthful incremental progress, persist a topic, continue on desktop, and see only safe shared-display representations.

**FRs covered:** FR-009, FR-010, FR-013, FR-014, FR-015, FR-017, FR-018, FR-021, FR-027, FR-028, FR-030, FR-033, FR-037, FR-039, FR-043, FR-044

### Epic 3: Household Membership and Personal Assistant Ownership

A household can onboard additional people and pets, manage account and role lifecycles, personalize each primary assistant, correct permitted profile data, and safely delete people or assistants.

**FRs covered:** FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-012, FR-031, FR-083, FR-091, FR-093

### Epic 4: Trusted Household Knowledge and Privacy

People can manage topics, durable facts, inferred observations, sharing, child and teen privacy, retention, and direct household-authored content with lineage-aware invalidation.

**FRs covered:** FR-016, FR-019, FR-020, FR-022, FR-023, FR-024, FR-025, FR-026, FR-032, FR-082, FR-090, FR-097

### Epic 5: Privacy-Safe Shared Display and Personal Handoff

Household members can use a conservative shared display, enter and leave verified states safely, and continue blocked private interactions on the intended personal device.

**FRs covered:** FR-029, FR-099

### Epic 6: Calendar Awareness and Accountable Action

People can connect private calendars, receive useful calendar-change exceptions at the least disruptive level, assign appropriate recipients, and complete the first real meaningful-action flow through exact, minimum-necessary approval, truthful mutation state, deterministic multi-principal decisions, authorized activity, and unknown-result reconciliation. Account, person-deletion, and assistant-lifecycle transitions preserve or block action state correctly.

**FRs covered:** FR-007 (action-state closure), FR-038, FR-045, FR-046, FR-048, FR-049, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058, FR-059, FR-060, FR-061, FR-083 (action-state closure), FR-087, FR-088, FR-092, FR-093 (action-state closure), FR-094, FR-100

### Epic 7: Safe Household Control Through Home Assistant

Household members can inspect and request physical-state changes in ordinary language while Home Assistant remains authoritative and uncertain results remain blocked for reconciliation.

**FRs covered:** FR-062, FR-063, FR-064, FR-065, FR-066, FR-067, FR-095

### Epic 8: Personal Settings and Operable Kinward Control

Adults can manage their own integrations, memory, assistant preferences, and sharing through personal settings, while authorized administrators can operate Kinward Control, inspect capability health, understand degraded states, and correlate safe operational evidence without exposing private content. Personal settings and Kinward Control remain separate route shells and navigation families.

**FRs covered:** FR-034, FR-068, FR-069, FR-070, FR-071, FR-072, FR-073

### Epic 9: Household-Owned Backup, Restore, Upgrade, and Import

Administrators can protect, verify, restore, recover access to, upgrade, and selectively import household data without partial activation, secret leakage, authority rebinding, unauthorized content release, or loss of a deletion-pending overlay and its reconciliation blockers.

**FRs covered:** FR-074, FR-075, FR-076, FR-077, FR-078, FR-080, FR-081, FR-083 (backup/restore closure), FR-084, FR-085, FR-086, FR-098

### Epic 10: Coordinated and Bounded Proactivity

Household members can coordinate requests to visible closure, use generated views with explicit persistence, receive bounded nudges and interruption behavior, and inspect autonomous-action consequences without enabling specialist assistants.

**FRs covered:** FR-042, FR-047, FR-050, FR-051, FR-089, FR-096

## Epic 1: A Reliable Kinward Home

Household owners can start a clean, single-household Kinward deployment and see polished, adaptive foundations across all five mock surface contexts.

### Story 1.1: Start a Healthy Core Deployment

As a household operator,
I want Kinward's core stack to start from a clean checkout without optional providers,
So that I can operate a reliable private household deployment without infrastructure expertise.

**Acceptance Criteria:**

**Given** a clean checkout with the documented default configuration
**When** the operator runs the unmodified documented `docker compose up` command
**Then** the migration runner, core web/API, worker, and default SQLite database start successfully
**And** the core stack reaches documented healthy states without manual database editing or additional setup commands.

**Given** a clean empty database
**When** the one-shot migration runner executes
**Then** it applies `001_initial_single_household` directly as the schema origin
**And** it does not execute, copy, import, or depend on the retired legacy migration chain
**And** API and worker readiness wait for successful migration completion
**And** neither the API nor worker runs migrations during normal startup.

**Given** the default Compose configuration
**When** the service and profile inventory is inspected
**Then** SQLite is the selected database
**And** PostgreSQL, memory, knowledge, observability, and development services are opt-in only
**And** Redis is neither started nor required
**And** absent optional services do not cause a core health failure.

**Given** no model, memory, knowledge, calendar, or Home Assistant provider is configured
**When** health and locally available smoke checks run
**Then** application, database, migration compatibility, bootstrap availability, worker/outbox readiness, and local health paths report healthy
**And** provider-dependent capabilities report `degraded`, `unavailable`, or `intentionally-disabled` separately
**And** the system does not claim unavailable provider data or capabilities are current.

**Given** the adopted compatibility lines in the architecture
**When** manifests and lockfiles are validated
**Then** they are reproducible and aligned with the adopted Node, pnpm, React, TypeScript, Vite, Zod, Python, FastAPI, SQLAlchemy, Alembic, SQLite, and optional PostgreSQL lines
**And** this story does not silently upgrade those lines.

**Given** the running clean-checkout stack
**When** containers or processes restart within the documented recovery behavior
**Then** committed schema state remains valid
**And** startup does not create duplicate migration effects or require manual repair
**And** exit, restart, health-probe, service inventory, optional-provider absence, and core smoke-check evidence is captured for the Milestone A gate.

**Given** any retained deployment, backend, frontend, or integration infrastructure used by this story
**When** its implementation is accepted
**Then** its useful behavior is documented, SaaS and multi-tenant assumptions are absent, its Kinward contract is explicit, focused checks pass, and only the smallest useful implementation is retained
**And** fixtures, examples, logs, configuration, and evidence contain only fictional or synthetic values and no secrets or deployment-specific private identifiers.

This story addresses `FR-001`, `FR-079`, `NFR-010`, `NFR-029`, `NFR-031–NFR-033`, `NFR-040`, and the deployment, migration, salvage, and public-safety architecture constraints.

### Story 1.2: Establish the Household Atomically

As the initial household administrator,
I want to establish my household and its foundational profiles and assistants in one secure operation,
So that Kinward never presents a partial, duplicated, or ambiguously owned household as usable.

**Acceptance Criteria:**

**Given** a clean deployment with no household record
**When** the setup experience is opened locally
**Then** Kinward exposes one fail-closed bootstrap path for creating the first household
**And** the path requires an explicit one-time setup authorization and CSRF protection for state-changing requests
**And** it does not require a model, memory, knowledge, calendar, Home Assistant, or other optional provider.

**Given** the initial administrator supplies the household name, their profile and account credentials, a primary-assistant name, and any selected adult, child, or pet profiles
**When** bootstrap is submitted
**Then** one application command creates exactly one household, the administrator profile, account binding, primary personal assistant, household fallback assistant, and every selected profile in one transaction
**And** the primary personal assistant is owned only by the administrator
**And** the fallback assistant is household-owned with no personal owner
**And** no tenant identifier, SaaS control-plane object, entitlement, billing, support-access, or routine object is created.

**Given** a selected pet profile
**When** bootstrap commits
**Then** the pet is created without an account, assistant, private memory, credential, approval role, delegation right, or action authority
**And** only explicitly entered household-shared care or relationship facts are eligible for storage.

**Given** an exact bootstrap request is submitted more than once with the same idempotency identity
**When** duplicate requests are processed sequentially or concurrently
**Then** only one household and one of each selected profile, binding, primary assistant, and fallback assistant exists
**And** every exact duplicate receives the prior committed result
**And** conflicting reuse of the idempotency identity fails without modifying committed state.

**Given** any validation, policy, persistence, or transaction failure occurs before commit
**When** bootstrap terminates
**Then** no partial household is presented as usable
**And** no orphan profile, account binding, assistant, selected relationship, or setup authorization remains active
**And** the user receives a household-safe result stating whether setup may be retried or requires reset or restore.

**Given** bootstrap has committed successfully
**When** any client attempts to use the setup path again
**Then** the server rejects creation of a second household
**And** the one-time setup authorization is consumed or terminally invalidated
**And** ordinary health and bootstrap-status responses reveal no credential, verifier, private profile field, or reusable setup capability.

**Given** bootstrap creates credentials and protected household records
**When** persistence and operational output are inspected
**Then** credential verifiers use the adopted Argon2id-equivalent local-authentication mechanism and plaintext credentials are never stored or logged
**And** every mutation follows the application-command, policy, unit-of-work, persistence, and transactional activity path
**And** each created record has explicit household-local ownership, classification, version, backup inclusion or exclusion, restore disposition, retention behavior, and import eligibility.

**Given** a keyboard-only administrator using ordinary household language
**When** they complete bootstrap with fictional fixture data
**Then** every field, validation error, retry outcome, and completion state is operable without infrastructure terminology
**And** no integration, room, device, routine, detailed schedule, notification rule, or layout configuration is required.

This story addresses `FR-001`, `FR-002`, `FR-011`, the bootstrap portion of `FR-091`, `NFR-002`, `NFR-007`, `NFR-025`, `NFR-027`, `NFR-030`, `NFR-032`, `NFR-040`, `UX-DR29`, and `AD-01`, `AD-17`, `AD-19`, `AD-23`, and `AD-24`.

### Story 1.3: Render the Common Registered Card Set

As a household member,
I want Kinward's common assistant capabilities to render through consistent registered cards,
So that every supported surface can present familiar information without arbitrary generated UI or provider-specific behavior.

**Acceptance Criteria:**

**Given** the frontend foundation
**When** the card registry is inspected
**Then** it contains versioned registrations for Assistant Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Assistant Input
**And** each registration declares its type, version, supported surface classes, view-model schema, renderer, sizing constraints, and supported capabilities.

**Given** a registered card receives a valid synthetic view model
**When** it renders
**Then** it consumes only that policy-filtered view model
**And** it does not query a provider, persistence adapter, or protected API directly
**And** it does not make an authorization or data-classification decision in the renderer.

**Given** synthetic fixtures for available, empty, loading, degraded, unavailable, stale, and error states
**When** each common card renders those states
**Then** the visible result uses direct household language
**And** uncertainty and capability status are explicit
**And** status does not rely on color alone
**And** degraded or unavailable states never fabricate data or completion.

**Given** the Assistant Input card in committed scope
**When** its capabilities and controls render
**Then** text input is available
**And** microphone, camera, screenshot, file, current-screen, selected-object, application, ambient-device, and context-targeted input are absent and not advertised as active.

**Given** the Approval card
**When** a synthetic prepared action is displayed
**Then** it can represent target, proposed effect, consequence, expiry, reversibility, required decision, and truthful action state
**And** `acting`, `submitted`, `unknown`, `completed`, `failed`, and `cancelled` are visually and semantically distinguishable.

**Given** the common card renderers
**When** keyboard, screen-reader, reduced-motion, high-contrast, and text-scaling checks run
**Then** each renderer has semantic structure, visible focus, non-color status, reduced-motion behavior, and no essential clipping or lost function at 200% text scale.

**Given** any model-produced content or generated view declaration
**When** the client resolves a card type
**Then** only a registered type with a valid versioned view model may render
**And** arbitrary JavaScript, React code, HTML execution, or provider-native payload rendering is rejected.

**Given** the shared schemas and API contract boundaries
**When** card contracts are validated
**Then** client card and configuration schemas remain in `packages/schemas`
**And** backend API view models remain authoritative through Pydantic/OpenAPI-generated client contracts
**And** no Python domain model is manually duplicated as a TypeScript authority.

**Given** public fixtures and visual evidence
**When** card states are tested or captured
**Then** all names, schedules, topics, locations, and household details are obviously fictional
**And** no secrets, internal endpoints, or deployment-specific identifiers appear.

This story addresses `FR-035`, `FR-040`, `NFR-023`, `NFR-026`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR1`, `UX-DR3`, `UX-DR14`, `UX-DR15`, `UX-DR20`, `UX-DR21`, `UX-DR25–UX-DR27`, and `AD-21–AD-22`.

### Story 1.4: Resolve Validated Layouts Safely

As a household member,
I want Kinward to choose a valid layout for my current surface and context,
So that information appears appropriately without invalid configuration breaking the experience or broadening access.

**Acceptance Criteria:**

**Given** a declarative layout definition
**When** it is parsed
**Then** its schema version, layout identity, surface class, grid, card instances, sizing, and configuration are validated through the versioned shared layout schema
**And** every referenced card type and version must exist in the card registry
**And** arbitrary executable client code is rejected.

**Given** multiple valid layout assignments could apply
**When** the resolver selects a layout
**Then** it uses the fixed precedence of explicit surface assignment, person plus surface, room plus surface, household surface profile, and immutable product default
**And** the selected result is deterministic for the same inputs
**And** resolution records the applicable layout and context versions for inspection.

**Given** a surface is resolved
**When** its context is assembled
**Then** the context includes surface class, owner, privacy, optional room, touch/keyboard capability, and viewing distance
**And** no authority is inferred from a client-supplied person, room, or surface identifier alone.

**Given** a valid layout references a registered card
**When** visibility is evaluated
**Then** visibility may narrow based on already-authorized view-model availability and safe surface capabilities
**And** the client cannot use layout rules, room context, presence, or card configuration to broaden server authorization or request forbidden fields.

**Given** a new or modified layout/configuration version is invalid, unknown, incompatible, or contains an unregistered card
**When** activation is attempted
**Then** the invalid version does not replace the active layout
**And** the last valid version remains active
**And** if no prior valid assignment exists, the immutable product default renders
**And** the error is available through a sanitized configuration result without private data or provider payloads.

**Given** a layout assignment or configuration mutation is persisted
**When** it commits
**Then** it follows the application-command and unit-of-work path
**And** it stores version, scope, ownership, expected prior version, and an idempotency identity where replay matters
**And** it defines backup inclusion, restore behavior, retention, and import eligibility without introducing a visual or declarative layout editor.

**Given** an older supported client receives a layout or card schema with unknown optional fields
**When** it validates the response
**Then** it safely ignores supported additive fields
**And** an unknown major version, required enum, required card semantics, or incompatible schema fails closed with upgrade-required behavior.

**Given** product defaults for personal and shared contexts
**When** they render with fictional fixture data
**Then** personal defaults prioritize assistant presence, Now, Briefing, Continue, and persistent text input
**And** shared defaults remain ambient and household-safe
**And** no routine builder, Home Assistant dashboard clone, or technical configuration concept appears in everyday navigation.

This story addresses `FR-035`, `FR-036`, `FR-040`, `FR-041`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR2`, `UX-DR4`, `UX-DR5`, `UX-DR8`, `UX-DR15–UX-DR17`, `UX-DR29`, and `AD-19`, `AD-21`, and `AD-22`.

### Story 1.5: Verify the Five-Surface Foundation

As a household member,
I want Kinward's common assistant experience to adapt coherently across personal and shared surfaces,
So that the product foundation proves privacy, layout, accessibility, and viewing-context behavior before live capabilities expand.

**Acceptance Criteria:**

**Given** the common registered cards, validated layouts, synthetic fixtures, and mock adapters
**When** the frontend-foundation suite renders personal mobile, personal tablet, personal desktop, shared kitchen display, and shared living-room display contexts
**Then** every context renders Assistant Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Assistant Input through the same card and layout registries
**And** no context uses a hard-coded alternative card tree.

**Given** the five authoritative surface contexts
**When** their resolved experiences are compared
**Then** mobile, tablet, desktop, kitchen, and living-room layouts are visibly adapted to their interaction capability, density, privacy, room, and viewing distance
**And** tablet and desktop are not merely enlarged mobile layouts
**And** kitchen and living-room displays use distinct room-appropriate defaults
**And** mock tablet support does not imply a committed live tablet workspace.

**Given** personal and shared synthetic fixtures with private, selected-share, household-shared, surface-ephemeral, and system-operational classes
**When** each context resolves its permitted mock view models
**Then** personal contexts receive only their authorized fixture data
**And** shared contexts receive only household-safe fixture data under deterministic surface policy
**And** private or selected-share fixture fields are absent from forbidden shared responses and rendered state rather than hidden after delivery.

**Given** an unknown, candidate, group, expired, or simulated authorization-loss shared-display state
**When** the mock policy resolver recomputes the shared view
**Then** only the fields permitted for that state are supplied to cards
**And** candidate data uses a neutral salutation with no name, identity signal, confidence, private existence, or broader household content
**And** downgrade or uncertainty clears no-longer-permitted rendered fixture state.

**Given** mobile and desktop viewport fixtures
**When** responsive behavior is inspected
**Then** content remains operable without horizontal loss of essential function
**And** persistent text input, primary navigation, Now, Briefing, and Continue retain appropriate hierarchy
**And** one dominant decision or action is emphasized at a time.

**Given** the reference shared-display fixture containing Now, Briefing, Approval, House Status, unavailable capability, identity downgrade, and private-handoff states
**When** accessibility checks run at 100% and 200% text scale
**Then** actionable targets are at least 48 by 48 CSS pixels with required inactive spacing
**And** critical and body text meet the specified room-display sizes
**And** contrast meets WCAG 2.2 AA
**And** content has no clipping, overlap, or loss of function
**And** status remains understandable without color
**And** keyboard and screen-reader semantics remain available where applicable.

**Given** reduced-motion, high-contrast, keyboard-only, and room-distance inspection modes
**When** the five contexts are exercised
**Then** motion is functional and suppressible
**And** focus is visible
**And** shared-display content remains readable at the defined room distance
**And** private-session and timeout states have non-color, plain-language cues.

**Given** optional providers are absent
**When** the complete five-context suite runs
**Then** every context still renders from mock adapters
**And** dependent capabilities display truthful degraded, unavailable, or intentionally-disabled states
**And** no mock data is presented as live provider data.

**Given** the Milestone A validation gate
**When** automated and inspectable evidence is produced
**Then** Playwright or equivalent checks cover layout resolution, common-card presence, per-surface distinction, privacy-field absence, invalid-layout fallback, responsive behavior, keyboard operation, and accessibility fixtures
**And** all evidence uses obviously fictional household data
**And** this mock-backed acceptance does not claim completion of the Milestone B live mobile, desktop, shared-display, authentication, or backend privacy slice.

This story addresses `FR-035`, `FR-036`, `FR-040`, `FR-041`, `NFR-003`, `NFR-023`, `NFR-024`, `NFR-025`, `NFR-026`, `NFR-027`, `NFR-031`, `NFR-032`, `UX-DR1–UX-DR9`, `UX-DR11–UX-DR17`, `UX-DR20`, `UX-DR25–UX-DR29`, and `AD-15`, `AD-21`, and `AD-22`.

## Epic 2: A Private Assistant That Continues Across Surfaces

A person can authenticate, ask by text, receive truthful incremental progress, persist a topic, continue on desktop, and see only safe shared-display representations.

### Story 2.1: Enter a Private Personal Assistant Session

As an account-bearing household member,
I want to authenticate into my own private personal assistant session,
So that only I can access my assistant, topics, memory boundary, and personal surface.

**Acceptance Criteria:**

**Given** an active account created during household bootstrap
**When** the person submits valid local credentials
**Then** the server verifies the password using the adopted Argon2id-equivalent mechanism
**And** creates an opaque high-entropy session whose verifier is stored server-side
**And** sends the session secret only in a `Secure`, `HttpOnly`, `SameSite` cookie
**And** binds the session to the existing account, person profile, issuance/expiry, security version, and revocation state.

**Given** a state-changing authenticated request
**When** it reaches `/api/v1`
**Then** the server validates the session and explicit CSRF protection before dispatch
**And** derives identity and authority from server-side bindings rather than client-supplied person, assistant, topic, or surface identifiers.

**Given** an authenticated active account without a deletion-pending overlay
**When** the personal assistant surface loads
**Then** the backend resolves exactly one primary personal assistant owned by that person
**And** the assistant cannot be reassigned to or selected from another person
**And** the household fallback assistant remains separately household-owned with no personal owner
**And** additional personal and specialist assistants are unavailable.

**Given** an unauthenticated request, expired or revoked session, invalid CSRF proof, non-active account, or deletion-pending overlay
**When** private personal-assistant content is requested
**Then** the request fails closed before protected repository or provider access
**And** the response contains no private content, protected identifier, ownership hint, or record-existence signal
**And** the personal surface clears or withholds private state.

**Given** one adult is a household administrator
**When** that adult requests another adult's personal assistant, private topic, conversation, memory reference, or personal integration data
**Then** access is denied solely on the ownership boundary
**And** administrator role does not broaden access
**And** the denial records only sanitized operational evidence with opaque references.

**Given** a valid authenticated session
**When** the person opens the personal mobile or desktop shell
**Then** the surface receives a server-derived `AccessContext` containing actor, active account state, owned assistant, surface, audience, requested capability, applicable policy versions, and opaque correlation identity
**And** every protected application, repository, and provider port requires that context
**And** authorization runs before query construction and again before serialization.

**Given** the person logs out or the session expires or is revoked
**When** a later request uses the old session secret
**Then** it is rejected as replay or invalid authority
**And** no private data remains available from application state or browser persistence
**And** the person must establish a new valid session.

**Given** authentication succeeds or fails
**When** logs, metrics, activity, and errors are inspected
**Then** they contain no plaintext password, session secret, credential verifier, private topic title, conversation body, or unrestricted personal identifier
**And** stable household-safe error codes and an opaque correlation reference support diagnosis.

**Given** backup and restore classification is inspected
**When** account and session records are evaluated
**Then** person/account bindings and explicitly portable recovery material have defined protected backup treatment
**And** reusable sessions, device trust, refresh artifacts, and pending authentication capabilities are excluded and invalid after restore.

**Given** the reference deployment under normal local-network conditions
**When** an authenticated local personal-home query is measured
**Then** the local API operation completes within 500 ms at p95
**And** authentication and personal-surface flows are keyboard-operable and use ordinary household language.

This story addresses `FR-009`, `FR-010`, `FR-028`, `FR-030`, `FR-031`, `FR-033`, `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-021`, `NFR-025`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR6`, `UX-DR7`, `UX-DR26`, `UX-DR27`, and `AD-01`, `AD-05`, `AD-17`, `AD-21`, and `AD-24`.

### Story 2.2: Submit and Cancel a Streaming Text Request

As an authenticated household member,
I want to submit a text request and see truthful incremental progress with cancellation,
So that I know what my assistant is doing and can stop work before anything unsubmitted proceeds.

**Acceptance Criteria:**

**Given** an authenticated personal mobile or desktop session
**When** the person submits text through the persistent Assistant Input
**Then** the client sends a versioned command under `/api/v1` with the server-authorized assistant, surface, explicit topic context when present, correlation identity, and idempotency key
**And** it sends no microphone, camera, screenshot, file, current-screen, selected-object, application, or ambient-device context.

**Given** a valid text request
**When** the application accepts it
**Then** it creates one canonical assistant-session/request identity
**And** returns or streams an `accepted` state within 500 ms at p95 on the reference deployment
**And** subsequent states use only the defined lifecycle: `accepted`, `understanding`, `responding`, `awaiting-approval`, `acting`, `completed`, `cancelled`, `uncertain`, or `failed`.

**Given** a provider capable of incremental output
**When** response generation proceeds
**Then** the client receives ordered, versioned SSE events with request identity, sequence, UTC time, correlation identity, event type, and policy-filtered payload
**And** first visible response content appears within 3 seconds at p95 outside documented provider outages
**And** exactly one truthful terminal event is emitted.

**Given** context is assembled for the request
**When** repository or provider data is selected
**Then** the immutable `AccessContext` authorizes the person, owned assistant, surface, audience, topic when present, requested capability, memory/facts, action authority, and external-state freshness
**And** authorization occurs before every protected query and before every event serialization
**And** only the minimum data required for the permitted task is sent to the model provider.

**Given** model or provider content proposes output or a capability invocation
**When** the orchestrator processes it
**Then** the content is treated as untrusted
**And** it cannot select identity, authority, policy, source permissions, or mutation targets
**And** only registered, backend-authorized, input/output-validated read capabilities available in Milestone B may execute
**And** external mutation capabilities remain unavailable.

**Given** the person cancels an accepted, understanding, responding, or awaiting-approval request
**When** the cancellation command wins serialization before terminal completion or submission
**Then** later model output is stopped or discarded
**And** every not-yet-submitted mutation or prepared side effect is prevented
**And** the request emits or records exactly one `cancelled` terminal result
**And** no later content or completion event is delivered.

**Given** cancellation races with a terminal event
**When** commands serialize
**Then** the first valid terminal transition is immutable
**And** an exact duplicate cancellation is idempotent
**And** a cancellation after terminal completion returns current terminal state without reopening the request.

**Given** the model provider times out, disconnects, fails, returns malformed events, or becomes unavailable
**When** the request can no longer proceed truthfully
**Then** the request ends `uncertain` or `failed` according to the known result
**And** the UI does not present `acting`, partial output, timeout, or transport success as `completed`
**And** it provides a household-safe retryability or next-step message.

**Given** the SSE connection disconnects before a terminal event
**When** the client reconnects with a supported cursor
**Then** ordered retained events resume without duplication when possible
**And** otherwise the client queries current request state
**And** the client never infers completion from a closed stream or unknown event.

**Given** an older supported client receives an unknown optional event field or unknown non-terminal event
**When** it processes the stream
**Then** it preserves sequence and queries current state when needed
**And** an unknown major version, required enum, or terminal semantic fails closed with upgrade-required behavior.

**Given** request processing and evidence capture
**When** logs, traces, metrics, errors, and fixtures are inspected
**Then** they contain no full private prompt, conversation body, provider-native payload, credential, or high-cardinality protected metric label
**And** generated TypeScript contracts compile for supported surfaces
**And** automated tests cover order, cancellation races, reconnect, timeout, malformed output, provider failure, one terminal event, authorization order, and data minimization using fictional inputs.

This story addresses `FR-013`, `FR-017`, `FR-021`, `FR-030`, `FR-033`, `NFR-001`, `NFR-005`, `NFR-006`, `NFR-008`, `NFR-011`, `NFR-018`, `NFR-019`, `NFR-029`, `NFR-030`, `NFR-032`, `UX-DR14`, `UX-DR20`, `UX-DR25`, `UX-DR27`, and `AD-02`, `AD-03`, `AD-05`, `AD-19`, and `AD-21`.

### Story 2.3: Persist Authorized Topics and Personal Context

As an authenticated household member,
I want my assistant conversation to create or update a durable private topic,
So that useful context remains available without depending on an external provider or crossing another person's privacy boundary.

**Acceptance Criteria:**

**Given** an authenticated person starts a request without an existing topic
**When** the request is accepted for durable continuation
**Then** the application creates a Kinward-local topic bound to the person, owned primary assistant, originating surface, current authorization, private-person class, and initial version
**And** creation follows the application-command and unit-of-work path
**And** an exact duplicate command is idempotent.

**Given** an authenticated person continues an existing authorized topic
**When** accepted conversation content or assistant output is persisted
**Then** the topic version advances atomically with the permitted conversation records and surface provenance
**And** optimistic concurrency rejects stale conflicting updates
**And** a failed transaction leaves the prior topic version intact.

**Given** a topic or conversation query
**When** the repository constructs the query
**Then** it requires `AccessContext` and constrains results by current person, assistant, topic ownership, lifecycle, sharing class, and requested purpose before reading protected rows
**And** authorization runs again before serialization
**And** unauthorized topics are absent rather than returned with redacted existence metadata.

**Given** two adults have separate primary assistants
**When** either adult queries topics, conversations, local memory references, counts, recent items, search results, or empty states
**Then** only that adult's authorized records can influence the response
**And** administrator role does not expose the other adult's private records
**And** the fallback assistant cannot query either adult's private topic, conversation, or memory index.

**Given** personal memory or optional knowledge references are associated with a topic
**When** they are stored or retrieved
**Then** each reference records the owning person, creating assistant or authority, source identity/version, data class, purpose, and current authorization
**And** Kinward SQL remains authoritative for topic and conversation continuity
**And** an optional memory or knowledge provider is never the sole copy of required topic state.

**Given** a request is cancelled, fails, or becomes uncertain
**When** persistence is finalized
**Then** only content accepted before the terminal boundary and permitted by policy is retained
**And** output arriving after cancellation is not persisted or rendered
**And** the terminal request state remains distinguishable from conversation content.

**Given** a model, memory, or knowledge provider is unavailable
**When** a person creates, reads, or updates a local topic
**Then** durable local topic operations continue
**And** unavailable provider context is marked unavailable rather than fabricated
**And** provider projection or retrieval failure does not roll back an otherwise valid local topic commit.

**Given** topic, conversation, and personal-memory-reference records are introduced
**When** their lifecycle metadata is inspected
**Then** backup inclusion, restore quarantine, ownership, class, retention, deletion, import eligibility, and provider-reference treatment are explicit
**And** personal records restore unavailable until same-owner reauthentication and disposition
**And** no credential or provider-native payload is stored in the topic contract.

**Given** logs, metrics, errors, activity, and fixtures for topic operations
**When** they are inspected
**Then** private prompts, conversation bodies, topic titles, memory bodies, and provider payloads are absent from ordinary operational output
**And** only opaque correlations and bounded categories are used
**And** tests use obviously fictional content.

This story addresses `FR-014`, `FR-018`, `FR-020`, `FR-021`, `FR-027`, `FR-030`, `FR-033`, `NFR-001`, `NFR-005`, `NFR-006`, `NFR-008`, `NFR-010`, `NFR-029`, `NFR-030`, `NFR-032`, `UX-DR13`, and `AD-04–AD-07`, `AD-19`, and `AD-25`.

### Story 2.4: Continue a Topic Across Mobile and Desktop

As an authenticated household member,
I want to resume an authorized topic on desktop after starting it on mobile,
So that I can continue useful work without repeating my original request or losing stored context.

**Acceptance Criteria:**

**Given** a person submits a text request on an authenticated personal mobile surface
**When** the request is accepted and creates or updates a topic
**Then** the mobile experience shows truthful incremental response state
**And** the resulting topic and permitted conversation context are durably available from Kinward-local persistence.

**Given** that topic has prior activity on mobile
**When** the same person explicitly opens it on an authenticated personal desktop surface
**Then** the server reauthorizes the person, account state, owned assistant, topic, sharing class, source versions, and destination surface before querying
**And** the desktop renders the topic's current permitted context without requiring the initial request to be restated.

**Given** a valid cross-surface continuation
**When** the desktop topic workspace loads
**Then** it presents the current topic identity, permitted conversation, decisions, unresolved questions, assistant progress, and truthful terminal or in-progress states available at that version
**And** it does not fabricate missing context or expose hidden prompts, provider payloads, or chain-of-thought.

**Given** a topic changed after the mobile surface last rendered it
**When** the desktop opens the topic
**Then** the desktop receives the current authorized server version
**And** stale client state does not overwrite newer context
**And** any attempted stale mutation fails with a household-safe conflict result and a current-state refresh path.

**Given** authorization was narrowed, revoked, expired, or made ambiguous between mobile activity and desktop open
**When** continuation is attempted
**Then** the backend denies the affected topic or fields before query and serialization
**And** the desktop receives no forbidden field, count, title, source, or existence signal
**And** cached or rendered no-longer-authorized state is cleared.

**Given** the same continuation is rendered through duplicate tabs, reconnects, or rerenders
**When** continuation metrics are recorded
**Then** they retain one canonical `continuation_id` for that explicit destination open
**And** a later explicit cross-surface open after closure receives a new identity
**And** passive rerendering does not inflate adoption or reliability evidence.

**Given** a keyboard-only person uses the mobile and desktop experiences
**When** they open Continue, select the topic, inspect context, submit follow-up text, and cancel or complete the request
**Then** the full journey is keyboard-operable with visible focus and screen-reader semantics
**And** mobile and desktop layouts remain distinct while using the same registered cards and generated API contracts.

**Given** the reference deployment and selected continuation evidence population
**When** personal-home and continuation performance are measured
**Then** cached personal-home content becomes interactive within 2 seconds p95 and cold load within 4 seconds p95
**And** local continuation reads complete within 500 ms p95
**And** the evidence distinguishes successful continuation without restatement, restatement, cancellation, and visible failure.

**Given** the model or optional memory provider is unavailable during continuation
**When** the person opens the persisted topic
**Then** locally stored authorized topic context still renders
**And** dependent assistant generation is marked unavailable or degraded separately
**And** the product does not present unavailable provider memory as known.

This story addresses `FR-013`, `FR-014`, `FR-015`, `FR-021`, `FR-027`, `FR-033`, `FR-037`, `NFR-001`, `NFR-010`, `NFR-017`, `NFR-021`, `NFR-023`, `NFR-025`, `NFR-027`, `NFR-030`, `NFR-031`, `UX-DR6`, `UX-DR7`, `UX-DR13`, `UX-DR14`, `UX-DR20`, `UX-DR26–UX-DR29`, and `AD-02`, `AD-04`, `AD-05`, `AD-21`, and `AD-22`.

### Story 2.5: Render a Live Household-Safe Shared Representation

As a household member,
I want an explicitly shared topic to appear safely on a live shared display,
So that the household can see useful coordination context without learning private details or that unshared private work exists.

**Acceptance Criteria:**

**Given** one fictional topic explicitly classified `household-shared` and one fictional topic that remains `private-person` and unshared
**When** an authorized personal request creates or updates both topics
**Then** both persist through the real backend topic path
**And** neither fixture uses static client-only data or hard-coded person identifiers.

**Given** at least one live shared-display context, either kitchen or living room
**When** it requests current household-safe topic representations
**Then** the backend constructs a shared-surface `AccessContext` and applies policy before repository query construction and before serialization
**And** the explicitly shared topic produces a live household-safe registered-card view model
**And** the other shared-display context may remain mock-backed without being represented as live.

**Given** the explicitly shared topic contains private preferences, costs, messages, source details, and household-safe coordination fields
**When** its shared representation is serialized
**Then** only the authorized household-safe representation is present
**And** every private field and private source reference is absent from the response payload, SSE events, rendered state, caches, logs, and fallback-assistant context
**And** the client performs no privacy filtering to obtain that result.

**Given** the unshared private topic exists
**When** the shared display queries topics, cards, counts, summaries, activity indicators, empty states, source categories, or assistant context
**Then** the unshared topic is entirely absent
**And** no identifier, count change, placeholder, timestamp, correlation, generic "private item" label, or other existence signal reveals it.

**Given** the permitted shared fixture is instead a separately approved household-safe coordination statement derived from a private topic
**When** the shared display renders it
**Then** only that separately reviewable statement is eligible
**And** it carries exact source identities and versions, transformation version, household-shared class, purpose, and expiry
**And** the private source topic remains entirely absent.

**Given** the shared topic or derived statement is narrowed, revoked, expired, deleted, or invalidated by a source-version change
**When** the shared display next fetches or receives an update
**Then** further backend authorization is revoked immediately
**And** the item disappears from shared and fallback context
**And** stale rendered or cached copies cannot preserve access.

**Given** a household member inspects the live shared item
**When** they request its explanation
**Then** the shared display shows only the permitted information class and household-safe reason it appeared
**And** it does not expose private sources, hidden reasoning, prompts, or protected existence
**And** full private correction is not offered on the shared display.

**Given** the shared-display browser stores application state
**When** storage, service workers, caches, IndexedDB, local storage, and error-report payloads are inspected
**Then** no private topic payload or private-derived source content is persisted
**And** only household-safe view models required for the current shared experience are retained.

**Given** authorization, payload, and UI tests run against the shared and unshared fixtures
**When** responses are inspected by field and byte content
**Then** the shared topic's forbidden details produce zero disclosures
**And** the unshared topic produces zero existence disclosures
**And** tests cover direct API responses, SSE events, rendered DOM, browser storage, fallback context, counts, and error paths.

**Given** the Milestone B demonstration
**When** the complete path is exercised
**Then** one authenticated adult can submit on mobile, receive incremental response, persist a topic, continue it on desktop, view the safe shared representation, and inspect why it appeared
**And** the five-context mock foundation remains passing
**And** all evidence uses fictional data.

This story addresses `FR-019`, `FR-020`, `FR-021`, `FR-030`, `FR-033`, `FR-035`, `FR-039`, `FR-043`, `FR-044`, `NFR-001`, `NFR-003`, `NFR-006`, `NFR-008`, `NFR-022`, `NFR-030–NFR-032`, `UX-DR8–UX-DR10`, `UX-DR15`, `UX-DR17`, `UX-DR19`, `UX-DR27`, and `AD-05`, `AD-07`, `AD-10`, `AD-21`, and `AD-22`.

### Story 2.6: Explain Context and Degrade Truthfully

As a household member,
I want Kinward to explain the context it used and clearly identify unavailable capabilities,
So that I can trust what the assistant knows without mistaking missing providers or stale information for current facts.

**Acceptance Criteria:**

**Given** an authorized personal item, response, topic representation, or assistant result
**When** the person opens its explanation
**Then** Kinward shows why it appeared, what changed when applicable, permitted source categories, recency, confidence or uncertainty, sharing class, and available correction
**And** it does not reveal hidden chain-of-thought, raw prompts, credentials, provider-native payloads, or sources the person cannot access.

**Given** an explanation depends on multiple protected sources
**When** the backend constructs the explanation view model
**Then** authorization occurs before source retrieval and before serialization
**And** the explanation includes only minimum permitted source metadata
**And** omitted sources do not leak through counts, ordering gaps, placeholders, timestamps, or existence hints.

**Given** no model provider is configured or the model provider is unavailable
**When** the person submits a text request
**Then** Kinward preserves authentication, personal surfaces, local topic reads and writes, and cross-surface continuation
**And** the assistant capability reports `unavailable`, `degraded`, or `intentionally-disabled` with a truthful next step
**And** no fabricated assistant response is generated.

**Given** memory and knowledge providers are absent or fail independently
**When** context is assembled or a local topic is opened
**Then** each affected capability is reported separately with health and freshness
**And** locally authoritative topic and conversation context remains available
**And** unavailable external memory is not presented as remembered fact, inferred confidence, or empty proof that no memory exists.

**Given** one or multiple optional providers fail
**When** core and capability health is evaluated
**Then** core application, database, authentication, bootstrap state, local topics, and supported continuation remain healthy when their own dependencies are healthy
**And** each provider-dependent capability reports its own state and actionable reason
**And** one provider's failure does not collapse unrelated capabilities.

**Given** provider data is stale, malformed, timed out, or freshness cannot be established
**When** it could influence an explanation or response
**Then** Kinward labels the dependency stale or unavailable and excludes it from current claims
**And** lower confidence reduces capability rather than inventing facts
**And** timeout or transport acknowledgement is never described as a completed user outcome.

**Given** a provider recovers
**When** a successful current refresh or capability check completes
**Then** only the recovered capability returns to available
**And** previously stale data is not silently treated as current without the required refresh evidence
**And** current authorization is re-evaluated before provider data re-enters context.

**Given** a degraded or unavailable state appears on mobile, desktop, or shared display
**When** it renders
**Then** status is conveyed by text and semantics rather than color alone
**And** the message uses ordinary household language
**And** it offers an actionable next step or explicitly states that no action is required
**And** a shared display reveals no private provider ownership, configuration, error, or protected source metadata.

**Given** outage and recovery evidence is collected
**When** automated tests inspect behavior
**Then** single-provider and multiple-provider failures cover every Milestone B capability available in this epic
**And** logs and metrics contain bounded capability categories and opaque correlations only
**And** no private body, provider payload, person identifier, or high-cardinality protected label appears.

This story addresses `FR-021`, `FR-027`, `FR-043`, `NFR-005`, `NFR-006`, `NFR-008`, `NFR-010`, `NFR-011`, `NFR-026`, `NFR-027`, `NFR-029`, `NFR-034`, `NFR-036`, `UX-DR19`, `UX-DR20`, `UX-DR25–UX-DR29`, and `AD-03`, `AD-05`, `AD-06`, and `AD-14`.
