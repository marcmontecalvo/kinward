---
status: draft
createdAt: "2026-07-13"
updatedAt: "2026-07-14"
documentType: "BMAD Product Requirements Document"
sourceDocuments:
  - "_bmad-output/planning-artifacts/product-brief-Kinward-Assistant-Experience.md"
  - "_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md"
  - "docs/pivot/single-household-pivot-and-rebuild-plan.md"
  - "docs/pivot/salvage-matrix.md"
---

# Product Requirements Document: Kinward Assistant Experience

**Product:** Kinward  
**Delivery model:** Private, single-household, Docker-deployed web/PWA platform

## 1. Purpose

Kinward is a private household intelligence platform in which each account-bearing household member has exactly one primary personal AI assistant in the first usable release. It combines durable personal and household context, privacy-bound memory, external integrations, and adaptive surfaces so that people can ask once, delegate outcomes, and receive useful exceptions without manually programming ordinary household life.

**Product thesis:** Kinward replaces routine construction with durable-fact inference and privacy-enforced personal assistance, so household members can delegate outcomes without surrendering control of their information or actions.

The primary product is the relationship between a person and their assistant. Cards, dashboards, chat history, integrations, and smart-home controls are supporting representations.

Kinward is not:

- a multi-tenant SaaS product,
- a routine or alarm builder,
- a generic chatbot,
- a family surveillance system,
- a shared repository of everyone’s private information,
- or a replacement for Home Assistant’s device registry and automation engine.

All unresolved scope or mechanism choices are represented by the open AD and PD records in Sections 18 and 19. Their stated safe interim behavior applies until resolution; this PRD makes no additional unstated assumptions.

## 2. Product outcomes

Kinward must:

1. Give each person a private, continuous assistant relationship.
2. Infer useful household logistics from durable facts and changing conditions rather than requiring routine construction.
3. Coordinate information and actions without exposing one person’s private memory to another person or to a household-shared assistant.
4. Continue authorized work across personal mobile, personal desktop, and shared-display surfaces without requiring the person to restate available context.
5. Surface what matters now while suppressing low-value noise.
6. Make external actions explicit, permission-bound, and reviewable, and disclose whether a verified inverse operation is available; otherwise mark the action irreversible before approval.
7. Make uncertainty, degraded capability, and incomplete work visible.
8. Remain household-owned and operable without a SaaS control plane.
9. Provide polished defaults so ordinary household use requires no infrastructure or configuration knowledge.

## 3. Product concepts and definitions

### 3.1 Personal assistant

An assistant owned by exactly one person. The first usable release provides exactly one **primary personal assistant** for each account-bearing person; it may use only information and capabilities that person is authorized to use, and its conversation, topics, personal memory, and personal integration data are private by default. Additional personal assistants are a non-committed planning horizon and require a future PRD amendment under Section 4.3. They are not implied by replacement lifecycle, salvage of the personal-assistant boundary, or the separate specialist-assistant concept.

### 3.2 Specialist assistant

An optional assistant owned by exactly one person and focused on a domain or temporary purpose. It never receives broader access than the owner’s primary assistant. Specialist creation, invocation, and delegation are a non-committed planning horizon; before a future PRD amendment may enable them, FR-089 and NFR-004 require the ownership and delegation boundary to be delivered and verified. When introduced, the primary assistant remains the default router unless the person explicitly invokes or delegates to a specialist.

### 3.3 Household fallback assistant

A household-owned assistant, provisioned during bootstrap with no personal owner, used for household-safe questions, shared information, timers, announcements, shared lists, media, and permitted Home Assistant actions. It is not a combined personal assistant and must never query or synthesize private personal memory.

### 3.4 Topic

A durable unit of ongoing work such as a trip, school project, maintenance issue, purchase decision, event, or household plan. A topic may contain conversation, decisions, artifacts, permitted integration references, assistant progress, approvals, and outcomes. It is not merely a chat thread.

### 3.5 Durable fact

A stored, explicitly confirmed statement intended to influence future assistance. Every durable fact has an owner or household scope, sharing class, source category, confirmation state, confidence, creation time, and update time. An inferred observation may be stored pending confirmation but is not a durable fact and may not influence future assistance as one until confirmed.

A **pending inferred observation** is a time-limited candidate fact governed by Section 8.4. It has a named subject or household scope, an authorized fact owner, source dependencies, and an expiry; before confirmation it exists only for inspection and disposition and cannot personalize assistance, trigger proactivity, authorize an action, or enter shared or fallback context.

### 3.6 Surface

A rendered interaction context. Initial live-supported classes are personal mobile, personal desktop, and shared display. A **shared surface** is any household-owned rendered context governed by Section 10; a **shared display** is the initial web/PWA shared-surface class. Personal tablet, shared kitchen, and shared living-room layouts must additionally render in the mock-backed frontend-foundation gate (Section 4.1.1) so the surface architecture is validated across all five authoritative contexts. Live personal-tablet and voice surfaces are non-committed product directions governed by Section 4.3, not implementation-ready release scope.

### 3.7 External action

An operation submitted to a system outside Kinward with the intent to change external state or communicate. Reads and prepared-but-unsubmitted proposals are not external actions.

### 3.8 Meaningful external action

An external action, or a Kinward coordination action, that communicates on a person’s behalf, affects another person, changes money or commitments, changes security or access, or changes household physical state. Every meaningful external action receives the approval and activity treatment in Section 11; no undefined consequence threshold exempts one.

### 3.9 Generated temporary view

An assistant-created, purpose-specific arrangement of registered cards. It declares a title, purpose, card instances, layout hint, and persistence mode (`ephemeral`, `topic`, or `pinned`). An `ephemeral` view and its unsaved data use the `surface-ephemeral` class and are deleted at every normal or abnormal authorized-session end. A `topic` view becomes durable only through an explicit save into an authorized topic and thereafter inherits that topic's ownership, class, narrowing, archive, and deletion lifecycle. A `pinned` view becomes durable only through an explicit pin into the pinning person's authorized scope and remains until unpinned, deleted, or invalidated by a source or authorization change. Reopening or rerendering never upgrades persistence, and invalidated views and copies clear under Sections 8.1 and 8.2. A generated view never contains arbitrary generated client code.

### 3.10 SaaS control plane and Kinward Control

Forbidden **SaaS control-plane behavior** includes provisioning or routing among multiple households, tenant administration, billing or entitlements, vendor-operated managed deployment, and support-operator access. Permitted **Kinward Control** is the local administrative experience for authorized members of the one household in this deployment; it manages only that household and remains separate from everyday assistant navigation.

## 4. Release boundaries

### 4.1 Cross-surface foundation and first live slice

#### 4.1.1 Frontend-foundation gate (mock-backed)

Before the first live slice, the frontend foundation must render the source-defined common capability set — Assistant Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Assistant Input — from one card registry and one layout registry across all five authoritative surface contexts:

- personal mobile,
- personal tablet,
- personal desktop,
- shared kitchen display,
- and shared living-room display.

This gate uses synthetic mock data and mock adapters, consistent with the rebuild plan's frontend-foundation phase preceding the household foundation. It must exercise real layout resolution, room and viewing-distance context, density adaptation, and deterministic per-surface privacy-policy resolution, and it must pass automated or inspectable checks. Mock data is acceptable only in this gate; its purpose is to validate the surface, privacy, card, and layout architecture across every authoritative context before live behavior narrows it.

#### 4.1.2 First live cross-surface slice

The first live implementation milestone must demonstrate one real assistant capability across:

- personal mobile,
- personal desktop,
- at least one live shared-display context (kitchen or living room),
- and backend privacy enforcement.

**Shared display live count:** at least one of the two mock-foundation shared-display contexts (kitchen or living room) must use live data and backend privacy enforcement in this slice; live delivery of the other is not committed without a future PRD amendment under Section 4.3.

For the purpose of this slice, a shared fixture is either a topic explicitly classified `household-shared`, or a separately reviewable, minimum-necessary household-safe coordination statement derived from a private topic and explicitly approved as `household-shared` under Section 8.2; unshared is neither — a private topic with no `household-shared` classification and no approved `household-shared` coordination statement. The slice uses two fictional fixture topics: one shared fixture and one fixture that remains `private-person` and unshared. When the coordination-statement branch is used, only that approved statement may render on the shared display; the private source topic remains entirely absent from shared-display responses and payloads, including any indication that it exists.

The slice is complete only when one authenticated adult can:

1. submit a text request on a personal mobile surface,
2. see the request accepted and receive an incremental response,
3. create or update a persisted topic,
4. continue that topic on a personal desktop without restating stored context,
5. view a live household-safe representation of the explicitly shared topic on a shared display,
6. inspect why that shared item appeared and what information class it contains,
7. confirm through automated tests that private details of the shared topic cannot reach the shared response or payload,
8. and confirm through automated tests that the unshared private topic is entirely absent from shared-display responses and payloads, including any indication that it exists. Absence is the required and sufficient privacy behavior for an unshared private topic; a shared surface must never be forced to disclose that a private topic exists.

Static mock data in the live slice, client-only filtering, hard-coded person IDs, or hiding the explicitly shared topic instead of rendering its household-safe representation do not satisfy this milestone.

### 4.2 First usable household release

The first usable household release must include:

- single-household bootstrap and authenticated accounts,
- the complete active, disabled, locked, and recovery-pending account lifecycle,
- the separate deletion-pending person lifecycle and its immediate account-authority shutdown,
- invitation and onboarding for at least one additional adult,
- optional pet profiles without accounts or authority,
- exactly one primary personal assistant per account-bearing person, with separate conversations, topics, integrations, and memory boundaries,
- owner-controlled primary-personal-assistant lifecycle without cross-person reassignment,
- text conversation and topic continuity,
- live personal mobile and desktop surfaces,
- a live privacy-conservative shared display,
- single-use intended-person private-device handoff with destination reauthorization,
- confirmed durable-fact management,
- pending inferred-observation inspection, confirmation, rejection, expiry, and restore lifecycle,
- one read-capable calendar integration with change detection,
- purpose-specific calendar and transportation recipient assignment,
- one calendar mutation flow with exact approval, unknown-result reconciliation, and activity records,
- one Home Assistant state-and-action flow,
- approval and activity records for meaningful external actions,
- basic Kinward Control for people, assistants, integrations, privacy, activity, backup, and health,
- direct household-authored content management and restore disposition under the current-administrator ownership/conflict policy,
- documented degraded behavior for unavailable optional capabilities,
- a new single-household baseline schema with controlled versioned import of explicitly allowed household data,
- confidentiality- and integrity-protected backup availability while AD-12 is open,
- and tested backup and restore of the defined household data contract, including unresolved-action blocking state.

The release is not usable if authentication, adult-to-adult privacy separation, shared-display backend privacy enforcement, external-action activity records, clean restore validation, or a working assistant conversation path is absent.

### 4.3 Committed later delivery and non-committed planning horizons

Milestone D is the only committed later delivery milestone. Its scope is limited to the requirements whose Section 17.4 rows carry D and the supporting behavior they expressly define: FR-042, FR-045–FR-047, FR-049–FR-054, FR-089, FR-096, and the Milestone D portions of NFR-004, NFR-009, NFR-012, NFR-015, NFR-028, and NFR-039. This statement does not enable specialist assistants or imply any capability beyond those requirements.

The following are non-committed planning horizons, not delivery scope or implementation-ready backlog:

- email reading and sending,
- additional personal assistants beyond the one primary personal assistant per account-bearing person,
- specialist-assistant creation, explicit invocation, and delegation beyond the FR-089 prerequisite boundary,
- voice-only endpoints and cross-surface voice handoff,
- personal-surface push-to-talk input,
- personal-surface camera capture,
- personal-surface screenshot capture or attachment,
- personal-surface file attachment or ingestion,
- personal-surface current-screen context access,
- any other personal-surface multimodal input,
- typed commands that target current-screen, selected-object, application, or other ambient context,
- richer topics, cards, or proactive coordination beyond issued requirements,
- visual or declarative layout editing,
- emergency surface mode,
- any emergency or legal exception to the unconditional denial of private-teen disclosure outside owner-authorized privacy-filtered sharing; such an exception requires its own policy, authority decisions, teen and recipient notice, append-protected audit rules, privacy and misuse tests, and an explicit future PRD amendment before any design or implementation,
- contextual maintenance recall,
- progressive school, work, personal, home, and transportation onboarding,
- live personal-tablet-specific workspaces,
- and native-platform evaluation or capabilities requiring operating-system access.

The safe interim for every personal-surface input horizon listed above is unavailable: committed surfaces accept text input only, and typed input carries only the text and explicit topic/surface context already authorized by Sections 12.1 and 12.2. Kinward shall not capture, attach, infer, or receive microphone, camera, screenshot, file, current-screen, selection, application, or ambient-device context, and shall not interpret typed text as a context-targeted command. Enabling any one of these capabilities requires the future PRD amendment defined below; enabling one does not imply any other.

Any horizon requires a future PRD amendment that adds or updates applicable journeys, FRs/NFRs, Section 17.4 trace rows, journey-summary coverage, milestone placement, success evidence, privacy and failure gates, and decision-register impacts before epic or story creation. Horizon descriptions preserve product direction only and do not authorize design or implementation.

### 4.4 Explicit exclusions

Kinward excludes:

- multi-household tenancy in one deployment,
- SaaS control-plane behavior as defined in Section 3.10; local Kinward Control is permitted,
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

**Alex**, an adult household administrator, opens a new deployment. Before the initial commit, Alex creates the initial account, names the household, creates a profile, selects another adult and a child as profiles without requiring their accounts, optionally selects a pet profile without an account, names Alex's primary personal assistant, and completes a short personality interview. The atomic operation includes all profiles selected before commit—including every adult, child, and pet profile—and only after it succeeds does Alex enter Kinward.

Alex is not required to configure integrations, rooms, devices, routines, detailed schedules, notification rules, or layouts.

**Successful outcome:** The household, account binding, every pre-commit people profile, any optional pet profile, Alex's primary personal assistant, and household fallback assistant are created with the transactional retry/rollback outcome defined by FR-002 and FR-091. A retry cannot duplicate a selected profile or binding. Alex reaches a useful personal home surface and sees optional next setup steps without being blocked.

**Failure outcome:** If setup fails before commit, no partially configured household is presented as usable. The product explains whether setup can be retried or requires restore/reset.

### UJ-2: Invited adult receives a separate assistant

**Jordan** accepts an invitation for an existing household profile, authenticates, confirms the intended profile, names Jordan's primary personal assistant, completes the same personality and interaction-preference interview required by FR-012, and enters a private personal surface.

**Successful outcome:** Jordan has a distinct account binding, assistant, memory boundary, topics, and personal integration space. No private content from Alex is visible or used.

**Failure outcome:** An expired or mismatched invitation cannot silently create a duplicate profile or attach to the wrong person.

**Account-state outcome:** A fixture disables Jordan's account, locks it after a security event, and enters recovery-pending through the authorized recovery path. Each non-active state immediately invalidates Jordan's active authority and security artifacts, removes private surfaces and assistant/provider access, suppresses proactivity, and expires or cancels unsubmitted work without transferring ownership. Reactivation binds Jordan to the same profile and retained data only after the Section 7.7 reauthentication, recovery, and authorization revalidation steps; submitted or `unknown` actions remain reconciliation-blocked throughout.

**Correction and binding-suspicion outcome:** Jordan directly corrects Jordan's preferred name and, as the adult subject, corrects one directly household-authored `household-shared` relationship fact. Each atomic correction refreshes or invalidates dependent policy without broadening authority. A stale concurrent correction fails closed. A separate fixture presents evidence that an account may be bound to the wrong profile; Kinward suspends every implicated access path under Section 7.8, offers no rebinding or private-state transfer, and permits recovery only when it proves the original intended same-profile binding. Otherwise access remains denied pending a future separately specified adjudication.

### UJ-3: A topic continues across surfaces

Jordan asks on a phone for help comparing options for a family trip. Kinward creates a trip topic with the permitted conversation and decisions. Later, Jordan opens Kinward on a desktop and continues from the same state.

**Successful outcome:** The desktop shows the current topic, decisions, unresolved questions, and assistant progress without requiring the original request to be repeated.

**Shared-display outcome:** The household display may show a generic item such as "Trip planning is active" when the topic is `household-shared` or when an approved `household-shared` coordination statement exists for the topic under Section 8.2. Only the household-safe topic representation or the approved coordination statement may render; it must never show private preferences, costs, messages, source details, or any topic-existence metadata beyond the approved statement.

**Non-committed specialist horizon:** A future PRD amendment may let Jordan explicitly delegate a bounded part of the trip topic. Before that capability can be enabled, the exchange boundary must satisfy FR-089 and NFR-004; expiry, revocation, or a record that permits more data than the task requires ends the exchange without broadening either assistant's access. This branch is directional context, not implementation-ready scope.

### UJ-4: Kinward surfaces a calendar change

**Sam**, Alex's fictional 10-year-old child, has an early-release event added to a permitted connected calendar. Kinward compares that change with confirmed household transportation facts and the calendars that Alex and Jordan have permitted for this purpose.

**Successful outcome:** The adults assigned for the specific calendar and transportation purpose under FR-092 receive a concise briefing item that identifies what changed, why it may matter, which source category supplied it, and whether action is required. The assignment is inspectable by Sam when Sam has an account and by every named adult. If no valid recipient is assigned or the facts are unconfirmed, Kinward does not infer responsibility or deliver the item; only an administrator authorized to manage Sam's policy receives a household-safe configuration-gap notice with no private event details.

**Non-goal:** Kinward does not create a recurring routine, infer a permanent transportation responsibility without confirmation, or interrupt everyone by default.

### UJ-5: Shared display refuses private disclosure

Jordan asks a shared display about a private appointment while another person is present or identity is not verified.

**Successful outcome:** Kinward provides a household-safe response and offers a single-use private-device handoff bound to Jordan as the intended person. Before the destination authenticates, the handoff carries only a neutral continuation instruction, opaque single-use redemption reference, expiry, and destination capability—not a name, topic, source, private-record-existence signal, or private content. At redemption, the backend re-evaluates intended identity, account state, topic access, current sharing and source authorization, and surface policy before any private retrieval. An authorized redemption reaches `accepted`; Jordan may instead produce `declined`, and timeout, sender or policy withdrawal, or lack of an authorized reachable target produces `expired`, `revoked`, or `unreachable`. Wrong-person redemption, replay, identity downgrade, authorization loss, or revocation fails closed, consumes or terminally invalidates the reference as applicable, and reveals neither private content nor that a private record exists. No private appointment details appear in rendered UI, pre-authentication API payloads, logs intended for ordinary administration, or household-fallback context.

### UJ-6: A prepared action requires exact approval

Alex asks Kinward to change Sam's calendar appointment. Because the adult-initiated action represents and targets a child, Kinward applies Sam's current action-category policy, gives the required minor notice, routes approval only to its named adults and quorum, and fails closed if that assignment is missing or invalid. The assistant prepares a proposed mutation and presents the exact date, time, calendar, affected event, integration, represented minor, expected consequence, and reversibility status without disclosing Sam's private source content.

**Successful outcome:** Approval executes only the exact prepared mutation. If source state changed, approval expires and the assistant prepares a new proposal instead of applying stale intent.

**Unknown-result outcome:** If the provider result is unknown, the approval is consumed, the action remains `unknown`, and Kinward reconciles the provider state before any new proposal can execute. A restart preserves that state. A concurrent proposal for the same target cannot execute until reconciliation and revalidation against current source state.

**Home Assistant branch:** Using an ordinary household-assigned room/device name, Alex asks Kinward to change a household device in a way that materially affects Sam. Kinward separately renders `observed` with the last device state and observation time, records Alex's `requested` action, shows the exact policy-routed prepared effect, and identifies whether the action has become `submitted`. Sam's minor-category policy applies regardless of Alex being the requester; only the adults named by that policy may satisfy its quorum, and no valid assignment means no preparation or submission. `Submitted` is never presented as complete. A subsequently observed matching physical state produces `confirmed`; a service-call success without matching observed state, stale observation, disconnect, timeout, or conflicting state produces `unknown` and preserves reconciliation and same-target blocking. Non-minor household fixtures exercise the same general multi-principal lifecycle when another adult or multiple household principals must approve.

### UJ-7: A child receives bounded assistance

**Sam**, Alex's fictional 10-year-old child, authenticates to Sam's policy-permitted account, starts a private minor conversation, asks for homework help, and later asks the assistant to prepare a fictional message to a teacher.

**Successful outcome:** Homework help can proceed within policy. Kinward may prepare the fictional message, but submission is unavailable; a future PRD amendment is required before any message-sending capability can exist, and it must retain approval by an adult named in Sam's action-policy assignment. Before any approval-required minor flow could disclose fields to a named adult, Sam sees which fields would be shared, with whom, and why. The minimum-necessary approval view excludes Sam's conversation and excludes the prepared message body unless that body is required to approve the exact future action and Kinward separately tells Sam before sharing it. Sam can cancel the prepared work, and deterministic expiry also leaves it unsubmitted. Sam's ordinary conversation is never automatically copied into an adult's memory.

**Teen branch:** **Riley**, a fictional 15-year-old, can see that private conversations and facts remain private, which explicitly shared categories are visible to named adults, and that no teen category is guardian-visible by default. When Riley requests a transportation booking or future message submission, Kinward either routes a minimum-necessary approval to the adult named for that action category or does not submit; it never broadcasts the request to all administrators. Before any approval view derived from Riley's private teen content is created or sent, Riley explicitly authorizes the exact recipients, fields, purpose, and expiry of a new, separately reviewable privacy-filtered `selected-share` item. Missing, expired, revoked, or mismatched sharing authorization denies both disclosure and submission, even when the adult is a named approver. Riley can cancel an awaiting request, and expiry leaves the action unsubmitted.

### UJ-8: Optional providers are unavailable

**Jordan** opens Kinward while the optional memory provider and Home Assistant are both offline and a connected calendar is stale after a failed sync.

**Successful outcome:** Kinward still starts, authenticates users, durably updates locally stored topics and configuration, permits local administration and backup, and separately marks every dependent capability unavailable or stale. It does not fabricate remembered facts, deliver stale calendar data as current, or claim a device action succeeded. A submitted-but-unconfirmed action remains `unknown` through the outage and is not retried until reconciliation.

### UJ-9: Administrator restores the household

Alex restores a supported backup to a clean compatible deployment.

