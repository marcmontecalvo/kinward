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

Kinward is a private household intelligence platform in which each account-bearing household member may have one or more personal AI assistants. It combines durable personal and household context, privacy-bound memory, external integrations, and adaptive surfaces so that people can ask once, delegate outcomes, and receive useful exceptions without manually programming ordinary household life.

The primary product is the relationship between a person and their assistant. Cards, dashboards, chat history, integrations, and smart-home controls are supporting representations.

Kinward is not:

- a multi-tenant SaaS product,
- a routine or alarm builder,
- a generic chatbot,
- a family surveillance system,
- a shared repository of everyone’s private information,
- or a replacement for Home Assistant’s device registry and automation engine.

## 2. Product outcomes

Kinward must:

1. Give each person a private, continuous assistant relationship.
2. Infer useful household logistics from durable facts and changing conditions rather than requiring routine construction.
3. Coordinate information and actions without exposing one person’s private memory to another person or to a household-shared assistant.
4. Continue authorized work across personal mobile, personal desktop, and shared-display surfaces without requiring the person to restate available context.
5. Surface what matters now while suppressing low-value noise.
6. Make external actions explicit, permission-bound, reviewable, and reversible where supported.
7. Make uncertainty, degraded capability, and incomplete work visible.
8. Remain household-owned and operable without a SaaS control plane.
9. Provide polished defaults so ordinary household use requires no infrastructure or configuration knowledge.

## 3. Product concepts and definitions

### 3.1 Personal assistant

An assistant owned by exactly one person. It may use only information and capabilities that person is authorized to use. Its conversation, topics, personal memory, and personal integration data are private by default.

### 3.2 Specialist assistant

An optional assistant owned by exactly one person and focused on a domain or temporary purpose. It never receives broader access than the owner’s primary assistant. The primary assistant remains the default router unless the person explicitly invokes or delegates to a specialist.

### 3.3 Household fallback assistant

A household-owned assistant used for household-safe questions, shared information, timers, announcements, shared lists, media, and permitted Home Assistant actions. It is not a combined personal assistant and must never query or synthesize private personal memory.

### 3.4 Topic

A durable unit of ongoing work such as a trip, school project, maintenance issue, purchase decision, event, or household plan. A topic may contain conversation, decisions, artifacts, permitted integration references, assistant progress, approvals, and outcomes. It is not merely a chat thread.

### 3.5 Durable fact

A stored statement intended to influence future assistance. Every durable fact has an owner or household scope, sharing class, source category, confirmation state, confidence, creation time, and update time.

### 3.6 Surface

A rendered interaction context. Initial supported classes are personal mobile, personal desktop, and shared display. Personal tablet and voice remain required product directions but are not required for the first usable release.

### 3.7 Meaningful external action

An action that changes external state, communicates on a person’s behalf, affects another person, changes money or commitments, changes security or access, or creates material household consequences.

## 4. Release boundaries

### 4.1 First cross-surface slice

The first implementation milestone must demonstrate one real assistant capability across:

- personal mobile,
- personal desktop,
- shared display,
- and backend privacy enforcement.

The slice is complete only when one authenticated adult can:

1. submit a text request on a personal mobile surface,
2. see the request accepted and receive an incremental response,
3. create or update a persisted topic,
4. continue that topic on a personal desktop without restating stored context,
5. view a live household-safe representation of the topic on a shared display,
6. inspect why that shared item appeared and what information class it contains,
7. and confirm through automated tests that private topic details cannot reach the shared response or payload.

Static mock data, client-only filtering, hard-coded person IDs, or a shared view that simply hides the entire topic do not satisfy this milestone.

### 4.2 First usable household release

The first usable household release must include:

- single-household bootstrap and authenticated accounts,
- invitation and onboarding for at least one additional adult,
- separate personal assistants, conversations, topics, integrations, and memory boundaries,
- text conversation and topic continuity,
- live personal mobile and desktop surfaces,
- a live privacy-conservative shared display,
- confirmed durable-fact management,
- one read-capable calendar integration with change detection,
- one Home Assistant state-and-action flow,
- approval and activity records for meaningful external actions,
- basic Kinward Control for people, assistants, integrations, privacy, activity, backup, and health,
- documented degraded behavior for unavailable optional capabilities,
- and tested backup and restore of the defined household data contract.

The release is not usable if authentication, adult-to-adult privacy separation, shared-display backend privacy enforcement, external-action activity records, clean restore validation, or a working assistant conversation path is absent.

### 4.3 Later scope

Later scope includes:

