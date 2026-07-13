---
status: draft
createdAt: "2026-07-13"
updatedAt: "2026-07-13"
documentType: "BMAD Product Requirements Document"
sourceDocuments:
  - "_bmad-output/planning-artifacts/product-brief-Kinward-Assistant-Experience.md"
  - "_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md"
  - "docs/pivot/single-household-pivot-and-rebuild-plan.md"
  - "docs/pivot/migration-status.md"
  - "docs/pivot/salvage-matrix.md"
---

# Product Requirements Document: Kinward Assistant Experience

**Product:** Kinward  
**Delivery model:** Private, single-household, Docker-deployed web/PWA platform

## 1. Purpose

Kinward is a private household intelligence platform in which each account-bearing household member may have one or more personal AI assistants. The product provides durable context, household coordination, integration-backed actions, and adaptive experiences across personal and shared surfaces without combining private personal information into a shared household brain.

Kinward is not a multi-tenant SaaS product, a routine builder, a generic chatbot, or a replacement for Home Assistant.

## 2. Product outcomes

Kinward must:

1. Give each person a private and continuous assistant relationship.
2. Infer useful household logistics from durable facts rather than requiring routine construction.
3. Coordinate information without exposing one person’s private memory to another person or to a household-shared assistant.
4. Continue authorized work across personal mobile, desktop, and shared-display surfaces.
5. Make external actions explicit, permission-bound, reviewable, and reversible where supported.
6. Remain household-owned and operable without a SaaS control plane.

## 3. Release boundaries

### 3.1 First cross-surface slice

The first implementation milestone must demonstrate one real assistant capability across:

- personal mobile,
- personal desktop,
- shared display,
- and backend privacy enforcement.

The slice is complete only when one authenticated adult can submit a text request on a personal surface, receive an incremental response, continue the resulting topic on another personal surface, and see a household-safe representation on a shared display. Automated tests must prove that the shared representation omits private details. Static mock data does not satisfy this milestone.

### 3.2 First usable household release

The first usable household release must include:

- single-household bootstrap and authenticated accounts,
- invitation and onboarding for at least one additional adult,
- separate personal assistants and memory boundaries,
- text conversation and topic continuity,
- live personal mobile and desktop surfaces,
- a live privacy-conservative shared display,
- one read-capable calendar integration,
- one Home Assistant state-and-action flow,
- approval and activity records for meaningful external actions,
- basic Kinward Control for people, assistants, integrations, privacy, activity, backup, and health,
- and tested backup and restore of the defined household data contract.

The release is not usable if authentication, adult-to-adult privacy separation, shared-display privacy enforcement, activity records for external actions, or clean restore validation is absent.

### 3.3 Later scope

Later scope includes email actions, voice-only endpoints, rich proactive coordination, visual and declarative layout editors, emergency surface mode, maintenance recall, advanced progressive onboarding, and native Android capabilities requiring OS-level access.

### 3.4 Explicit exclusions

Kinward excludes multi-household tenancy, SaaS control-plane behavior, billing and entitlements, support-operator access, mandatory external memory or knowledge services, routine-centric product behavior, permanent legacy frontend code, and arbitrary AI-generated client code.

## 4. Measurable success and counter-metrics

The first usable release must meet these conditions during a 30-day household pilot:

- At least two adults complete onboarding without developer intervention.
- At least two adults use Kinward on 10 or more distinct days.
- At least 80% of sampled cross-surface topic continuations resume without restating the initial request.
- Shared-surface privacy tests produce zero disclosures in unknown-person, candidate-identity, multiple-person, and expired-session states.
- At least 90% of sampled meaningful external actions contain complete requester, assistant, authority, approval, integration, result, and reversibility records.
- A clean deployment restores the supported backup and passes post-restore verification.

Default counter-metrics:

- No more than three non-critical proactive interruptions per person per day.
- Fewer than 10% of proactive nudges are dismissed as irrelevant or disabled by category.
- Fewer than 5% of autonomous actions are reversed because intent or scope was wrong.
- Zero private items remain visible after shared-surface identity confidence drops or a personal session expires.
- Ordinary household use requires no YAML, entity IDs, service names, schema editing, or model administration.

## 5. User and privacy classes

### 5.1 Household administrator

An adult account that manages household membership, child policy, integrations, shared surfaces, system health, and household-wide defaults. Administrator status does not grant access to another adult’s private memory, conversations, topics, calendar details, or email content.

### 5.2 Adult member

An adult controls their personal assistant, private memory, private topics, personal integrations, and personal surfaces.

### 5.3 Teen member

A teen account uses the `teen` privacy class.

