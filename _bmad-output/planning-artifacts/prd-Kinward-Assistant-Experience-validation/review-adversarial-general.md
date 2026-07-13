# Adversarial PRD Review: Kinward Assistant Experience

## Review Basis

This review evaluates `prd-Kinward-Assistant-Experience.md` only against these authoritative sources:

- `product-brief-Kinward-Assistant-Experience.md`
- `ux-design-specification-Kinward-Assistant-Experience.md`
- `docs/pivot/single-household-pivot-and-rebuild-plan.md`
- `docs/pivot/salvage-matrix.md`

## Verdict

**Not ready for architecture or epic decomposition without correction.** The PRD captures the broad product direction, but it weakens or leaves unresolved several source-level invariants at the exact boundaries where implementation needs deterministic contracts: source authority, one-household enforcement, shared-assistant ownership, youth privacy, identity-confidence behavior, external-action authority, inference degradation, and recovery scope. It also moves the required cross-surface foundation behind the personal-mobile slice, conflicting with both the UX specification and rebuild execution order.

## Severity Counts

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 10 |
| Medium | 5 |
| Low | 0 |

## Findings

### 1. High: The PRD declares the wrong source set

**Exact PRD lines:** 6-10, 381-384

**Impact:** The frontmatter omits the authoritative salvage matrix and adds `docs/pivot/migration-status.md`, which is not one of the governing sources. The body grants explicit continuing authority only to the UX specification and does not establish the product brief, rebuild plan, and salvage matrix as constraints. Architecture and epics could therefore justify scope or completion claims from a non-authoritative status document or bypass the salvage acceptance rule.

**Concrete fix:** Replace line 10 with `docs/pivot/salvage-matrix.md`. Add a source-authority statement naming all four governing documents and state that status reports and legacy Homefront material are evidence only, not product authority. Preserve the UX specification's authority over surface behavior while preserving the rebuild plan and salvage matrix as authority over sequencing and migration.

**Authoritative basis:** Rebuild plan lines 115-117 and 206-210 require an authoritative current planning set; salvage matrix lines 34-43 define the acceptance rule for moved subsystems.

### 2. High: "Foundation already accepted" is unsupported by the authoritative sources

**Exact PRD lines:** 331-340

**Impact:** None of the four authoritative sources certifies these items as accepted. Several listed items are salvage candidates whose movement is conditional, including the Honcho and LLM-Wiki adapters and generic infrastructure. Treating them as accepted can cause architecture and stories to inherit code before current behavior, removed assumptions, Kinward contracts, focused tests, and subsystem checks are demonstrated.

**Concrete fix:** Rename Milestone A to a planned or evidence-gated foundation milestone unless acceptance is established by an authorized readiness process. For every salvaged item, make completion contingent on the six salvage-matrix checks; do not infer acceptance from migration status or repository presence.

**Authoritative basis:** Rebuild plan lines 33-34 and 163-168 prohibit automatic movement; salvage matrix lines 34-43 require six checks before a subsystem may move.

### 3. High: The single-household invariant is not carried into enforceable storage and service boundaries

**Exact PRD lines:** 123-129, 180-182, 280-286, 384

**Impact:** FR-001 states the outcome, but FR-002 only prevents a second household through the "normal setup flow." It does not require all APIs, background jobs, persistence paths, imports, or recovery paths to preserve one household, nor does it prohibit retained tenant identifiers and tenant routing. An implementation could satisfy the onboarding test while retaining multi-tenant architecture and permitting a second household through another path, directly undermining the simplification and privacy boundary of the pivot.

**Concrete fix:** Require the one-household invariant at database, service, import/restore, and background-work boundaries; reject creation or import of a second household through every path. State that current Kinward contracts and schema must not retain tenant routing, tenant IDs, control-plane ownership, or commercial-role semantics unless a non-tenancy use is explicitly justified.

**Authoritative basis:** Product brief lines 38-46; rebuild plan lines 101-107 and 123-129; salvage matrix lines 7-8, 21-22, and 25-32.

### 4. High: The shared fallback assistant has no ownership or capability contract

**Exact PRD lines:** 22, 193-200, 206-215, 219-226