- email reading and sending,
- voice-only endpoints and cross-surface voice handoff,
- richer proactive coordination between household members,
- visual and declarative layout editors,
- emergency surface mode,
- contextual maintenance recall,
- progressive school, work, personal, home, and transportation onboarding,
- personal tablet-specific workspaces,
- and native Android capabilities requiring operating-system access.

### 4.4 Explicit exclusions

Kinward excludes:

- multi-household tenancy in one deployment,
- SaaS control-plane behavior,
- billing and commercial entitlements,
- support-operator access,
- mandatory external memory, knowledge, Home Assistant, or cloud inference services,
- routine-centric product behavior,
- permanent legacy frontend code,
- arbitrary AI-generated client code,
- administrator access to another adult’s private content merely because of role,
- and covert monitoring or hidden disclosure of household members’ private assistant activity.

## 5. Core user journeys

All names below are fictional test personas.

### UJ-1: Administrator establishes a household

**Alex**, an adult household administrator, opens a new deployment. Alex creates the initial account, names the household, creates a profile, adds another adult and a child as profiles without requiring their accounts, names the first personal assistant, completes a short personality interview, and enters Kinward.

Alex is not required to configure integrations, rooms, devices, routines, detailed schedules, notification rules, or layouts.

**Successful outcome:** The household, account binding, profiles, and first personal assistant are created as one recoverable operation. Alex reaches a useful personal home surface and sees optional next setup steps without being blocked.

**Failure outcome:** If setup fails before commit, no partially configured household is presented as usable. The product explains whether setup can be retried or requires restore/reset.

### UJ-2: Invited adult receives a separate assistant

**Jordan** accepts an invitation for an existing household profile, authenticates, confirms the intended profile, names a personal assistant, and enters a private personal surface.

**Successful outcome:** Jordan has a distinct account binding, assistant, memory boundary, topics, and personal integration space. No private content from Alex is visible or used.

**Failure outcome:** An expired or mismatched invitation cannot silently create a duplicate profile or attach to the wrong person.

### UJ-3: A topic continues across surfaces

Jordan asks on a phone for help comparing options for a family trip. Kinward creates a trip topic with the permitted conversation and decisions. Later, Jordan opens Kinward on a desktop and continues from the same state.

**Successful outcome:** The desktop shows the current topic, decisions, unresolved questions, and assistant progress without requiring the original request to be repeated.

**Shared-display outcome:** The household display may show a generic item such as “Trip planning is active” only when the topic is household-shared. It must not show private preferences, costs, messages, or source details.

### UJ-4: Kinward surfaces a calendar change

A connected calendar adds an early-release event associated with a child profile. Kinward compares the event with confirmed household transportation facts and permitted adult calendars.

**Successful outcome:** The appropriate adults receive a concise briefing item that identifies what changed, why it may matter, which source category supplied it, and whether action is required.

**Non-goal:** Kinward does not create a recurring routine, infer a permanent transportation responsibility without confirmation, or interrupt everyone by default.

### UJ-5: Shared display refuses private disclosure

Jordan asks a shared display about a private appointment while another person is present or identity is not verified.

**Successful outcome:** Kinward provides a household-safe response and offers private-device handoff. No private appointment details appear in rendered UI, API payloads, logs intended for ordinary administration, or household-fallback context.

### UJ-6: A prepared action requires exact approval

Alex asks Kinward to change a calendar appointment. The assistant prepares a proposed mutation and presents the exact date, time, calendar, affected event, integration, expected consequence, and reversibility status.

**Successful outcome:** Approval executes only the exact prepared mutation. If source state changed, approval expires and the assistant prepares a new proposal instead of applying stale intent.

### UJ-7: A child receives bounded assistance

A child account asks for homework help and later asks the assistant to send a message to a teacher.

**Successful outcome:** Homework help can proceed within policy. Message sending is blocked or routed to authorized-adult approval. The child’s ordinary conversation is not automatically copied into guardian memory.

### UJ-8: Optional providers are unavailable

The memory provider or Home Assistant is offline.

**Successful outcome:** Kinward still starts, authenticates users, loads local topics and configuration, permits local administration and backup, and clearly marks dependent capabilities unavailable. It does not fabricate remembered facts or claim a device action succeeded.

### UJ-9: Administrator restores the household

Alex restores a supported backup to a clean compatible deployment.

**Successful outcome:** Household identity, people, assistants, topics, policies, layouts, activity, confirmed facts, and supported provider mappings pass verification. Excluded credentials are listed as explicit reauthorization tasks.

## 6. Measurable success and counter-metrics

The first usable release must meet these conditions during a 30-day household pilot:

### 6.1 Adoption and utility

