---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
status: revised-ha-native
revisionDate: 2026-07-15
homeAssistantBaseline: 2026.7.2
inputDocuments:
  - _bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md
  - _bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md
  - _bmad-output/planning-artifacts/ha-native-pivot-2026-07-15.md
  - docs/pivot/single-household-pivot-and-rebuild-plan.md
  - docs/pivot/salvage-matrix.md
supersedes:
  - standalone five-surface frontend decomposition
  - Story 1.6 exceptional visual foundation
---

# Kinward — Home Assistant Native Epic Breakdown

## 1. Purpose

This revision preserves Kinward's backend, household, assistant, privacy, memory, action, provider, activity, backup, restore, and operational requirements while replacing the standalone Kinward frontend with Home Assistant as the committed application shell.

Home Assistant owns dashboards, responsive rendering, mobile access, areas, devices, entities, physical state, service execution, and Assist voice pipelines. Kinward owns household intelligence and exposes it through a documented Home Assistant custom integration.

The implementation target for this revision is Home Assistant Core **2026.7.2**. CI and local development must pin the supported version rather than depend on an unbounded latest image.

## 2. Scope correction

### Removed from committed scope

- Standalone `apps/web` Assistant Experience
- Five Kinward-owned surface shells
- Kinward card registry and renderer registry as product architecture
- Kinward layout resolver, layout persistence, and layout editor
- Kinward design-token and primitive system
- Standalone PWA and Kinward-owned mobile shell
- Running Home Assistant or HACS cards outside Home Assistant
- Story 1.6 and its visual approval gates

### Preserved

All non-UI requirements in the PRD and architecture remain active unless this document explicitly changes their presentation mechanism. In particular, preserve:

- Single-household deployment and atomic bootstrap
- Profile/account binding, invitations, roles, privacy classes, and minor policy
- Personal and household assistants and ownership boundaries
- Truthful conversation lifecycle, cancellation, topic continuity, and context authorization
- Personal memory, household-shared knowledge, inferred-observation confirmation, correction, deletion, lineage, and provider degradation
- Server-side authorization and shared/private disclosure boundaries
- Proactive prioritization, calendar change detection, coordination, approvals, and meaningful-action reconciliation
- Home Assistant action policy and fresh-observation completion rules
- Activity, audit, health, diagnostics, backup, restore, import, deletion, and recovery
- Provider-neutral ports for models, memory, knowledge, calendars, communications, and Home Assistant
- SQLite default, optional PostgreSQL parity, SQL jobs/outbox, modular-monolith boundaries, and public-repository safety

## 3. Cross-cutting architecture rules