**Successful outcome:** Before restore, Kinward warns Alex that the archive is a point-in-time household snapshot and may contain content deleted, revoked, or narrowed after it was made, which the archive alone cannot reveal. Household identity and direct household configuration restore normally. Direct household-authored facts, topics, and other user content remain quarantined and absent from shared-display and household-fallback context until disposition under the current-administrator content-ownership lifecycle in Sections 8.5 and 14.3; household-shared derived statements never reactivate. A no-conflict fixture permits one current administrator to republish after inspection, while conflicting administrator dispositions keep the content quarantined until all current administrators agree or an explicit versioned household policy resolves the conflict. People and pet profiles, assistants, policies, layouts, activity, confirmed facts, unexpired pending observations, supported provider mappings, and every preserved unresolved-action blocking state pass verification. A deletion-pending fixture restores disabled with its overlay and reconciliation-only restriction intact, including after abandonment. Excluded credentials are listed as explicit reauthorization tasks. Alex re-establishes administrator access through the documented secure recovery procedure bound to the existing restored administrator profile; every personal account and every restored personal, private, or `selected-share` item remains disabled or quarantined until its restored owner reauthenticates and explicitly reauthorizes its access or disposition. Every pre-restore session, invitation, approval, and handoff token is invalid; recovery cannot create a duplicate profile or bind an account to a different person's profile; and restore never silently completes, retries, or unblocks an unresolved action.

### UJ-10: Household coordination reaches visible closure

**Maya**, an adult household member, asks her primary assistant to coordinate a household task with **Theo**, another adult. Kinward delivers one minimum-necessary request to Theo. Theo can accept, decline, or counter; expiry, sender withdrawal as revocation, authorization revocation, delivery failure, duplicate responses, and concurrent responses resolve under the deterministic Section 13.6 coordination state machine to exactly `accepted`, `declined`, `countered`, `expired`, `revoked`, or `delivery-failed`, and both people see the same authorized terminal state without either person's private source being disclosed.

Maya then asks for a generated view of the task and explicitly chooses each supported disposition in turn: leave one view ephemeral, save one to its authorized topic, and pin one to her authorized scope. The ephemeral view disappears at session end, while the topic and pinned views follow the durable ownership, narrowing, invalidation, and deletion rules in Section 3.9.

During the Milestone D pilot, Maya receives a permitted nudge and a permitted non-critical interruption, each classified against Maya's versioned personal review-opportunity setting and household timezone; inspects why each appeared; and corrects the category. A bounded autonomous action fixture then records either a verified inverse and its requested rollback result, or an irreversible outcome disclosed before authority is used; failure or unknown rollback is visible and never described as completed. No specialist assistant is created, invoked, or enabled in this journey.

**Successful outcome:** Coordination delivery and response, generated-view disposition, proactive explanation/correction, and autonomous-action consequence and rollback evidence all reach accurate visible terminal states under expiry, revocation, concurrency, privacy, activity, and evidence-catalog rules.

### UJ-11: Administrator performs a controlled import

**Nora**, a fictional household administrator, imports a supported versioned household-data package into a valid clean single-household baseline. The package contains the complete minimum import set (the required minimum positive set): people and profile relationships; one primary personal assistant and personality settings for each mapped account-bearing person; confirmed durable facts with provable ownership and sharing class; non-secret integration configuration; and Home Assistant mappings.

**Successful outcome:** Kinward validates the whole candidate household graph before commit, imports every valid minimum class atomically, idempotently skips and reports exact duplicates, quarantines personal/private and `selected-share` content for same-owner authentication and disposition, quarantines qualifying direct household-authored content under FR-097, lists manifest-declared credential reauthorization and unsupported legacy-state tasks without importing those records, and produces a privacy-safe report without exposing protected bodies.

**Failure and rollback outcome:** Separate fixtures introduce a conflicting duplicate in every minimum class; a class-specific invalid ownership, sharing, cardinality, configuration, or mapping record; a credential; a derived shared statement; and an unsupported legacy record. Every invalid package is rejected as a whole; no partial person, relationship, assistant, binding, authority, fact, configuration, or mapping remains, and the database is bit-for-bit or contract-equivalent to its prior valid state. Correcting the package and starting a new explicit import is permitted; the failed import is never resumed or partially committed.

## 6. Measurable success and counter-metrics

The first usable household release (Milestone C) must meet the conditions in Sections 6.1 through 6.4 during a 30-day household pilot. Its parent-follow-up outcome compares that pilot with the immediately preceding 14-day baseline defined below. Milestone C proactive delivery is limited to the ambient and briefing levels (Section 13.6), so its pilot measures only those levels. Metrics that depend on nudges, interruptions, autonomous actions, or coordination requests gate Milestone D and are listed separately in Section 6.5.

The single pilot evidence contract, including its selection and evidence-close contract, is:

- **Windows and populations:** The Milestone C window is the first 30 consecutive calendar days after two adult pilot participants have completed onboarding and all Milestone C capabilities are enabled. Its populations are all accepted adult assistant sessions, all cross-surface continuations, all rendered Now and Briefing UI items, all meaningful external-action attempts, all shared-surface sessions and identity transitions, all authorization tests, all provider-result transitions, all ordinary-workflow support incidents, all proactive deliveries, and all canonical parent-follow-up events during that window. The parent-follow-up baseline is the immediately preceding 14 consecutive household-local calendar days for the same participating parents/guardians and minor household members, captured with the same instrument and frozen rubric before Milestone C begins. The Milestone D window is a separate 30 consecutive calendar days beginning only after its delivered levels and the proactive categories recorded by PD-04 are enabled; its populations add all nudges, interruptions, autonomous actions, and coordination requests in that window.
- **Selection and minimums:** Percentage metrics in Sections 6.1, 6.4, and 6.5 use the first consecutive eligible events in timestamp order across all pilot participants, never a hand-picked subset: at least 30 accepted assistant sessions, 20 cross-surface continuations, 20 rendered Now/Briefing items, 20 completed assistant actions, 20 Milestone D nudges, and 20 Milestone D autonomous actions. The Milestone D autonomous intent/scope error rate is the exception to sampling: once its minimum of 20 is reached, it uses every autonomous action and every dispute or adjudication in the window. Session utility requires closed rated or observed evidence for all 30 selected sessions, and Now/Briefing utility requires closed rated or observed evidence for all 20 selected items. Milestone D coordination evidence requires at least 20 coordination requests even though its zero-tolerance privacy result uses all requests. If a population does not reach its minimum, or a required selected event lacks closed evidence, that metric has insufficient evidence and its milestone gate does not pass. Adoption counts use all pilot participants and days.
- **Zero-tolerance population:** Mandatory meaningful-action record completeness, daily interruption caps, privacy/disclosure conditions, authorization conditions, incorrect-completion conditions, disabled-level conditions, coordination minimum-disclosure conditions, and every other zero-tolerance metric use every eligible event in the applicable 30-day pilot window plus the complete required automated test matrix; they are never sampled.
- **Utility, reliability, and adjudication:** A response or accurate terminal state is reliability evidence, not usefulness. A selected session or Now/Briefing item counts as useful only when its participant affirmatively marks it useful, completes its offered action, or a different benefit named in the product owner's pre-window rubric is directly observed. Silence, absence of dispute, or a missing disposition is missing evidence and never affirmative utility. Pilot participants supply ratings, dismissal, dispute, and reversal dispositions; QA records qualifying offered actions and other predeclared observed benefits. QA applies the fixed rubric and flags ambiguous records; the product owner adjudicates them without changing the rubric or selected population. A disagreement is counted against the target unless the participant corrects it.
- **Fixed evidence close:** Baseline parent-follow-up events and disputes close and are frozen at the baseline's end before the Milestone C window begins. Pilot events through the end of day 30 remain eligible. Ratings, disputes, and predeclared observed benefits for all selected pilot events, including items rendered late in the window, close at the end of day 37. Evidence arriving after the applicable close cannot change the gate. Any selected event with neither an affirmative rating nor a qualifying observed benefit at close is missing evidence, so the applicable milestone gate does not pass.
- **Evidence ownership:** QA owns population extraction, ordering, sample completeness, automated matrices, and the signed evidence pack. The product owner owns the predeclared rubric and subjective adjudication. BE owns server authorization, provider-result, activity-completeness, and invalidation evidence; FE owns rendered-surface, handoff, ordinary-language, and timing evidence; OPS owns outage, backup, restore, and reference-deployment evidence. QA and the product owner jointly sign the milestone result.

**Pilot metric canonical event units and boundaries:** Every unit below has a server-issued opaque unique ID and immutable UTC creation time. Eligibility is determined once from the stated start event occurring inside the applicable window; a terminal event may occur later but must close by the evidence-close instant. The household's frozen, configured IANA timezone at the applicable 30-day window start defines local dates and midnight day boundaries; the parent-follow-up comparison instead freezes that timezone once at its 14-day baseline start for both baseline and pilot. Changing the configured timezone during a window does not reassign events or active-use days. A bounded transport retry before an acceptance boundary keeps the same ID. A new deliberate user submission after a terminal failure or cancellation receives a new ID; automatic retry of an `unknown` mutation remains forbidden. Rerendering, reconnecting, reopening, mirroring on another surface, or replaying the same canonical object never creates another eligible unit. A materially new source version, newly prepared mutation, newly delivered proactive object, or explicit new request receives a new ID.

- **Assistant session (`assistant_session_id`):** starts when a user-initiated assistant request first reaches `accepted`; ends at its first terminal request state (`completed`, `cancelled`, or `failed`) or at `uncertain` when no further response can proceed. It is eligible when acceptance occurs in-window. Provider retries and incremental response chunks remain in the same session; reopening its topic or rerendering its transcript does not reopen the session.
- **Cross-surface continuation (`continuation_id`):** starts when a person explicitly opens an authorized existing topic on a different eligible surface after prior activity on the origin surface; ends when stored topic context is rendered and the person either continues without restating the initial request, restates it, cancels, or encounters a visible failure. It is eligible at that destination-open event. Duplicate tabs, rerenders, and reconnects to that open are one unit; a later explicit cross-surface open after closure is a new unit.
- **Now/Briefing item (`presentation_item_id`):** identifies one underlying user-visible item and source version across Now and Briefing. It starts at its first eligible render and ends on completion, dismissal, correction, expiry, invalidation, or window evidence close. It is eligible when first rendered in-window. Placement in both areas, duplicate surfaces, rerenders, and reopenings retain one ID; a substantively changed source version creates a new item ID.
- **Meaningful external-action attempt (`action_attempt_id`):** starts when Kinward begins authority evaluation for one requested or autonomously initiated meaningful external mutation and ends `blocked`, `cancelled`, `failed`, `unknown`, or `completed` after the Section 11 record sequence. It is eligible when evaluation starts in-window, including attempts blocked before preparation or submission. Exact-proposal replacement after stale state, user-authorized retry after confirmed failure, and reconciliation-authorized new execution are new attempts; bounded provider transport retries before a known result retain the ID.
- **Completed assistant action (`completed_action_id`):** is the canonical action object associated with an assistant session, offered item, coordination response, or external-action attempt that reaches a truthful `completed` user-visible effect. It becomes eligible once, at that transition, and excludes response-only sessions, mere renders, prepared or awaiting work, and `blocked`, `cancelled`, `failed`, `unknown`, expired, or revoked outcomes. Multi-step execution, rerenders, reopenings, and duplicate surfaces remain one unit. This class—and no broader request, session, item, or external-attempt class—is the denominator for the Section 6.4 plain-language-explanation counter-metric.
- **Active-use day (`active_use_day_id`):** is the unique canonical unit deterministically bound to one account-bearing pilot person's ID plus one household-local calendar date and containing at least one eligible assistant session, cross-surface continuation, completed assistant action, or explicit Now/Briefing disposition. Any number of events or surfaces on that date retains that one ID and counts once; passive rerender, background refresh, and proactive delivery without person interaction do not create an active-use day.
- **Interruption (`interruption_id`):** starts when one logical interruption first becomes visible or audible to its intended person and ends on acknowledgement, dismissal, correction, expiry, revocation, or delivery failure. It is eligible at first delivery in-window; mirrored or duplicate surfaces and retry of the same delivery retain the ID. A corrected category does not create a replacement unless a separately evaluated new underlying event is later delivered.
- **Nudge (`nudge_id`):** starts when one logical nudge first becomes visible to its intended person and ends on acknowledgement, dismissal, correction, expiry, revocation, or delivery failure. It is eligible at first delivery in-window; rerenders, reopenings, and duplicate surfaces retain the ID, while a separately evaluated later delivery receives a new ID.
- **Autonomous action (`autonomous_action_id`):** starts when an explicit bounded autonomous policy authorizes one meaningful external-action attempt to enter submission without per-action approval and ends with that attempt's `failed`, `unknown`, or `completed` result plus the recorded inverse availability. It is eligible when submission begins in-window; cancellation before submission is recorded but is not an autonomous-action unit. Provider retries retain the ID, and any later reconciliation-authorized new attempt receives a new ID. Reversal is linked evidence and never replaces or removes the original unit.
- **Coordination request (`coordination_request_id`):** starts when a validated request is committed for delivery to its named recipient and ends in exactly one visible terminal state: `accepted`, `declined`, `countered`, `expired`, `revoked`, or `delivery-failed`. It is eligible when committed in-window. Delivery retries, duplicate surfaces, rerenders, and reopenings retain the ID. Sender withdrawal is `revoked` and creates no additional terminal state. A counter creates a new linked request ID and leaves the original `countered`; any later renewed request receives a new ID.
- **Parent follow-up event (`parent_follow_up_event_id`):** is one participant-recorded instance in which a participating parent or guardian repeats, chases, or independently rechecks the same expected outcome with the same participating child or teen after that outcome was previously requested or acknowledged. The first request is not a follow-up; each later distinct follow-up is one event. Transport retries, duplicate capture, edits, reminders generated solely by the evidence instrument, and the same follow-up reported by multiple participants retain one ID. A materially changed outcome, new deadline, or new request is not the same event. Predeclared exclusions are genuine safety or medical emergencies, a minor's explicit request for clarification or help, a materially changed underlying obligation, and a proven Kinward delivery failure; ordinary urgency, lateness, or participant dissatisfaction is not an exclusion. QA applies the frozen rule, links duplicates, and records exclusions. A participant dispute remains in the population and counts as a follow-up unless the participant corrects the underlying report before the applicable evidence close. The household's IANA timezone frozen at baseline start governs both the 14-day baseline and 30-day pilot, including every local-day boundary; a timezone change during either window does not reassign an event.

### 6.1 Adoption and utility

- At least two adults complete onboarding without developer intervention.
- At least two adults use Kinward on 10 or more distinct days.
- At least 27 of the 30 selected accepted assistant sessions reach a response or an accurate visible terminal state without developer repair; this is the separate reliability measure.
- At least 70% of those 30 sessions have affirmative usefulness, a completed offered action, or another directly observed benefit predeclared in the fixed rubric; all 30 must have closed rated or observed evidence.
- At least 80% of sampled cross-surface topic continuations resume without restating the initial request.
- At least 75% of the 20 selected Now or Briefing items have affirmative usefulness, a completed offered action, or another directly observed benefit predeclared in the fixed rubric; all 20 must have closed rated or observed evidence.
- The mean number of canonical `parent_follow_up_event_id` units per household-local day during the 30-day Milestone C pilot shall be at least 10% lower than during the immediately preceding 14-day baseline. All consecutive days, including zero-event days, enter each mean. The baseline must contain at least 10 canonical events; otherwise this outcome has insufficient evidence and the Milestone C gate does not pass. QA owns capture completeness, deduplication, exclusions, timezone application, and the signed comparison; the product owner may adjudicate only non-mechanical rubric questions, and participant-disputed events count against the reduction unless corrected before the applicable close.

### 6.2 Trust and privacy

- Shared-surface privacy tests produce zero disclosures in unknown, candidate, group, expired, and identity-downgrade states.
- Adult-to-adult private-resource authorization tests produce zero cross-person reads.
- **Zero missing mandatory activity records:** Across every eligible meaningful external-action attempt and the complete automated action matrix, zero attempts may lack any mandatory FR-053 or Section 11 activity record or field. A single missing mandatory record fails the Milestone C gate.
- Across all eligible action attempts, zero actions are reported complete when the provider returned failure, timeout, unknown status, or no confirmed result.

### 6.3 Operations

- A clean compatible deployment restores the supported backup and passes all post-restore checks.
- An optional provider outage does not prevent authentication, local topic access, Kinward Control, or backup creation.
- No manual database editing is required for ordinary onboarding, invitation, integration reconnect, backup, or restore workflows.

### 6.4 Counter-metrics (Milestone C pilot)

- Zero private items remain visible after shared-surface identity confidence drops or a personal session expires.
- Fewer than 5% of canonical `completed_action_id` units defined above lack a plain-language explanation of what happened; no other session, item, attempt, or delivery class enters this denominator.
- Across the ordinary-workflow acceptance checklist and every pilot support incident, ordinary household use requires no YAML, entity IDs, service names, schema editing, database access, or model administration.
- Zero nudge, interruption, or autonomous-action deliveries occur during the Milestone C pilot, confirming those levels remain disabled until Milestone D delivers them.

### 6.5 Milestone D proactive and coordination measures

These conditions gate only the issued Milestone D nudge, interruption, autonomous-action, and coordination requirements listed in Section 16. The separate Milestone D measurement window and event populations are defined by the evidence contract above, and the enabled proactive categories must match the recorded disposition of PD-04:

- No more than three non-critical proactive interruptions per person per day by default.
- Fewer than 20% of proactive nudges are dismissed as irrelevant during the Milestone D measurement window. The prior 10% target is a post-pilot optimization goal.
- **Critical interruption classification:** An interruption is critical only when, at delivery time, waiting until the next configured review opportunity would either (a) miss an explicit deadline from a current authorized source or (b) violate a confirmed safety requirement. The activity evidence must identify the allowed predicate, source identity and version, deadline or safety requirement, delivery time, next review opportunity, and evaluator result. QA applies these predicates mechanically; the product owner adjudicates an ambiguous fixture against the frozen catalog rubric, and an unresolved or participant-disputed classification counts as non-critical for the cap.
- **Review-opportunity classification:** Every Milestone D nudge or interruption record shall identify the person's review-setting ID/version, configured household IANA timezone and freshness, evaluated local time, resulting next review opportunity, any confirmed deadline, and the Section 12.4.1 boundary result. Unknown or stale setting/timezone evidence cannot support an interruption. QA shall verify immediately-before, exactly-at, immediately-after, and prospective-setting-change cases; a mismatch fails the applicable level-selection gate.
- Fewer than 5% of all autonomous actions in the window have a participant-disputed or fixed-rubric-adjudicated intent or scope mismatch. Every such mismatch is in the error numerator whether the action is reversible, reversed successfully, reversed unsuccessfully, or irreversible. Reversal is reported separately with counts for reversal requested, verified inverse available, successful, unsuccessful, and unavailable or irreversible; a successful reversal never removes the original error.
- Coordination requests disclose only minimum-necessary information, verified by privacy tests.

### 6.6 Controlled acceptance evidence catalog

Before either pilot window begins, QA shall freeze a versioned controlled acceptance evidence catalog. Each entry names its fixture or checklist case, applicable surface/provider/state variants, expected result, verification method, evidence owner, and exact FR/NFR IDs. At minimum the catalog contains:

- the complete shared-identity state and transition matrix for FR-029, FR-033, FR-039, FR-044, NFR-001, NFR-003, NFR-020, and NFR-022, including candidate entry, candidate-to-group, candidate-to-verified, and verified confidence-loss fixtures; byte/field inspection proving every candidate response contains exactly the unknown/expired operational allowlist plus a neutral salutation and no name, identity, account, confidence, recognition, verification, household-shared, or private-existence signal; and a verified-state fixture proving names first become eligible only after current verification and surface-policy authorization;
- data-class, role, exactly-one-primary-personal-assistant, household-fallback, adult/teen/child, administrator, and mixed-owner boundaries for FR-007–FR-011, FR-018–FR-021, FR-026, FR-030–FR-032, FR-070–FR-071, FR-087–FR-088, FR-093–FR-094, and NFR-004, including unconditional private-teen denial outside owner-authorized privacy-filtered sharing; positive teen-approval fixtures with exact owner-authorized recipient/field/purpose/expiry transformations; negative fixtures for absent, expired, revoked, and mismatched teen sharing authorization even when the requester is an adult and the recipient is a named approver; FR-008 fixtures for permitted own-name and policy-authorized household-relationship correction, atomic rollback, exact duplicate, stale/concurrent conflict, audit, dependent-policy refresh/invalidation, same-profile recovery, suspected wrong-binding suspension, unsupported rebinding, and zero private-state transfer; assistant deletion fixtures that preserve an authorized person-owned calendar credential while revoking assistant-scoped grants/references and that delete a credential only under explicit person-level disposition; and every authorized transition among `active`, `disabled`, `locked`, and `recovery-pending`, plus the separate `deletion-pending` overlay, including session/token/authority invalidation, surface/provider/proactivity denial, pending and submitted-work disposition, retained ownership, same-profile reactivation, ambiguous-policy denial, and no administrator private access;
- every protected-resource class and provider-query class for FR-021, FR-030, FR-033–FR-034, FR-055–FR-056, FR-059, NFR-001, NFR-005, and NFR-006, including allow and deny cases;
- request and external-action lifecycle, provider success/failure/timeout/unknown results, exact approval, same-target concurrency, cancellation, restart, backup, restore, deletion-pending, and reconciliation for FR-013, FR-017, FR-052–FR-053, FR-060, FR-064–FR-066, FR-074, FR-077, FR-083, FR-086–FR-087, FR-095, FR-100, NFR-011–NFR-012, and NFR-015–NFR-016, including adult-initiated calendar and Home Assistant actions representing, targeting, or materially affecting a child/teen; minor notice and named-policy routing; Home Assistant household-resource allow/deny fixtures for requester class, quorum and independently required approver, limits, target class, affected-person approval, bounded delegation, and missing or ambiguous policy; plus deletion-pending entry from every account state, complete authority/artifact invalidation and cache clearing, reconciliation-only access, abandonment/restart, process restart, backup/restore, concurrent/idempotent completion, binding/auth removal, and tombstone-only retention;
- every mandatory activity field and the audience/classification matrix in Section 11 for FR-053–FR-054 and NFR-009, including adult-to-adult private-resource and minor-approval metadata fixtures, plus general non-minor household and minor-specialization `any-one`, `all`, and threshold quorum fixtures covering version binding, mixed/concurrent approve and decline, exact and conflicting duplicate response, approval withdrawal, irreversible decline on the request, cancellation/revocation/disablement/expiry precedence, authority or sharing loss, policy/assignment/affected-principal change invalidation, and atomic revalidation/consumption/exactly-once `acting` for FR-087, FR-094–FR-095, and FR-100;
- active-deployment deletion, share narrowing, revocation, derived dependency/freshness, direct household authorship versus privacy-filtered derivation, and downstream invalidation for FR-016, FR-024, FR-026, FR-042, FR-082–FR-083, FR-090, and FR-093, including old-archive deletion and narrowing fixtures for directly household-authored facts and topics;
- initial onboarding atomicity and retry, invitation binding, invited-adult interview, integration reconnect, protected backup, point-in-time restore warning, post-restore quarantine/reactivation denial, owner reauthorization, absent/deleted-owner denial, normal direct household-configuration restore, and unresolved-action preservation for FR-002–FR-006, FR-012, FR-061, FR-074–FR-086, FR-091, NFR-013–NFR-015, and NFR-038;
- direct household-authored content fixtures for FR-097 covering bootstrap current-administrator joint authority, verified inspection without private-source access, editor-version changes, any-administrator quarantine, one-administrator no-conflict republication/narrow/export/delete, concurrent and sequential conflicting dispositions, all-current-administrator agreement, explicit versioned household-policy resolution, administrator addition/removal, last-administrator rejection, former-administrator denial, ambiguity quarantine, audit completeness, old-archive restore, and continued derived/private-source denial;
- database-reset and UJ-11 controlled-import end-to-end cases for FR-079 and FR-098 covering a clean `001_initial_single_household` database with no legacy migration-chain execution or dependency; a successful non-empty package containing people/profile relationships, primary personal assistants with personality settings and correct cardinality, confirmed durable facts with ownership/sharing, non-secret integration configuration, and Home Assistant mappings; version compatibility; ownership, privacy/class, source/dependency, and policy validation; exact duplicate skip and conflicting duplicate rejection separately in every minimum class; credential/token/secret, derived-share, unknown-class, invalid-mapping, and disallowed legacy tenant/control-plane/billing/support rejection; same-owner personal-content and FR-097 household-content quarantine/release denial; privacy-safe rejection reporting; and bit-for-bit or contract-equivalent whole-import rollback after an invalid record in each minimum class;
- private-device handoff cases for FR-099 and NFR-007 covering intended-person binding; exact pre-authentication payload; current identity, topic, share, account, source/dependency, and surface-policy re-evaluation; single-use `accepted`, `declined`, `expired`, `revoked`, and `unreachable` outcomes; wrong person, replay, concurrent redemption, identity downgrade, account disable/lock/recovery-pending, source/share narrowing, authorization revocation, expiry, connectivity uncertainty, and attempted weaker-path downgrade, with byte/field proof that every denial reveals neither private content nor private existence;
- the authenticated minor end-to-end journey for FR-009, FR-013, FR-032, FR-087–FR-088, FR-094, and NFR-004;
- UJ-10 end-to-end cases for the exact coordination terminal set `accepted`, `declined`, `countered`, `expired`, `revoked`, and `delivery-failed`, including sender withdrawal as revocation, authorization revocation, duplicates, and concurrent mixed responses; all three generated-view dispositions; nudge/interruption correction; and autonomous-action inverse success, inverse failure/unknown, and irreversible disclosure for FR-042, FR-045–FR-047, FR-049–FR-054, FR-096, NFR-009, NFR-012, NFR-015, NFR-028, and NFR-039;
- Section 12.4.1 and FR-046 review-opportunity cases immediately before, exactly at, and immediately after 08:00/18:00 local; local-day and timezone-offset rollover; prospective setting changes on both sides of commit; stale, missing, invalid, and unknown setting/timezone; confirmed-deadline nudge allowance; and interruption denial absent the independent Section 6.5 critical predicate;
- the 14-day parent-follow-up baseline and 30-day Milestone C comparison, including event creation, duplicate reports, changed-outcome non-matches, every permitted exclusion, non-permitted urgency, household-timezone freezing, participant dispute and correction, minimum-population failure, evidence close, and the 10% reduction calculation; and
- ordinary onboarding, invitation, integration reconnect, backup, restore, conversation, topic continuation, approval, Home Assistant, and Kinward Control workflows requiring no technical intervention for FR-004, FR-008, FR-063, FR-068–FR-073, NFR-025, NFR-027, and NFR-031.

The signed evidence pack records the catalog version and content hash. Adding, removing, or changing a case after freeze creates a new version and cannot silently alter the active window. A missing required case, variant, expected result, owner, evidence artifact, requirement ID, version, or hash fails the applicable milestone gate; NFR-039 makes this catalog contract mandatory.

**Frozen gate-blocking defect rule:** A known defect automatically blocks the applicable milestone gate when it is any violation of a zero-tolerance privacy or authorization rule, any failure to perform mandatory deletion or invalidation, any unauthorized release of restored content, any false completion claim, or any loss of data included by the backup contract. QA classifies these automatic cases mechanically from this rule and the frozen evidence catalog. The product owner adjudicates only a known defect that does not meet an automatic predicate; neither severity labels, priority changes, waivers, duplicate closure, deferral, nor relabeling can make an automatic case non-blocking. The signed evidence pack lists every open known defect, its predicate evidence, classification, owner, and disposition. Any omitted open defect or unresolved automatic case fails the gate.

## 7. User, role, and privacy classes

### 7.1 Household administrator

An adult account that manages membership, invitations, child policy, household integrations, shared surfaces, system health, backup, and household-wide defaults.

Administrator status does not grant access to another adult’s private memory, conversations, topics, calendar details, email content, credentials, or assistant instructions.

### 7.2 Adult member

An adult controls their personal assistant, private memory, private topics, personal integrations, personal surfaces, and personal sharing decisions.

An adult may explicitly share a fact, topic summary, calendar, or action outcome with the household or selected people. Sharing does not transfer ownership of the underlying private source.

### 7.3 Teen member

A teen account uses the `teen` privacy classification, which is a policy state, not a data class. Teen private content uses the `private-person` data class; sharing with named guardians uses `selected-share` naming the authorized guardians, and household sharing uses `household-shared`.

- Private conversations, topics, inferred preferences, and private memory are not visible to administrators or other household members.
- Administrators may manage account state, safety policy, maximum action authority, allowed integrations, and household-sharing settings.
- Administrators may not read private content solely because of their role.
- **Unconditional deny — current product outcome:** Kinward shall unconditionally deny every request, query, operation, or output that would disclose private teen content outside an owner-authorized, explicit privacy-filtered sharing transformation. That transformation produces a new, separately reviewable item classified `selected-share` for named recipients or `household-shared` for the household and never reclassifies or exposes its private source. The unconditional deny applies to approval and activity views as well as ordinary assistant output and has no emergency, legal, safety, administrator, guardian, approver, operator, or other current-scope exception.
- Money, transportation, appointments, account security, message sending, and actions representing, targeting, or materially affecting the teen require the teen-category policy and named authorized-adult approval by default regardless of requester; every private-derived approval field additionally requires the teen's exact sharing authorization under Section 11.
- The product must show the teen which categories are guardian-visible and which are private.
- Approval authority comes from named adult assignments in the teen's action policy by action category; administrator status alone does not make an adult an approver.

### 7.4 Child member

A child profile uses the `child` privacy classification, which is a policy state, not a data class, and may exist without an account. Child private content uses the `private-child` data class; guardian sharing uses `selected-share` naming the authorized guardians; household sharing uses `household-shared`.

- External integrations are disabled unless explicitly permitted.
- External-state actions representing, targeting, or materially affecting the child require the child's category policy and named authorized-adult approval regardless of requester unless that exact category is narrowly pre-authorized by the same policy.
- Each durable fact must be classified `private-child`, `selected-share`, or `household-shared`. An explicit privacy-filtered transformation that produces a shared child fact is a new, separately reviewable item classified `selected-share` for named recipients or `household-shared` for the household; it does not reclassify or expose its private source.
- Administrator review of child content is subordinate to the canonical data classes and PD-02: until PD-02 is resolved, administrators may review only `household-shared` child facts and `selected-share` facts that explicitly name them; no broad necessity exception overrides `private-child`.
- Child conversation content is not automatically copied into guardian memory.
- The child experience must use age-appropriate language without presenting hidden monitoring as privacy.
- The product must identify when a child request will be shared with or approved by an adult before any such disclosure or submission.
- Approval authority comes from named adult assignments in the child's action policy by action category; administrator status alone does not make an adult an approver. With no valid assignment or no approval before expiry, the action remains unsubmitted.

### 7.5 Profile without account

A profile may exist for a child, infant, or other household member who does not authenticate. It may hold explicitly entered household facts and relationships but has no private assistant conversation or personal integration credentials.

#### 7.5.1 Optional pet profile

An administrator may optionally add a pet during initial onboarding or later household-profile management. A pet profile has no account and holds only explicitly entered `household-shared` care and relationship facts, such as species, household relationship, care note, appointment, or medication fact. It has no personal assistant, private conversation, private memory, credentials, integration ownership, approval role, delegation right, or action authority. A pet may be the stated subject of a household action, but authority and accountability remain with an authorized person.

### 7.6 Shared-surface participant

A participant may be unknown, a likely candidate, a verified member, or one of several people present. Shared surfaces always begin in household-safe mode.

### 7.7 Account, role, and policy-class transitions

- Account state is exactly one of `active`, `disabled`, `locked`, or `recovery-pending`. The separate person lifecycle condition `deletion-pending` in Section 7.9 is not a fifth account state and overrides the authority otherwise associated with any account state. Only `active` without `deletion-pending` may establish a new authenticated session, exercise personal or delegated authority, access personal surfaces, invoke an assistant or provider, receive proactivity, approve work, or create new work.
- An account owner may move their `active` account to `disabled`; a current administrator authorized for household membership/security may also disable an account but gains no private access or ownership. A security control may move `active` or `disabled` to `locked` on a frozen security predicate, and the account owner or an authorized administrator may explicitly lock it. Only an owner-initiated recovery request, or the minimum administrator-initiated recovery operation permitted by the resolved AD-01 policy, may enter `recovery-pending`. Every transition records actor or security predicate, prior and new state, reason category, time, affected authority, and result without private content.
- Entry into `disabled`, `locked`, or `recovery-pending` fails closed immediately: every active session, refresh/device token, handoff reference, pending invitation bound to the account, unconsumed approval capability, and delegated active authority is invalidated; private surfaces and assistant/provider retrieval are denied; proactivity and coordination delivery to the account are suppressed; pending approvals expire; and prepared or awaiting unsubmitted work is cancelled or expired. Submitted or `unknown` actions preserve their reconciliation and same-target blocking state and are never retried, completed, or unblocked by the account transition.
- Non-active state retains the person's profile, ownership, private and shared data, assistant, person-owned credentials, policy history, activity, and unresolved-action state under their existing classes. It never transfers ownership, grants administrator inspection, republishes restored content, or converts retained data to household ownership. Deletion remains a separate FR-083 flow.
- A disabled account may begin reactivation only through the same-owner proof selected by AD-01; a locked account must additionally clear or explicitly resolve its recorded security predicate. Recovery-pending can return only to `active`, `disabled`, or `locked` through the resolved recovery policy, bound to the same existing profile. Before `active` commit, Kinward reauthenticates the intended owner, rotates or replaces invalidated credentials and tokens, re-evaluates current role, policy class, shares, delegations, integration grants, and account binding, and leaves invalid or ambiguous authority revoked. Reactivation issues new security artifacts, does not revive expired approvals or cancelled work, and does not release restore-quarantined content without its separate authorized disposition.
- Creating an account for a profile without one binds the account to that existing intended profile through the invitation protections in FR-005 and preserves the profile's existing ownership and data classifications; it must not create a replacement profile.
- An authorized administrator may change adult/member administrator roles, and every change records actor, affected person, prior role, new role, time, and result. A role change that would leave the household without an administrator is rejected.
- A child, teen, or adult policy-class change does not silently reclassify, broaden sharing of, or transfer ownership of existing data. Before commit, Kinward evaluates every affected action policy, approval, delegation, integration authority, share, and derived item. Until each has a valid explicit disposition, the transition is incomplete, ambiguous access fails closed, the more restrictive prior access remains effective, and no new approval or submission may rely on the proposed state. On commit, every approval, delegation, share, or derived access no longer valid under the new state is expired, revoked, or invalidated immediately.
- Automatic age-triggered policy-class transitions are a non-committed planning horizon requiring the Section 4.3 amendment package. First usable scope supports an explicit authorized transition with a review of action policy, named adult assignments, integrations, existing shares, and data classes before commit.

### 7.8 Profile corrections and suspected binding errors

Current correction scope is deliberately narrow. An authenticated account-bearing person may directly correct only their own display name and preferred name. A directly household-authored `household-shared` relationship fact may be corrected by its account-bearing adult subject, or, for a minor or profile without an account, only by an adult named by that subject's current versioned policy for profile/relationship management. Administrator status, household membership, a claimed relationship, or possession of another profile's invitation is not sufficient authority. A correction never changes another person's private fact, owner, data class, account binding, assistant ownership, credential, or authority by implication.

Each permitted correction is one serializable transaction bound to the authenticated actor, intended subject, correction type, prior record ID and version, proposed value, current policy version, and an idempotency key. It either commits the corrected fact, its new version, the append-protected audit record, and all required dependent invalidations together, or commits none of them. Competing same-version corrections are serialized; an exact duplicate is idempotent, while a stale, conflicting, ambiguous, or policy-version-mismatched correction fails closed and requires a fresh review. The audit records actor, authority basis, subject, correction category, old and new opaque version references, policy version, time, and outcome without private content.

Before commit, Kinward enumerates every relationship-dependent recipient assignment, minor action policy, approval, delegation, share, derived item, household-resource rule, invitation, and rendered or cached authorization. On commit, each dependent is atomically refreshed against the corrected relationship and current policy or is expired, revoked, invalidated, and cleared under NFR-020; until refresh completes, it cannot authorize retrieval, delivery, preparation, approval, or submission. A name correction refreshes presentation references without changing identity or authority. If dependency enumeration is incomplete or a correction would require unsupported authority adjudication, the correction does not commit.

Cross-profile rebinding is unsupported and fails closed. Account recovery may rotate or replace credentials and supersede unusable authentication artifacts only for the same intended existing profile; it may not move an account or credential to another profile, exchange two bindings, merge profiles, create a replacement profile, reassign an assistant, or transfer private assistant state. Evidence suggesting a wrong binding immediately suspends both the presented account access path and every distinct account/profile access path implicated by the evidence by moving the applicable accounts to `locked` or `recovery-pending` under the security policy, invalidating their authority under Section 7.7, and recording only sanitized evidence. Current scope provides no adjudication or rebinding operation: resolution requires a future separately specified policy, authority model, notices, audit, privacy tests, journeys, requirements, and PRD amendment. Until then, recovery may only prove and restore the original same-profile binding; otherwise all implicated access stays denied, and private assistant state is never inspected, copied, exchanged, or transferred.

### 7.9 Person deletion-pending lifecycle

`deletion-pending` is a separate person lifecycle condition that overlays and is recorded alongside the person's current `active`, `disabled`, `locked`, or `recovery-pending` account state. Entry is atomic with the authorized deletion request and immediately disables all account authority regardless of the underlying state; it invalidates sessions, refresh tokens, device trust, invitations, approval and handoff capabilities, delegations, provider and integration grants, proactive and coordination authority, and any other authentication or authorization artifact. It cancels or expires prepared and awaiting work, denies new work, approval, private retrieval, assistant/provider queries, export, sharing, and ordinary administration, and clears rendered, cached, provider-context, and `surface-ephemeral` copies within NFR-020. Only minimum-necessary action-state observation and reconciliation authorized by FR-083 may continue; it cannot retrieve unrelated private content or create a new external mutation.

Entry and completion are serialized against person, account-binding, account-state, deletion-request, policy, and unresolved-action versions. A duplicate request is idempotent; a concurrent role, binding, policy, recovery, reactivation, or second deletion change either precedes the atomic entry and is re-evaluated or loses as stale. Once pending, no account reactivation or correction can bypass the overlay. Every transition, reconciliation observation, abandonment, restart, denial, and completion produces an append-protected sanitized record with actor or policy predicate, authority basis, affected opaque person/account references, prior and new lifecycle/state versions, time, unresolved-action references, and result.

The condition and every FR-083 reconciliation blocker survive process restart, backup, and restore without restoring authority. Explicit abandonment applies only to further reconciliation effort: it preserves each result as `unknown`, keeps automatic retry and same-target execution blocked, leaves the person `deletion-pending`, and permits neither deletion completion nor account reactivation. A later authorized reconciliation restart resumes observation against the same attempt and idempotency identity; it does not submit or retry the action. Restore of a pending person keeps the account disabled and deletion overlay active, invalidates all pre-restore artifacts, and permits only the same reconciliation path.

Deletion completes only after FR-083's confirmation, sole-administrator, and unresolved-action conditions pass in one final transaction. That transaction performs every FR-083 content, share, credential, assistant, integration, dependency, and cache disposition; removes or irreversibly disables the profile-to-account binding and all authentication, recovery, device, invitation, approval, handoff, delegation, provider, and proactive artifacts; marks the profile deleted and unavailable for rebinding; and retains only the append-protected sanitized deletion tombstone plus protected minimum reconciliation records allowed by FR-082/FR-083. A failed final transaction leaves the person `deletion-pending` with no authority and may be retried idempotently after the failure is corrected; it never partially restores access or partially completes deletion.

## 8. Data classification and sharing

Every stored or transmitted item must have an effective data class.

### 8.1 Data classes

- `private-person`: available only to the owning person and authorized assistants/services acting for that person. Teen private content uses this class.
- `private-child`: available according to child policy; shared with guardians only as `selected-share` or with the household as `household-shared`.
- `selected-share`: shared with named household members for a defined purpose.
- `household-shared`: available to household-safe experiences and the household fallback assistant.
- `surface-ephemeral`: available only during the current authorized surface session and not durable unless explicitly saved.
- `system-operational`: health, configuration, sanitized audit, and diagnostics that exclude private content; authorized user content is never reclassified into this class.

An explicit privacy-filtered transformation is a new, separately reviewable item classified `selected-share` for named recipients or `household-shared` for the household; it does not reclassify or expose its private source.

**Sharing-class narrowing:** Whenever a topic, fact, calendar, outcome, direct household share, or separately approved derived statement narrows from `household-shared` to `selected-share` or private, or from one `selected-share` recipient set to a narrower set or private, Kinward immediately revokes every ineligible authorization and prevents further fetch. It also removes the item from shared-display and household-fallback context, invalidates all now-ineligible derived access, and clears rendered and cached copies within the NFR-020 fail-closed timing rule. Revocation or expiry has the same outcomes. The change retains only the sanitized activity record defined in Section 14 and never changes ownership of the private source. A `surface-ephemeral` item is deleted when its authorized session ends, crashes, restarts, or becomes uncertain and must never become visible to a later session unless the user explicitly saved it under a durable data class.

### 8.2 Derived data

A summary, embedding, classification, recommendation, or model-generated inference inherits the most restrictive data class of its source inputs unless an authorized explicit privacy-filtered transformation produces a separately reviewable shared item. Receiving a `selected-share` item grants no onward sharing or transformation authority by default. A transformation to `household-shared` or to a new or broader `selected-share` recipient set requires approval from every private source owner, or explicit onward sharing permission from every such owner that covers the transformation's purpose, permitted source data, and exact recipients. Mixed-owner inputs fail closed unless every private source owner supplies one of those authorizations; one owner's permission never substitutes for another's.

**Derived dependency and freshness tracking:** Every internally stored derived item must record each exact source ID, source version, source data class, transformation version, and expiry. Every separately approved `selected-share` or `household-shared` transformed statement is bound to those values. Any source content or version change, source deletion, access revocation, or expiry immediately invalidates the statement and every downstream dependent; removes them from shared access, household-fallback and shared-display context, rendered output, provider context, and caches within NFR-020; and prevents retrieval. Reuse requires a new privacy-filtered transformation against current source versions and new approval from every source owner required by this section. If dependency/version tracking is absent or incomplete, or expiry is absent or passed, the derived item fails closed and is not retrievable.

On person deletion, only a directly authored `household-shared` item with no private or privacy-filtered source dependency may remain under household ownership. Every privacy-filtered or otherwise derived `household-shared` item whose source is owned by the deleted person, and every downstream dependent of that item, is invalidated and removed under the preceding rule even if it was previously approved for household sharing.

When immediate deletion from an external provider is impossible, Kinward must immediately prevent provider queries and local retrieval through that reference, mark it deletion-pending or externally retained, submit the provider's deletion operation if one is exposed, and disclose the affected provider and limitation to the data owner. External inability to delete never preserves Kinward access or permits the provider data to influence assistance.

### 8.3 Data minimization

Context assembly and provider calls must include only the data required for the current permitted task. Entire mailboxes, calendars, topic histories, or memory stores must not be sent when a narrower subset is sufficient.

### 8.4 Pending inferred-observation lifecycle

Every pending inferred observation identifies its subject or household scope, authorized fact owner, source category and source-item dependencies, confidence, creation time, sharing class, and fixed expiry 30 days after creation. A person-specific observation is owned for disposition by its subject when that subject can act; otherwise only an adult explicitly authorized by the subject's policy may act. A household-scope observation is owned for disposition by an authorized household administrator and may not contain a private-person or private-child inference.

Before confirmation, the observation may be used only to show its permitted subject or fact owner a candidate for inspection and confirmation, with source category, confidence, and expiry. It cannot personalize a response, rank or recommend content, trigger proactive evaluation or delivery, enter model or provider context for another task, authorize an action, appear on a shared surface, or enter household-fallback context.

The subject or authorized fact owner can inspect the candidate and its permitted source explanation, correct it and explicitly confirm the corrected statement as a durable fact, or reject/delete it. Rejection or deletion immediately removes the candidate body and invalidates dependents, retaining only the sanitized record allowed by FR-082. Expiry has the same deletion and invalidation disposition. After rejection, deletion, or expiry, the same inference cannot recur from the same source evidence or a replay/reprocessing of it; recurrence requires genuinely new source evidence with a new source identity or version and observed time.