- At least two adults complete onboarding without developer intervention.
- At least two adults use Kinward on 10 or more distinct days.
- At least 70% of sampled assistant sessions produce a response, topic update, useful explanation, or permitted action without developer repair.
- At least 80% of sampled cross-surface topic continuations resume without restating the initial request.
- At least 75% of sampled Now or briefing items are marked useful, acted upon, or left undisputed.

### 6.2 Trust and privacy

- Shared-surface privacy tests produce zero disclosures in unknown, candidate, group, expired, and identity-downgrade states.
- Adult-to-adult private-resource authorization tests produce zero cross-person reads.
- At least 95% of sampled meaningful external actions contain complete requester, assistant, represented person, authority, approval, integration, result, and reversibility records.
- Zero actions are reported complete when the provider returned failure, timeout, unknown status, or no confirmation.

### 6.3 Operations

- A clean compatible deployment restores the supported backup and passes all post-restore checks.
- An optional provider outage does not prevent authentication, local topic access, Kinward Control, or backup creation.
- No manual database editing is required for ordinary onboarding, invitation, integration reconnect, backup, or restore workflows.

### 6.4 Counter-metrics

- No more than three non-critical proactive interruptions per person per day by default.
- Fewer than 20% of proactive nudges are dismissed as irrelevant during the pilot. The prior 10% target is a post-pilot optimization goal.
- Fewer than 5% of autonomous actions are reversed because intent or scope was wrong.
- Zero private items remain visible after shared-surface identity confidence drops or a personal session expires.
- Fewer than 5% of completed assistant actions lack a plain-language explanation of what happened.
- Ordinary household use requires no YAML, entity IDs, service names, schema editing, database access, or model administration.

## 7. User, role, and privacy classes

### 7.1 Household administrator

An adult account that manages membership, invitations, child policy, household integrations, shared surfaces, system health, backup, and household-wide defaults.

Administrator status does not grant access to another adult’s private memory, conversations, topics, calendar details, email content, credentials, or assistant instructions.

### 7.2 Adult member

An adult controls their personal assistant, private memory, private topics, personal integrations, personal surfaces, and personal sharing decisions.

An adult may explicitly share a fact, topic summary, calendar, or action outcome with the household or selected people. Sharing does not transfer ownership of the underlying private source.

### 7.3 Teen member

A teen account uses the `teen` privacy class.

- Private conversations, topics, inferred preferences, and private memory are not visible to administrators or other household members.
- Administrators may manage account state, safety policy, maximum action authority, allowed integrations, and household-sharing settings.
- Administrators may not read private content solely because of their role.
- Private teen content may be shared only through an explicit teen action or a separately documented emergency/legal policy.
- Money, transportation, appointments, account security, message sending, and actions affecting another person require confirmation or authorized-adult approval by default.
- The product must show the teen which categories are guardian-visible and which are private.

### 7.4 Child member

A child profile uses the `child` privacy class and may exist without an account.

- External integrations are disabled unless explicitly permitted.
- External-state actions require authorized-adult approval unless a narrow category is explicitly pre-authorized.
- Each durable fact must be classified `private-to-child`, `shared-with-guardians`, or `household-shared`.
- Administrators may review configured facts and activity necessary for care, safety, school, transportation, health, and household responsibilities.
- Child conversation content is not automatically copied into guardian memory.
- The child experience must use age-appropriate language without presenting hidden monitoring as privacy.
- The product must clearly identify when a child request will be shared with or approved by an adult before submission where feasible.

### 7.5 Profile without account

A profile may exist for a child, infant, or other household member who does not authenticate. It may hold explicitly entered household facts and relationships but has no private assistant conversation or personal integration credentials.

### 7.6 Shared-surface participant

A participant may be unknown, a likely candidate, a verified member, or one of several people present. Shared surfaces always begin in household-safe mode.

## 8. Data classification and sharing

Every stored or transmitted item must have an effective data class.

### 8.1 Data classes

- `private-person`: available only to the owning person and authorized assistants/services acting for that person.
- `private-child`: available according to child policy and explicit guardian-visible categories.
- `selected-share`: shared with named household members for a defined purpose.
- `household-shared`: available to household-safe experiences and the household fallback assistant.
- `surface-ephemeral`: available only during the current authorized surface session and not durable unless explicitly saved.
- `system-operational`: health, configuration, audit, and diagnostics that must exclude private content unless strictly required and authorized.

### 8.2 Derived data

A summary, embedding, classification, recommendation, or model-generated inference inherits the most restrictive data class of its source inputs unless an explicit privacy-filtered transformation produces a separately reviewable household-safe statement.

Deleting or revoking access to source data must invalidate or remove derived data where the product can identify the dependency. When immediate removal from an external provider is not possible, Kinward must mark the reference inaccessible and disclose the limitation.

### 8.3 Data minimization

