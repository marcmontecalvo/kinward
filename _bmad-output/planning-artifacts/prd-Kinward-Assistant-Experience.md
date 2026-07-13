---
status: draft
createdAt: "2026-07-13"
updatedAt: "2026-07-13"
documentType: "BMAD Product Requirements Document"
sourceDocuments:
  - "product-brief-Kinward-Assistant-Experience.md"
  - "ux-design-specification-Kinward-Assistant-Experience.md"
  - "docs/pivot/single-household-pivot-and-rebuild-plan.md"
  - "docs/pivot/migration-status.md"
---

# Product Requirements Document: Kinward Assistant Experience

**Author:** Marc Montecalvo  
**Date:** 2026-07-13  
**Product:** Kinward  
**Delivery model:** Private, single-household, Docker-deployed web/PWA platform

## 1. Purpose

This PRD defines the product requirements for Kinward as a private household intelligence platform in which each household member has one or more personal AI assistants. It translates the approved product brief and UX specification into stable, testable product requirements for architecture, epic creation, implementation planning, and readiness review.

Kinward is not a multi-tenant SaaS product, a smart-home dashboard with a chatbot attached, a routine builder, or a generic chat interface. Its primary value is the continuing relationship between a person and their assistant: the assistant understands durable context, preserves privacy, coordinates with household systems and other people, and surfaces only what requires attention.

## 2. Product outcomes

Kinward must enable a household to:

1. Give each person a private, continuous assistant relationship.
2. Build useful household understanding from durable facts rather than manually authored routines.
3. Coordinate calendars, email, school, work, transportation, household responsibilities, and smart-home state without combining everyone’s private information into one shared memory.
4. Continue work across personal devices, shared displays, and voice endpoints while applying surface-appropriate privacy.
5. Delegate outcomes to assistants with understandable permissions, approvals, activity records, and undo where possible.
6. Operate locally as a single-household Docker deployment while allowing optional cloud inference and external services.

## 3. Success measures

Initial success is behavioral and household-focused rather than commercial.

### 3.1 Primary measures

- Household members voluntarily use their personal assistants for recurring real needs.
- A household member can complete initial setup without technical assistance or configuring routines, rooms, devices, or integrations.
- Important calendar, school, household, or coordination changes are surfaced before they cause a missed commitment or preventable conflict.
- Shared surfaces do not expose private information in tested low-confidence, multiple-person, or unknown-person scenarios.
- Users can distinguish an assistant proposal, an action awaiting approval, an action in progress, and a completed action.
- Users can inspect why a meaningful item appeared or why an action was allowed without seeing hidden prompts, chain-of-thought, credentials, or secrets.
- Normal use does not require household members to understand cards, layouts, entities, services, automations, YAML, or integrations.

### 3.2 Counter-metrics

Kinward must not improve engagement by increasing noise or dependency. The product should monitor for:

- Excessive notifications, nudges, or interruptions.
- Repeated requests for information Kinward should already know.
- Routine, checklist, or reminder proliferation replacing durable context.
- Private information appearing on shared surfaces.
- Autonomous actions that users routinely reverse or distrust.
- Technical administration required for ordinary household use.

## 4. Users and operating context

### 4.1 Household administrator

Creates the household, manages people and invitations, configures integrations and permissions, reviews system health and activity, and may customize surfaces and layouts.

### 4.2 Adult household member

Uses a private assistant for planning, communication, calendar and email awareness, household coordination, delegation, and ongoing topics.

### 4.3 Teen household member

Uses a respectful private assistant with age-appropriate autonomy, school and activity support, and privacy from parents and shared surfaces except where explicit household policy permits otherwise.

### 4.4 Child household member

Receives a simpler age-appropriate experience governed by stronger permissions and privacy boundaries. A child may exist in the household before receiving an account.

### 4.5 Shared-surface participant

May be a recognized member, an unknown person, or one of several people present. Receives only information allowed for the current identity confidence, privacy state, room policy, and audience.

### 4.6 Pets and guests

Pets may be represented for care, medication, appointments, and household context but do not receive accounts. Guests are excluded from initial onboarding. Any later guest capability must be temporary and limited.

## 5. Product scope

### 5.1 Initial product scope

The initial usable product must include:

- Single-household deployment and bootstrap.
- Accounts, invitations, and current-person identity on personal surfaces.
- Personal assistant creation and personality configuration.
- Text-based assistant conversation with continuity.
- Permission-bound memory and durable context.
- A responsive personal web/PWA experience.
- A privacy-conservative shared-display experience.
- Registry-driven cards and declarative layouts with polished defaults.
- Activity and approval records for meaningful actions.
- At least one live calendar integration and one Home Assistant vertical slice.
- Optional memory and knowledge providers that do not prevent Kinward from starting when unavailable.
- Administrative Kinward Control foundations for people, assistants, integrations, permissions, activity, and health.
- Backup, restore, and upgrade procedures adequate for a household-owned deployment.

### 5.2 Later product scope

The following remain product requirements but are not required for the first usable milestone:

- Email actions and deeper mailbox workflows.
- Voice-only endpoints and cross-surface voice handoff.
- Rich proactive coordination between household members.
- Visual and declarative layout editors.
- Emergency surface takeover.
- Contextual maintenance recall.
- Advanced school, work, personal, home, and transportation onboarding sessions.
- Native Android capabilities such as background wake word, foreground services, widgets, share targets, proximity, biometrics, Android Auto, and system assistant integration.

### 5.3 Explicitly out of scope

- Multi-household tenancy within one deployment.
- SaaS control-plane behavior.
- Billing, subscriptions, package entitlements, marketplace features, or managed deployment regions.
- Support-operator access to household data.
- Mandatory Home Assistant, Honcho, LLM-Wiki, or cloud inference dependencies.
- A routine-centric product model.
- A permanent legacy Homefront frontend or migration chain.
- Arbitrary AI-generated client code.

## 6. Core user journeys

### UJ-1: Administrator creates the household

Marc starts a new Kinward deployment. He creates the initial account, names the household, creates his profile, adds known adults and children, optionally records pets, names his first assistant, completes a short personality and interaction interview, and enters the assistant experience. He is not required to configure rooms, devices, integrations, routines, school details, notification rules, or layouts.

**Successful outcome:** The household, administrator, household members, and first personal assistant exist; Marc reaches a useful default home surface; incomplete optional setup is clearly available later without blocking entry.

### UJ-2: Invited member establishes a private assistant

Lisa accepts an invitation, confirms her profile, creates or signs into her account, names her assistant, completes the short assistant interview, and enters a private personal surface. Her assistant does not inherit Marc’s private memories or account data.

**Successful outcome:** Lisa has a distinct identity, personal assistant, memory boundary, and default experience while still participating in shared household coordination.

### UJ-3: A user asks once and continues elsewhere

Lisa asks Kinward on her phone to help plan a family trip. Later she opens Kinward on a desktop and sees the trip as an active topic with prior context, decisions, relevant calendar information, and assistant progress. She does not restate the request or search through raw chat history.

**Successful outcome:** The topic continues across surfaces with the correct person, assistant, context, and privacy policy.

### UJ-4: Kinward surfaces a meaningful change

A school calendar adds an early-release day. Kinward associates the event with the correct child, compares it with household calendars and transportation context, and places a concise item in the appropriate adults’ briefings. It does not create a routine or send an urgent interruption unless the timing and conflict justify one.

**Successful outcome:** The right people understand what changed, why it matters, and whether action is required.

### UJ-5: Shared surface protects private information

Marc asks a shared kitchen display about a private appointment while other people are present. Kinward recognizes that the request concerns personal information and either answers generically, asks to continue privately, or transfers details to Marc’s personal device.

**Successful outcome:** The request remains useful without disclosing protected details to the room.

### UJ-6: A delegated action requires approval

Lisa asks her assistant to reschedule an appointment. The assistant prepares the proposed change and presents an approval that states what will change, which service will be used, why approval is required, and whether the action can be reversed. After approval, the activity record distinguishes preparation, execution, result, and any failure.

**Successful outcome:** Lisa understands and controls the action without operating the underlying integration directly.

### UJ-7: Administrator inspects and repairs the system

Marc opens Kinward Control to see that Home Assistant is available, the knowledge provider is disabled, and a calendar integration needs reauthorization. He can inspect plain-language health, recent activity, and actionable remediation without exposing secrets.

**Successful outcome:** The household can operate and troubleshoot Kinward without a separate SaaS control plane.

## 7. Functional requirements