Backup creation includes only observations that are unexpired and not rejected or deleted at that backup's point in time, together with their lifecycle and dependency metadata. A current deployment never undeletes a rejected, deleted, or expired body, and any backup created after that disposition excludes it while retaining only the permitted sanitized record. An older archive may honestly contain a body that was deleted, rejected, expired, or narrowed after its snapshot; restore cannot infer that later event from the archive and therefore applies the warning, quarantine, owner-reauthorization, and absent-owner rules in Section 14.3 rather than claiming retroactive erasure. Restore preserves the original owner, subject, source dependencies, confirmation state, and absolute expiry and deletes rather than quarantines an observation whose recorded expiry has passed.

### 8.5 Direct household-authored content ownership and management

This lifecycle applies only to content authored directly into household scope with verified `household-shared` classification and no personal, private-child, selected-share, privacy-filtered, or other derived source dependency. If direct authorship, dependency completeness, ownership, or class is absent or ambiguous, Kinward quarantines the item and denies ordinary retrieval, provider use, shared-display/fallback use, republication, export, and body inspection until the ambiguity is resolved without private access.

At bootstrap, the default household content-ownership policy makes the set of current household administrators the joint holders of management authority over qualifying household-owned content. “Joint holders” identifies the current authority set; it does not grant access to private sources and does not require unanimity for an uncontested disposition. Any current administrator may inspect a verified qualifying item and its household-safe provenance, author/editor history, versions, classification, audience, dependencies, and audit history; may edit it into a new version; and may quarantine it immediately. An editor change records the editor and base version, preserves household ownership, re-evaluates class and dependencies, invalidates stale downstream items, and never creates access to a private source.

One current administrator may republish, narrow, export, or delete a quarantined qualifying item when no other current administrator has recorded a conflicting disposition against the same base version. Conflicting dispositions—including concurrent republish/delete, different audiences or classes, or an editor change against a pending disposition—fail closed, keep the item quarantined, and require either an identical disposition from every current administrator or an explicit versioned household policy that names the conflict rule, eligible decision makers, quorum, notice, and effective period. No role, prior authorship, former-administrator status, or last-writer result bypasses the conflict rule.

Adding or removing an administrator changes the authority set prospectively and records the policy version. Removing the last current administrator is rejected. A former administrator loses management authority immediately but household-owned content remains household-owned; pending single-administrator dispositions by a removed administrator are invalidated and re-evaluated. Every inspection, edit, quarantine, republication, narrowing, export, deletion, conflict, vote, policy change, invalidation, and denial produces an append-protected minimum household-content audit record without private source content. Active-deployment and restore flows use this same lifecycle; restore adds the mandatory quarantine in Section 14.3 and never weakens it.

## 9. Assistant ownership and privacy boundaries

### 9.1 Personal and specialist assistants

- A personal or specialist assistant has exactly one owner.
- First usable scope has exactly one primary personal assistant per account-bearing person. Additional personal assistants are unavailable and have no lifecycle, routing, salvage, or delivery commitment until a future Section 4.3 amendment; specialist assistants remain a separate, also-disabled concept.
- It may use only information its owner can access.
- Its private memory, conversations, topics, and personal integration data are private by default.
- A specialist assistant inherits no broader access than the owner’s primary assistant.
- A personal or specialist assistant cannot be reassigned to another person. Its ownership never transfers across people through administration, account recovery, deletion, or replacement.
- Only its owner may disable or delete it, except that an account-recovery operation may perform the minimum lifecycle step explicitly permitted by the resolved recovery policy without exposing or transferring private assistant state.
- Credential lifecycle distinguishes: (1) a **person-owned credential**, such as the owner's calendar authorization, whose authority belongs to that person; (2) an **assistant-scoped grant**, which gives one assistant bounded use of a person- or household-authorized integration; and (3) an **integration reference**, which points to configuration or provider objects but is not itself a credential. Assistant ownership never converts a person-owned credential into assistant-owned data.
- Personal-assistant deletion accepts only this complete disposition: memory, conversations, topics, and other content are deleted or retained only for an atomically created replacement owned by the same person; every unsubmitted approval and prepared or awaiting work is cancelled or expired; every delegation record and assistant-scoped grant is revoked; and every integration reference is removed or transferred only to that same-owner replacement. A person-owned credential is preserved when it remains authorized to its owner or to the same-owner replacement and is deleted only through a separate, explicit person-level credential disposition; deleting an assistant alone never deletes it. Submitted or `unknown` actions remain governed by Section 11, preserve reconciliation blocking, and cannot be silently completed, retried, or unblocked. If any item lacks one of these valid outcomes, deletion is rejected. Disablement expires approvals, cancels unsubmitted work, revokes delegation and assistant-scoped grants, and disconnects assistant integration references without transferring ownership; retained private content and preserved person-owned credentials remain available only to the same owner after re-enablement or same-owner replacement authorization.
- Deleting the primary personal assistant required by FR-009 is rejected unless a primary replacement for the same owner is created atomically. Replacement does not create an additional assistant, transfer another person's assistant, or broaden access.
- Administrator management may show non-private lifecycle and health state but may not reveal, copy, transfer, or reassign another adult's private assistant state.
- Specialist creation, invocation, and delegation are not committed delivery capabilities and remain disabled until a future PRD amendment supplies their complete scope; FR-089 and NFR-004 remain mandatory prerequisites.
- When assistant delegation is introduced, assistants may exchange information only through an enforced and inspectable delegation record containing provenance, sharing class, purpose, permitted data, recipient, and expiry. An absent, expired, revoked, mismatched, or over-broad record denies the exchange.

### 9.2 Household fallback assistant

The household fallback assistant is provisioned in the same bootstrap transaction as the household, is household-owned, and has no personal owner. Administrators may configure or disable its permitted household capabilities but may not reassign it to a person, convert it into a personal assistant, or delete it independently of the household; disabling it leaves household-safe shared-display responses available without personal fallback context. It may access:

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

A personal assistant may send the fallback assistant only a minimum-necessary, privacy-filtered coordination statement. That statement is a restricted delegation record and must carry provenance, sharing class, purpose, permitted data (exactly the statement content), recipient (the household fallback assistant), and expiry. Any field mismatch, expiry, or revocation prevents its use and removes it from fallback context.

## 10. Deterministic shared-surface identity policy

Shared surfaces use these states:

- `unknown`: no recognized person or confidence below recognition threshold,
- `candidate`: one likely person but not verified for private disclosure,
- `verified`: one person completed an accepted verification method for the active session,
- `group`: multiple people are present or audience exclusivity is not established,
- `expired`: a prior verified session timed out or confidence dropped.

Required outcomes:

- `unknown` and `expired` expose `household-shared` information and only the **household-display-safe operational allowlist**, which is a subset of `system-operational`, not a new data class. Its complete allowed schema is: (1) one generic capability category from `assistant`, `calendar`, or `home control`, paired with one availability value from `available`, `unavailable`, `degraded`, or `intentionally disabled`; and (2) the current display status as `ready`, `degraded`, or `offline`. No other field is allowed. In particular, the subset excludes household, person, account, assistant, device, room, topic, and action identifiers; activity metadata and cross-person timestamps; opaque correlation references; private-derived content; provider names, references, errors, and configuration details; and every other `system-operational` field.
- `candidate` returns exactly the household-display-safe operational allowlist permitted to `unknown`/`expired`, plus one greeting field containing a neutral salutation. It never contains a name or personalized greeting; names are reserved for a currently `verified` state whose surface policy permits them. No other payload field or value is permitted: in particular it contains no identity, candidate/recognition signal or identifier, confidence value or band, account state, verification hint, private-record existence signal, private or derived content, or household-shared content outside that exact operational allowlist. Candidate entry, candidate-to-group, candidate-to-verified, candidate confidence loss to `unknown` or `expired`, and connectivity uncertainty all recompute the payload under the destination policy and clear every no-longer-permitted field within NFR-020.
- `verified` may expose private information only when the surface policy permits it and no additional audience is detected.
- `group` may render only `household-shared` data. It categorically prohibits every other data class, including `selected-share`, and any private-derived content that has not become a separately approved `household-shared` statement under Section 8.2; all blocked content is reachable only through private-device handoff.
- While in `group` state, shared surfaces must not query or derive from private memory at render time, and presence detection is never treated as proof that every audience member is known.
- Any transition away from `verified` immediately invalidates private fetch authorization at the backend. A connected client removes private content within the NFR-020 timing bound after the downgrade signal; connectivity loss, session uncertainty, or inability to confirm current authorization makes the surface fail closed and remove private content rather than wait for reconnection.
- When disclosure is blocked, Kinward provides a household-safe response and offers private-device handoff. If no authorized handoff target is reachable, it does not queue or reveal private content and gives only a neutral instruction to continue on a personal device when available.
- Shared surfaces must not cache private payloads for later household-safe rendering.
- A personal shared-surface session must expire after a configurable inactivity period no longer than 10 minutes by default.

### 10.1 Private-device handoff lifecycle

A private-device handoff is bound to one intended person, originating surface/session, purpose, expiry, and opaque single-use redemption reference. Before destination authentication, its complete payload is limited to a neutral continuation instruction, that opaque reference, expiry, and destination capability. It contains no person or account name/identifier, topic or source identifier, confidence or recognition signal, private data, derived data, private-record-existence signal, or authorization hint.

At redemption, the backend atomically consumes or rejects the reference and re-evaluates all of: authenticated intended-person binding, `active` account state, destination surface policy, originating and current identity state, topic ownership/access, current sharing class and recipients, each source and dependency authorization/version, revocation, and expiry. Only a successful current evaluation may retrieve private content on the authenticated destination. Successful redemption is terminal `accepted`; intended-person refusal is `declined`; elapsed time is `expired`; sender, policy, source, account, topic, or authorization withdrawal is `revoked`; and absence of a currently authorized reachable destination is `unreachable`. These are the only terminal handoff outcomes.

Wrong-person presentation, replay, duplicate redemption, identity downgrade, account transition away from `active`, source/share narrowing, authorization loss, revocation, expiry, destination-policy mismatch, or evaluation uncertainty fails closed without revealing private content or that a private item exists. A failed or terminal reference cannot be downgraded to a less protected path, revived, redirected to another person, or queued back to the shared surface. AD-16 selects device discovery, delivery transport, destination authentication, and redemption mechanics; it may not weaken this lifecycle.

Accepted verification methods and confidence thresholds are architecture decisions under AD-10, and handoff mechanics are an architecture decision under AD-16, but the authorization, removal timing, payload, redemption, terminal-state, and fail-closed outcomes above apply regardless of the selected mechanisms.

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
- A prepared mutation includes target, every field to be submitted and its proposed value, source version or freshness marker, expected result, expiration, and reversibility status.
- `confirm` executes only the exact approved mutation. Any change to the target, any prepared field or value, integration, represented person, authority basis, or expected result requires a new prepared mutation and approval.
- Approval expires when its prepared mutation expires, any source-version or freshness marker changes, any prepared-mutation field changes, identity changes, the integration is disabled, or authority is revoked.
- `autonomous` requires an explicit category, target scope, limits, effective period, review date, revocation control, and activity visibility.
- For action authority, including each cross-person action, the **requester** is the person initiating the request; the **represented adult** is any adult on whose behalf the action is prepared or submitted; the **target owner** is the person who owns the private resource or commitment being changed; and an **affected adult** is any other adult whose private resource, rights, commitment, access, money, schedule, communication, or material outcome would change.
- The corresponding minor roles are the **represented minor**, any minor on whose behalf the action is prepared or submitted; the **target minor**, any minor whose resource, schedule, care, access, or commitment is targeted; and the **affected minor**, any other minor whose safety, privacy, care, access, schedule, communication, or material outcome would change. These roles are cumulative, and minor-category policy applies when any one is present regardless of requester identity, adult initiation, household ownership of the target, or whether the minor has an account.
- Requester confirmation is sufficient only when the requester acts solely on their own resources, is not representing another person, and no other adult is a target owner or affected adult. Representing another adult, changing another adult's private resource or commitment, or otherwise affecting another adult requires that adult's explicit approval of the exact proposed effect. A bounded delegation may substitute only when it names that principal and matches the action's purpose, scope, target, permitted data, and unexpired period. Missing, expired, revoked, mismatched, or over-broad authority blocks both preparation and submission.
- For a direct household-owned external resource, including Home Assistant, administrators configure a versioned category policy but gain no request or approval authority merely from administrator status. Each policy names the people or policy classes that may request, every eligible approver, one explicit `any-one`, `all`, or `threshold(k)` quorum when more than one approver is eligible (defaulting to `all` only for a policy version that explicitly accepts that default), whether per-action approval is required or a Section 11 bounded autonomous policy applies, quantitative or categorical limits, permitted target classes, and rules for identifying affected people. A requester may prepare or submit only within every matching field of the current policy and the general multi-principal lifecycle below. Any other adult whose security, access, safety, private information, or private material outcome would be affected must explicitly approve the exact effect unless an unexpired bounded delegation from that adult matches the purpose, target, effect, limits, and permitted data; a category quorum never overrides an independently affected adult's required approval. A missing, ambiguous, stale, internally inconsistent, or multiply matching policy fails closed before preparation and submission.
- Ambiguous identity, ambiguous target, stale provider state, policy mismatch, unavailable or disabled integration, or missing approval prevents submission.
- Approval is consumed when submission begins. A timeout or unknown provider result is recorded as `unknown`, not `completed`; it survives restart as `unknown`, is never retried automatically, and requires provider-state reconciliation before another mutation for the same target may execute.
- For concurrent prepared mutations against the same target and source version, at most one may enter `acting`. A confirmed source-version change expires the others; an unknown first result blocks them until reconciliation and revalidation.
- Every meaningful external-action attempt records the complete mandatory sequence: request, preparation or the authority block that prevented it, approval or its absence, execution attempt or prevention, provider response or absence, final result, and undo status. It identifies every required principal—requester, represented adult or minor, target owner or target minor, affected adult or minor, and approver as applicable—and each principal's approval, delegation, policy assignment, sharing authorization, absence, or mismatch. No eligible attempt or required field may be omitted, including failed, cancelled, blocked, timed-out, and `unknown` attempts.
- Every external action requiring decisions from more than one principal uses the **general multi-approver lifecycle**, represented by one general multi-principal approval object bound to a server-issued request ID; immutable prepared-mutation ID and version; exact target, represented/target/affected principals and roles; policy or assignment ID and version; source/freshness versions; eligible decision makers; quorum; expiry; sharing-authority references; and action-authority basis. Its only pre-submission terminal states are `declined`, `cancelled`, `revoked`, and `expired`; `approved` is a transient commit predicate that may enter `acting` only through the atomic revalidation below. Approval responses serialize against the request, prepared mutation, and policy versions. Duplicate identical responses are idempotent; a conflicting duplicate is rejected. Before `acting`, an approver may withdraw an approval and return to unanswered, but a decline cannot be withdrawn on that request.
- General quorum evaluation is deterministic: `any-one` approves on one valid approval and declines only when every eligible approver has declined; `all` approves only when all approve and declines on any decline; `threshold(k)` approves on `k` approvals and declines when recorded declines make `k` approvals impossible. Independently required affected-principal approvals must all be present in addition to the category quorum. For events serialized at the same effective version and time, authority or policy revocation and integration disablement win first, expiry at or before the event wins next, requester cancellation wins next, a satisfied decline predicate wins over an approval predicate, and only then may approval succeed. Otherwise the first serialized terminal predicate is immutable and later responses are stale. Any policy/assignment membership, quorum, category, scope, affected-principal set, sharing authority, or version change immediately resolves the old pending request as `revoked` rather than reinterpreting responses; a new request and new approvals are required.
- Reaching the approval predicate and entering `acting` is one atomic compare-and-commit operation. It revalidates current identity and active authority for every principal and approver; exact request, mutation, target, consequence, provider and source/freshness versions; policy/assignment membership, version, quorum, limits and affected-principal set; every delegation and sharing authorization; integration availability; expiry; cancellation/revocation state; and same-target concurrency. It consumes the approvals and permits exactly one submission, or commits a terminal non-submission result and no external call. Revocation after `acting` cannot erase or reinterpret submission and instead follows recorded reconciliation and verified-inverse rules. This lifecycle applies equally to minor and non-minor, personal and household-owned actions; non-minor household fixtures cover every quorum, duplicate, withdrawal, decline, cancellation, revocation/disablement, expiry boundary, concurrent mixed response, policy-change invalidation, atomic revalidation failure, and exactly-once transition to `acting`.
- For every action that represents, targets, or materially affects a minor, approval routes only to the adults named in that minor's current versioned action-policy assignment for the exact category, including adult-initiated child calendar mutations and household/Home Assistant actions. Each assignment encodes exactly one `any-one`, `all`, or `threshold(k)` quorum where `k` is from 1 through the number of named approvers and specializes, but never weakens, the general lifecycle. The request carries the assignment version, action category, every represented/target/affected minor role, target class, consequence, expiry, and only other fields required to decide the exact mutation. An account-bearing minor receives age-appropriate notice before approval disclosure or submission naming the action category, exact recipients, fields, purpose, consequence, expiry, and cancellation control; for a minor/profile without an account, the same notice is delivered to the adult named by policy to receive notice and is retained for later subject inspection if an account is created. No valid named-adult assignment, notice disposition, or approval by expiry means no preparation or submission.
- A minor approval request never carries the private conversation or message body unless FR-088 permits that exact field and its separate notice/share requirements are satisfied. When any approval field is derived from private teen content, regardless of who initiated the action or which minor role applies, the field is a new, separately reviewable privacy-filtered `selected-share` item and may be created or sent only after the teen explicitly authorizes its exact recipients, fields, purpose, and expiry. A named-approver assignment is action authority, not sharing authorization; absent, expired, revoked, or mismatched teen sharing authorization denies disclosure, approval processing, and submission without revealing private existence.

### 11.1 Activity-record classification and audience

The activity-record audience and data-class matrix below governs activity authorization. Activity authorization is independent of the ability to administer Kinward or operate the deployment. The canonical full record stays private to the requester or represented owner as applicable and never grants one principal access to another principal's protected source; linked principal-private records may be used when one combined body would over-disclose. Every affected-principal or approver view is a separate minimum-necessary item with its own data class and named audience. The effective class of a mixed-person record is the most restrictive class among its fields and sources.

| Activity case | Full record and audience | Separate minimum-necessary view | Administrator/operator view |
|---|---|---|---|
| Personal action with requester as sole represented person and target owner, and no other affected adult | Owner-only `private-person` record for the requester | None unless independently authorized | Sanitized `system-operational` result and opaque correlation only |
| Selected-recipient or adult-to-adult represented, target-owner, affected-adult, delegated, or approval action | Requester- and represented-owner-private record(s), each excluding the other person's protected source unless independently authorized; mixed fields use the most restrictive class | Named affected adult or approver receives a `selected-share` view containing only identity/role in the action, proposed effect on them, consequence, authority/approval choice, expiry, result, and undo availability needed for their decision or outcome | Sanitized `system-operational` result and opaque correlation only unless the administrator is independently a named principal |
| Action representing, targeting, or materially affecting a minor | `private-child` full or linked record for each child role, or `private-person` for each teen role, subject to each minor's policy and excluding another principal's protected source | Only named policy approvers receive a `selected-share` view limited to the Section 11/FR-087 fields; for a teen, every private-derived field requires the teen's exact owner-authorized privacy-filtered transformation and otherwise does not exist; conversation, prompt, and prepared body remain excluded under FR-088 | Sanitized `system-operational` result and opaque correlation only unless independently named by policy and, for teen-derived content, authorized by the teen's exact privacy-filtered transformation |
| Direct household action with no personal/private source | `household-shared` record available only to household members authorized for that action category | Any selected-recipient consequence view is separately `selected-share` | Sanitized `system-operational` result and opaque correlation; role alone does not reveal a principal-private linked record |

Filters in FR-054 apply authorization before matching and return only records or separately classified views the caller may access; counts, facets, empty states, timestamps, and correlation behavior must not reveal that an unauthorized record exists. Adult-to-adult fixtures verify that private source and unrelated metadata do not cross principals, and minor fixtures verify that conversation/body content and unrelated minor metadata do not enter approver or administrator/operator views.

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
- integration data permitted and required for the requested capability,
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
- and delete it while retaining only the sanitized deletion/activity record defined in Section 14.

Deleting a topic removes its underlying user content from the active deployment and invalidates its derived data; audit retention never blocks deletion of that content, and an older archive can expose it only through the Section 14.3 quarantine and restored-owner reauthorization flow.

Changing a topic's sharing class to a narrower audience immediately applies the authorization revocation, shared-display and fallback removal, derived invalidation, and rendered/cache clearing outcomes in Section 8.1; a previously rendered copy never preserves access.

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

The **Briefing UI area** is a place where authorized users review items; **briefing delivery** is one proactive delivery level describing how an item is surfaced. In Milestone C, the only proactively detected category allowed into ambient or briefing delivery is calendar-change exceptions under PD-04. The Briefing UI area may also contain user-requested items, pending approvals, and completed or unknown action results because those are workflow states, not additional proactive categories. Non-calendar proactive categories and nudge, interruption, and autonomous-action delivery remain disabled until their later milestone and PD-04 disposition permit them.

#### 12.4.1 Review opportunities for proactive level selection

Each account-bearing person's review-opportunity setting is versioned, editable only on an authenticated personal surface, and interpreted in the household's configured IANA timezone. Until that person changes it, the default local review opportunities are 08:00 and 18:00 every household-local day. This is a level-selection preference only: the personal surface exposes the two review times and timezone, not recurrence rules, triggers, actions, routine steps, or a routine/alarm builder.

At evaluation, the next review opportunity is deterministic. Immediately before a configured instant, that instant is next; exactly at the instant, it is the current opportunity and an item that can be reviewed then remains briefing; immediately after it, the next later configured instant is next, rolling to the following household-local day after the final daily instant. Calendar resolution follows the configured IANA timezone, including its offset transitions. A setting change commits a new version and applies only to evaluations beginning at or after its commit time; it does not relabel, recall, escalate, or redeliver an already committed delivery. Each evaluation records the setting/timezone versions and resolved UTC instant used.