Context assembly and provider calls must include only the data required for the current permitted task. Entire mailboxes, calendars, topic histories, or memory stores must not be sent when a narrower subset is sufficient.

## 9. Assistant ownership and privacy boundaries

### 9.1 Personal and specialist assistants

- A personal or specialist assistant has exactly one owner.
- It may use only information its owner can access.
- Its private memory, conversations, topics, and personal integration data are private by default.
- A specialist assistant inherits no broader access than the owner’s primary assistant.
- Assistants may exchange information only through an explicit delegation record containing purpose, permitted data, expiry, and recipient.

### 9.2 Household fallback assistant

The household fallback assistant is household-owned. It may access:

- household-shared profiles and relationships,
- household-shared calendars,
- shared lists and announcements,
- household-safe durable facts,
- permitted Home Assistant state and actions,
- shared timers and media,
- and its own household activity history.

It may not access:

- private personal memory indexes,
- private conversations or topics,
- private email,
- private calendar details,
- personal credentials,
- hidden summaries derived from private sources,
- or another assistant’s private instructions.

A personal assistant may send the fallback assistant only a minimum-necessary, privacy-filtered coordination statement. The statement must carry provenance, sharing class, purpose, and expiry.

## 10. Deterministic shared-surface identity policy

Shared surfaces use these states:

- `unknown`: no recognized person or confidence below recognition threshold,
- `candidate`: one likely person but not verified for private disclosure,
- `verified`: one person completed an accepted verification method for the active session,
- `group`: multiple people are present or audience exclusivity is not established,
- `expired`: a prior verified session timed out or confidence dropped.

Required outcomes:

- `unknown` and `expired` expose household-shared and system-safe information only.
- `candidate` may personalize a greeting but may not expose private details or confirm that private records exist.
- `verified` may expose private information only when the surface policy permits it and no additional audience is detected.
- `group` suppresses private information unless every affected person explicitly permitted group disclosure for that data class.
- Any transition away from `verified` removes private content from the next render and invalidates private fetch authorization.
- When disclosure is blocked, Kinward provides a household-safe response and offers private-device handoff.
- Shared surfaces must not cache private payloads for later household-safe rendering.
- A personal shared-surface session must expire after a configurable inactivity period no longer than 10 minutes by default.

Accepted verification methods and confidence thresholds are architecture decisions, but the resulting state and product outcome must be deterministic and testable.

## 11. Deterministic external-action policy

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
- A prepared mutation includes target, changed fields, source version or freshness marker, expected result, expiration, and reversibility status.
- `confirm` executes only the exact approved mutation. Material changes require a new approval.
- Approval expires when its prepared mutation expires, source state changes materially, identity changes, or authority is revoked.
- `autonomous` requires an explicit category, target scope, limits, effective period, review date, revocation control, and activity visibility.
- Ambiguous identity, ambiguous target, stale provider state, policy mismatch, unavailable integration, or missing provider confirmation prevents mutation.
- A timeout or unknown provider result is recorded as `unknown`, not `completed`, and requires reconciliation before retry when duplicate execution is possible.
- Meaningful actions record request, preparation, approval, execution attempt, provider response, final result, and undo status.

## 12. Assistant interaction and topic behavior

### 12.1 Request lifecycle

Every assistant request has an observable lifecycle:

- `accepted`,
- `understanding`,
- `responding`,
- `awaiting-approval`,
- `acting`,
- `completed`,
- `cancelled`,
- `uncertain`,
- or `failed`.

The UI must not present `acting` as `completed`. Cancellation must stop further model output and prevent any not-yet-submitted mutation.

### 12.2 Context assembly

Context assembly must identify:

- current person,
- acting assistant,
- topic,
- surface,
- audience state,
- requested capability,
- permitted memory and facts,
- relevant integration data,
- action authority,
- and freshness of external state.

Missing optional context must reduce confidence or capability rather than produce invented facts.

### 12.3 Topic lifecycle

A person can:

- create a topic from conversation,
- rename it,
- archive it,
- reopen it,
- change its sharing class,
- inspect related sources and actions,
- and delete it subject to required audit retention.

Archived topics remain searchable to authorized users but do not appear in Continue by default.

### 12.4 Now and briefing behavior

The Now area contains at most one dominant current item by default. It may be absent when nothing is useful.

A briefing item must include:

- concise meaning,
- why it matters,
- source category,
- recency,
- affected person or household scope,
- required action if any,
- and correction or dismissal control.

Briefing is not a raw notification feed. Duplicate source events must be grouped where they describe the same underlying change.

## 13. Functional requirements

### 13.1 Household, accounts, and onboarding