### 7.1 Household, people, accounts, and onboarding

- **FR-001:** Kinward shall support exactly one household per deployment.
- **FR-002:** Kinward shall prevent a normal setup flow from creating a second household in an already configured deployment.
- **FR-003:** The initial administrator flow shall create the household, administrator profile, and first personal assistant as one recoverable setup operation.
- **FR-004:** An administrator shall be able to add adults and children before those people have accounts.
- **FR-005:** An administrator shall be able to optionally record pets without creating accounts for them.
- **FR-006:** Initial onboarding shall not require integrations, rooms, devices, routines, detailed school or work context, notification rules, or layout configuration.
- **FR-007:** An administrator shall be able to invite eligible household members by email.
- **FR-008:** An invited member shall be able to accept an invitation, establish an account, confirm the intended household profile, and create a personal assistant.
- **FR-009:** Kinward shall distinguish household role, account state, age-related policy state, and assistant ownership.
- **FR-010:** Kinward shall provide short, optional, targeted onboarding sessions after initial entry for work, school, personal, home, and transportation context.

### 7.2 Assistants and conversation

- **FR-011:** Each account-bearing household member shall be able to have at least one personal assistant.
- **FR-012:** A personal assistant shall have exactly one personal owner.
- **FR-013:** A household member shall be able to name an assistant and configure its personality, interaction preferences, and available voice characteristics.
- **FR-014:** Kinward shall preserve a primary assistant as the default router when a user has multiple assistants.
- **FR-015:** Kinward shall support text conversation from the web/PWA client.
- **FR-016:** Assistant responses shall support incremental delivery and cancellation where the selected model provider permits it.
- **FR-017:** Conversation continuity shall be associated with the current person, assistant, topic, and permissions rather than only a raw chat session.
- **FR-018:** Kinward shall represent ongoing work as topics that may contain conversation, decisions, artifacts, relevant integration data, and assistant actions.
- **FR-019:** A user shall be able to begin an interaction on one authorized personal surface and continue it on another without restating available context.
- **FR-020:** The assistant shall clearly distinguish a proposal, a pending action, an action in progress, a completed action, uncertainty, and failure.

### 7.3 Memory, knowledge, and durable context

- **FR-021:** Personal memory shall be bound to the person and assistant permissions under which it was created.
- **FR-022:** Shared assistants and shared surfaces shall not receive unrestricted access to household members’ private memories.
- **FR-023:** Kinward shall support a neutral memory-provider contract with a disabled provider and optional external providers.
- **FR-024:** Kinward shall support a neutral knowledge-provider contract with a disabled provider and optional external providers.
- **FR-025:** Kinward shall remain operational when optional memory or knowledge providers are disabled or temporarily unavailable.
- **FR-026:** The assistant shall be able to retrieve relevant permitted memories and durable facts when constructing a response or action plan.
- **FR-027:** Kinward shall distinguish user-confirmed durable facts from unconfirmed observations or transient conversation context.
- **FR-028:** The assistant shall request confirmation before promoting an inferred observation into durable context when the information is consequential, sensitive, or likely to affect future behavior.
- **FR-029:** Authorized users shall be able to inspect, correct, and delete durable memories and contextual facts that concern them.
- **FR-030:** Kinward shall preserve provenance sufficient to explain the source category and confidence of a surfaced fact without exposing hidden model reasoning or secrets.

### 7.4 Identity, privacy, and permissions

- **FR-031:** Personal surfaces shall resolve the signed-in person before exposing private assistant content.
- **FR-032:** Shared surfaces shall evaluate identity confidence, surface privacy, room policy, known audience, and user preference before showing personal information.
- **FR-033:** When identity confidence is insufficient, Kinward shall use a household-safe response, ask for identity, or offer private-device handoff.
- **FR-034:** When multiple people are present, Kinward shall not expose private information unless the applicable policy explicitly permits group disclosure.
- **FR-035:** Kinward shall support age-appropriate permissions and stronger default restrictions for children.
- **FR-036:** Kinward shall enforce assistant ownership and data-access rules in backend services rather than relying only on client visibility.
- **FR-037:** Administrators shall be able to manage household policies without gaining automatic access to another adult’s private assistant memory.
- **FR-038:** The product shall disclose uncertainty when identity, source data, or action eligibility is ambiguous.