- Private conversations, private topics, inferred preferences, and private memory are not visible to administrators or other household members.
- Administrators may manage account state, safety policy, action authority, and household-sharing settings, but may not read private content solely because of their role.
- Private teen content may be shared only through an explicit teen sharing action or a separately defined emergency/legal policy.
- Money, transportation, appointments, account security, and actions affecting another person require confirmation by default.

### 5.4 Child member

A child profile uses the `child` privacy class and may exist without an account.

- External integrations are disabled unless explicitly permitted.
- External-state actions require authorized-adult approval unless a narrow category is explicitly pre-authorized.
- Each durable fact must be labeled `private-to-child`, `shared-with-guardians`, or `household-shared`.
- Administrators may review configured facts and activity necessary for care, safety, school, transportation, health, and household responsibilities.
- Child conversation content is not automatically copied into guardian memory.

### 5.5 Shared-surface participant

A participant may be unknown, a likely candidate, a verified member, or one of several people present. Shared surfaces always begin in household-safe mode.

## 6. Assistant ownership and privacy boundaries

### 6.1 Personal and specialist assistants

- A personal or specialist assistant has exactly one owner.
- It may use only information its owner can access.
- Its private memory, conversations, topics, and personal integration data are not household-shared by default.
- Specialist assistants inherit no broader access than the owner’s primary assistant.

### 6.2 Household fallback assistant

The household fallback assistant is household-owned. It is not a combined personal assistant and does not aggregate private memories.

It may access household-shared profiles, household-shared calendars, shared lists, announcements, household-safe facts, permitted Home Assistant state, and its own household activity history.

It may not access private personal memory, private conversations, private topics, private email, private calendar details, personal credentials, or hidden summaries derived from those sources.

A personal assistant may send it only a minimum-necessary, privacy-filtered coordination statement.

## 7. Deterministic shared-surface identity policy

Shared surfaces use these states:

- `unknown`: no recognized person or confidence below the recognition threshold,
- `candidate`: one likely person, but not verified for private disclosure,
- `verified`: one person has completed an accepted verification method for the active session,
- `group`: multiple people are present or audience exclusivity is not established,
- `expired`: a prior verified session timed out or confidence dropped.

Required outcomes:

- `unknown` and `expired` expose household-safe information only.
- `candidate` may personalize a greeting but may not expose private details.
- `verified` may expose private information only when the surface policy permits it and no additional audience is detected.
- `group` suppresses private information unless every affected person has explicitly permitted group disclosure for that data class.
- Any transition away from `verified` immediately removes private content.
- When disclosure is blocked, Kinward must provide a household-safe summary and offer private-device handoff. It may not choose a less restrictive response.

## 8. Deterministic external-action policy

Authority levels are:

- `observe`: read-only,
- `suggest`: describe a possible action,
- `prepare`: construct a proposed mutation without submitting it,
- `confirm`: submit only after explicit approval of the exact prepared mutation,
- `autonomous`: submit without per-action approval only within a named bounded policy.

Requirements:

- New integrations default to `observe`.
- Every capability declares a maximum authority level per person, action category, and integration.
- Money, account security, legal commitments, medical actions, transportation bookings, appointment cancellation, message sending, and actions affecting another person default to `confirm` or lower.
- `prepare` never changes external state.
- `confirm` executes only the exact approved mutation; material changes require new approval.
- `autonomous` requires an explicit category, target scope, limits, expiry or review date, and revocation control.
- Ambiguous identity, ambiguous target, stale provider state, or policy mismatch prevents mutation and returns a deterministic approval-required or failed result.
- Meaningful actions record request, preparation, approval, execution, result, and undo status.

## 9. Functional requirements

### Household and onboarding

- **FR-001:** Kinward shall support exactly one household per deployment.
- **FR-002:** Initial bootstrap shall create the household, administrator profile, account binding, and first personal assistant as one recoverable operation.
- **FR-003:** Administrators shall add adults and minors before those people have accounts.
- **FR-004:** Initial onboarding shall not require integrations, rooms, devices, routines, detailed school/work context, notification rules, or layout editing.
- **FR-005:** Invitation acceptance shall bind the authenticated account to the intended existing profile without silently creating a duplicate.
- **FR-006:** Kinward shall distinguish household role, account state, privacy class, assistant ownership, and action authority.

### Assistants, conversation, and topics