- **FR-001:** Kinward shall support exactly one household per deployment.
- **FR-002:** Initial bootstrap shall create the household, administrator profile, account binding, and first personal assistant as one recoverable operation.
- **FR-003:** Administrators shall add adults and minors before those people have accounts.
- **FR-004:** Initial onboarding shall not require integrations, rooms, devices, routines, detailed school/work context, notification rules, or layout editing.
- **FR-005:** Invitation acceptance shall bind the authenticated account to the intended existing profile without silently creating a duplicate.
- **FR-006:** Invitations shall be single-use, expiring, revocable, and unusable after the target profile is bound.
- **FR-007:** Kinward shall distinguish household role, account state, privacy class, assistant ownership, and action authority.
- **FR-008:** A person shall be able to review and correct their profile information after onboarding.

### 13.2 Assistants, conversation, and topics

- **FR-009:** Each account-bearing person shall have at least one personal assistant.
- **FR-010:** Every personal or specialist assistant shall have exactly one owner.
- **FR-011:** The household fallback assistant shall enforce Section 9.2.
- **FR-012:** A person shall name an assistant and configure personality and interaction preferences without changing its permission boundary.
- **FR-013:** Kinward shall support the request lifecycle in Section 12.1.
- **FR-014:** Conversation continuity shall be bound to person, assistant, topic, surface, and current authorization.
- **FR-015:** A user shall continue an authorized topic across mobile and desktop without restating stored context.
- **FR-016:** Users shall manage topic lifecycle and sharing as defined in Section 12.3.
- **FR-017:** Assistant cancellation shall prevent unsubmitted actions and visibly mark the request cancelled.

### 13.3 Memory and durable context

- **FR-018:** Personal memory shall be bound to the owning person and creation permissions.
- **FR-019:** Household-shared facts shall be stored or labeled separately from private memory.
- **FR-020:** The household fallback assistant shall never query private personal memory indexes.
- **FR-021:** Context assembly shall retrieve only information permitted for the current person, assistant, topic, surface, audience, and action.
- **FR-022:** Kinward shall distinguish confirmed facts, inferred observations, transient context, and household-shared facts.
- **FR-023:** Consequential, sensitive, or behavior-changing observations require confirmation before becoming durable facts.
- **FR-024:** Users shall inspect, correct, reclassify, and delete durable facts about themselves, subject to required audit retention.
- **FR-025:** Durable facts shall include source category, timestamp, sharing class, confirmation state, and confidence.
- **FR-026:** Derived data shall enforce Section 8.2.
- **FR-027:** Optional memory or knowledge provider failure shall not cause Kinward to claim unavailable memory as known.

### 13.4 Identity, privacy, and permissions

- **FR-028:** Personal surfaces require authentication before exposing private assistant content.
- **FR-029:** Shared surfaces shall implement every state and outcome in Section 10.
- **FR-030:** Authorization shall be enforced by backend services and provider-query construction, not only client rendering.
- **FR-031:** Administrators shall not receive another adult’s private data merely because of role.
- **FR-032:** Teen and child policy shall implement Section 7 and be covered by automated tests.
- **FR-033:** Every API response containing personal information shall be scoped to the authenticated identity and effective surface policy.
- **FR-034:** Kinward shall log denied private-resource access without logging the protected content.

### 13.5 Surfaces, cards, and layouts

- **FR-035:** Kinward shall support personal mobile, personal desktop, and shared-display layouts in the first cross-surface slice.
- **FR-036:** Every surface shall receive ownership, privacy, room when applicable, interaction capability, and viewing-distance context.
- **FR-037:** The personal default shall include assistant presence, Now, briefing, topics, and persistent input.
- **FR-038:** Now and briefing shall implement Section 12.4.
- **FR-039:** The shared-display default shall show household-safe ambient information and return to that state after personal-session expiry.
- **FR-040:** Product surfaces shall render registered cards from validated layouts.
- **FR-041:** Invalid configuration shall fail safely and preserve the last valid layout.
- **FR-042:** Generated temporary views shall use registered components only.
- **FR-043:** Users shall inspect why an item appeared, source categories, confidence, sharing class, and available correction without exposing hidden reasoning or secrets.
- **FR-044:** Shared-display rendering shall never receive private card data when the effective policy forbids it.

### 13.6 Proactivity, coordination, approvals, and activity