### 7.5 Surfaces, cards, layouts, and interaction

- **FR-039:** Kinward shall support surface classes for personal mobile, personal tablet, personal desktop, shared display, and voice.
- **FR-040:** Every rendered experience shall receive a surface context containing ownership, room when applicable, privacy state, interaction capabilities, and viewing distance.
- **FR-041:** Surface context shall influence available content, density, interaction size, personal-data visibility, layout selection, and handoff behavior.
- **FR-042:** The default personal mobile surface shall support assistant presence, a Now area, quiet briefing, active topics, and persistent assistant input.
- **FR-043:** A shared display shall default to household-safe ambient information and shall automatically return to that state after a personal interaction expires.
- **FR-044:** Kinward shall render product surfaces from registered card definitions and validated layout definitions.
- **FR-045:** Card definitions shall declare supported surfaces, data and configuration schemas, privacy characteristics, size constraints, and rendering behavior.
- **FR-046:** Invalid or unknown card configuration shall fail safely and shall not replace the last valid layout.
- **FR-047:** Built-in default layouts shall remain available and recoverable after customization.
- **FR-048:** The assistant may generate temporary views only from registered components and validated schemas.
- **FR-049:** A user shall be able to target a visible item as structured context for the next assistant request.
- **FR-050:** A user shall be able to request an explanation of why a meaningful item appeared, what changed, which source categories were used, the relevant confidence, and available corrections.

### 7.6 Proactivity, coordination, approvals, and activity

- **FR-051:** Kinward shall prioritize surfaced information by expected household relevance and required action rather than presenting an unfiltered notification feed.
- **FR-052:** Proactive delivery shall support ambient, briefing, nudge, interruption, and explicitly authorized autonomous-action levels.
- **FR-053:** Kinward shall default to the least disruptive delivery level consistent with timing, risk, and household policy.
- **FR-054:** Kinward shall not require routine definitions to detect meaningful calendar, school, household, or transportation exceptions.
- **FR-055:** A coordination request between household members shall disclose only the minimum information needed for the recipient to decide or respond.
- **FR-056:** Coordination requests shall support accept, decline, counter, and delegate-to-assistant outcomes where applicable.
- **FR-057:** Meaningful external actions shall be governed by an authority level of observe, suggest, prepare, act with confirmation, or act autonomously within explicit limits.
- **FR-058:** An approval shall state the intended action, affected person or resource, service used, reason approval is required, and reversibility when known.
- **FR-059:** Kinward shall record meaningful assistant and integration actions in a plain-language activity history.
- **FR-060:** Activity records shall identify what happened, who requested it, which assistant acted, on whose behalf, why it was allowed, whether approval occurred, which integration was used, the result, and whether undo is available.

### 7.7 Integrations

- **FR-061:** Integrations shall use vendor-neutral capability contracts where practical so product behavior is not embedded directly in one provider.
- **FR-062:** Kinward shall expose integration capability and health independently from general application health.
- **FR-063:** An unavailable optional integration shall degrade only the features that depend on it.
- **FR-064:** Calendar integration shall support reading events and detecting relevant changes within the connected person’s authorization boundary.
- **FR-065:** Calendar actions that modify external state shall follow the applicable approval and activity requirements.
- **FR-066:** Email integration shall preserve account boundaries and shall not expose private message content to other household members or shared surfaces without permission.
- **FR-067:** Home Assistant shall remain the authority for imported physical areas, devices, entities, and current home state.
- **FR-068:** Kinward shall translate Home Assistant state and actions into household language rather than requiring ordinary users to operate entities or services directly.
- **FR-069:** Home Assistant actions shall honor permissions, approvals, current state, and activity logging.
- **FR-070:** Integrations shall use secure defaults, bounded retries, timeouts, and failure isolation.

### 7.8 Kinward Control

- **FR-071:** Kinward shall provide a separate administrative experience rather than mixing system management into the default assistant navigation.
- **FR-072:** Authorized administrators shall be able to manage household profiles, invitations, assistants, permissions, integrations, surfaces, layouts, proactivity settings, and system health.
- **FR-073:** Users shall be able to manage their own assistant preferences, private memory, and personal integration connections without entering unrelated household administration.
- **FR-074:** Kinward Control shall present health and degraded capabilities in plain language with actionable remediation.
- **FR-075:** Administrative views shall not display credentials, secret values, raw hidden prompts, or unrestricted private memory.
- **FR-076:** Authorized users shall be able to inspect activity and approvals using person, assistant, integration, status, and time filters.