- **FR-007:** Each account-bearing person shall have at least one personal assistant.
- **FR-008:** Every personal or specialist assistant shall have exactly one owner.
- **FR-009:** The household fallback assistant shall enforce Section 6.2.
- **FR-010:** Kinward shall support text conversation with accepted, streaming, completed, uncertain, cancelled, and failed states.
- **FR-011:** Conversation continuity shall be bound to person, assistant, topic, surface, and current authorization.
- **FR-012:** A user shall continue an authorized topic across mobile and desktop without restating stored context.

### Memory and context

- **FR-013:** Personal memory shall be bound to the owning person and creation permissions.
- **FR-014:** Household-shared facts shall be stored or labeled separately from private memory.
- **FR-015:** The household fallback assistant shall never query private personal memory indexes.
- **FR-016:** Context assembly shall retrieve only information permitted for the current person, assistant, topic, surface, and action.
- **FR-017:** Kinward shall distinguish confirmed facts, inferred observations, transient context, and household-shared facts.
- **FR-018:** Consequential, sensitive, or behavior-changing observations require confirmation before becoming durable facts.
- **FR-019:** Users shall inspect, correct, and delete durable facts about themselves, subject to required audit retention.
- **FR-020:** Durable facts shall include source category, timestamp, sharing class, and confidence.

### Identity and privacy

- **FR-021:** Personal surfaces require authentication before exposing private assistant content.
- **FR-022:** Shared surfaces shall implement all states and outcomes in Section 7.
- **FR-023:** Authorization shall be enforced by backend services, not only client rendering.
- **FR-024:** Administrators shall not receive another adult’s private data merely because of role.
- **FR-025:** Teen and child policy shall implement Section 5 and be covered by automated tests.

### Surfaces and layouts

- **FR-026:** Kinward shall support personal mobile, personal desktop, and shared-display layouts in the first cross-surface slice.
- **FR-027:** Every surface shall receive ownership, privacy, room when applicable, interaction, and viewing-distance context.
- **FR-028:** The personal default shall include assistant presence, Now, briefing, topics, and persistent input.
- **FR-029:** The shared-display default shall show household-safe ambient information and return to that state after personal-session expiry.
- **FR-030:** Product surfaces shall render registered cards from validated layouts.
- **FR-031:** Invalid configuration shall fail safely and preserve the last valid layout.
- **FR-032:** Generated temporary views shall use registered components only.
- **FR-033:** Users shall inspect why an item appeared, source categories, confidence, sharing class, and available correction without exposing hidden reasoning or secrets.

### Proactivity, approvals, and activity

- **FR-034:** Proactive delivery shall support ambient, briefing, nudge, interruption, and autonomous-action levels.
- **FR-035:** Kinward shall default to the least disruptive level consistent with timing, risk, and policy.
- **FR-036:** Non-critical interruptions shall respect the default cap in Section 4.
- **FR-037:** Kinward shall detect relevant exceptions without requiring routine definitions.
- **FR-038:** Coordination requests shall disclose only the minimum information required for a response.
- **FR-039:** External actions shall implement all authority rules in Section 8.
- **FR-040:** Activity records shall identify requester, acting assistant, represented person, authority basis, approval, integration, result, and undo availability.

### Integrations and administration

- **FR-041:** Optional integration failure shall degrade only dependent features.
- **FR-042:** Calendar integration shall detect additions, removals, time changes, and cancellations within the connected person’s boundary.
- **FR-043:** Home Assistant shall remain authoritative for physical areas, devices, entities, and current state.
- **FR-044:** Home Assistant actions shall follow permission, stale-state, approval, and activity requirements.
- **FR-045:** Kinward Control shall be separate from everyday assistant navigation.
- **FR-046:** Administrators shall manage people, invitations, assistants, child policy, integrations, shared surfaces, proactive defaults, backup status, and health.
- **FR-047:** Administrative views shall not expose credentials, hidden prompts, or unrestricted private adult content.

## 10. Backup, restore, export, and upgrade contract

The first usable release backup contract includes:

- household configuration,
- people and account bindings excluding reusable authentication secrets,
- assistants and personality settings,
- privacy and authority policies,
- topics and locally stored conversation records,
- confirmed durable facts and sharing metadata,
- layouts and surface assignments,
- integration configuration excluding credentials that cannot be exported safely,
- encrypted credential material where supported,
- approvals and activity history,
- and provider reference mappings required to reconnect optional stores.

Requirements:

- **FR-048:** Backups shall contain a versioned manifest listing included, excluded, encrypted, and externally referenced data.
- **FR-049:** Restore shall support a clean deployment on the same or a declared compatible schema version.
- **FR-050:** Restore shall complete atomically or stop without replacing the existing valid household state.
- **FR-051:** Post-restore verification shall validate household identity, people, assistants, topics, policies, layouts, activity, and provider-reference integrity.
- **FR-052:** Excluded credentials shall be listed as required reauthorization steps.
- **FR-053:** Migration export shall use documented versioned formats independent of the original host path.
- **FR-054:** Upgrade shall require a restorable pre-upgrade backup and stop with actionable instructions when compatibility checks fail.