**Impact:** FR-012 defines ownership only for personal assistants, while FR-022 refers to shared assistants without defining their owner, lifecycle, routing role, memory boundary, or permitted capability set. Low-confidence shared-surface behavior can therefore be implemented by routing into a personal assistant, a synthetic "household owner," or a combined household memory, all contrary to the source model that personal assistants are primary and shared AI is a limited fallback.

**Concrete fix:** Add an explicit shared-assistant contract: it has no personal owner, is household-scoped, is the limited fallback for household-safe requests, and cannot receive unrestricted personal memory. Define routing from low-confidence/unknown shared interactions to that fallback and keep personal-assistant access contingent on resolved identity and surface policy.

**Authoritative basis:** Product brief lines 175-181, 183-190, and 238-245; UX specification lines 206-208 and 465.

### 5. High: Teen and child privacy is reduced to an undefined policy override

**Exact PRD lines:** 72-79, 223-226, 272-275

**Impact:** The teen persona changes source language from privacy from parents and shared surfaces to privacy "except where explicit household policy permits otherwise." No requirement bounds that exception. FR-035 merely says "age-appropriate" and "stronger default restrictions," while FR-037 protects only another adult's memory from administrators. The result permits an implementation in which an administrator or parent can expose teen or child assistant memory through policy, Kinward Control, activity, approvals, or shared surfaces without violating a testable PRD statement. It also gives no deterministic behavior for a child profile without an account.

**Concrete fix:** Define testable youth privacy and permission rules separately from adult administration. Preserve the teen's private-assistant and parent/shared-surface boundary from the product brief; specify which narrowly defined household-safe coordination facts may be shared without exposing private assistant memory. Extend server-side authorization and administrative-view requirements to child and teen resources, and define the restricted behavior of child profiles that have no account or personal assistant.

**Authoritative basis:** Product brief lines 94-100 and 175-181; UX specification lines 49-53, 206-208, 433, 465, and 478-483.

### 6. High: Identity-confidence behavior cannot be tested independently of undecided signals

**Exact PRD lines:** 80-82, 219-226, 294-295, 311-312, 398-405

**Impact:** FR-032 lists inputs and FR-033 uses the undefined threshold "insufficient," but the PRD does not retain the authoritative high/medium/low behavior matrix. The signals themselves remain an open decision even though shared-display privacy is due in Milestone C. Tests can cover named states without a normative expected result, especially for medium confidence, confidence drops during a session, unknown people, multiple people, and private handoff. This makes privacy acceptance implementation-defined.

**Concrete fix:** Specify behavior by confidence state without depending on which signals supply it: high confidence may personalize only within surface policy; medium confidence must stay generic and offer authenticated private-device handoff; low confidence must ask identity or use the household fallback; multiple-person state must not disclose private memory. Define immediate removal and ambient reset when confidence drops or a personal session expires. Resolve only the signal implementation separately.

**Authoritative basis:** Product brief lines 183-190; UX specification lines 206-208, 220-228, and 421-425.

### 7. High: External-action authority and approval semantics are not executable requirements

**Exact PRD lines:** 164-168, 245-254, 262-267, 303-305, 319-320, 392

**Impact:** "Meaningful," "explicit limits," "applicable approval," and "consistent with their configured authority level" are not defined. The PRD does not say how authority is bound to a person, assistant, capability, resource, or period; who may grant or revoke it; what happens when policy or external state changes after preparation; or which result prevents a duplicate retry. Teams cannot derive a stable policy schema or acceptance tests, and a provider-specific implementation could silently widen autonomous action.

**Concrete fix:** Define a testable action-policy contract for observe, suggest, prepare, confirm, and bounded autonomous action. Require an explicit authorized principal and scope, deny execution outside that scope, re-check permissions and relevant current state at execution, identify the approver, preserve distinct prepared/approved/executing/succeeded/failed states, and specify duplicate and reversal behavior. Define which action classes are always recorded instead of relying on the word "meaningful."

**Authoritative basis:** Product brief lines 192-204; UX specification lines 20-22, 34-47, 234-244, and 270; salvage matrix line 15.

### 8. High: The milestone sequence contradicts the required first cross-surface slice

**Exact PRD lines:** 331-360