### 7.9 Deployment and household operations

- **FR-077:** A standard Kinward deployment shall start through documented Docker Compose commands.
- **FR-078:** The default deployment shall not require Home Assistant, external memory, external knowledge, or observability services to start.
- **FR-079:** Kinward shall provide persistent storage for household configuration, people, assistants, layouts, approvals, activity, and memory references.
- **FR-080:** Kinward shall provide documented backup and restore procedures for household-owned data and configuration.
- **FR-081:** Kinward shall provide a documented upgrade process that preserves household data or stops safely with actionable recovery instructions.
- **FR-082:** Kinward shall provide export and import mechanisms for supported household data required to move deployments or recover from a rebuild.
- **FR-083:** Health reporting shall distinguish core application failure from optional capability degradation.

## 8. Nonfunctional requirements

### 8.1 Privacy and security

- **NFR-001:** Authorization shall be enforced server-side for every private person, assistant, memory, topic, integration, approval, and activity resource.
- **NFR-002:** Secrets and integration credentials shall be encrypted at rest or stored in a platform-appropriate secret mechanism and shall never be returned through normal API responses or logs.
- **NFR-003:** Shared-surface privacy rules shall be covered by automated tests for recognized, unknown, multiple-person, timed-out, and reduced-confidence states.
- **NFR-004:** Content obtained from email, calendars, documents, web pages, or Home Assistant shall be treated as untrusted input and shall not be able to override system permissions or action policy.
- **NFR-005:** Sensitive operations shall produce tamper-evident or append-protected audit data sufficient for household troubleshooting.
- **NFR-006:** The product shall minimize data sent to model and integration providers to the information required for the current permitted task.

### 8.2 Reliability and recoverability

- **NFR-007:** Failure of an optional provider shall not prevent core household setup, authentication, administration, or local data access.
- **NFR-008:** External calls shall use explicit timeouts, bounded retries, and circuit-breaking or equivalent failure isolation.
- **NFR-009:** Actions that modify external state shall be idempotent where the provider permits it or shall guard against accidental duplicate execution.
- **NFR-010:** Database migrations shall be transactional where supported and shall provide a tested rollback or restore path.
- **NFR-011:** Backup restoration shall be tested against a clean deployment before the first household production milestone is declared ready.

### 8.3 Performance

- **NFR-012:** The personal home surface shall render locally available content without waiting for model inference or unavailable external integrations.
- **NFR-013:** Kinward shall visibly acknowledge a submitted assistant request promptly even when full model output or tool execution takes longer.
- **NFR-014:** Shared-display privacy transitions shall remove disallowed private content immediately when identity confidence or audience state changes.
- **NFR-015:** Health and administration pages shall remain usable during external-provider degradation.

### 8.4 Accessibility and usability

- **NFR-016:** Core web/PWA experiences shall meet WCAG 2.2 AA expectations for keyboard access, contrast, semantics, focus, and assistive technology support.
- **NFR-017:** Shared-display controls shall support room-distance readability and appropriately large touch targets.
- **NFR-018:** Normal household workflows shall use household language and shall not require knowledge of infrastructure, model providers, entities, schemas, or configuration syntax.
- **NFR-019:** Meaningful destructive or externally visible actions shall provide confirmation or undo consistent with their configured authority level.

### 8.5 Portability and maintainability

- **NFR-020:** Core product behavior shall depend on capability interfaces rather than direct assumptions about one model, memory, knowledge, calendar, email, or smart-home provider.
- **NFR-021:** Shared schemas shall validate API payloads, cards, layouts, and integration boundaries across backend and frontend consumers.
- **NFR-022:** Registered cards and layouts shall be versioned sufficiently to support validation and future migration.
- **NFR-023:** The repository shall maintain automated backend and frontend validation gates for all accepted product foundations.
- **NFR-024:** Current product documentation shall be maintained separately from archived Homefront SaaS and routine-centric material.

## 9. Delivery milestones

### Milestone A: Foundation already accepted