If the setting or household timezone is missing, stale, invalid, or cannot resolve a next opportunity, Kinward fails closed to briefing or a less disruptive level. A nudge is allowed only when a current authorized source contains a confirmed deadline that would be missed without a response before the setting can be safely resolved. Uncertain review configuration never authorizes interruption; interruption still requires the critical predicate and evidence in Section 6.5, including a confirmed deadline or safety requirement. Tests cover immediately before, exactly at, immediately after, household-local day rollover and timezone offset change, a prospective setting change on each side of commit, stale/unknown setting or timezone, the confirmed-deadline nudge exception, and denial of interruption without its independent critical predicate.

## 13. Functional requirements

### 13.1 Household, accounts, and onboarding

- **FR-001**: Kinward shall support exactly one household per deployment.
- **FR-002**: Initial bootstrap shall create the household, administrator profile, account binding, administrator's primary personal assistant, household-owned fallback assistant, and every adult, child, and pet profile selected before the initial commit as one transactional operation that either commits completely or leaves no usable partial household and can be retried or rolled back without duplicating any selected profile or binding. Here `recoverable operation` means transactional retry/rollback, not the account-recovery mechanism governed by AD-01.
- **FR-003**: Administrators shall add adults and minors before those people have accounts, either as profiles selected inside the FR-002 initial transaction or through later household-profile management.
- **FR-004**: Initial onboarding shall not require integrations, rooms, devices, routines, detailed school/work context, notification rules, or layout editing.
- **FR-005**: Invitation acceptance shall bind the authenticated account to the intended existing profile without silently creating a duplicate.
- **FR-006**: Invitations shall be single-use, expiring, revocable, and unusable after the target profile is bound.
- **FR-007**: Kinward shall distinguish household role, account state, privacy class, assistant ownership, and action authority and shall enforce every transition outcome in Section 7.7, including the complete `active`/`disabled`/`locked`/`recovery-pending` lifecycle, transition authorization and audit, non-active fail-closed session/token/authority invalidation, surface and assistant/provider denial, pending-work and proactivity disposition, retained ownership without administrative access, same-profile reactivation and revalidation, last-administrator rejection, continued restrictive prior access while disposition is incomplete, and immediate expiry, revocation, or invalidation of approvals, delegations, shares, and derived access made invalid by a committed transition.
- **FR-008**: After onboarding, a person shall review at minimum their display and preferred name, household role, privacy/policy class, account-binding state, and household relationships, and Kinward shall implement the complete Section 7.8 correction boundary. An authenticated account-bearing person may directly correct their own display/preferred names; a directly household-authored `household-shared` relationship fact may be corrected only by its adult subject or, for a minor/profile without an account, the adult named by that subject's current policy. Corrections shall be atomic, version-serialized, idempotent for exact duplicates, append-protected and privacy-safe in audit, and shall atomically refresh or invalidate dependent policy and authorization; stale, conflicting, ambiguous, incompletely enumerable, or unauthorized changes fail closed. Role and policy-class changes remain Section 7.7 transitions. Cross-profile rebinding is unavailable; recovery may replace credentials only for the same intended profile. Suspected wrong binding suspends every implicated access path and requires a future separately specified adjudication, with no profile/credential exchange and no private assistant-state inspection or transfer. Acceptance shall cover every authorized actor/type, unauthorized and stale concurrency, rollback, audit, dependency refresh/invalidation, same-profile recovery, suspected-binding denial, and absence of private-state transfer.

### 13.2 Assistants, conversation, and topics

- **FR-009**: In the first usable release, each account-bearing person shall have exactly one primary personal assistant. Additional personal assistants are unavailable and require a future Section 4.3 PRD amendment; specialist assistants remain separate and disabled under Sections 3.2 and 9.1.
- **FR-010**: Every primary personal or specialist assistant shall have exactly one owner; this ownership rule does not imply that more than the one committed primary personal assistant is available.
- **FR-011**: Bootstrap and lifecycle management of the household fallback assistant shall enforce Section 9.2, including household ownership and the absence of a personal owner.
- **FR-012**: During initial or invited-adult onboarding, a person shall complete a short personality and interaction-preference interview to name an assistant and configure at minimum response tone/formality, verbosity, warmth/humor, directness, explanation style, confirmation style, and input/output preferences declared available for the active surface; an unavailable choice is neither shown as active nor saved. These persisted presentation preferences shall not change data access, sharing, action authority, identity policy, or any other permission boundary.
- **FR-013**: Kinward shall support the request lifecycle in Section 12.1.
- **FR-014**: Conversation continuity shall be bound to person, assistant, topic, surface, and current authorization.
- **FR-015**: A user shall continue an authorized topic across mobile and desktop without restating stored context.
- **FR-016**: Users shall manage topic lifecycle and sharing as defined in Section 12.3.
- **FR-017**: Assistant cancellation shall prevent unsubmitted actions and visibly mark the request cancelled.

### 13.3 Memory and durable context

- **FR-018**: Personal memory shall be bound to the owning person and creation permissions.
- **FR-019**: Household-shared facts shall be stored or labeled separately from private memory.
- **FR-020**: The household fallback assistant shall never query private personal memory indexes.
- **FR-021**: Context assembly shall retrieve only information permitted for the current person, assistant, topic, surface, audience, and action.
- **FR-022**: Kinward shall store and expose for inspection two independent classifications: knowledge state (`confirmed durable fact`, `inferred observation pending confirmation`, or `transient context`) and sharing class from Section 8.1. `Household-shared fact` means a confirmed durable fact whose sharing class is `household-shared`; it is not a fourth knowledge state. Fact management and item explanation shall show both classifications without exposing protected source content.
- **FR-023**: Every inferred observation requires explicit confirmation by its subject or an otherwise authorized fact owner before promotion to a durable fact; an unconfirmed observation shall not influence future assistance as a durable fact.
- **FR-024**: Users shall inspect, correct, reclassify, and delete durable facts about themselves; deleting the underlying fact remains available while only the sanitized deletion/activity record defined in Section 14 may be retained.
- **FR-025**: Durable facts shall include source category, timestamp, sharing class, confirmation state, and confidence.
- **FR-026**: Sharing and derived data shall enforce every narrowing, revocation, expiry, backend authorization, shared-display/fallback removal, dependent-access invalidation, and rendered/cache clearing outcome in Section 8.1 within NFR-020; it shall also enforce Section 8.2 exact source IDs and versions, transformation version and expiry, invalidation on any source content/version change, new privacy-filtered transformation and source-owner approval before reuse, default denial of recipient onward-sharing authority, unanimous private-source-owner transformation authority (or equally scoped owner permissions), mixed-owner fail-closed behavior, direct-versus-derived person-deletion disposition, downstream invalidation, external deletion-pending, and owner disclosure.
- **FR-027**: Optional memory or knowledge provider failure shall not cause Kinward to claim unavailable memory as known.

### 13.4 Identity, privacy, and permissions

- **FR-028**: Personal surfaces require authentication before exposing private assistant content.
- **FR-029**: Shared surfaces shall implement every state and outcome in Section 10, including the exact neutral candidate payload and all transition-clearing fixtures.
- **FR-030**: Authorization shall be enforced by backend services and provider-query construction, not only client rendering.
- **FR-031**: Administrators shall not receive another adult’s private data merely because of role.
- **FR-032**: Teen and child policy shall implement Section 7 and shall unconditionally deny every request, query, operation, or output that would disclose private teen content outside owner-authorized, explicit privacy-filtered sharing. No emergency, legal, safety, administrator, guardian, operator, or other current-scope or role-derived exception may override that denial. The policy shall also implement the visible statement of private and explicitly shared categories, the PD-02 child-policy interim of no guardian-visible child category by default, named-adult action-policy assignments, and fail-closed policy-class transitions, and shall be covered by automated tests.
- **FR-033**: Every API response containing personal information shall be scoped to the authenticated identity and effective surface policy.
- **FR-034**: Kinward shall log denied private-resource access without logging the protected content.

### 13.5 Surfaces, cards, and layouts

- **FR-035**: Kinward shall render personal mobile, personal tablet, personal desktop, shared kitchen, and shared living-room layouts from one card registry and one layout registry in the frontend-foundation gate (Section 4.1.1), and shall support live personal mobile, personal desktop, and at least one live shared-display context (kitchen or living room) in the first live slice (Section 4.1.2).
- **FR-036**: Every surface shall receive ownership, privacy, room when applicable, interaction capability, and viewing-distance context.
- **FR-037**: The personal default shall include assistant presence, Now, briefing, topics, and persistent input.
- **FR-038**: Now and briefing shall implement Section 12.4.
- **FR-039**: The shared-display default shall show household-safe ambient information and return to that state after personal-session expiry.
- **FR-040**: Product surfaces shall render registered cards from validated layouts.
- **FR-041**: Invalid configuration shall fail safely and preserve the last valid layout.
- **FR-042**: Generated temporary views shall implement Section 3.9, use registered components only, and delete `surface-ephemeral` state on every normal or abnormal session end under Section 8.1.
- **FR-043**: Users shall inspect why an item appeared, source categories, confidence, sharing class, and available correction without exposing hidden reasoning or secrets.
- **FR-044**: Shared-display rendering shall never receive private card data when the effective policy forbids it.

### 13.6 Proactivity, coordination, approvals, and activity

- **FR-045**: Proactive delivery shall support ambient, briefing, nudge, interruption, and autonomous-action levels and shall keep delivery level distinct from the Briefing UI area under Section 12.4. In Milestone C, only calendar-change exceptions may be proactively evaluated and delivered, only at ambient or briefing level, with suppression, deduplication, household-safe explanation, category-level correction through an authorized personal surface, and metric instrumentation. Nudge, interruption, autonomous-action, and every non-calendar proactive category remain disabled until Milestone D and the recorded PD-04 category disposition permit them.
- **FR-046**: Kinward shall select the least disruptive permitted level using the versioned Section 12.4.1 review-opportunity model: ambient when no response window exists; briefing when action can wait until the deterministically resolved next review opportunity; nudge only when a response is needed before that review; interruption only when delay would satisfy the Section 6.5 confirmed deadline or safety critical predicate; and autonomous action only within an explicit Section 11 policy. Personal settings default to 08:00 and 18:00 in the household IANA timezone, change prospectively, and remain a simple level-selection preference rather than a routine builder. Lower confidence or a tie selects the lower level, privacy policy may only reduce or suppress delivery, and stale/unknown setting or timezone fails closed to briefing except for the confirmed-deadline nudge allowance; it never independently permits interruption. Acceptance includes every Section 12.4.1 boundary and setting-change fixture.
- **FR-047**: Non-critical interruptions shall respect the default cap in Section 6.5 (Milestone D).
- **FR-048**: In Milestone C, Kinward shall evaluate every FR-057 addition, removal, time, location, attendee, or cancellation change from permitted calendars against confirmed durable facts and events on calendars permitted for that purpose, without routine definitions. It shall create a calendar-change exception only when the change creates or removes a time overlap, changes a confirmed departure or transportation obligation, changes a required attendee's ability to attend, or adds/removes a response obligation; each supported predicate shall have positive and negative fixtures.
- **FR-049**: A proactive item shall expose a household-safe reason for its category and selected level and provide category-level correction. A private surface provides the full permitted explanation and correction; a shared display shows only information class and household-safe reason and hands correction to an authorized private device, satisfying PD-07 without exposing private source details.
- **FR-050**: Coordination requests shall disclose only the minimum information required for a response and shall be backed by the delegation fields in Section 9: provenance, sharing class, purpose, permitted data, recipient, and expiry. Coordination requests are Milestone D scope.
- **FR-051**: Coordination requests shall identify sender or represented person, requested outcome, response options (`accept`, `decline`, and `counter`), recipient, purpose, permitted data, provenance, sharing class, and expiry; a missing, expired, revoked, or mismatched field prevents delivery. Delivery commits the canonical request ID and state. The only terminal states are `accepted`, `declined`, `countered`, `expired`, `revoked`, and `delivery-failed`; sender withdrawal and authorization withdrawal both resolve as `revoked` and create no additional state. A valid accept or decline makes the original terminal `accepted` or `declined`; a counter makes it terminal `countered` and creates a new linked request with its own expiry and authority validation; expiry before closure makes it `expired`; and exhausted delivery to the validated recipient makes it `delivery-failed` without revealing a private source. Duplicate responses are idempotent. Responses are serialized against request version; sender revocation, authorization revocation, or expiry at or before response time wins, and a concurrent same-version response batch otherwise resolves by fixed precedence `decline`, then `counter`, then `accept`. The first resulting terminal state is immutable, later responses are rejected as stale, and sender and recipient each see the same terminal state through their authorized views. Coordination requests are Milestone D scope.
- **FR-052**: External actions shall implement every adult and minor principal-definition, requester-independent minor-policy, cross-person authority, bounded-delegation, preparation block, exact-approval, general multi-principal lifecycle, expiry, unknown-result, restart, and same-target concurrency rule in Section 11.
- **FR-053**: Every meaningful external-action attempt, including preparation blocked for missing authority and every cancelled, failed, timed-out, and `unknown` attempt, shall produce the complete mandatory Section 11 record sequence and identify acting assistant, integration, attempt, provider result or its absence, final result, undo availability, and every required principal—requester, represented adult/minor, target owner/minor, affected adult/minor, and approver as applicable—with the authority, policy assignment, sharing authorization, approval, delegation, absence, or mismatch for each. Records and separate views shall enforce the Section 11.1 audience/classification matrix. Zero eligible attempts or mandatory fields may be omitted; the complete event population and automated test matrix govern Milestone C acceptance.
- **FR-054**: Users shall filter activity by person, assistant, integration, action category, result, and date only after record-level and view-level authorization; filters, counts, facets, empty states, and metadata shall return or reveal only activity the caller is authorized to access under Section 11.1.

### 13.7 Calendar integration

- **FR-055**: A person shall connect and disconnect a calendar account as a person-owned credential under Section 9.1 without exposing it to other household members; assistant deletion revokes only assistant-scoped grants and references and does not delete that credential absent explicit person-level disposition.
- **FR-056**: Calendar integration shall read events only within the connected account’s granted scope.
- **FR-057**: Calendar change detection shall identify additions, removals, time changes, location changes, attendee changes, and cancellations.
- **FR-058**: Detected changes shall retain provider event identity, observed version, observed time, and affected account.
- **FR-059**: Private calendar details shall not appear on a shared surface or household fallback context unless explicitly shared.
- **FR-060**: Calendar mutations shall implement Section 11, produce the FR-053 activity sequence, consume approval at submission, preserve unknown state across restart, reconcile unknown provider results before any retry or same-target mutation, and require new approval after any source-version or prepared-field change.
- **FR-061**: Integration reconnect shall preserve local configuration while marking calendar data with its last successful observation time. Stale or unavailable calendar data shall not generate a current-change briefing or permit mutation; current visibility and mutation resume only after a successful refresh.

### 13.8 Home Assistant integration

- **FR-062**: Home Assistant shall remain authoritative for physical areas, devices, entities, services, and current state.
- **FR-063**: On everyday assistant and shared-display surfaces, Kinward shall describe supported Home Assistant state and actions using household-assigned room/device names, ordinary state words, and plain action verbs. It shall not expose raw entity IDs, `domain.service` names, provider field names, error codes, or payload syntax there or in household-facing approvals/activity; an authorized administrator may deliberately inspect technical mappings only inside separate Kinward Control.
- **FR-064**: Kinward shall distinguish observed device state, requested action, submitted action, and confirmed resulting state.
- **FR-065**: Post-action confirmation is required by default for every Home Assistant mutation. Unless Home Assistant supplies or Kinward subsequently observes the resulting physical state matching the approved target, the outcome is `unknown`, never `completed`, even when the service call itself succeeded.
- **FR-066**: Home Assistant actions shall follow identity, permission, stale-state, approval, activity, and direct household-resource authority requirements, including FR-095.
- **FR-067**: Home Assistant unavailability shall remove or mark stale dependent cards without preventing core Kinward use. If unavailability begins after submission and before resulting-state confirmation, the action remains `unknown`, is not retried automatically, and awaits reconciliation after reconnect.

### 13.9 Kinward Control

- **FR-068**: Kinward Control shall be separate from everyday assistant navigation.
- **FR-069**: Administrators shall manage people, invitations, assistants, child policy, household integrations, shared surfaces, proactive defaults, backup status, and health. Disabling an integration immediately revokes new authority, expires pending approvals, cancels unsubmitted work, and leaves already submitted work `unknown` until reconciliation; it never triggers an automatic retry.
- **FR-070**: Adults shall manage their own private integrations, memory, assistant preferences, and sharing without unrelated administrative access.
- **FR-071**: Administrative views shall not expose credentials, hidden prompts, unrestricted private adult content, or model chain-of-thought.
- **FR-072**: Health shall distinguish core failure, degraded optional capability, intentionally disabled capability, stale data, reauthorization required, and configuration error.
- **FR-073**: Every degraded state shall include an actionable next step or explicitly state that no action is required.

### 13.10 Minor approval privacy and later assistant delegation

- **FR-087**: Every action that represents, targets, or materially affects a minor—regardless of requester, adult initiation, minor account availability, or household ownership of the resource—shall apply that minor's category policy and route only to the named adults and exact `any-one`, `all`, or `threshold(k)` quorum encoded in the current versioned assignment. This includes adult-initiated child calendar mutations and household/Home Assistant actions. It shall give the Section 11 age-appropriate subject or policy-recipient notice; disclose only the minimum exact fields; and implement the general multi-principal serialization, duplicate idempotency, approval withdrawal, decline, cancellation/revocation/disablement/expiry precedence, concurrent response, assignment-change invalidation, and atomic acting revalidation rules. For a teen, every approval field derived from private teen content shall additionally require the teen's explicit authorization of the exact privacy-filtered recipients, fields, purpose, and expiry; named action-approval authority alone never authorizes disclosure. Missing assignment, notice disposition, sharing authorization, or valid approval fails closed before preparation and submission, and administrator/requester status alone confers no approval authority.
- **FR-088**: A minor's private conversation, prompt, and prepared message body shall never be copied into an adult's memory or approval payload by default. If a future exact-action approval cannot be decided without a prepared body, a child's specific body may be disclosed only to the assigned approver after the child is separately told what will be shared and why and only when the child's policy permits it. A teen's specific body may be disclosed only as a new, separately reviewable `selected-share` item after the teen explicitly authorizes the exact privacy-filtered transformation, recipient, body field, purpose, and expiry; otherwise Kinward unconditionally denies the disclosure and submission. Neither path exposes the private source or copies the body into adult memory.
- **FR-089**: Before specialist invocation or inter-assistant delegation is enabled, Kinward shall enforce and expose for owner inspection the delegation record in Section 9.1 and shall deny exchange for an absent, expired, revoked, mismatched, or over-broad record.

### 13.11 Additional lifecycle, policy, and E2E requirements

- **FR-090**: Pending inferred observations shall implement the complete Section 8.4 lifecycle, including subject and authorized fact owner, permitted pre-confirmation inspection-only use, correction and explicit confirmation, rejection/deletion, fixed expiry, source dependencies, backup/restore and retention disposition, dependent invalidation, and suppression of recurrence after rejection, deletion, or expiry absent genuinely new versioned source evidence.
- **FR-091**: Initial onboarding and later household-profile management shall support an optional pet profile without an account; when selected before the initial commit, it participates with every selected adult and child profile in the FR-002 atomic, duplicate-safe retry/rollback outcome. Every pet profile shall enforce Section 7.5.1: only explicitly entered `household-shared` care and relationship facts, with no assistant, private conversation or memory, credentials, integration ownership, approval role, delegation right, or action authority.
- **FR-092**: Milestone C shall require a purpose-specific calendar and transportation recipient assignment for each represented person used by FR-048. An account-bearing adult configures their own assignment; for a minor or profile without an account, only an adult explicitly authorized by that person's policy may configure it, and administrator status alone grants no authority. The subject when account-bearing and every named adult shall inspect the exact purpose and recipients. Kinward shall deliver only to those recipients; with no valid assignment it shall fail closed and send only a household-safe configuration-gap notice, without private event details, to an administrator authorized to manage that person's policy.
- **FR-093**: Personal-assistant lifecycle shall enforce Section 9.1: exactly one primary personal assistant per account-bearing person in current scope; no cross-person reassignment; owner-only disablement or deletion except a minimum account-recovery operation under an explicit resolved policy; content deleted or retained only for an atomic same-owner replacement; unsubmitted approvals/work cancelled or expired; delegation and assistant-scoped grants revoked; integration references removed or transferred only to that replacement; person-owned credentials preserved while still owner-authorized and deleted only by explicit person-level disposition; submitted/`unknown` actions left reconciliation-blocked; rejection when any item lacks a valid disposition or when a last-required assistant lacks an atomic same-owner replacement; and no administrative reveal, copy, or transfer of another adult's private assistant state.
- **FR-094**: Milestone C shall pass an end-to-end UJ-7 fixture in which a policy-permitted minor authenticates, conducts a private assistant conversation, receives homework help, prepares but cannot submit a fictional teacher message, sees the exact recipient/field/purpose disclosure notice before any approval-required sharing, cancels one prepared request, and allows another to expire. Additional branches shall exercise each Section 11 quorum rule and mixed/concurrent approve-decline, approval withdrawal, authority revocation, and assignment-change invalidation. Teen branches shall prove one exact owner-authorized privacy-filtered approval view and unconditional denial with no private-existence signal when that sharing authorization is absent, expired, revoked, or mismatched, including when the recipient remains a named approver. Every non-approved branch remains unsubmitted, the request lifecycle remains accurate, and no conversation, prompt, prepared body, or unrelated minor metadata enters adult memory, approval views, administrator/operator views, or activity filters beyond the separately authorized minimum in Sections 11 and 11.1.
- **FR-095**: Direct household-owned external actions, including Home Assistant actions, shall enforce the versioned category-policy and general multi-principal authority model in Section 11: administrator configuration without role-derived request or approval authority; named requester eligibility, eligible approvers, explicit quorum, independently required affected-principal approvals, or an exact bounded autonomous policy; limits, target classes, and affected-person rules; explicit approval from another adult affected in security, access, safety, private information, or private material outcome unless that adult supplied a matching bounded delegation; application of FR-087 whenever a minor is represented, targeted, or materially affected; and fail-closed preparation and submission for missing, ambiguous, stale, inconsistent, or multiply matching policy.
- **FR-096**: Milestone D shall pass the complete UJ-10 end-to-end fixture without creating, invoking, or enabling a specialist assistant: coordination delivery and the exact `accepted`, `declined`, `countered`, `expired`, `revoked`, and `delivery-failed` terminal set under duplicate, sender withdrawal, authorization loss, and concurrent-response cases; generated-view `ephemeral`, `topic`, and `pinned` disposition; nudge and interruption explanation and category correction; and a bounded autonomous action with either verified inverse rollback success/failure/unknown evidence or an irreversible outcome disclosed before action, with every result truthfully visible and recorded.
- **FR-097**: Milestone C shall implement the direct household-authored content lifecycle in Section 8.5 for active and restored content: bootstrap current-administrator joint management authority over qualifying household-owned content only; verified inspection without private-source access; versioned editor changes; any-current-administrator quarantine; one-current-administrator no-conflict republication or other disposition; fail-closed conflicting dispositions requiring all current administrators or an explicit versioned household policy; prospective administrator-set changes and last-administrator rejection; ambiguity quarantine; append-protected audit; and restore fixtures for each lifecycle branch.
- **FR-098**: Kinward shall import explicitly allowed household data only from a documented versioned format into the new single-household baseline. Every supported Milestone C format shall define and accept a non-empty **minimum import set** (the minimum positive set) containing all five classes: (1) people and profile relationships; (2) primary personal assistants and their personality settings, with exactly one mapped primary per imported account-bearing person; (3) confirmed durable facts with provable ownership and sharing class; (4) non-secret integration configuration; and (5) Home Assistant mappings. Import shall validate manifest and schema version; allowed record class; stable import identity; household, person, assistant, and content ownership; knowledge state, privacy/sharing class, source dependencies, and policy compatibility; and integration/provider mapping shape before commit. Exact duplicates in each minimum class are idempotently reported and skipped, while conflicting duplicates or ownership/class ambiguity reject the whole import. Reusable credentials, sessions, tokens, secrets, legacy tenant/control-plane/billing/support records and other disallowed legacy state, privacy-filtered or otherwise derived shared statements, unknown classes, and unlisted data are rejected and reported as reauthorization or unsupported tasks without exposing protected bodies. Imported personal/private or `selected-share` content remains quarantined until the mapped same owner authenticates and explicitly accepts its current access/sharing disposition; qualifying direct household-authored content remains quarantined until FR-097 disposition. Any invalid or rejected record rolls back the complete import to the prior valid state; no partial household, binding, authority, content, configuration, or mapping is committed. Milestone C UJ-11 evidence shall separately cover successful import of each minimum class, exact and conflicting duplicates in each class, every applicable quarantine/release denial, credential and disallowed-legacy-state rejection, unknown/derived/privacy/ownership/policy/mapping rejection, privacy-safe reporting, and bit-for-bit or contract-equivalent atomic rollback after a failure in each class.
- **FR-099**: Private-device handoff shall implement Section 10.1, including intended-person binding, the exact non-private pre-authentication payload, atomic single-use redemption with current identity/topic/share/account/source/dependency/surface authorization re-evaluation, terminal `accepted`, `declined`, `expired`, `revoked`, and `unreachable` outcomes, and fail-closed wrong-person, replay, downgrade, revocation, expiry, ambiguity, and downgrade-to-weaker-path cases without revealing private content or private existence.
- **FR-100**: Every external action requiring decisions from multiple principals shall implement the general multi-approver lifecycle defined by Section 11's multi-principal approval object across minor and non-minor, personal and household-owned actions: immutable request/prepared-mutation/policy versions and complete principal roles; one explicit quorum plus every independently required affected-principal approval; serialized responses; exact-duplicate idempotency and conflicting-duplicate rejection; pre-acting approval withdrawal and irreversible decline on that request; deterministic cancellation/revocation/disablement/expiry and mixed-response precedence; immutable terminal result; immediate invalidation rather than reinterpretation after policy, assignment, sharing-authority, or affected-principal change; and atomic revalidation/approval consumption/exactly-once transition to `acting`. Acceptance shall include non-minor household fixtures for `any-one`, `all`, and `threshold(k)`, every precedence boundary, concurrent mixed responses, stale versions, policy change, sharing/authority loss, source change, and failure of atomic acting revalidation; minor quorum remains the stricter FR-087 specialization.