- **FR-045:** Proactive delivery shall support ambient, briefing, nudge, interruption, and autonomous-action levels.
- **FR-046:** Kinward shall default to the least disruptive level consistent with timing, consequence, confidence, and policy.
- **FR-047:** Non-critical interruptions shall respect the default cap in Section 6.4.
- **FR-048:** Kinward shall detect relevant exceptions without requiring routine definitions.
- **FR-049:** A proactive item shall expose why it was delivered at its selected level and allow category-level correction.
- **FR-050:** Coordination requests shall disclose only the minimum information required for a response.
- **FR-051:** Coordination requests shall identify sender or represented person, requested outcome, response options, and expiry.
- **FR-052:** External actions shall implement every authority rule in Section 11.
- **FR-053:** Activity records shall identify requester, acting assistant, represented person, authority basis, approval, integration, attempt, provider result, final result, and undo availability.
- **FR-054:** Users shall filter activity by person, assistant, integration, action category, result, and date.

### 13.7 Calendar integration

- **FR-055:** A person shall connect and disconnect a calendar account without exposing its credentials to other household members.
- **FR-056:** Calendar integration shall read events only within the connected account’s granted scope.
- **FR-057:** Calendar change detection shall identify additions, removals, time changes, location changes, attendee changes, and cancellations.
- **FR-058:** Detected changes shall retain provider event identity, observed version, observed time, and affected account.
- **FR-059:** Private calendar details shall not appear on a shared surface or household fallback context unless explicitly shared.
- **FR-060:** Calendar mutations shall implement Section 11 and reconcile unknown provider results before retry.
- **FR-061:** Integration reconnect shall preserve local configuration while clearly marking stale or unavailable data.

### 13.8 Home Assistant integration

- **FR-062:** Home Assistant shall remain authoritative for physical areas, devices, entities, services, and current state.
- **FR-063:** Kinward shall translate relevant state and actions into household language without requiring entity IDs or service syntax.
- **FR-064:** Kinward shall distinguish observed device state, requested action, submitted action, and confirmed resulting state.
- **FR-065:** A successful service call without confirmed resulting state shall not be described as confirmed physical completion when confirmation is expected.
- **FR-066:** Home Assistant actions shall follow identity, permission, stale-state, approval, and activity requirements.
- **FR-067:** Home Assistant unavailability shall remove or mark stale dependent cards without preventing core Kinward use.

### 13.9 Kinward Control

- **FR-068:** Kinward Control shall be separate from everyday assistant navigation.
- **FR-069:** Administrators shall manage people, invitations, assistants, child policy, household integrations, shared surfaces, proactive defaults, backup status, and health.
- **FR-070:** Adults shall manage their own private integrations, memory, assistant preferences, and sharing without unrelated administrative access.
- **FR-071:** Administrative views shall not expose credentials, hidden prompts, unrestricted private adult content, or model chain-of-thought.
- **FR-072:** Health shall distinguish core failure, degraded optional capability, stale data, reauthorization required, and configuration error.
- **FR-073:** Every degraded state shall include an actionable next step or explicitly state that no action is required.

## 14. Backup, restore, export, retention, and upgrade contract

### 14.1 Included data

The first usable release backup includes:

- household identity and configuration,
- people and account bindings excluding reusable authentication secrets,
- assistants and personality settings,
- privacy, sharing, and authority policies,
- topics and locally stored conversation records,
- confirmed durable facts and sharing metadata,
- layouts and surface assignments,
- integration configuration excluding credentials that cannot be exported safely,
- encrypted credential material where supported,
- approvals and activity history,
- and provider reference mappings required to reconnect optional stores.

### 14.2 Excluded or conditional data

The manifest must identify:

- credentials requiring reauthorization,
- externally stored content not copied into the backup,
- external provider data subject to separate retention,
- caches that can be rebuilt,
- and unsupported historical data.

### 14.3 Requirements

- **FR-074:** Backups shall contain a versioned manifest listing included, excluded, encrypted, externally referenced, and rebuildable data.
- **FR-075:** Restore shall support a clean deployment on the same or a declared compatible schema version.
- **FR-076:** Restore shall complete atomically or stop without replacing the existing valid household state.
- **FR-077:** Post-restore verification shall validate household identity, people, assistants, topics, policies, layouts, activity, durable facts, and provider-reference integrity.
- **FR-078:** Excluded credentials shall be listed as required reauthorization steps.
- **FR-079:** Migration export shall use documented versioned formats independent of the original host path.
- **FR-080:** Upgrade shall require a restorable pre-upgrade backup and stop with actionable instructions when compatibility checks fail.
- **FR-081:** Backup creation and restore shall produce activity records without recording secret material.
- **FR-082:** The product shall document retention behavior for conversations, topics, activity, approvals, durable facts, and integration caches.
- **FR-083:** Deleting a person shall require an explicit disposition for owned assistants, topics, facts, integration connections, shared contributions, and required audit records.

## 15. Nonfunctional requirements

### 15.1 Privacy and security