## 11. Nonfunctional requirements

### Privacy and security

- **NFR-001:** Server-side authorization shall protect every private resource.
- **NFR-002:** Secrets and credentials shall be encrypted at rest or stored in a platform-appropriate secret mechanism and shall not appear in normal responses or logs.
- **NFR-003:** Automated tests shall cover every shared-surface state and transition.
- **NFR-004:** Automated tests shall cover adult, teen, child, administrator, personal-assistant, specialist-assistant, and household-fallback boundaries.
- **NFR-005:** External content shall be treated as untrusted and shall not override authorization or action policy.
- **NFR-006:** Data sent to external providers shall be minimized to the permitted task.

### Reliability and recoverability

- **NFR-007:** Optional provider failure shall not prevent setup, authentication, local administration, backup access, or local data access.
- **NFR-008:** External calls shall use explicit timeouts, bounded retries, and failure isolation.
- **NFR-009:** External mutations shall be idempotent where supported or protected against duplicate execution.
- **NFR-010:** A clean-deployment restore test shall pass before the first usable release.
- **NFR-011:** Automated backup/restore acceptance tests shall have zero known loss of data included in the backup contract.

### Performance thresholds

Measured on the documented reference deployment under normal local-network conditions:

- **NFR-012:** Cached personal-home content shall become interactive within 2 seconds at p95; cold load within 4 seconds at p95.
- **NFR-013:** A submitted assistant request shall show accepted or streaming state within 500 ms at p95.
- **NFR-014:** When a provider streams, first visible response content shall appear within 3 seconds at p95, excluding documented provider outage conditions.
- **NFR-015:** Private shared-surface content shall be removed within 250 ms of the client receiving an identity downgrade and within 1 second of backend detection.
- **NFR-016:** Local-only API operations shall complete within 500 ms at p95.

### Accessibility and maintainability

- **NFR-017:** Core web/PWA experiences shall meet applicable WCAG 2.2 AA requirements.
- **NFR-018:** Shared-display controls shall meet UX-specified room-distance readability and touch-target requirements.
- **NFR-019:** Capability interfaces shall avoid direct dependency on one model, memory, knowledge, calendar, email, or smart-home provider.
- **NFR-020:** Cards, layouts, policies, schemas, and backup manifests shall be versioned for migration.

## 12. Delivery milestones

### Milestone A: Accepted foundation

Repository reset, domain and persistence baseline, bootstrap API, optional integration resilience, neutral memory/knowledge contracts, provider adapters, registry frontend proof of concept, Docker, CI, `mise`, and `uv`.

### Milestone B: First cross-surface assistant slice

Authentication, onboarding UI, text assistant endpoint, topic persistence, permission-bound context assembly, live mobile view, live desktop continuation, live household-safe shared-display representation, privacy tests, and activity evidence for the demonstrated flow.

### Milestone C: First usable household release

Invited second adult, separate adult assistants and memory, durable fact management, calendar change detection, Home Assistant state and approved action, deterministic identity policy, external-action policy, basic Kinward Control, versioned backup manifest, clean restore verification, and performance/accessibility/security gates.

### Milestone D: Coordinating household assistant

Email, progressive onboarding, coordination requests, proactive evaluation, richer topics/cards, and layout editing.

### Milestone E: Voice and advanced experiences

Voice orchestration, private handoff, emergency mode, maintenance recall, and native evaluation based on measured PWA limitations.

## 13. Architecture decisions required

Architecture must resolve the default authentication and recovery mechanism, initial model provider contract, initial calendar synchronization transport, physical storage split among Kinward/Honcho/LLM-Wiki, mechanisms accepted for `verified` shared-surface identity, backup encryption and credential portability, and the reference deployment used for performance testing.

These decisions may select mechanisms but may not weaken the product outcomes defined in this PRD.

## 14. PRD readiness criteria

This PRD may be marked final only when:

- repository safety review confirms no private household names, addresses, credentials, infrastructure identifiers, or private fixtures,
- every source path resolves,
- deterministic privacy and action policies are accepted,
- the cross-surface slice and first usable release are accepted,
- architecture can map every Milestone B and C requirement to a concrete boundary,
- epics map every functional and nonfunctional requirement without creating competing scope,
- and implementation-readiness review finds no unresolved blocker for Milestone B.