## 14. Backup, restore, export, retention, and upgrade contract

### 14.1 Included data

The first usable release backup includes:

- household identity and configuration,
- people and account bindings excluding reusable authentication secrets,
- assistants and personality settings,
- privacy, sharing, and authority policies,
- topics and locally stored conversation records,
- confirmed durable facts and sharing metadata,
- unexpired pending inferred observations with their owner, subject, absolute expiry, disposition state, and source dependencies,
- layouts and surface assignments,
- integration configuration excluding every integration credential while PD-06 remains open,
- approvals and activity history,
- unresolved-action reconciliation and blocking state containing at minimum attempt identity, target, provider reference, source version, idempotency marker when one exists, and current status,
- every deletion-pending person's overlay version, underlying account state, deletion-request authority/version, unresolved-action references, abandonment/reconciliation status, and completion blocker without restoring invalidated authority artifacts,
- and provider reference mappings required to reconnect optional stores.

### 14.2 Excluded or conditional data

The manifest must identify:

- every integration credential as excluded and requiring reauthorization while PD-06 remains open,
- externally stored content not copied into the backup,
- external provider data subject to separate retention,
- caches that can be rebuilt,
- and unsupported historical data.

### 14.3 Post-restore account access

The backup manifest must classify every authentication and recovery artifact as portable or excluded:

- **Portable:** person/account binding records, and administrator account-recovery material explicitly designed for restore (for example password verifiers or restore recovery codes, where the architecture declares them safe to export).
- **Excluded:** reusable session tokens, refresh tokens, pending invitation tokens, device-trust records, and every provider OAuth or integration credential while PD-06 remains open.

Portable administrator account-recovery material is governed only by Section 14.3 and AD-01/AD-12; it is not an integration credential. While PD-06 is open, every integration credential is excluded from Milestone C backups and every restored integration requires reauthorization, even if an encryption mechanism could technically export it.

While AD-12 is open, an archive containing private household data or portable account-recovery data may be exported or restored only when its confidentiality and integrity are protected under NFR-038; otherwise those operations are unavailable. Before export or restore, the authenticated administrator performing the operation must be told which account-access and recovery material is portable or excluded and the resulting reauthentication or recovery consequences. Each affected account holder must receive the consequences applicable to their account on their next authenticated personal access or recovery flow, without exposing another person's recovery state. AD-12 selects the key, archive format, and storage mechanism, not this protection or notice outcome.

**Point-in-time restore semantics:** A household-owned archive is an honest snapshot of what it contained when created. It cannot reveal a deletion, revocation, share narrowing, owner removal, or other disposition that happened only after that snapshot. Before restore begins, Kinward must explicitly warn the authenticated administrator that an older archive may therefore contain later-deleted or later-restricted content, that restore cannot apply unknown later events retroactively, and that the safeguards below prevent casual reactivation rather than claiming impossible retroactive erasure.

Restore must re-establish access without unsafe identity rebinding:

- Direct household configuration with no personal/private source dependency may restore into normal household use.
- Direct household-authored user content—including directly authored `household-shared` facts, topics, and topic content with no personal/private or privacy-filtered source dependency—restores quarantined and absent from shared-display, household-fallback, assistant/provider context, search, ordinary rendering, and export. The current Section 8.5 content-ownership policy governs inspection and disposition: by bootstrap default, current household administrators jointly hold management authority over this household-owned content only; any current administrator may keep or place it in quarantine; and one current administrator may republish, narrow, export, or delete after inspection when no conflict exists. Conflicting dispositions against the same base version remain quarantined and require agreement from all current administrators or an explicit versioned household policy. Missing or ambiguous direct authorship, dependency state, current authority, classification, audience, or disposition remains quarantined and fails closed. This review is required even when the archive does not reveal that the item was deleted or narrowed after its snapshot, and it never grants inspection of private or derived source content.
- Every personal account is restored disabled and every `private-person`, `private-child`, `selected-share`, personal-assistant, personal-integration reference, and other owner-personal item is quarantined from retrieval, provider queries, assistant/fallback context, rendering, export, and ordinary administration. A restored `deletion-pending` person additionally retains the Section 7.9 overlay and may enter only reconciliation; restore and recovery cannot reactivate that account or cancel/completely resolve deletion. The administrator must be able to authenticate, or complete a documented secure recovery procedure, bound to the restored administrator profile without manual database editing, but that recovery does not itself release quarantined items.
- Members re-establish authentication against their existing restored profiles. Member re-access after restore is administrator-initiated: a documented administrator-initiated recovery invitation must target the member's existing restored profile after administrator authentication and intended-member verification. Successful recovery establishes replacement credentials and account binding for that same profile, invalidates and supersedes the prior unusable credentials and binding, and must not create a duplicate profile or bind another person's account. The personal account remains limited to its private quarantine/recovery flow until the restored owner reauthenticates and explicitly accepts its access disposition. The owner then receives a private inventory and must explicitly reauthorize the access/sharing disposition or choose deletion or owner-only export for each item or clearly bounded batch before release; a restored `selected-share` item requires the owner to reauthorize its exact purpose and recipients.
- A restored `selected-share` item or household-shared privacy-filtered/derived statement is never reactivated automatically. A derived statement remains invalid and unavailable—not merely quarantined for republishing—and reuse requires a new transformation against current source IDs/versions and new approval from every required source owner under Section 8.2.
- Content whose restored owner is absent, marked deleted in the snapshot, or never reauthenticates remains inaccessible. Administrator or operator role grants no inspection or release authority. Deletion or owner-directed export of that content is unavailable until a future, separately authorized policy defines authority, notice, unresolved-action handling, audit limits, and privacy-preserving execution; no current role may infer that authority.
- Every pre-restore session, invitation, approval, and handoff token is invalid after restore.

### 14.4 Baseline migration and controlled import

The rebuild has one schema origin: `001_initial_single_household`. A clean database applies that baseline directly and has no executable dependency on, copy of, or compatibility shim for the retired legacy migration chain. Upgrade migrations may begin only after this baseline and remain distinct from the explicit data-transfer contract.

Legacy or external household data can enter only through FR-098's versioned import. Every supported Milestone C import version publishes its allowed record classes and field schemas and must accept the non-empty minimum import set: people and profile relationships; primary personal assistants and personality settings, with exactly one primary for each imported account-bearing person; confirmed durable facts with provable ownership and sharing class; non-secret integration configuration; and Home Assistant mappings. Other useful memory or configuration classes are unsupported unless explicitly allowlisted by a later version. Allowlisting any class never bypasses owner, privacy, source-dependency, authority, cardinality, or policy validation. Credentials, authentication/security artifacts, and disallowed legacy tenant/control-plane/billing/support state are never imported and become named reauthorization or unsupported tasks; derived shared statements are rejected and require a new authorized transformation under Section 8.2. Imported personal/private and `selected-share` content is inaccessible until same-owner authentication and explicit disposition, while qualifying direct household-authored content enters FR-097 quarantine. The importer runs against a valid single-household baseline, produces a privacy-safe accepted/skipped/rejected report, and commits only after the whole candidate household graph validates; any rejection restores the bit-for-bit or contract-equivalent prior valid database state.

### 14.5 Requirements

**Audit retention semantics:** Deleting underlying user content remains available. In the active deployment, retention applies only to the append-protected, sanitized deletion and activity records allowed by FR-082 and never permits an in-place undelete or restoration of access to the deleted body. An older point-in-time archive may still contain that body because it predates the deletion; Section 14.3 quarantine prevents it from becoming accessible without the restored owner's new authorization and never gives administrators inspection authority.

**Whole-household deletion boundary:** Deletion of the household deployment and all household data is outside the current release scope and is unavailable. It requires a future PRD amendment with an authority model, confirmation and recovery behavior, external-provider disposition, unresolved-action handling, backup disposition, audit limits, journeys, FR/NFRs, traceability, and release gates before implementation.