**Impact:** Milestone B delivers only a personal mobile home surface, while shared displays arrive in Milestone C and tablet/desktop distinct layouts are not committed in either milestone. The UX source requires the first implementation slice to render the same capability set across mobile, tablet, desktop, shared kitchen, and shared living-room surfaces to validate cards, layouts, surfaces, and privacy before expansion. The rebuild plan likewise places that cross-surface frontend foundation before household foundation. Deferring shared and larger surfaces allows the architecture to harden around a mobile-only layout and postpones the primary privacy proof.

**Concrete fix:** Put the source-defined cross-surface slice into the first frontend foundation milestone, using mocks where live household capabilities are not yet available. Require mobile, tablet, desktop, shared kitchen, and shared living-room layouts from one registry with the initial Presence, Now, Briefing, Continue, Schedule, House Status, Approval, and Input capability set. Keep live authentication, memory, calendar, and Home Assistant delivery in later milestones as needed.

**Authoritative basis:** UX specification lines 435-448 and 450-466; rebuild plan lines 135-140 and 170-180.

### 9. High: Cloud/model inference can become an undeclared mandatory dependency

**Exact PRD lines:** 35, 44-49, 104-105, 185, 301-312, 400-401

**Impact:** The PRD calls cloud inference optional and says onboarding requires no integrations, but the startup requirements enumerate Home Assistant, memory, knowledge, and observability while omitting model inference. The first assistant slice depends on an unresolved model provider, and no requirement defines behavior when no inference provider is configured or the configured provider is unavailable. This can produce either a hidden mandatory cloud dependency or an apparently successful onboarding flow whose assistant cannot function, conflicting with household-owned deployment and safe degradation.

**Concrete fix:** State explicitly that Kinward can boot, authenticate, onboard, administer, restore, and render locally available surfaces without cloud inference. Define the visible degraded state and unavailable capabilities when no model provider is configured or it fails. Separately define what configured inference capability is required before text conversation is considered usable; do not imply that a third-party SaaS backend is mandatory.

**Authoritative basis:** Product brief lines 38-46 and 206-224; rebuild plan lines 101-111 and 123-125.

### 10. High: Backup and recovery are milestone requirements with an unresolved and incomplete data contract

**Exact PRD lines:** 106, 279-286, 299-305, 354-360, 398-405

**Impact:** FR-080 requires documentation, FR-082 refers circularly to "supported household data required" for recovery, and the minimum export/restore guarantee remains open while Milestone C claims backup/restore validation. Persistence enumerates only part of the user-visible state and does not establish whether people, accounts, assistants, personality, conversations/topics, useful memories versus references, integration settings, Home Assistant mappings, approvals, activity, cards/layouts, and recovery-critical configuration survive a clean rebuild. A restore test can pass against a narrow implementation while losing the household's assistant continuity or integration mapping.

**Concrete fix:** Resolve the recovery data contract before Milestone C stories are ready. At minimum, carry forward the rebuild plan's explicit people, assistants, personality settings, useful memories, integration settings, and Home Assistant mappings, then identify all additional PRD-owned state required for assistant continuity. Define clean-deployment restore acceptance, version compatibility/failure behavior, and a verification step proving restored ownership and privacy boundaries before declaring the household production milestone ready.

**Authoritative basis:** Product brief lines 38-43; rebuild plan lines 127-133; PRD's authoritative operational direction is also constrained by the rebuild plan's requirement for explicit export/import rather than legacy migration.

### 11. Medium: Multiple-assistant support has routing but no lifecycle requirements

**Exact PRD lines:** 22, 96, 193-200, 272-273

**Impact:** FR-014 presumes multiple assistants and a primary router, but the only creation requirements cover the first assistant during onboarding. There is no requirement to create, classify, select as primary, retire, or delete specialist or temporary assistants while preserving ownership and memory boundaries. Architecture must nevertheless choose cardinality and lifecycle behavior, and stories can accidentally implement a permanent one-assistant model that still satisfies FR-011.

**Concrete fix:** Add the minimum lifecycle contract supported by the source: an account-bearing user can create additional specialist or temporary personal assistants, each has exactly one owner, one assistant is the default router, and changing or retiring assistants does not merge private memory implicitly. Assign this to a milestone or explicitly defer it while keeping the schema compatible.