1. Kinward remains a hexagonal modular monolith with framework-free domain and application layers.
2. The HA integration is an adapter. It must not own household policy or directly mutate persistence.
3. Every protected request carries immutable Kinward access context derived from the Home Assistant person entity synced to that request's HA user - not an explicit admin-configured mapping (superseded 2026-07-16: Kinward has no identity system of its own; every HA `person` entity syncs automatically, keyed on its durable HA person id).
4. Being an HA administrator makes a synced person a Kinward administrator too (role is read from HA's own admin flag on every sync pass, plural admins supported, no separate Kinward-side designation - superseded 2026-07-16). That household role never by itself grants another adult's private Kinward data - role and privacy authorization remain separate axes (see Story 3.3).
5. Standard HA entities are used only when state is compact, useful in dashboards/automations, and safe for HA history/logbook.
6. Private bodies, secrets, unrestricted payloads, prompts, and large nested documents must not be placed in entity state or attributes.
7. Rich data uses authorization-checked backend APIs or integration WebSocket commands only when required.
8. Home Assistant remains authoritative for areas, devices, entities, and observed physical state.
9. HA action success means submitted. Kinward marks an action completed only after the required fresh confirming observation.
10. Optional providers degrade independently and truthfully.
11. The default distributable dashboard uses only core HA cards. Optional HACS enhancements must be additive.
12. Custom frontend cards or panels are deferred until real household usage proves a core-card limitation.

## 4. Epic summary

| Epic | Outcome |
| --- | --- |
| 1 | A healthy Kinward backend and HA 2026.7.2 integration can be installed and used today. |
| 2 | Household members can speak or type to their private Kinward assistant through Assist with truthful lifecycle behavior. |
| 3 | The household and account graph is safely established and managed through backend workflows and HA-hosted configuration entry points. |
| 4 | Topics, memory, knowledge, and corrections remain private, inspectable, and portable across authorized HA interactions. |
| 5 | Kinward produces useful briefings and calendar-aware attention without becoming a notification feed. |
| 6 | Meaningful actions and household coordination are approved, executed, reconciled, and recorded safely. |
| 7 | Home Assistant state and actions are used through policy-bound, observation-confirmed adapters. |
| 8 | Administration, health, activity, and diagnostics are available without exposing protected content. |
| 9 | Backup, restore, import, retention, deletion, and recovery preserve the complete household authority model. |
| 10 | Advanced generated views, custom cards, and broader clients remain evidence-gated extensions rather than foundation blockers. |

# Epic 1: Installable HA-Native Household Foundation

## Goal

From a clean checkout, start Kinward and a pinned Home Assistant 2026.7.2 development instance, install the Kinward integration, and display a useful core-card dashboard with truthful health and household state.

### Story 1.1: Preserve the backend deployment foundation

As the household operator,
I want the existing Kinward backend foundation retained and revalidated,
So that the UI pivot does not discard working domain, persistence, policy, worker, and deployment capability.

#### Acceptance criteria

- Existing single-household backend, database, migration, API, worker, outbox/job, policy, and test foundations are inventoried and retained when compatible.
- `docker compose up` starts a healthy core Kinward stack without optional providers.
- SQLite remains the required default; PostgreSQL remains optional and unadvertised until parity passes.
- No standalone frontend is required for backend readiness.
- The old five-surface frontend is isolated from active build and test gates before deletion.

### Story 1.2: Preserve atomic household bootstrap

As the initial administrator,
I want the household graph created atomically and duplicate-safely,
So that the HA pivot does not weaken identity, assistant ownership, or privacy foundations.

#### Acceptance criteria

- One transaction creates the household, initial administrator/profile binding, primary personal assistant, fallback assistant, and selected adult, child, and pet profiles.
- Retry is duplicate-safe.
- Exactly one household exists per deployment.
- Pets receive no account, assistant, private memory, credentials, approval, delegation, or authority.
- Existing Story 1.2 tests remain authoritative after presentation dependencies are removed.

> **Superseded (2026-07-16, HA-native identity redesign):** Kinward has no local accounts, so bootstrap
> no longer creates an "initial administrator" at all - it only creates the household, the fallback
> assistant, and any pets. People (including whoever ends up administrator) exist solely via HA
> `person` sync (see Story 3.1's note). "As the initial administrator" and "initial
> administrator/profile binding" above no longer describe the implementation; retained for history.

### Story 1.3: Add a pinned Home Assistant development profile

As a developer,
I want a reproducible HA 2026.7.2 environment,
So that integration behavior can be tested against the actual supported platform.

#### Acceptance criteria

- Local development provides a documented HA 2026.7.2 container/profile with persistent config outside source-controlled secrets.
- The Kinward backend and HA can start together without requiring optional model, memory, knowledge, or calendar providers.
- Version compatibility is explicit in docs and CI.
- Upgrade tests fail visibly when an unsupported HA version is introduced.

### Story 1.4: Create the Kinward custom integration and config flow

As the household operator,
I want to configure Kinward through Home Assistant's UI,
So that installation does not require editing dashboard or integration internals.

#### Acceptance criteria

- `custom_components/kinward` includes a versioned manifest, config flow, translations, coordinator/client boundary, diagnostics redaction, and uninstall/reload behavior.
- Configuration accepts the Kinward backend URL and performs a bounded health check.
- Duplicate integration entries are rejected safely.
- Authentication material is stored using HA-supported config-entry mechanisms and is never logged.
- Backend unavailable, authentication failure, incompatible API, and configuration error are distinct.

### Story 1.5: Expose the initial safe entity set

As a household member,
I want useful Kinward state in ordinary Home Assistant cards,
So that I can use Kinward without custom frontend development.

#### Acceptance criteria

- Initial entities include `conversation.kinward`, backend availability, household status, briefing, attention count, next household event, and last successful refresh where useful.
- HA `person.*` entities remain authoritative for presence; Kinward profiles may map to them without duplicating presence state.
- Entity state and attributes are bounded, sanitized, and safe for recorder/logbook exposure.
- Stale, unavailable, disabled, and configuration-error states are distinguishable.
- Entity updates are coordinated and do not cause duplicate backend polling.

### Story 1.6: Ship the first core-card Kinward dashboard

As a household member,
I want a simple dashboard I can use immediately,
So that backend behavior can be tested in daily life before custom UI work resumes.

#### Acceptance criteria

- An importable dashboard named Kinward uses only built-in HA cards by default.
- The first view shows household-member status using HA person tiles/status chips, household status, today's calendar, briefing, attention items, conversation access, and integration health.
- The dashboard is usable in HA web and Companion apps without Kinward-owned responsive code.
- Optional HACS examples are documented separately and never required.
- The dashboard remains truthful when Kinward is unavailable.

### Story 1.7: Verify the same-day usable slice

As the product owner,
I want one end-to-end household trial,
So that planning is replaced by real usage quickly.

#### Acceptance criteria

- Install the integration on HA 2026.7.2.
- Configure a Kinward backend entry.
- Display at least one HA person state and one Kinward-produced summary.
- Run refresh or briefing generation from HA.
- Submit one text request through `conversation.kinward` or an explicitly temporary action fallback.
- Stop Kinward and verify truthful unavailable behavior.
- Record defects and observed missing UI needs without immediately creating custom cards.

# Epic 2: Private Assistant Through Home Assistant Assist

## Goal

Each account-bearing person can use exactly one private primary assistant through HA Assist while Kinward preserves person, assistant, topic, surface, and authorization boundaries.

### Story 2.1: Map HA users to Kinward profiles

- An HA user maps to at most one account-bearing Kinward profile.
- Missing, stale, disabled, deleted, or ambiguous mappings fail closed.
- Mapping changes are versioned and audited without protected content.
- HA administrators gain no role-derived access to another adult's private data.

> **Superseded (2026-07-16, HA-native identity redesign):** there is no explicit admin-configured
> mapping step or `HaUserMappingRecord` anymore - every HA `person` entity syncs automatically, and
> `PersonRecord.ha_user_id` (set only while that person has an HA login) is the resolution key, kept
> current every sync pass instead of admin-edited. "Fails closed" still holds exactly as stated: no
> row for that `ha_user_id` resolves to nothing. The last bullet is unchanged and still load-bearing:
> being an HA admin makes someone a Kinward admin (cross-cutting rule 4), but that role alone still
> grants no access to another adult's private data - only privacy classification does (Story 3.3).

### Story 2.2: Implement the Kinward conversation entity

- A `ConversationEntity` sends policy-filtered requests to Kinward.
- Conversation IDs preserve authorized multi-turn continuity.
- Accepted, responding, completed, cancelled, uncertain, and failed outcomes remain truthful.
- Model/tool output is treated as untrusted typed proposals.
- No-model operation still supports local commands and truthful capability reporting.

### Story 2.3: Support cancellation and terminal integrity

- Cancellation stops further model output and prevents every unsubmitted action.
- Exactly one terminal outcome is recorded.
- Unknown provider or action results survive restart and are reconciled before retry.
- HA UI limitations must not weaken backend cancellation semantics.

### Story 2.4: Continue topics across authorized HA clients

- Topics are durable work contexts, not raw chat sessions.
- The same authorized person can continue a topic across HA web and Companion apps.
- Authorization is re-evaluated on every request.
- Topic rename, archive, reopen, reclassify, inspection, and deletion remain backend capabilities even if the first HA UI exposes only a subset.

### Story 2.5: Preserve the household fallback assistant boundary

- One household-owned fallback assistant has no personal owner.
- It cannot query private personal memory.
- Shared-display or unmapped-user requests receive only household-safe context.
- Private continuation requires authenticated handoff to the intended person's authorized client.

# Epic 3: Household, Profiles, Invitations, and Assistant Setup

## Goal

Safely manage household people and assistant ownership while keeping initial HA-hosted setup minimal.

### Story 3.1: Manage pre-account people and pets

- Administrators can create adult and minor profiles before accounts exist.
- Pet profiles remain optional and household-shared only.
- Initial setup does not require rooms, devices, routines, detailed schedules, notification rules, or dashboard editing.

> **Superseded (2026-07-16, HA-native identity redesign):** the "people" half is gone - administrators
> don't create profiles at all anymore. Every HA `person` entity (with or without a linked login) syncs
> in automatically as a Kinward profile; a no-login person (e.g. a young child) is simply a `person`
> entity with no `user_id`, which already *is* the "pre-account person" concept this story wanted -
> nothing separate to build. Only the pet half remains genuinely new work: pet CRUD after bootstrap
> (create/list/update/remove), since bootstrap already accepts initial pets but has no later add path.
>
> **Implemented (2026-07-16):** pet CRUD lives in `application/pets.py`, exposed as
> `GET/POST /api/v1/integration/pets` and `PATCH`/`DELETE /api/v1/integration/pets/{id}`, admin-only
> for mutation (see Story 8.2's admin-plural note). Tests in `tests/test_pets.py` and the API round
> trip in `tests/test_integration_api.py`.

### Story 3.2: Bind invitations without duplicate profiles

- Invitations are single-use, expiring, revocable, hashed, and invalid after binding.
- Acceptance binds to the intended existing profile.
- Stale, ambiguous, cross-profile, or replayed acceptance fails closed.

> **Superseded (2026-07-16, HA-native identity redesign):** eliminated entirely. HA already has real
> user management and Kinward has no email-delivery mechanism to build an invitation flow on top of;
> a person becomes usable the moment they exist in HA, via sync. Nothing in this story is built or
> planned.

### Story 3.3: Enforce account, role, privacy, ownership, and authority separately

- Household role, account state, privacy class, assistant ownership, action authority, retained ownership, reactivation, and deletion overlay are separate concepts.
- Adult, teen, and child policies are deterministic.
- Teen private disclosure remains unconditionally denied outside the exact owner-authorized, privacy-filtered exception.

> **Updated (2026-07-16, HA-native identity redesign):** "account state" is dead - there is no local
> Kinward account. "Household role" is narrower than it reads above and is no longer admin-assigned:
> it is exactly two values, `admin`/`member`, mechanically derived every sync pass from whether the
> synced person's linked HA user is currently an HA administrator (plural admins are expected and
> supported - see cross-cutting rule 4). This story's still-real, still-unbuilt remainder is
> `profile_kind` reclassification (adult/teen/child) and privacy-class management for a synced person -
> that's a genuine admin-facing action this story still owns; admin/member role is not.
>
> **Implemented (2026-07-16):** `application/people.reclassify_person` sets `profile_kind` and keeps
> the person's `classification` (privacy class) in lockstep - `child` -> `private-child`, `adult`/`teen`
> -> `private-person` - never touching `role`. Exposed admin-only as
> `PATCH /api/v1/integration/people/{id}/reclassify`. Tests in `tests/test_people_admin.py` and
> `tests/test_integration_api.py`.

### Story 3.4: Configure the primary assistant

- Every account-bearing person has exactly one primary personal assistant in the first release.
- The owner sets assistant name and supported personality/interaction preferences.
- Preferences never alter authority, privacy, or action policy.
- Disablement, deletion, and replacement preserve same-owner boundaries and defined content/work disposition.

> **Updated (2026-07-16, HA-native identity redesign):** "account-bearing" now just means "synced from
> HA" - every synced person gets their primary assistant auto-created atomically as part of the same
> sync pass that creates their profile, with a default name. What's left of this story is letting the
> owner rename/customize their own assistant's personality after the fact; auto-creation is no longer
> new scope.
>
> **Implemented (2026-07-16):** `application/assistants.update_own_primary_assistant` lets the resolved
> owner (by `ha_user_id`) rename their primary assistant and/or set its `personality` dict, exposed as
> `PATCH /api/v1/integration/assistants/primary`. It only ever touches the `AssistantRecord`, never the
> owning `PersonRecord`, so preferences structurally cannot alter authority/privacy/action policy.
> Tests in `tests/test_assistants.py` and `tests/test_integration_api.py`.

# Epic 4: Topics, Memory, Knowledge, and Corrections

## Goal

Provide useful continuity without allowing optional memory systems or inferred knowledge to bypass Kinward policy.

### Story 4.1: Persist authorized topics and context

- Context is assembled only for the current person, assistant, topic, HA interaction, audience, action, capability, and freshness state.
- Kinward SQL remains authoritative for topics and conversations.
- Provider retrieval is minimized and authorization-bound before query construction.

### Story 4.2: Separate private memory and household-shared knowledge

- Personal memory is owned by one person.
- Household facts use a separate sharing classification.
- Fallback and shared contexts cannot query private indexes.
- Memory/knowledge providers are optional projections or retrieval adapters.

### Story 4.3: Manage inferred observations

- Pending observations cannot become durable facts or influence future assistance as facts without authorized explicit confirmation.
- Ownership, correction, confirmation, rejection, fixed expiry, recurrence suppression, dependency invalidation, backup, and restore are deterministic.

### Story 4.4: Inspect, correct, reclassify, and delete durable facts

- Users can inspect and correct authorized facts about themselves.
- Every fact records source category, timestamp, sharing class, confirmation state, confidence, and lineage.
- Narrowing, revocation, expiry, source-version invalidation, downstream clearing, and external deletion-pending behavior are enforced.

### Story 4.5: Degrade memory and knowledge truthfully

- Provider failure never becomes a claim that unavailable memory is known.
- Core conversation and household functions remain usable.
- Health indicates disabled, degraded, stale, reauthorization-required, and configuration-error states separately.

# Epic 5: Briefings, Calendar Awareness, and Proactive Attention

## Goal

Use Home Assistant dashboards and notifications to surface prioritized household meaning without recreating a notification feed.

### Story 5.1: Connect private person-owned calendars

- Calendar credentials are person-owned and independent of assistant lifecycle.
- Reads are limited to granted scope.
- Provider event identity, version, observed time, account, capability, and freshness are retained.
- Private details do not enter shared HA entity state unless explicitly shared.

### Story 5.2: Detect meaningful calendar changes

- Additions, removals, time, location, attendee, and cancellation changes are detected.
- Attention items are created only for supported overlap, transportation, attendee, or response-obligation predicates.
- Stale calendar state cannot support current-change claims or mutation.

### Story 5.3: Generate prioritized briefings

- Briefings prioritize meaning, recency, required action, uncertainty, and household scope.
- The initial HA sensor exposes a short safe summary; richer private details remain behind authorization-checked requests.
- An empty useful state is allowed.
- Correction and dismissal are durable backend commands even when first exposed through simple HA actions.

### Story 5.4: Deliver at the least disruptive permitted level

- Milestone C is limited to calendar-change ambient or briefing delivery.
- Timezone, quiet periods, confidence fallback, privacy suppression, review opportunities, and interruption caps are deterministic.
- HA notifications are an adapter; Kinward policy selects whether and what may be delivered.

# Epic 6: Approvals, Actions, and Household Coordination

## Goal

Every meaningful external action is authorized, approved where required, submitted once, reconciled, and recorded truthfully.

### Story 6.1: Implement the meaningful-action state machine

- Persist immutable attempts, optimistic versions, conflict keys, same-target locking, approval state, submission, unknown result, reconciliation, and terminal outcome.
- Submitted never means completed.
- Unknown attempts survive restart, backup, restore, account transition, assistant lifecycle, and deletion.

### Story 6.2: Enforce general multi-principal approval

- Approval objects identify principals, quorum, affected-principal approvals, expiry, invalidation, serialized responses, precedence, and exactly-once transition to acting.
- Minor actions apply requester-independent policy and exact named-adult quorum.
- Protected minor conversation and prepared-message bodies are excluded from adult approval by default.

### Story 6.3: Support bounded household coordination

- Coordination uses minimum-necessary context and complete delegation metadata.
- Accept, decline, counter, revoke, expire, cancel, complete, fail, and unknown outcomes close consistently for authorized participants.
- Specialist assistants remain disabled until delegation prerequisites pass.

### Story 6.4: Expose safe HA actions

- HA integration actions invoke application commands rather than persistence or providers directly.
- Selectors and response payloads expose only authorized minimum-necessary data.
- Action calls produce correlatable sanitized activity.
- Retry is blocked while same-target status is unknown.

# Epic 7: Home Assistant State and Device Actions

## Goal

Use HA as the physical-world authority while Kinward adds household language, policy, and reconciliation.

### Story 7.1: Map Kinward household concepts to HA resources

- Areas, devices, entities, and services are referenced by stable HA identifiers.
- Ordinary outputs use household language.
- Raw entity/service syntax is limited to authorized technical diagnostics.
- Mapping changes are versioned and invalid mappings fail safely.

### Story 7.2: Read fresh HA state through a provider-neutral port

- Observed state includes source identity, observation time, availability, and freshness.
- Unavailable or stale state cannot be represented as current.
- HA-dependent Kinward capability degrades without blocking unrelated core use.

### Story 7.3: Execute and reconcile HA mutations

- Identity, permission, resource authority, freshness, approval, and activity policy run before submission.
- Requested, submitted, observed, completed, failed, and unknown remain separate.
- Completion requires a fresh matching HA observation.
- Ambiguous or missing observations preserve unknown state until reconciliation.

### Story 7.4: Add purpose-specific HA automation hooks

- Kinward exposes documented events, actions, triggers, or conditions only when they express stable household intent.
- Hooks avoid leaking private details into HA automation traces.
- Generic entity-state automation remains possible for safe compact state.

# Epic 8: Administration, Activity, Health, and Diagnostics

## Goal

Operate Kinward through HA-hosted configuration and backend administration without exposing private content or requiring the retired standalone UI.

### Story 8.1: Provide configuration-entry options and reauthentication

- Integration options manage backend connection, profile mapping, safe polling/push behavior, and feature enablement.
- Reauthentication and reconnect preserve non-secret local configuration.
- Disablement is distinguishable from failure.

> **Superseded (2026-07-16, HA-native identity redesign):** "profile mapping" as an integration option
> is gone - there is no options flow and nothing to map. People sync automatically; admin role is
> derived automatically. The remaining real scope here is backend connection/reauthentication only.

### Story 8.2: Preserve Kinward administrative authority

- Authorized administrators manage people, invitations, assistants, child policy, household integrations, proactive defaults, backup, and health.
- Adults manage their own integrations, memory, preferences, and sharing without unrelated administrative access.
- Complex functions may initially use backend CLI/API workflows; lack of a custom panel does not weaken policy.

> **Superseded (2026-07-16, HA-native identity redesign):** "invitations" is dead (Story 3.2). "People"
> here now means the still-real remainder: `profile_kind`/privacy reclassification and pet CRUD (Story
> 3.1/3.3), not creating people (that's sync-only now). "Authorized administrators" (plural, by design)
> means every current HA admin - see cross-cutting rule 4; there is no single distinguished admin to
> authorize against.

### Story 8.3: Provide authorized activity

- Mandatory action and security records are append-protected and transactionally coupled.
- Filtering occurs after record/view authorization and leaks no unauthorized counts or facets.
- HA logbook is not the authority for Kinward private or meaningful-action activity.

### Story 8.4: Provide health and sanitized diagnostics

- Health is separate for application, database, model, memory, knowledge, calendar, Home Assistant, jobs, and backup.
- Every degraded state has an actionable next step or states none is needed.
- Diagnostics use allowlisted versions, capability states, and opaque correlations only.
- Prompts, bodies, secrets, credentials, unrestricted provider payloads, and protected high-cardinality labels are prohibited.

# Epic 9: Backup, Restore, Import, Retention, Deletion, and Recovery

## Goal

Preserve the whole household authority graph and all unresolved safety obligations across lifecycle operations.

### Story 9.1: Create versioned protected backups

- Backups contain a versioned manifest with included, excluded, protected, external, rebuildable, pending-observation, deletion, and unresolved-action metadata.
- Export requires confidentiality and integrity protection.
- Credentials excluded under policy are listed as reauthorization tasks.
- Backup archives are stored outside the live database volume.

### Story 9.2: Restore atomically and quarantine before activation

- Restore targets a clean same/compatible deployment.
- A point-in-time warning is shown before restore.
- The staged graph is validated in isolation and activated atomically.
- Failure leaves the existing valid household unchanged.
- Ownership, account binding, pending observations, deletions, unresolved actions, provider references, and quarantine are verified.

### Story 9.3: Import the documented minimum household data set

- Import uses a versioned allowlist for the documented five classes.
- Graph validation, duplicate handling, quarantine, disallowed-state rejection, safe reporting, and rollback are atomic.
- Legacy executable migrations are not required; `001_initial_single_household` remains the schema origin.

### Story 9.4: Enforce retention and deletion-pending lifecycle

- Named durable classes have documented retention.
- Ephemeral, invalidated, expired-security, and user-deleted content is removed as specified.
- Person deletion immediately shuts down authority, permits reconciliation-only access, preserves blockers, protects the sole administrator, and reaches atomic final disposition.

> **Needs redesign (2026-07-16, HA-native identity redesign):** "protects the sole administrator"
> assumed exactly one administrator; that assumption no longer holds - any number of people can be
> admins, derived live from HA. Whoever builds this story must redefine the invariant in terms that
> hold under multiple admins (e.g. "a deletion/demotion in HA can never silently leave the household
> with zero admins" is the closest equivalent to today's rule) rather than protecting one named person.
> Also note: Kinward never deletes a `PersonRecord` on its own when a `person` entity disappears from
> HA sync (see Story 3.1's note) - actual deletion is this story's explicit, auditable action, not a
> side effect of sync.
>
> **Partially implemented (2026-07-16):** the redesigned invariant itself is built -
> `domain/admin_invariant.validate_admin_removal` blocks exactly the "would leave zero admins" case,
> not "isn't the one designated admin" - and `application/person_deletion.delete_person` wires it into
> an explicit, auditable deletion action (`DELETE /api/v1/integration/people/{id}`, admin-only,
> transactional, records an `ActivityRecord`). Tests in `tests/test_admin_invariant.py` and
> `tests/test_person_deletion.py`. Still open, and out of this pass's scope: documented per-class
> retention enforcement, the deletion-pending/reconciliation-only access overlay, and blocker
> preservation - this only covers the admin-invariant redesign the previous pass flagged, not the rest
> of the story.
>
> **Needs redesign (2026-07-16, remainder scoping pass):** "deletion-pending", "reconciliation-only
> access", and "blocker preservation" as written come from `AD-01 — Local account authentication
> [DORMANT]`, which is explicitly parked for the HA-native path (Kinward has no session/account of its
> own to place into an overlay state). `SOLUTION-DESIGN.md`'s "Account baseline" section still
> describes that overlay verbatim with no dormant marker - treat `ARCHITECTURE-SPINE.md`'s AD-01
> dormant status as controlling; that stale section should get the same marker (tracked separately,
> not part of this doc-only pass).
>
> The underlying obligation that survives the pivot is not about account authority at all - it's
> `AD-13` ("required deletion erases or crypto-shreds protected payload and appends a disposition
> event while retaining only the permitted sanitized envelope/tombstone and minimum reconciliation
> state") and `AD-20` ("unknown results survive restart/backup/restore and block retry ... until
> reconciliation"). Both are properties of the *action/activity records themselves*, not a person
> lifecycle state. Concretely: **"blocker preservation" on person deletion means checking for any
> unresolved (`submitted`/`unknown`) meaningful-action attempts tied to that person before deleting,
> and retaining a sanitized tombstone rather than silently losing them** - there is no separate
> "reconciliation-only access mode" to build; there's nothing left to grant access to once the person
> is gone.
>
> **Decided (2026-07-16):** `application/person_deletion.delete_person` does a hard
> `session.delete(person)` and relies on SQLAlchemy FK `ondelete` behavior for cleanup.
> `ActivityRecord.person_id` is `ondelete="SET NULL"` (tombstone-shaped - the activity entry survives,
> only the person reference is cleared), while `AssistantRecord.owner_person_id`, `TopicRecord.person_id`,
> and `MemoryIndexRecord.person_id` are all `ondelete="CASCADE"` - deleting a person today immediately
> and irreversibly hard-deletes their personal assistant and their entire conversation/memory history in
> the same transaction. This is the intended disposition for now - a full hard delete of everything tied
> to the person is fine as-is; no tombstone/grace-period work is needed here. See the new
> cross-instance-migration horizon below for the actual scenario this data would otherwise need to
> survive.
>
> **Real dependency gaps, not just naming problems:**
> - "Blocker preservation" needs something to check against. `ApprovalRecord` exists in
>   `persistence/models.py` but has zero call sites anywhere in the codebase - Epic 6's meaningful-action/
>   approval machinery (AD-20) isn't built yet. Until it exists, a pre-deletion blocker check is
>   vacuously true and can't be meaningfully implemented.
> - "Named durable classes have documented retention" has exactly one numerically-decided rule today:
>   `AD-25`'s fixed 30-day `pending-inferred-observation` expiry - and that knowledge-state lifecycle
>   itself isn't implemented (`memory/contracts.py` has `proposed`/`confirmed`/`retired` only, no
>   expiry field, no scheduled job; `worker.py` is a heartbeat-only shim with no cleanup logic).
>   Everything else falls under the "Open product safe interims" line in `ARCHITECTURE-SPINE.md`:
>   *"named durable classes have no automatic deletion while required/user deletion remains"* - i.e.
>   no other numeric retention period has been decided. `domain/lifecycle.py`'s
>   `BOOTSTRAP_RECORD_LIFECYCLES` table already sketches a per-record-type taxonomy
>   (`classification`/`backup_eligible`/`import_eligible`/`restore_disposition`/`deletion`) but nothing
>   imports it - it's the right seam to wire retention into once durations are decided, not something
>   to invent numbers for unilaterally here.
> - Acceptance criteria referencing backup/restore survival (`epics.md:516`, `528`) can't be verified
>   yet either way: Stories 9.1-9.3 (backup/restore/import) have no implementation at all - no code
>   under `application/` or `api/` for any of the three.
>
> **Recommended buildable-now slice**, once product signs off on this scoping: wire
> `BOOTSTRAP_RECORD_LIFECYCLES` into a real per-class retention disposition doc. Defer the
> blocker-preservation check until Epic 6's approval/meaningful-action machinery exists, and defer
> backup/restore verification until Stories 9.1-9.3 exist. `delete_person`'s CASCADE hard-delete
> behavior is confirmed correct as-is and needs no further work. No code changes in this pass - this
> is scoping only, pending sign-off.

> **Deferred to v2 (2026-07-16, non-committed horizon):** cross-instance Home Assistant re-binding.
> Scenario: the household's HA instance is lost or rebuilt from scratch (corruption, hardware
> replacement) but the Kinward deployment/database survives intact. The operator recreates their
> `person` entities in the fresh HA instance and wants to re-attach the surviving Kinward household
> (people, pets, assistants, topics, memory, activity - everything) to that new HA instance rather than
> starting over. This is **not** the same capability as Stories 9.1-9.3 (single-deployment backup/
> restore/import of a point-in-time snapshot) - it's re-establishing the identity link between an
> already-intact Kinward household and a different/rebuilt HA instance.
>
> Why this doesn't work today: `application/people_sync.sync_people` matches purely on
> `PersonRecord.ha_person_id`, the durable id from HA's own person registry
> (`services/kinward/src/kinward/application/people_sync.py:38-40`). A rebuilt HA instance generates
> brand-new registry ids even for identically-named `person` entities, so today's sync would treat
> every recreated person as new and silently orphan every existing `PersonRecord` (and everything
> owned by it) rather than reattaching to it.
>
> Out of scope for this pass and for Story 9.4 generally - this needs its own future PRD and
> architecture amendment (per `ARCHITECTURE-SPINE.md`'s "Non-committed horizons" convention) covering
> at minimum: an explicit admin-driven rebind action (never automatic/inferable from name matching
> alone, to avoid silently binding the wrong person), export/import of the rebind mapping, and how it
> composes with the admin invariant and Stories 9.1-9.3 once those exist. Tracked in
> `ARCHITECTURE-SPINE.md`'s "Non-committed horizons" list.

### Story 9.5: Recover the same administrator profile safely

- Portable account-access material and excluded recovery artifacts are explicitly classified.
- Recovery restores access to the same administrator profile without database editing.
- Post-restore tests verify reauthorization, quarantine, token invalidation, deletion restrictions, and unresolved-action blocking.

> **Superseded (2026-07-16, HA-native identity redesign):** there is no local Kinward account or
> password to recover - HA is the sole login (AD-01 marked dormant in ARCHITECTURE-SPINE.md).
> Recovering access to an admin's login is entirely Home Assistant's own responsibility, outside
> Kinward's remit; nothing in this story is built or planned unless a non-HA standalone client is ever
> built (Story 10.4).

# Epic 10: Evidence-Gated Extensions

## Goal

Expand presentation only after the household trial demonstrates a concrete need.

### Story 10.1: Evaluate custom Kinward cards

- A custom card is authorized only when core cards cannot represent a validated daily-use need safely.
- Cards remain thin clients over safe entities/actions or authorization-checked requests.
- No card imports unsupported HA internal frontend components.
- Accessibility, mobile behavior, stale/error states, and privacy are tested.

### Story 10.2: Evaluate a custom dashboard strategy

- A strategy is introduced only when generated per-person/per-context composition provides demonstrated value.
- It uses documented HA strategy registration and produces standard dashboard configuration.
- Manual HA customization and a stable fallback dashboard remain available.

### Story 10.3: Evaluate a Kinward administration panel

- A panel is introduced only for administration that cannot be handled adequately through config flow, options flow, actions, and backend tooling.
- It is not required for everyday assistant use.
- It preserves Kinward authorization independently of HA navigation visibility.

### Story 10.4: Reconsider standalone clients

- A standalone web/mobile client requires an explicit future PRD and architecture amendment.
- Evidence must show a need such as non-HA households, appliance-grade shell control, or workflows HA cannot host.
- The HA integration and backend remain first-class even if another client is later added.

## 5. Story 1.1–1.6 historical disposition

| Previous story | Status under this plan |
| --- | --- |
| 1.1 | Retained and revalidated as new Story 1.1. |
| 1.2 | Retained as new Story 1.2. |
| 1.3 | Backend/privacy portions salvaged; standalone renderer requirements superseded. |
| 1.4 | Kinward layout resolver product requirement retired. |
| 1.5 | Five-surface verification replaced by HA-native end-to-end verification. |
| 1.6 | Cancelled as obsolete before completion. |

## 6. Immediate execution queue

The next implementation work is intentionally narrow:

1. Story 1.3 — pinned HA 2026.7.2 development profile.
2. Story 1.4 — custom integration and config flow.
3. Story 1.5 — initial safe entities.
4. Story 1.6 — importable core-card dashboard.
5. Story 1.7 — install and use the household slice.
6. Story 2.1/2.2 — HA user mapping and conversation entity.

No custom card, custom dashboard strategy, custom panel, or standalone frontend work may block this queue.

## 7. Definition of the first usable release

The first usable release is reached when:

- Kinward starts from a clean checkout with SQLite and no optional providers.
- HA 2026.7.2 installs and configures the Kinward integration through the UI.
- One household and its initial profile/assistant graph exist atomically.
- The Kinward dashboard shows HA person status and truthful Kinward summaries using core cards.
- One authorized user can submit a private assistant request through Assist.
- Backend, HA, model, memory, knowledge, and calendar degradation are shown separately.
- Server-side privacy tests prove HA admin status cannot disclose another adult's private data.
- No standalone Kinward frontend is required.