- **NFR-001:** Server-side authorization shall protect every private resource and every provider query.
- **NFR-002:** Secrets and credentials shall be encrypted at rest or stored in a platform-appropriate secret mechanism and shall not appear in normal responses or logs.
- **NFR-003:** Automated tests shall cover every shared-surface state and transition.
- **NFR-004:** Automated tests shall cover adult, teen, child, administrator, personal-assistant, specialist-assistant, and household-fallback boundaries.
- **NFR-005:** External content shall be treated as untrusted and shall not override authorization, system policy, or action authority.
- **NFR-006:** Data sent to external providers shall be minimized to the permitted task.
- **NFR-007:** Authentication, invitation, approval, and handoff tokens shall expire and be protected against replay.
- **NFR-008:** Normal logs and telemetry shall not contain full private prompts, conversation bodies, credentials, or unrestricted integration payloads.
- **NFR-009:** Security-sensitive configuration changes shall produce append-protected audit records.

### 15.2 Reliability and recoverability

- **NFR-010:** Optional provider failure shall not prevent setup, authentication, local administration, backup access, or local topic access.
- **NFR-011:** External calls shall use explicit timeouts, bounded retries, and failure isolation.
- **NFR-012:** External mutations shall be idempotent where supported or protected against duplicate execution.
- **NFR-013:** A clean-deployment restore test shall pass before the first usable release.
- **NFR-014:** Automated backup/restore acceptance tests shall have zero known loss of data included in the backup contract.
- **NFR-015:** Restarting Kinward during an in-progress action shall not convert an unknown or incomplete action into completed.
- **NFR-016:** Background jobs shall be observable, retry-bounded, and recoverable without duplicate user-visible outcomes.

### 15.3 Performance thresholds

Measured on the documented reference deployment under normal local-network conditions:

- **NFR-017:** Cached personal-home content shall become interactive within 2 seconds at p95; cold load within 4 seconds at p95.
- **NFR-018:** A submitted assistant request shall show accepted or responding state within 500 ms at p95.
- **NFR-019:** When a provider streams, first visible response content shall appear within 3 seconds at p95, excluding documented provider outage conditions.
- **NFR-020:** Private shared-surface content shall be removed within 250 ms of the client receiving an identity downgrade and within 1 second of backend detection.
- **NFR-021:** Local-only API reads and writes shall complete within 500 ms at p95 under the documented reference load.
- **NFR-022:** The shared display shall return to household-safe state within 1 second of session expiry detection.

### 15.4 Accessibility and usability

- **NFR-023:** Core web/PWA experiences shall meet applicable WCAG 2.2 AA requirements.
- **NFR-024:** Shared-display controls shall meet UX-specified room-distance readability and touch-target requirements.
- **NFR-025:** Keyboard-only users shall complete onboarding, conversation, topic continuation, approval, and basic Kinward Control workflows.
- **NFR-026:** Status shall not rely solely on color.
- **NFR-027:** Ordinary household workflows shall use household language and shall not require infrastructure or provider terminology.
- **NFR-028:** Destructive actions, privacy-sharing changes, and external mutations shall clearly state consequence before confirmation.

### 15.5 Portability and maintainability

- **NFR-029:** Capability interfaces shall avoid direct product dependency on one model, memory, knowledge, calendar, email, or smart-home provider.
- **NFR-030:** Cards, layouts, policies, schemas, provider references, and backup manifests shall be versioned for migration.
- **NFR-031:** Accepted foundations and Milestone B/C requirements shall have automated validation gates before being marked complete.
- **NFR-032:** Public repository fixtures and examples shall use fictional or synthetic data only.
- **NFR-033:** Current documentation shall remain separate from archived Homefront SaaS and routine-centric artifacts.

### 15.6 Observability and supportability

- **NFR-034:** Health reporting shall distinguish application, database, model, memory, knowledge, calendar, Home Assistant, background-work, and backup capabilities.
- **NFR-035:** Operators shall correlate a user-visible failed action with its sanitized activity and operational event without exposing private content.
- **NFR-036:** Metrics shall include request latency, provider latency, provider failure, action result, job backlog, privacy-policy denial, and backup result without high-cardinality private labels.
- **NFR-037:** A household administrator shall obtain a sanitized diagnostic bundle that excludes credentials and private conversation bodies.

## 16. Delivery milestones and exit gates

### Milestone A: Accepted foundation

**Content:** Repository reset, domain and persistence baseline, bootstrap API, optional integration resilience, neutral memory/knowledge contracts, provider adapters, registry frontend proof of concept, Docker, CI, `mise`, and `uv`.

**Exit gate:** Existing migration-status acceptance remains valid and tests pass from a clean checkout.

### Milestone B: First cross-surface assistant slice