- Clean single-household repository and vocabulary.
- Core domain and persistence baseline.
- Initial household bootstrap API.
- Integration resilience and health capability reporting.
- Neutral memory and knowledge provider contracts.
- Honcho and LLM-Wiki provider adapters.
- Registry-driven frontend proof of concept.
- Docker, CI, `mise`, and `uv` workflows.

### Milestone B: First end-to-end personal assistant slice

- Authentication and current-person identity.
- Web onboarding connected to household bootstrap.
- Personal assistant conversation endpoint and model-provider contract.
- Conversation and topic persistence.
- Permission-bound memory retrieval and confirmed durable facts.
- Live personal mobile home surface.
- Activity records for assistant and integration operations.

### Milestone C: Household-aware usable product

- Invitations and invited-member onboarding.
- Multiple household profiles and personal assistants.
- Calendar integration with change detection.
- Home Assistant state and one permitted action flow.
- Shared-display privacy behavior.
- Approvals and basic Kinward Control.
- Backup, restore, and upgrade validation.

### Milestone D: Coordinating household assistant

- Email integration.
- Progressive context onboarding.
- Coordination requests.
- Proactive delivery policy and background evaluation.
- Richer cards, topics, and cross-surface continuity.
- Layout editing and deeper administration.

### Milestone E: Voice and advanced experiences

- Voice orchestration and private handoff.
- Emergency surface mode.
- Contextual maintenance recall.
- Native Android evaluation and only those modules justified by measured PWA limitations.

## 10. Dependencies and constraints

- The architecture specification must define authentication, model-provider routing, assistant runtime, context assembly, memory flow, background work, integration credential storage, action execution, and deployment recovery before implementation stories for those areas are considered ready.
- UX specifications remain authoritative for surface behavior, information architecture, card interaction, and shared-display privacy unless this PRD explicitly narrows release scope.
- Home Assistant remains the authority for physical home state; Kinward must not recreate its device registry or automation engine.
- Optional providers must remain optional and must not become implicit startup dependencies.
- Legacy Homefront code may be referenced or selectively salvaged only after removal of multi-tenant, SaaS, routine-centric, support-access, and public-repository exposure assumptions.

## 11. Product risks

1. **Privacy leakage across shared surfaces or household relationships.** Mitigation requires backend authorization, conservative display policy, identity-confidence handling, and dedicated tests.
2. **A generic chatbot experience instead of a useful household assistant.** Mitigation requires live durable context, topics, action capability, and meaningful Now/Briefing behavior in the first vertical slices.
3. **Overbuilding abstractions before delivering a working assistant.** Milestone B must produce a complete user-visible flow before additional provider or framework expansion.
4. **Notification and proactivity fatigue.** Delivery levels, counter-metrics, and conservative defaults must be implemented before broad background monitoring.
5. **Unsafe external actions.** Approval, authority, idempotency, activity, and prompt-injection defenses must precede autonomous execution.
6. **Household operations becoming fragile.** Backup, restore, upgrade, and degraded-mode behavior are release requirements rather than post-launch cleanup.
7. **Identity ambiguity.** Shared-surface and voice experiences must fail toward privacy, not convenience.

## 12. Open product decisions

These decisions do not block the PRD but must be resolved during architecture, epic planning, or readiness review before affected stories enter implementation:

- Which authentication method is the default for a private household deployment and how account recovery works without a SaaS control plane.
- Which model-provider implementation is used for the first assistant slice and which capabilities are mandatory in the neutral provider contract.
- Which calendar provider is implemented first and what polling, webhook, or synchronization behavior is acceptable for the initial household.
- Which data is stored directly in Kinward versus indexed or referenced in Honcho and LLM-Wiki.
- Which identity-confidence signals are available in the initial shared-display release before voice or proximity features exist.
- The minimum supported export format and restore guarantee for the first production household deployment.
- The threshold and household controls for moving proactive behavior from briefing to nudge, interruption, or autonomous action.

## 13. PRD completion criteria

This PRD is ready to be marked final when:

- The product owner reviews scope, milestones, functional requirements, and open decisions.
- The architecture specification confirms that every Milestone B and Milestone C requirement has an implementable system boundary.
- Epics map every functional and nonfunctional requirement to delivery work without creating a competing product scope.
- Stories for the first milestone have testable acceptance criteria and identify required security, privacy, and operational validation.
- The implementation-readiness review finds no unresolved phase blocker for the first planned milestone.