- **FR-074**: Backups shall contain a versioned manifest listing included, excluded, protected, externally referenced, and rebuildable data, including the unresolved-action reconciliation state, deletion-pending overlay/blocker state, and unexpired pending-observation lifecycle metadata defined by Sections 14.1, 7.9, and 8.4. Backup creation shall either preserve the minimum unresolved-action and deletion-pending state or reject/quiesce export while such actions exist; it shall never emit an archive that can silently lose their blocking state or restore invalidated authority.
- **FR-075**: Restore shall support a clean deployment on the same or a declared compatible schema version and shall present the Section 14.3 point-in-time warning before any archive state is applied.
- **FR-076**: Restore shall complete atomically or stop without replacing the existing valid household state.
- **FR-077**: Post-restore verification shall validate household identity, normal direct household-configuration availability, people and pet profiles, disabled personal accounts, every deletion-pending overlay and reconciliation-only restriction, quarantine of every personal/private/`selected-share` item and every direct household-authored user-content item, permanent non-reactivation of household-shared derived statements, assistants, policies, layouts, activity, durable facts, unexpired pending-observation owner/source/expiry state, provider-reference integrity, and every unresolved action's attempt identity, target, provider reference, source version, idempotency marker when present, status, and retry/same-target blocking state. Mandatory fixtures include a deletion-pending person before and after reconciliation abandonment; archives predating deletion and share narrowing/revocation for direct household-authored facts and topics; a restored derived household share; the complete FR-097 inspection, editor, quarantine, no-conflict single-administrator disposition, conflict/all-current-administrator or explicit-policy resolution, administrator-change/last-admin, ambiguity, and audit lifecycle; restored-person-owner reauthentication and exact reauthorization; absent/deleted-owner and administrator private-content inspection denial; and normal direct household-configuration restore. A mismatch fails restore; restore never silently republishes household-authored content, reactivates a deletion-pending account, share, or derived statement, unblocks, retries, completes, or discards an unresolved action.
- **FR-078**: Every integration credential excluded under the PD-06 safe interim shall be listed as a required reauthorization step; portable account-recovery material remains separately classified under Section 14.3.
- **FR-079**: The rebuilt repository shall start from one new single-household baseline migration, `001_initial_single_household`, that creates the current schema without executing, copying, or depending on the legacy migration chain. Legacy data enters only through the explicit versioned FR-098 import contract, never through schema-history replay or host-path coupling.
- **FR-080**: Upgrade shall require a restorable pre-upgrade backup and stop with actionable instructions when compatibility checks fail.
- **FR-081**: Backup creation and restore shall produce activity records without recording secret material.
- **FR-082**: The product shall document retention behavior for conversations, topics, activity, approvals, durable facts, pending inferred observations, and integration caches. While PD-05 is open, the no-automatic-deletion interim applies only to these named durable retention classes: persisted conversation and topic bodies in `private-person`, `private-child`, `selected-share`, or `household-shared`; confirmed durable facts in those classes; active sharing and authority-policy records; durable approval-decision and activity records; durable integration configuration/provider mappings; and unexpired pending inferred observations until FR-090's fixed expiry. It explicitly does not retain `surface-ephemeral` data; rendered, cached, or provider-context copies invalidated by authorization, source-dependency, narrowing, revocation, or expiry; expired or revoked session, invitation, approval-capability, handoff, recovery, security, or integration-authorization tokens or artifacts (as distinct from a permitted sanitized durable decision record); or any data whose deletion is mandatory for privacy or security. User-requested deletion of underlying content remains available. In the active deployment, deletion has no casual undelete path and removes the body from all later backups; it may retain only an append-protected sanitized record containing actor or policy disposition, time, data class, opaque target reference, requested disposition, and result—never the deleted body, secret, private title, or unrestricted provider payload. An archive created before deletion remains an honest point-in-time snapshot and, if restored, is governed by the Section 14.3 warning and quarantine rather than automatic access.
- **FR-083**: Deleting a person shall implement the complete separate Section 7.9 `deletion-pending` lifecycle and shall be blocked if that person is the sole administrator unless another adult is first made administrator. An account-bearing adult must request or confirm their own deletion; administrator status alone cannot authorize it, except for a minimum operation under the explicit resolved account-recovery policy. For a minor or profile without an account, only an adult explicitly authorized by that person's policy may confirm deletion. Atomic entry into `deletion-pending` immediately overrides any `active`/`disabled`/`locked`/`recovery-pending` account state; disables account authority; invalidates every session, refresh/device/invitation/approval/handoff/delegation/provider/proactive artifact; cancels unsubmitted work; denies new work, approval, private retrieval, sharing, export, and ordinary administration; clears rendered/cache/provider-context/ephemeral copies within NFR-020; and permits only minimum reconciliation. Before deletion can complete, every submitted or `unknown` action represented by, targeting, or materially affecting that person must reconcile to a confirmed result. If reconciliation cannot complete, Kinward preserves the protected minimum attempt identity, target, provider reference, source version, idempotency marker when present, status, and blocking state. Explicit reconciliation abandonment leaves the person pending, result `unknown`, retry and same-target execution blocked, deletion incomplete, and authority unavailable; a later authorized reconciliation restart observes the same attempt without resubmission. Pending state and blockers survive process restart, backup, and restore. Once eligible, the confirmed atomic disposition shall: delete `private-person` and `private-child` content they own, including conversations, topics, facts, the primary personal assistant, person-owned credentials, assistant-scoped grants, integration references, and personal integration connections; delete `selected-share` items they own and revoke their access to `selected-share` items owned by others; preserve under household ownership only directly authored `household-shared` items with no private or privacy-filtered source dependency, with provenance reduced to `former member`; invalidate and remove every privacy-filtered or otherwise derived `household-shared` item whose source they own plus all downstream dependents under Section 8.2; clear `surface-ephemeral` data; remove or irreversibly disable the profile/account binding and every authentication/recovery artifact; mark the profile unavailable for rebinding; reduce `system-operational` data to the append-protected sanitized deletion tombstone and protected minimum reconciliation records allowed by this requirement and FR-082; and leave the household fallback assistant household-owned. Acceptance includes entry from every account state, immediate invalidation/denial/clearing, concurrent transition and idempotent retry, abandonment and reconciliation restart, process restart, backup and restore, atomic completion failure, binding/auth-artifact removal, both direct-share preservation and derived-share/downstream removal, and tombstone/reconciliation-only retention. Earlier archives may contain pre-deletion state, but Section 14.3 quarantine and Section 7.9 overlay prevent reactivation and never grant administrator inspection.
- **FR-084**: The backup manifest shall classify every authentication and recovery artifact as portable or excluded per Section 14.3, shall exclude every integration credential while PD-06 is open, and restore shall import only portable account-access material.
- **FR-085**: After a clean restore, the administrator shall be able to re-establish authenticated access through a documented secure recovery procedure bound to the restored administrator profile, without manual database editing.
- **FR-086**: Post-restore verification shall confirm administrator access recovery without release of quarantined personal content; successful reauthentication for at least one non-administrator restored profile using the documented member re-access procedure (including that recovery supersedes the prior unusable credentials and binding, and prevents duplicate profiles or binding another person's account); explicit restored-person-owner reauthorization before any personal/private/`selected-share` release; continued quarantine and administrator/operator denial for an absent, deleted, or non-reauthenticated owner; continued deletion-pending reconciliation-only denial with no recovery/reactivation bypass; quarantine of direct household-authored user content until FR-097's current-administrator no-conflict or conflict-resolution disposition completes; old-archive deletion/narrowing outcomes for direct household-authored facts and topics; non-reactivation of restored `selected-share` and household-shared derived statements; person-to-account binding integrity; invalidation of all pre-restore session, invitation, approval, and handoff tokens; and that FR-077 unresolved-action states remain `unknown` or incomplete and continue to block retry and same-target execution until reconciliation.

## 15. Nonfunctional requirements

### 15.1 Privacy and security

- **NFR-001**: Server-side authorization shall protect every private resource and every provider query.
- **NFR-002**: Secrets and credentials shall be encrypted at rest or stored in a platform-appropriate secret mechanism and shall not appear in normal responses or logs.
- **NFR-003**: Automated tests shall cover every shared-surface state and transition.
- **NFR-004**: Automated tests shall cover adult, teen, child, administrator, personal-assistant, and household-fallback boundaries in Milestone C, and shall cover specialist-assistant ownership and delegation boundaries before any future PRD amendment enables specialist capability.
- **NFR-005**: External content shall be treated as untrusted and shall not override authorization, system policy, or action authority.
- **NFR-006**: Data sent to external providers shall be minimized to the permitted task.
- **NFR-007**: Authentication, invitation, approval, and handoff tokens shall expire and be protected against replay; private-device handoff references shall additionally be single-use and terminally invalidated under Section 10.1.
- **NFR-008**: Normal logs and telemetry shall not contain full private prompts, conversation bodies, credentials, or unrestricted integration payloads.
- **NFR-009**: Security-sensitive configuration changes and every mandatory FR-053 activity or FR-082 deletion disposition shall produce append-protected records; integrity evidence must cover all eligible events, not a quality sample.

### 15.2 Reliability and recoverability

- **NFR-010**: Failure of one or multiple optional providers shall identify every affected capability separately and shall never represent unavailable provider data as current. Milestone B evidence covers only capabilities available in B: bootstrap/setup, authentication, the assistant request path, and durable local topic reads, writes, and cross-surface continuation. Milestone C evidence additionally covers local administration and backup creation/access. Each milestone tests its own available subset under single- and multiple-provider failure; neither milestone is required to exercise a capability assigned only to a later milestone.
- **NFR-011**: External calls shall use explicit timeouts, bounded retries, and failure isolation.
- **NFR-012**: When a provider offers an idempotency control, external mutations shall use it. Otherwise, an unconfirmed attempt shall block automatic retry and same-target execution until reconciliation proves whether the first attempt changed state.
- **NFR-013**: A clean-deployment restore test covering the Section 14.3 point-in-time warning; personal and direct household-authored content quarantine; restored-person-owner reauthorization; preserved deletion-pending overlays with reconciliation-only authority, including abandonment; the complete FR-097 current-administrator ownership, inspection, edit, no-conflict, conflict, policy, audit, ambiguity, and last-admin lifecycle; absent/deleted-owner denial; normal direct household configuration; old-archive deletion/narrowing of directly household-authored facts and topics; share/derived non-reactivation; and unresolved-action fixtures shall pass before the first usable release.
- **NFR-014**: Automated backup/restore acceptance tests shall have zero known loss of data included in the backup contract and zero unauthorized release of quarantined restored data.
- **NFR-015**: Restarting, backing up, restoring, entering or remaining in person deletion-pending, abandoning reconciliation, or restarting reconciliation during an in-progress or unknown action shall preserve the deletion overlay and minimum reconciliation/blocking state as incomplete or `unknown`, shall not restore account authority, resubmit automatically, or convert or silently unblock it as `completed`; the authorized reconciliation view shall show that reconciliation is required, abandoned, resumed, or still deletion-blocking without exposing unrelated private content.
- **NFR-016**: Background jobs shall be observable, retry-bounded, and recoverable without duplicate user-visible outcomes.

### 15.3 Performance thresholds

Measured on the documented reference deployment under normal local-network conditions:

- **NFR-017**: Cached personal-home content shall become interactive within 2 seconds at p95; cold load within 4 seconds at p95.
- **NFR-018**: A submitted assistant request shall show accepted or responding state within 500 ms at p95.
- **NFR-019**: When a provider streams, first visible response content shall appear within 3 seconds at p95, excluding documented provider outage conditions.
- **NFR-020**: Backend detection of an identity downgrade shall invalidate further private fetch authorization immediately. A connected shared-display client shall remove private content within 250 ms of receiving the downgrade signal and no later than 1 second after backend detection; on connectivity loss, session uncertainty, or inability to verify freshness of authorization, the client shall fail closed and remove private content within 1 second of detecting that condition. AD-10 selects the verification and signaling mechanism, not these privacy outcomes.
- **NFR-021**: Local-only API reads and writes shall complete within 500 ms at p95 under the documented reference load.
- **NFR-022**: The shared display shall return to household-safe state within 1 second of session expiry detection.

### 15.4 Accessibility and usability

- **NFR-023**: Core web/PWA experiences shall meet applicable WCAG 2.2 AA requirements.
- **NFR-024**: The **reference room shared-display class** is a fixed 15–24-inch, 1080p-equivalent landscape touch display viewed at 1.5 metres under ordinary indoor lighting; architecture shall document the exact Milestone C deployment within that class. At 100% text scale, actionable touch targets shall be at least 48 by 48 CSS pixels with at least 8 CSS pixels of inactive spacing between adjacent target boundaries; critical text shall be at least 32 CSS pixels and body text at least 24 CSS pixels. Text and essential UI shall meet WCAG 2.2 AA contrast (at least 4.5:1 for normal text and 3:1 for large text and essential graphical controls), remain operable with text scaled to 200%, and avoid clipping, overlap, or loss of content or function. The Milestone C accessibility audit shall run a fixed fixture containing Now, Briefing, Approval, House Status, unavailable-capability, identity-downgrade, and private-handoff states at 100% and 200% scale; measure target boxes and spacing, verify contrast programmatically, and have QA inspect every fixture from 1.5 metres in both ordinary and high-contrast conditions on the documented reference display.
- **NFR-025**: Keyboard-only users shall complete onboarding, conversation, topic continuation, approval, and basic Kinward Control workflows.
- **NFR-026**: Status shall not rely solely on color.
- **NFR-027**: Ordinary household workflows shall use household language and shall not require infrastructure or provider terminology.
- **NFR-028**: Destructive actions, privacy-sharing changes, and external mutations shall clearly state consequence before confirmation.

### 15.5 Portability and maintainability

- **NFR-029**: Capability interfaces shall avoid direct product dependency on one model, memory, knowledge, calendar, email, or smart-home provider.
- **NFR-030**: Cards, layouts, policies, schemas, provider references, and backup manifests shall be versioned for migration.
- **NFR-031**: Milestone A foundation-baseline acceptances and Milestone B/C requirements shall have automated or inspectable validation gates before being marked complete.
- **NFR-032**: Public repository fixtures and examples shall use fictional or synthetic data only.
- **NFR-033**: Current documentation shall remain separate from archived Homefront SaaS and routine-centric artifacts.

### 15.6 Observability and supportability

- **NFR-034**: Health reporting shall distinguish application, database, model, memory, knowledge, calendar, Home Assistant, background-work, and backup capabilities.
- **NFR-035**: Operators shall correlate a user-visible failed action with its sanitized activity and operational event without exposing private content.
- **NFR-036**: Metrics shall include request latency, provider latency, provider failure, action result, job backlog, privacy-policy denial, and backup result without high-cardinality private labels.
- **NFR-037**: A household administrator shall obtain a sanitized diagnostic bundle containing allowlisted system health, component versions, capability states, and opaque correlation references only. It shall exclude credentials, prompts, conversation or message bodies, private titles, unrestricted provider payloads, person-identifying activity detail, and cross-person timestamps or action labels that reveal another member's private use.

### 15.7 Backup confidentiality

- **NFR-038**: While AD-12 is open, every backup archive containing private household data or portable account-recovery data shall have confidentiality and integrity protection; if both protections cannot be established and verified, backup export and restore shall be unavailable. Before either operation, the authenticated administrator performing it shall receive the account-access, reauthorization, and recovery consequences, and each affected account holder shall receive only their own applicable consequences on their next authenticated access or recovery flow. AD-12 may select the key, format, and storage mechanism but may not weaken these outcomes.

For NFR-038, **confidentiality and integrity protected** means both protections are established and verified before export or restore; absence or failed verification of either protection keeps both operations unavailable.

### 15.8 Controlled acceptance evidence

- **NFR-039**: Milestone C and D evidence shall use the versioned, frozen-before-window controlled catalog in Section 6.6. The signed evidence pack shall record its version and content hash and list every open known defect with the frozen-rule predicate evidence, classification, owner, and disposition. Any missing required catalog case, variant, expected result, owner, artifact, requirement ID, version, hash, open defect, or unresolved automatic gate-blocking defect shall fail the applicable gate; severity, priority, waiver, duplicate, deferral, or relabeling cannot bypass the Section 6.6 rule.

### 15.9 Default deployment startup

- **NFR-040**: From a clean checkout using the documented default configuration, `docker compose up` shall start the core web/API, single-household application, and database stack and reach documented health results without any optional provider. Core application, database, bootstrap/health, and locally available capability checks shall be `healthy`; capabilities that require an absent optional provider shall be individually `degraded`, `unavailable`, or `intentionally disabled` without making the core stack unhealthy. Memory, knowledge, observability, and development services shall remain opt-in Compose profiles and shall not be started or required by the default command. Milestone A evidence shall include the clean-checkout revision, unmodified command and configuration, container/process exit and restart status, health-probe output, default service/profile inventory, optional-provider absence, and successful core smoke checks.

## 16. Delivery milestones and exit gates

**Common exit rule for Milestones A–D:** A milestone may exit only when every Section 17.4 row carrying that milestone has passed **every** verification method listed in that row and the resulting evidence has been reviewed and accepted from the row's named evidence owner. A comma-separated verification cell is conjunctive, not a menu. The slice, pilot, catalog, salvage, clean-checkout, frozen gate-blocking-defect rule, and other milestone-specific conditions below are additional gates and never replace this row-level rule.

### Milestone A: Foundation baseline (evidence-gated)

**Content:** Repository reset, domain and persistence baseline with the new `001_initial_single_household` migration and no legacy chain, bootstrap API, optional integration resilience, neutral memory/knowledge contracts, provider adapters, the mock-backed frontend-foundation gate defined in Section 4.1.1, default Docker startup, CI, and the requirement-backed reproducible clean-checkout validation.

**Exit gate:** The foundation is accepted only on inspectable, current Kinward evidence; status reports are evidence inputs and carry no product authority. For every subsystem retained from the legacy repository — including optional provider adapters and retained infrastructure — the salvage-matrix acceptance rule must be satisfied and evidenced: (1) current behavior documented, (2) SaaS and multi-tenant assumptions identified and removed, (3) a Kinward contract defined, (4) tests selected or rewritten around retained behavior, (5) the smallest useful implementation migrated, and (6) the subsystem passes its own unit and integration checks. In addition, the Section 4.1.1 frontend-foundation gate passes across all five surface contexts; schema inspection proves a direct new `001_initial_single_household` baseline with no legacy-chain execution or dependency; the NFR-040 evidence pack proves the unmodified documented default `docker compose up` command reaches the defined core healthy and optional-capability degraded states from a clean checkout with memory, knowledge, observability, and development profiles absent; and all tests pass from that clean checkout.

### Milestone B: First live cross-surface assistant slice

**Content:** Authentication, text assistant endpoint, request lifecycle, topic persistence, permission-bound context assembly, live mobile view, live desktop continuation, live household-safe shared-display representation, backend privacy tests, explanation surface, and activity evidence for the demonstrated flow.

**Exit gate:** Every condition in Section 4.1.2 passes in an automated or inspectable demonstration using non-private synthetic fixtures, including both the shared-topic and unshared-private-topic cases; the Milestone B subset of NFR-010 passes only against B-available setup, authentication, assistant-request, topic, and continuation capabilities; and the Section 4.1.1 frontend-foundation gate remains passing.

### Milestone C: First usable household release

**Content:** Invited second adult with the FR-012 personality/interaction interview and FR-008 correction/binding-suspicion closure; optional pet profiles; exactly one primary personal assistant per account-bearing person with separate memory and owner-controlled lifecycle, assistant-scoped grant/reference revocation, and person-owned credential preservation; the full FR-007 account-state lifecycle, separate FR-083 deletion-pending lifecycle, and explicit role/policy transitions with last-admin, restrictive-incomplete-state, invalidation, abandonment/restart, backup/restore, and tombstone verification; the authenticated minor UJ-7 acceptance flow, requester-independent minor policy in FR-087, and deterministic general/minor approval quorums in FR-094/FR-100; durable-fact and pending-observation management; calendar change detection, purpose-specific calendar/transportation recipients, and the UJ-6 child calendar and Home Assistant branches with exact approval, mandatory complete classified activity, truthful observed/requested/submitted/confirmed/unknown state, and reconciliation; the Milestone C proactive subset (ambient and briefing delivery for calendar-change exceptions with evaluation, suppression, deduplication, explanation, category-level correction, and metric instrumentation per FR-045); Home Assistant state and an approved action under the FR-095 household-resource policy; deterministic identity policy including neutral candidate transitions and the FR-099 private-device handoff lifecycle; external-action policy; basic Kinward Control; the Milestone C administration/backup subset of NFR-010; UJ-11/FR-098 versioned controlled import of every minimum positive class with privacy, duplicate, quarantine, credential/disallowed-state rejection, reporting, and whole-import atomic-rollback evidence; versioned protected backup manifest; clean point-in-time restore verification including warning, personal quarantine, the FR-097 direct-household-content ownership/quarantine/conflict lifecycle, absent/deleted-owner denial, post-restore account access, pending observations, share/derived non-reactivation, and unresolved-action blocking state (Section 14); the 14-day parent-follow-up baseline and 10% pilot reduction; the frozen NFR-039 evidence catalog, open-defect list, and pack; and performance/accessibility/security gates.

**Exit gate:** Every mandatory capability in Section 4.2 exists, all Section 6.1 through 6.4 conditions pass the evidence contract in Section 6, the frozen Section 6.6/NFR-039 catalog has no missing case or evidence field, the signed pack lists every open known defect, and no gate-blocking defect under the frozen automatic rule in Section 6.6 remains open. QA applies every automatic predicate; product-owner adjudication of a nonautomatic case cannot override or relabel an automatic case.

### Milestone D: Coordinating household assistant

**Content:** Only the Section 17.4-traced D behavior: the complete named-protagonist UJ-10 and FR-096 E2E closure; generated temporary-view dispositions (FR-042); versioned review opportunities, level selection, explanation/correction, nudge, interruption, and bounded autonomous-action behavior (FR-045–FR-047 and FR-049); minimum-necessary coordination delivery and the deterministic `accepted`, `declined`, `countered`, `expired`, `revoked`, and `delivery-failed` terminal set (FR-050–FR-051); applicable authority, activity, filtering, rollback, unknown-result, and irreversibility evidence (FR-052–FR-054, NFR-009, NFR-012, NFR-015, and NFR-028); the specialist ownership/delegation prerequisite boundary and owner inspection without committing specialist enablement (FR-089 and NFR-004); and the Milestone D frozen evidence catalog and pack in NFR-039. Enabled proactive categories are exactly those recorded in the resolved PD-04 disposition; UJ-10 creates or invokes no specialist, and no additional capability or category is enabled by implication.

**Exit gate:** Each listed D requirement passes its Section 17.4 verification, applicable Section 6.5 evidence, the frozen Section 6.6/NFR-039 catalog, explicit household controls, privacy tests, and rollback or correction behavior. No non-committed horizon is part of this gate.

### Non-committed planning horizons (no delivery gate)

Email, progressive onboarding, specialist enablement, richer topics/cards, layout editing, voice, personal push-to-talk/camera/screenshot/file/current-screen/multimodal input, typed context-targeted commands, emergency mode, any emergency/legal exception to private-teen disclosure, maintenance recall, live personal-tablet workspaces, and native-platform evaluation remain the Section 4.3 planning horizons. They have no milestone assignment, delivery commitment, exit gate, epic, or story authority; text-only input is the safe interim. A teen-disclosure exception additionally requires its own policy, decisions, notice, audit, and tests. Each requires the future PRD amendment and complete readiness package defined in Section 4.3 before decomposition.

## 17. Requirement traceability

### 17.1 ID governance

Issued FR, NFR, UJ, AD, PD, and INV identifiers are never renumbered or reused. A removed requirement is marked deprecated in place and links to any superseding identifier. Material changes to a requirement's meaning are recorded in the document history.

### 17.2 Governing invariants

- **INV-1:** Exactly one household per deployment; no tenancy, SaaS control-plane behavior as defined in Section 3.10, billing, or support-operator behavior.
- **INV-2:** Content is private by default and authorization is enforced by backend services.
- **INV-3:** No cross-person private disclosure, including shared surfaces and the household fallback assistant.
- **INV-4:** External actions are explicit, bounded, approved, and recorded.
- **INV-5:** No fabricated facts, state, or completion claims; uncertainty stays visible.
- **INV-6:** Home Assistant remains the physical-state authority.
- **INV-7:** Optional providers degrade safely and never block core use.
- **INV-8:** The household is recoverable from its own backups, including account access.
- **INV-9:** Ordinary household use requires household language only, with no infrastructure knowledge.
- **INV-10:** Public repository content is fictional, synthetic, and secret-free.
- **INV-11:** UI surfaces render only registered cards from validated declarative layouts.

A `—` in the Invariant column means the requirement is a quality threshold (performance, accessibility) rather than an invariant guard; it still carries a milestone and verification gate.

### 17.3 Verification methods and evidence owners

Verification methods: `unit`, `integration`, `contract` (schema/interface conformance), `privacy-test` (automated privacy and authorization suite), `e2e`, `restore-test`, `perf-test`, `a11y-audit`, `security-review`, `inspection` (documented manual review). Evidence owners: `BE` backend engineering, `FE` frontend engineering, `QA` test engineering, `PO` product owner, `OPS` operations/administrator.

### 17.4 Per-requirement traceability

Sources: `Brief` = product brief, `UX` = UX design specification, `Plan` = rebuild plan, `Salvage` = salvage matrix. A journey of `—` marks an operational or architectural requirement with no single user journey; the milestone and verification gate still apply.

| ID | Source | Journey | Milestone | Invariant | Verification | Owner |
|---|---|---|---|---|---|---|
| FR-001 | Brief §Deployment model; Plan §Executive Decision | UJ-1 | A | INV-1 | integration | BE |
| FR-002 | Brief §Initial Onboarding | UJ-1 | A | INV-8 | integration | BE |
| FR-003 | Brief §Initial Onboarding | UJ-1 | C | INV-2 | integration | BE |
| FR-004 | Brief §Initial Onboarding | UJ-1 | C | INV-9 | e2e | FE |
| FR-005 | Brief §Invited member | UJ-2 | C | INV-2 | integration | BE |
| FR-006 | Brief §Invited member | UJ-2 | C | INV-2 | unit, integration | BE |
| FR-007 | Brief §Target Users | UJ-1, UJ-2, UJ-7 | C | INV-2 | contract, integration, privacy-test | BE |
| FR-008 | Brief §Target Users | UJ-2 | C | INV-2, INV-9 | integration, e2e, privacy-test | QA |
| FR-009 | Brief §Assistant Model | UJ-2, UJ-7 | B, C | INV-2 | integration | BE |
| FR-010 | Brief §Assistant Model; Salvage (personal-assistant boundary) | UJ-2 | B | INV-3 | contract, unit | BE |
| FR-011 | Brief §Assistant Model | UJ-1, UJ-5 | A, C | INV-3 | integration, privacy-test | BE |
| FR-012 | Brief §Assistant Model | UJ-1, UJ-2 | C | INV-2 | integration, e2e | BE |
| FR-013 | Brief §Core Experiences | UJ-3, UJ-7 | B, C | INV-5 | integration, e2e | BE |
| FR-014 | Brief §Core Experiences | UJ-3 | B | INV-2 | integration | BE |
| FR-015 | Brief §Experience by Surface | UJ-3 | B | INV-2 | e2e | QA |
| FR-016 | Brief §Core Experiences | UJ-3 | C | INV-2 | e2e | FE |
| FR-017 | Brief §Proactivity and Trust | UJ-6 | B | INV-4 | integration | BE |
| FR-018 | Brief §Identity and Privacy; Salvage (memory) | UJ-2 | B | INV-3 | privacy-test | BE |
| FR-019 | Brief §Identity and Privacy | UJ-3 | C | INV-3 | integration | BE |
| FR-020 | Brief §Assistant Model | UJ-5 | C | INV-3 | privacy-test | BE |
| FR-021 | Brief §Identity and Privacy | UJ-5 | B | INV-3 | privacy-test | BE |
| FR-022 | Brief §Progressive Context Building | UJ-4 | C | INV-5 | unit | BE |
| FR-023 | Brief §Progressive Context Building | UJ-4 | C | INV-5 | integration | BE |
| FR-024 | Brief §Progressive Context Building | UJ-4 | C | INV-2 | e2e | FE |
| FR-025 | Brief §Progressive Context Building | — | C | INV-5 | unit | BE |
| FR-026 | Brief §Identity and Privacy | UJ-5 | C | INV-3 | integration, privacy-test | BE |
| FR-027 | Brief §Product Boundaries | UJ-8 | B | INV-7 | integration | BE |
| FR-028 | Brief §Identity and Privacy | UJ-2, UJ-7 | B, C | INV-2 | security-review, privacy-test | BE |
| FR-029 | Brief §Identity and Privacy | UJ-5 | C | INV-3 | privacy-test | BE |
| FR-030 | Plan §Architecture Direction | UJ-5 | B | INV-2 | privacy-test | BE |
| FR-031 | Brief §Household administrator | — | C | INV-3 | privacy-test | BE |
| FR-032 | Brief §Teen household member, §Child household member | UJ-7 | C | INV-3 | privacy-test | QA |
| FR-033 | Brief §Identity and Privacy | UJ-5 | B | INV-2 | privacy-test | BE |
| FR-034 | Brief §Identity and Privacy | — | C | INV-2 | unit | BE |
| FR-035 | UX §Initial Cross-Surface Vertical Slice | UJ-3 | A, B | INV-3 | integration, inspection | FE |
| FR-036 | UX §Surface Context | UJ-3 | A | INV-3 | contract | FE |
| FR-037 | UX §Personal Mobile | UJ-3 | B | INV-9 | e2e | FE |
| FR-038 | UX §Now, §Quiet briefing | UJ-4 | C | INV-9 | e2e | FE |
| FR-039 | UX §Shared Household Display | UJ-5 | B | INV-3 | privacy-test | FE |
| FR-040 | UX §Card Registry, §Layout Registry | UJ-3 | A | INV-11 | unit | FE |
| FR-041 | UX §Layout Registry | — | A | INV-11 | unit | FE |
| FR-042 | UX §Generated Views | UJ-10 | D | INV-11 | unit | FE |
| FR-043 | UX §Explain-on-Hold | UJ-3 | B | INV-5 | e2e | FE |
| FR-044 | UX §Shared Household Display (Privacy) | UJ-5 | B | INV-3 | privacy-test | BE |
| FR-045 | Brief §Proactivity and Trust | UJ-4, UJ-10 | C, D | INV-4 | integration | BE |
| FR-046 | Brief §Proactivity and Trust | UJ-4, UJ-10 | C, D | INV-4 | unit | BE |
| FR-047 | Brief §Proactivity and Trust | UJ-10 | D | INV-4 | integration | BE |
| FR-048 | Brief §Product Thesis | UJ-4 | C | INV-9 | integration | BE |
| FR-049 | Brief §Proactivity and Trust | UJ-4, UJ-10 | C, D | INV-5 | e2e | FE |
| FR-050 | UX §Coordination Request | UJ-10 | D | INV-3 | privacy-test | BE |
| FR-051 | UX §Coordination Request | UJ-10 | D | INV-4 | integration | BE |
| FR-052 | Brief §Proactivity and Trust | UJ-6, UJ-7, UJ-10 | C, D | INV-4 | integration, privacy-test | BE |
| FR-053 | Brief §Proactivity and Trust; Salvage (activity ledger) | UJ-6, UJ-7, UJ-10 | C, D | INV-4 | contract, privacy-test | BE |
| FR-054 | UX §Kinward Control | UJ-6, UJ-7, UJ-10 | C, D | INV-2 | e2e, privacy-test | FE |
| FR-055 | Salvage (calendar integration) | UJ-4 | C | INV-2 | integration | BE |
| FR-056 | Brief §Core Experiences | UJ-4 | C | INV-2 | integration | BE |
| FR-057 | Brief §Core Experiences | UJ-4 | C | INV-5 | unit | BE |
| FR-058 | Brief §Core Experiences; Plan §Contract reset | UJ-4 | C | INV-5 | unit | BE |
| FR-059 | Brief §Identity and Privacy | UJ-5 | C | INV-3 | privacy-test | BE |
| FR-060 | Brief §Proactivity and Trust | UJ-6 | C | INV-4 | integration | BE |
| FR-061 | Brief §Product Boundaries | UJ-4, UJ-8 | C | INV-7 | integration | BE |
| FR-062 | Brief §Product Boundaries; Salvage (Home Assistant) | — | C | INV-6 | contract | BE |
| FR-063 | Brief §Core promise | UJ-6 | C | INV-9 | e2e | FE |
| FR-064 | Brief §Proactivity and Trust | UJ-6 | C | INV-5 | unit | BE |
| FR-065 | Brief §Proactivity and Trust | UJ-6, UJ-8 | C | INV-5 | integration | BE |
| FR-066 | Brief §Proactivity and Trust | UJ-6 | C | INV-4 | integration | BE |
| FR-067 | Brief §Product Boundaries | UJ-8 | C | INV-7 | integration | BE |
| FR-068 | UX §Kinward Control | UJ-1 | C | INV-9 | e2e | FE |
| FR-069 | UX §Kinward Control | UJ-1 | C | INV-2 | e2e | FE |
| FR-070 | UX §Kinward Control | UJ-2 | C | INV-2 | e2e | FE |
| FR-071 | UX §Kinward Control | UJ-1 | C | INV-3 | privacy-test | BE |
| FR-072 | Plan §Architecture Direction | UJ-8 | C | INV-7 | integration | BE |
| FR-073 | Brief §Product Boundaries | UJ-8 | C | INV-7 | e2e | FE |
| FR-074 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | unit | BE |
| FR-075 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| FR-076 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| FR-077 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test, privacy-test | QA |
| FR-078 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| FR-079 | Plan §Architecture Direction, §Database reset; Salvage (legacy migration chain) | — | A | INV-8 | contract, integration | BE |
| FR-080 | Plan §Infrastructure simplification | — | C | INV-8 | integration | OPS |
| FR-081 | Brief §Deployment model | — | C | INV-2 | unit | BE |
| FR-082 | Brief §Deployment model | — | C | INV-8 | inspection | PO |
| FR-083 | Brief §Identity and Privacy | — | C | INV-2 | integration, privacy-test | BE |
| FR-084 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| FR-085 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| FR-086 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-8 | restore-test, privacy-test | QA |
| FR-087 | Brief §Target Users, §Proactivity and Trust; UX §Content Design | UJ-6, UJ-7 | C | INV-3, INV-4 | integration, privacy-test | QA |
| FR-088 | Brief §Identity and Privacy; UX §Content Design | UJ-7 | C | INV-3 | privacy-test | QA |
| FR-089 | Brief §Assistant Model; UX §UX Acceptance Criteria | UJ-3 | D | INV-3 | contract, privacy-test | BE |
| FR-090 | Brief §Progressive Context Building | UJ-4 | C | INV-5 | integration | BE |
| FR-091 | Brief §Target Users, §Initial Onboarding | UJ-1 | C | INV-2 | e2e | FE |
| FR-092 | Brief §Core Experiences, §Progressive Context Building | UJ-4 | C | INV-3 | integration, privacy-test | QA |
| FR-093 | Brief §Assistant Model, §Identity and Privacy | UJ-2 | C | INV-3 | privacy-test | BE |
| FR-094 | Brief §Target Users, §Core Experiences; UX §Content Design | UJ-7 | C | INV-3 | e2e, privacy-test | QA |
| FR-095 | Brief §Product Boundaries; Salvage (Home Assistant) | UJ-6 | C | INV-4, INV-6 | contract, integration, privacy-test | QA |
| FR-096 | Brief §Proactivity and Trust; UX §Generated Views, §Coordination Request | UJ-10 | D | INV-4, INV-5, INV-11 | e2e, privacy-test | QA |
| FR-097 | Brief §Deployment model; Plan §Database reset | UJ-9 | C | INV-2, INV-8 | restore-test, privacy-test | QA |
| FR-098 | Plan §Database reset | UJ-11 | C | INV-2, INV-8 | contract, e2e, privacy-test | QA |
| FR-099 | UX §Shared Household Display (Privacy), §Content Design | UJ-5 | C | INV-3 | e2e, privacy-test | QA |
| FR-100 | Brief §Proactivity and Trust; Salvage (Home Assistant) | UJ-6 | C | INV-4 | contract, integration, privacy-test | QA |
| NFR-001 | Brief §Identity and Privacy | UJ-5 | B | INV-2 | privacy-test | BE |
| NFR-002 | Plan §Infrastructure simplification | — | C | INV-2 | security-review | BE |
| NFR-003 | UX §Shared Household Display (Privacy) | UJ-5 | C | INV-3 | privacy-test | QA |
| NFR-004 | Brief §Target Users | UJ-7 | C, D | INV-3 | privacy-test | QA |
| NFR-005 | Brief §Proactivity and Trust | — | B | INV-4 | security-review | BE |
| NFR-006 | Brief §Identity and Privacy | — | B | INV-3 | integration | BE |
| NFR-007 | Brief §Identity and Privacy | UJ-2, UJ-5 | C | INV-2 | security-review | BE |
| NFR-008 | Brief §Identity and Privacy | — | B | INV-3 | inspection | BE |
| NFR-009 | Brief §Proactivity and Trust | UJ-6, UJ-10 | C, D | INV-4 | security-review | BE |
| NFR-010 | Brief §Product Boundaries | UJ-8 | B, C | INV-7 | integration | BE |
| NFR-011 | Plan §Architecture Direction | — | B | INV-7 | unit | BE |
| NFR-012 | Brief §Proactivity and Trust | UJ-6, UJ-10 | C, D | INV-4 | integration | BE |
| NFR-013 | Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| NFR-014 | Plan §Database reset | UJ-9 | C | INV-8 | restore-test | QA |
| NFR-015 | Brief §Proactivity and Trust; Brief §Deployment model | UJ-6, UJ-9, UJ-10 | C, D | INV-5 | integration, restore-test | BE |
| NFR-016 | Plan §Architecture Direction | — | C | INV-7 | integration | BE |
| NFR-017 | UX §Experience principles | — | C | — | perf-test | QA |
| NFR-018 | UX §Experience principles | UJ-3 | B | — | perf-test | QA |
| NFR-019 | UX §Experience principles | UJ-3 | B | — | perf-test | QA |
| NFR-020 | UX §Shared Household Display (Privacy) | UJ-5 | C | INV-3 | perf-test, privacy-test | QA |
| NFR-021 | UX §Experience principles | — | C | — | perf-test | QA |
| NFR-022 | UX §Shared Household Display (Privacy) | UJ-5 | C | INV-3 | perf-test | QA |
| NFR-023 | UX §Accessibility | — | C | — | a11y-audit | FE |
| NFR-024 | UX §Room profiles, §Accessibility | UJ-5 | C | — | a11y-audit | FE |
| NFR-025 | UX §Accessibility | UJ-1 | C | — | a11y-audit | QA |
| NFR-026 | UX §Accessibility | — | C | — | a11y-audit | FE |
| NFR-027 | Brief §Core promise; UX §Content Design | — | C | INV-9 | inspection | PO |
| NFR-028 | Brief §Proactivity and Trust; UX §Content Design | UJ-6, UJ-10 | C, D | INV-4 | e2e | FE |
| NFR-029 | Brief §Strategic Decisions; Plan §Architecture Direction | — | B | INV-7 | contract | BE |
| NFR-030 | Plan §Contract reset | — | C | INV-8 | contract | BE |
| NFR-031 | Plan §BMAD and Ringer | — | A | INV-5 | inspection | PO |
| NFR-032 | Plan §Repository Strategy | — | A | INV-10 | inspection | PO |
| NFR-033 | Plan §Documentation cleanup | — | A | INV-10 | inspection | PO |
| NFR-034 | Plan §Architecture Direction | UJ-8 | C | INV-7 | integration | BE |
| NFR-035 | Plan §Architecture Direction | — | C | INV-5 | integration | BE |
| NFR-036 | Plan §Architecture Direction | — | C | INV-3 | inspection | BE |
| NFR-037 | Brief §Household administrator | UJ-8 | C | INV-3 | integration | BE |
| NFR-038 | Brief §Deployment model, §Identity and Privacy | UJ-9 | C | INV-2 | security-review, restore-test | QA |
| NFR-039 | Plan §BMAD and Ringer; UX §UX Acceptance Criteria | UJ-1–UJ-11 | C, D | INV-5 | inspection | QA |
| NFR-040 | Plan §Infrastructure simplification | — | A | INV-7 | integration | OPS |

### 17.5 Journey coverage summary (derived from Section 17.4)

This summary is derived from the per-requirement table above; the table is authoritative when they differ.

- **UJ-1:** FR-001–FR-004, FR-007, FR-011–FR-012, FR-068–FR-069, FR-071, FR-091, NFR-025, NFR-039.
- **UJ-2:** FR-005–FR-010, FR-012, FR-018, FR-028, FR-070, FR-093, NFR-007, NFR-039.
- **UJ-3:** FR-013–FR-016, FR-019, FR-035–FR-037, FR-040, FR-043, FR-089, NFR-018–NFR-019, NFR-039.
- **UJ-4:** FR-022–FR-024, FR-038, FR-045–FR-046, FR-048–FR-049, FR-055–FR-058, FR-061, FR-090, FR-092, NFR-039.
- **UJ-5:** FR-011, FR-020–FR-021, FR-026, FR-029–FR-030, FR-033, FR-039, FR-044, FR-059, FR-099, NFR-001, NFR-003, NFR-007, NFR-020, NFR-022, NFR-024, NFR-039.
- **UJ-6:** FR-017, FR-052–FR-054, FR-060, FR-063–FR-066, FR-087, FR-095, FR-100, NFR-009, NFR-012, NFR-015, NFR-028, NFR-039.
- **UJ-7:** FR-007, FR-009, FR-013, FR-028, FR-032, FR-052–FR-054, FR-087–FR-088, FR-094, NFR-004, NFR-039.
- **UJ-8:** FR-027, FR-061, FR-065, FR-067, FR-072–FR-073, NFR-010, NFR-034, NFR-037, NFR-039.
- **UJ-9:** FR-074–FR-078, FR-084–FR-086, FR-097, NFR-013–NFR-015, NFR-038–NFR-039.
- **UJ-10:** FR-042, FR-045–FR-047, FR-049–FR-054, FR-096, NFR-009, NFR-012, NFR-015, NFR-028, NFR-039.
- **UJ-11:** FR-098, NFR-039.

Epic and story decomposition must preserve the Section 17.4 mapping bidirectionally: every FR and NFR must appear in at least one epic with its milestone and verification method intact, and every journey's listed requirements must close that journey's outcomes. No journey may depend only on an untracked narrative statement.

## 18. Architecture decision register

Each architecture decision carries a stable ID, owner, status, due milestone, affected requirements, and a safe interim behavior that applies until the decision is resolved. A resolved decision records its disposition and links a decision record (ADR). Every safe interim must be implementable for its due milestone; no Milestone B requirement may be explicitly blocked by an open decision. These decisions may select mechanisms but may not weaken the product outcomes, privacy boundaries, action states, or release gates defined in this PRD.

| ID | Decision | Owner | Status | Due | Affected requirements | Safe interim behavior | Disposition / record |
|---|---|---|---|---|---|---|---|
| AD-01 | Default authentication, session, invitation, and account-recovery mechanism | Architect | Open | Milestone A start | FR-002, FR-005–FR-008, FR-028, FR-083, FR-085, FR-093, NFR-007 | Kinward-local single-household identity and profile binding are authoritative; server-side authentication issues expiring, replay-resistant sessions bound to one existing profile and enforces the Section 7.7 non-active-state invalidations. Invitations and recovery use expiring single-use opaque capabilities bound to the intended existing profile, never create a duplicate or transfer private ownership, and use the minimum same-owner recovery outcomes already required by this PRD. Recovery may rotate or replace credentials only for that same intended profile; suspected wrong binding follows Section 7.8 suspension and has no current rebinding or private-state-transfer path. Exact authenticator, credential, token, and recovery transport choices remain architectural | — |
| AD-02 | Initial model-provider contract and streaming/cancellation behavior | Architect | Open | Milestone A start | FR-013, FR-017, NFR-019, NFR-029 | Kinward exposes a provider-neutral ordered incremental-response contract with visible `accepted`/`responding` progress, monotonic content events, one truthful terminal event, cancellation propagation that stops later output, explicit timeout, and visible provider failure. Provider adapters normalize their streaming or bounded incremental output to that contract; exact wire transport, chunk framing, and initial provider remain architectural | — |
| AD-03 | Assistant runtime and tool-execution boundary | Architect | Open | Milestone B start | FR-052, NFR-005 | Milestone B tool execution is backend-authorized, read-only, allowlisted, input/output validated, and isolated so external content cannot change system policy or authority; external-mutation tool capabilities remain unavailable until their Milestone C FR-052 boundary is selected and verified. Exact runtime isolation and later mutation boundary remain architectural | — |
| AD-04 | Topic and conversation persistence model | Architect | Open | Milestone B start | FR-014–FR-016 | Kinward-local persistence is authoritative for topics and conversations under backend authorization and records person, assistant, topic, surface provenance, current class, version, and lifecycle state sufficient for FR-014–FR-016 and every Milestone B continuation/privacy test. Exact tables/documents, indexing, event shape, and optional provider-storage boundaries remain architectural | — |
| AD-05 | Context assembly and authorization enforcement points | Architect | Open | Milestone B start | FR-021, FR-030, NFR-001 | Backend-only enforcement assumed; no client-trusted filtering | — |
| AD-06 | Physical storage split among Kinward, Honcho, and LLM-Wiki | Architect | Open | Milestone A start | FR-018–FR-020, NFR-010, NFR-029 | Kinward-local storage is authoritative; providers remain optional peers | — |
| AD-07 | Deletion request and verification mechanism for externally stored derived data | Architect | Open | Milestone C start | FR-026, Section 8.2 | Enforce internal dependency deletion; immediately block provider queries and local retrieval, mark external references deletion-pending or externally retained, submit an exposed provider deletion operation, and disclose the provider limitation | — |
| AD-08 | Calendar synchronization transport and freshness model | Architect | Open | Milestone C start | FR-057–FR-058, FR-060 | Calendar data is treated as stale unless observed in the current sync; stale state blocks mutation | — |
| AD-09 | Home Assistant freshness and availability model (observed timestamps or version markers, stale presentation, reconnection refresh, per-action current-state rules) | Architect | Open | Milestone C start | FR-064–FR-067 | Cached state is stale and blocks actions that need current state; after every submitted mutation, absent confirmed matching resulting state is `unknown`, never `completed`, and is not retried before reconciliation | — |
| AD-10 | Accepted mechanisms for `verified` shared-surface identity and downgrade signaling | Architect | Open | Milestone C start | FR-029, Section 10, NFR-020 | Shared surfaces remain household-safe with no `verified` state until resolved; backend invalidation and client fail-closed outcomes remain mandatory regardless of mechanism | — |
| AD-11 | Background-job and action-reconciliation design | Architect | Open | Milestone C start | FR-052–FR-053, FR-060, FR-074, FR-077, FR-083, FR-086–FR-087, FR-093–FR-094, FR-100, NFR-012, NFR-015–NFR-016 | Unknown provider results survive restart, backup, restore, person or assistant deletion-pending state; preserve the Section 14 minimum state, block retry and same-target mutation, require visible reconciliation, deterministically expire/cancel unsubmitted work, and perform no background mutation until resolved; pending multi-principal responses remain version-bound and cannot enter `acting` without the atomic Section 11 revalidation | — |
| AD-12 | Credential storage, backup encryption, and portability | Architect | Open | Milestone C start | FR-074–FR-078, FR-084–FR-086, NFR-002, NFR-013–NFR-014, NFR-038 | Every integration credential is excluded from backups and requires reauthorization; portable account-recovery material remains separately governed by Section 14.3 and AD-01; any archive containing private or portable recovery data is confidentiality- and integrity-protected or export/restore is unavailable, with the point-in-time warning, quarantine, reauthorization, and NFR-038 notices mandatory regardless of mechanism | — |
| AD-13 | Activity append-protection, integrity, and storage strategy | Architect | Open | Milestone C start | FR-053–FR-054, FR-081–FR-083, FR-094, NFR-009, NFR-039 | Retain complete append-protected action and audit records with the Section 11.1 audience boundaries, plus sanitized deletion or deletion-pending records, with zero missing eligible events and no pruning; the signed catalog version/hash remains required, and PD-05 separately owns retention periods | — |
| AD-14 | Diagnostic data redaction | Architect | Open | Milestone C start | NFR-037 | Export only the NFR-037 allowlisted system-operational fields; omit all other fields until the redaction decision is resolved | — |
| AD-15 | Reference deployment and load used for performance and shared-display accessibility testing | Architect | Open | Milestone B start | NFR-017–NFR-024, NFR-039 | Performance and NFR-024 accessibility gates cannot be marked passed until the exact reference environment and shared display within the NFR-024 class are documented in the frozen evidence catalog | — |
| AD-16 | Private-device discovery, delivery, destination authentication, and redemption mechanism | Architect | Open | Milestone C start | FR-099, NFR-007 | Use a backend-issued opaque single-use expiring reference bound to the intended person, origin, and purpose; consider only an already registered destination for that intended person reachable; send only the Section 10.1 pre-authentication allowlist; and perform the complete atomic backend redemption re-evaluation before retrieval. Exact discovery signal, transport, destination authenticator, and delivery protocol remain architectural | — |

## 19. Product decision register

Each product decision carries the same closure metadata as Section 18. Affected stories are implementation-ready only when the decision is resolved or the stated interim behavior fully covers them.

| ID | Decision | Owner | Status | Due | Affected requirements | Safe interim behavior | Disposition / record |
|---|---|---|---|---|---|---|---|
| PD-01 | Default inactivity timeout for shared-display personal sessions within the Section 10 maximum | Product owner | Open | Milestone C start | FR-029, Section 10 | The 10-minute maximum applies as the default | — |
| PD-02 | Which child durable-fact categories are guardian-visible by default versus opt-in | Product owner | Open | Milestone C start | FR-032, Section 7.4 | The product states that no category is guardian-visible by default; administrators may see only `household-shared` child facts and `selected-share` facts explicitly naming them, with no broader guardian-review implementation | — |
| PD-03 | Whether the first calendar integration supports one provider or a vendor-neutral local calendar source first | Product owner | Open | Milestone C start | FR-055–FR-061 | Calendar work stays provider-neutral per NFR-029; no provider-specific coupling | — |
| PD-04 | Initial proactive categories enabled by default during the Milestone C and D household pilots | Product owner | Open | Milestone C start | FR-045–FR-049, Section 6.5 | Calendar-change is the only enabled Milestone C category; no additional Milestone D category or measurement window may begin until the disposition names it | — |
| PD-05 | Default retention periods for private conversations, archived topics, activity, and approvals | Product owner | Open | Milestone C start | FR-082, FR-090 | No automatic deletion applies only to FR-082's named durable classes: persisted conversation/topic bodies, confirmed durable facts, active sharing/authority policies, durable approvals/activity, durable integration configuration/provider mappings, and unexpired pending observations until FR-090 expiry. It never preserves surface-ephemeral data, authorization/dependency-invalid rendered/cache/provider-context copies, expired or revoked security artifacts, or data subject to mandatory privacy/security deletion; user-requested underlying-content deletion and AD-13 sanitized records remain honored | — |
| PD-06 | Whether backup archives include encrypted integration credential material by default or require reauthorization for every integration | Product owner | Open | Milestone C start | FR-074, FR-078, FR-084 | Exclude every integration credential; every integration requires reauthorization after restore; portable account-recovery material is separate | — |
| PD-07 | Which forms of explanation and correction are required on the first shared display versus private handoff | Product owner | Open | Milestone C start | FR-043, FR-049 | The shared display shows only the item's information class and household-safe reason and offers private handoff; the authorized private surface supplies full explanation and correction | — |

Unresolved decisions must be carried into epics as explicit assumptions restating the implementable safe interim behavior, with the decision ID attached. Only behavior beyond that interim may be blocked pending resolution; no Milestone B requirement is blocked by an open decision in this register. Decisions must not be silently made inside implementation stories.

## 20. PRD readiness criteria

This PRD may be marked final only when:

- repository safety review confirms no private household names, addresses, credentials, infrastructure identifiers, or private fixtures,
- every source path resolves,
- user journeys and requirement coverage are accepted,
- deterministic privacy, data-classification, assistant-boundary, and action policies are accepted,
- the frontend-foundation gate, first live cross-surface slice, and first usable release boundaries are accepted,
- success thresholds and counter-metrics are accepted as milestone-scoped targets,
- every entry in the Section 18 and Section 19 decision registers is resolved with a recorded disposition, or explicitly accepted as open with its owner, due milestone, and safe interim behavior,
- the Section 17.4 per-requirement traceability table is complete and accepted, with every FR and NFR carrying a source, milestone, invariant or quality gate, verification method, and evidence owner,
- architecture can map every Milestone B and C requirement to a concrete boundary,
- epics map every functional and nonfunctional requirement without creating competing scope,
- stories for Milestone B include acceptance tests for privacy, failure, degraded mode, and observability,
- and implementation-readiness review finds no unresolved blocker for Milestone B.

## 21. Document history

| Date | Status | Change |
|---|---|---|
| 2026-07-14 | draft | Resolved the sixth polishing gate; added contiguous UJ-11 and FR-100 with one new trace row; narrowed FR-008 corrections and prohibited cross-profile rebinding; placed personal multimodal/context input beyond committed scope; removed incidental tool choices from Milestone A; completed deletion-pending, requester-independent minor, general multi-principal approval, review-opportunity, controlled-import, Home Assistant journey, evidence, milestone, and traceability contracts while preserving prior safeguards. |
| 2026-07-14 | draft | Resolved the fifth polishing gate; added contiguous FR-097–FR-099, NFR-040, and AD-16; removed the teen emergency/legal exception from committed scope and canonicalized sender withdrawal as coordination revocation; fixed candidate and handoff payloads; defined account-state and direct-household-content lifecycles, baseline migration and controlled import, Docker startup evidence, parent-follow-up reduction, frozen gate-blocking defects, and implementable AD-01/AD-02/AD-04 interims; and reconciled milestones, evidence, journeys, sources, and traceability. |
| 2026-07-14 | draft | Resolved the fourth polishing gate; added contiguous FR-095–FR-096 and UJ-10, canonicalized pilot event units, milestone-wide row closure, household-resource and minor-quorum authority, primary-assistant cardinality and credential ownership, candidate payloads, durable-retention limits, direct-household-content restore quarantine, milestone-scoped provider-failure evidence, and reconciled D traceability without enabling specialist assistants. |
| 2026-07-14 | draft | Resolved the third polishing gate; added contiguous FR-094 and NFR-039, defined point-in-time restore quarantine, deletion and cross-person authority dispositions, classified activity views, frozen acceptance evidence, Milestone D adjudication, onboarding and minor-flow closure, derived freshness, role-transition verification, and reconciled traceability without changing the product boundary. |
| 2026-07-14 | draft | Resolved the second polishing gate; added contiguous FR-090–FR-093 and NFR-038, strengthened affected existing requirements and decision interims, reconciled journeys, milestones, evidence, and traceability, and preserved all prior stable IDs. |