**Authoritative basis:** Product brief lines 175-181; rebuild plan lines 35-40; salvage matrix line 8.

### 12. Medium: Personal-memory correction and deletion authority is ambiguous for cross-person facts

**Exact PRD lines:** 206-215, 225-226, 273-275

**Impact:** FR-029 gives unspecified "authorized users" access to facts that "concern them." A fact may concern several people while residing in one person's or one assistant's private memory. The wording can be interpreted either to deny a person correction of shared household facts or to permit them to inspect and delete another owner's private memory merely because it mentions them. FR-037 only rules out automatic administrator access to another adult's memory and does not settle this conflict.

**Concrete fix:** Define separate authorization semantics for owner-bound personal memory, assistant-bound memory, confirmed shared household facts, and multi-person coordination facts. Make inspection, correction, and deletion preserve the source requirement for per-user/per-assistant ownership and privacy; expose only the minimum shared fact needed for coordination rather than the containing private memory.

**Authoritative basis:** Product brief lines 14-20, 175-181, and 192-204; salvage matrix line 9.

### 13. Medium: Optional memory and knowledge degradation has no functional fallback contract

**Exact PRD lines:** 104, 208-215, 259-267, 301-312

**Impact:** FR-025 says Kinward remains "operational," and FR-063 says only dependent features degrade, but neither identifies which assistant behaviors remain available with the disabled provider versus a temporarily failed provider. The PRD does not define whether durable writes queue, fail visibly, remain local, or are discarded, nor how retrieval confidence and recovery are presented. Different adapters can therefore produce materially different continuity and privacy behavior while all claiming safe degradation.

**Concrete fix:** Define the provider-neutral degraded contract: core boot/auth/onboarding/admin/local data remain available; provider-dependent retrieval or indexing reports an explicit unavailable/degraded result; no durable-memory claim is made for data that was not persisted; health identifies the affected capability; and recovery does not silently duplicate or broaden stored data. Keep provider-specific retry details outside the product contract.

**Authoritative basis:** Rebuild plan lines 101-105 and 123-125; salvage matrix lines 9 and 19-20.

### 14. Medium: Home Assistant authority lacks an explicit stale/unavailable-state edge condition

**Exact PRD lines:** 258-267, 301-312, 382-383

**Impact:** FR-067 correctly names Home Assistant as current-state authority, but the PRD does not say how cached imported state is represented when Home Assistant becomes unavailable. FR-063 permits degradation and FR-069 requires current state for action, yet no requirement prevents Kinward from displaying cached data as current or executing against an unverifiable state. This can create false physical-state claims and unsafe controls during provider degradation.

**Concrete fix:** Require imported physical state to carry availability/freshness sufficient to avoid presenting stale data as current. When Home Assistant is unavailable or relevant current state cannot be verified, show the capability as degraded and do not claim action completion or execute an action whose policy requires current state. Do not create a competing Kinward device registry or authoritative automation state.

**Authoritative basis:** Product brief lines 48-58; rebuild plan lines 101-105; salvage matrix line 13.

### 15. Medium: Action transparency drops the source requirement to identify information used

**Exact PRD lines:** 47-48, 164-168, 251-254

**Impact:** FR-060 records why an action was allowed and which integration was used, but omits what information was used. An approval likewise describes the intended change without requiring the relevant source information or categories. Users may be unable to detect an action based on stale, incorrect, or inappropriate context even though the product brief explicitly requires this transparency for every meaningful action.

**Concrete fix:** Add the permitted source categories and relevant user-correctable facts used to approval and activity explanations, with privacy filtering and without exposing hidden reasoning, credentials, or another person's private data. Link this requirement to FR-030 and FR-050 so action explanations use the same provenance model.

**Authoritative basis:** Product brief lines 192-204; UX specification lines 188-190, 355-367, and 270.

## Release-Blocking Corrections

Before architecture or epics are treated as ready, the PRD should at minimum resolve findings 1, 3-10. Finding 2 must be corrected before any salvaged subsystem is accepted as complete. Findings 11-15 can be assigned to explicit milestones, but their contracts must be settled before the affected architecture and stories enter implementation.