**Content:** Authentication, onboarding UI, text assistant endpoint, request lifecycle, topic persistence, permission-bound context assembly, live mobile view, live desktop continuation, live household-safe shared-display representation, backend privacy tests, explanation surface, and activity evidence for the demonstrated flow.

**Exit gate:** Every condition in Section 4.1 passes in an automated or inspectable demonstration using non-private synthetic fixtures.

### Milestone C: First usable household release

**Content:** Invited second adult, separate adult assistants and memory, durable-fact management, calendar change detection, Home Assistant state and approved action, deterministic identity policy, external-action policy, basic Kinward Control, degraded-mode behavior, versioned backup manifest, clean restore verification, and performance/accessibility/security gates.

**Exit gate:** Every mandatory capability in Section 4.2 exists, all Section 6 trust and operations conditions are measurable, and no critical privacy or data-loss defect is open.

### Milestone D: Coordinating household assistant

**Content:** Email, progressive onboarding, coordination requests, proactive evaluation, richer topics/cards, and layout editing.

**Exit gate:** Coordination and proactivity have explicit household controls, privacy tests, counter-metric reporting, and rollback or correction behavior.

### Milestone E: Voice and advanced experiences

**Content:** Voice orchestration, private handoff, emergency mode, maintenance recall, and native evaluation based on measured PWA limitations.

**Exit gate:** Voice privacy, interruption, identity uncertainty, and screen handoff are validated independently from visual UI assumptions.

## 17. Requirement-to-journey coverage

- UJ-1 is primarily covered by FR-001 through FR-008 and FR-068 through FR-073.
- UJ-2 is primarily covered by FR-005 through FR-011 and FR-028 through FR-034.
- UJ-3 is primarily covered by FR-013 through FR-017 and FR-035 through FR-044.
- UJ-4 is primarily covered by FR-045 through FR-061.
- UJ-5 is primarily covered by FR-028 through FR-044 and NFR-001 through NFR-009.
- UJ-6 is primarily covered by FR-045 through FR-060 and Section 11.
- UJ-7 is primarily covered by FR-032 and Section 7.4.
- UJ-8 is primarily covered by FR-027, FR-061, FR-067, FR-072 through FR-073, and NFR-010 through NFR-016.
- UJ-9 is primarily covered by FR-074 through FR-083 and NFR-013 through NFR-014.

Epic and story decomposition must preserve this coverage. No journey may depend only on an untracked narrative statement.

## 18. Architecture decisions required

Architecture must resolve:

- default authentication, session, invitation, and recovery mechanism,
- initial model-provider contract and streaming/cancellation behavior,
- assistant runtime and tool-execution boundary,
- topic and conversation persistence model,
- context assembly and authorization enforcement points,
- physical storage split among Kinward, Honcho, and LLM-Wiki,
- invalidation and deletion behavior for externally stored derived data,
- calendar synchronization transport and freshness model,
- accepted mechanisms for `verified` shared-surface identity,
- background-job and action-reconciliation design,
- credential storage, backup encryption, and portability,
- activity retention and append-protection strategy,
- diagnostic data redaction,
- and the reference deployment and load used for performance testing.

These decisions may select mechanisms but may not weaken the product outcomes, privacy boundaries, action states, or release gates defined in this PRD.

## 19. Open product decisions

The following require explicit product-owner decisions before affected stories are implementation-ready:

1. Default inactivity timeout for shared-display personal sessions within the maximum defined in Section 10.
2. Which child durable-fact categories are guardian-visible by default versus opt-in.
3. Whether the first calendar integration supports one provider or a vendor-neutral local calendar source first.
4. Initial proactive categories enabled by default during the household pilot.
5. Default retention periods for private conversations, archived topics, activity, and approvals.
6. Whether backup archives include encrypted credential material by default or require reauthorization for every integration.
7. Which forms of explanation and correction are required on the first shared display versus private handoff.

Unresolved decisions must be carried into epics as explicit blockers or assumptions with owners. They must not be silently decided inside implementation stories.

## 20. PRD readiness criteria

This PRD may be marked final only when:

- repository safety review confirms no private household names, addresses, credentials, infrastructure identifiers, or private fixtures,
- every source path resolves,
- user journeys and requirement coverage are accepted,
- deterministic privacy, data-classification, assistant-boundary, and action policies are accepted,
- the first cross-surface slice and first usable release boundaries are accepted,
- success thresholds and counter-metrics are accepted as pilot targets,
- every open product decision has an owner and disposition,
- architecture can map every Milestone B and C requirement to a concrete boundary,
- epics map every functional and nonfunctional requirement without creating competing scope,
- stories for Milestone B include acceptance tests for privacy, failure, degraded mode, and observability,
- and implementation-readiness review finds no unresolved blocker for Milestone B.
