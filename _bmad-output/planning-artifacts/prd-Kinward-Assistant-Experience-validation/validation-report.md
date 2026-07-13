# Validation Report — Kinward Assistant Experience

- **PRD:** `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md`
- **Rubric:** BMAD PRD Quality Rubric
- **Run at:** 2026-07-13T17:37:47+00:00
- **Grade:** Poor

## Overall verdict

The PRD has a coherent product thesis, a useful requirement skeleton, and strong alignment on the broad single-household, privacy-conservative, web/PWA-first direction. It is not ready to be finalized or used as the sole basis for architecture and epic decomposition because release boundaries, source authority, shared-assistant and youth-privacy invariants, action policy, degraded behavior, recovery scope, and measurable acceptance remain unresolved.

The adversarial pass reinforces the rubric verdict: several gaps occur at security and architecture boundaries where downstream authors would otherwise have to invent product policy. One public-repository safety issue also requires immediate correction.

## Dimension verdicts

- Decision-readiness — thin
- Substance over theater — adequate
- Strategic coherence — adequate
- Done-ness clarity — thin
- Scope honesty — thin
- Downstream usability — thin
- Shape fit — adequate

## Findings by severity

### Critical (1)

**Downstream usability — Journey fixtures use apparent real household identities** (§6, lines 134-174)

The journeys repeatedly use `Marc` and `Lisa`; `Marc` matches the named author, so the examples are not obviously fictional and violate the repository rule against real household names. UJ-4 also lacks a named protagonist, and no journey exercises teen or child privacy.

Fix: Replace all household identities with clearly fictional names, give every journey a named fictional protagonist and role, and add teen and child journeys covering age policy, privacy, and account/no-account behavior.

### High (12)

**Strategic coherence — The PRD declares the wrong authority set** (frontmatter lines 6-10; §10, lines 378-384)

The source list omits the authoritative salvage matrix and includes `docs/pivot/migration-status.md`, which is not an authoritative product-direction document. This allows status evidence to override migration rules.

Fix: Replace the migration-status entry with `docs/pivot/salvage-matrix.md`, use repository-relative paths for all four authoritative sources, and state that legacy planning and status reports are non-authoritative evidence.

**Substance over theater — “Foundation already accepted” lacks authoritative acceptance evidence** (§9, lines 329-340)

The four authoritative sources do not certify the listed foundations as accepted, while the salvage matrix requires explicit behavior documentation, assumption removal, Kinward contracts, focused tests, minimal migration, and checks.

Fix: Rename Milestone A to a baseline or planned milestone unless each item links to inspectable acceptance evidence; apply the six-step salvage gate to every retained subsystem.

**Decision-readiness — Open product decisions are incorrectly labeled non-blocking** (§12, lines 396-406)

Authentication/recovery, model capability, calendar synchronization, storage boundaries, identity signals, export/restore guarantees, and proactivity thresholds define acceptance behavior for Milestones B and C.

Fix: Turn §12 into a decision register with owner, due milestone, affected IDs, safe interim default, and blocking status; resolve each item before affected stories become ready.

**Decision-readiness — Completion and release gates are ambiguous** (§8.2, line 305; §13, lines 408-416)

“First household production milestone,” “first milestone,” and “first planned milestone” do not identify Milestone B or C, and PRD approval is conflated with implementation and production readiness.

Fix: Define separate named gates for PRD approval, Milestone B implementation readiness, Milestone C first usable release, and household production readiness.

**Strategic coherence — The one-household invariant is not enforced across all paths** (§5.3, lines 121-130; FR-001/002; §7.9)

FR-002 blocks a second household only through the normal setup flow, leaving APIs, jobs, imports, restore, and persistence unconstrained and allowing tenant-routing remnants.

Fix: Require database, service, background-work, import, and restore paths to reject a second household, and prohibit tenant IDs, tenant routing, control-plane ownership, and commercial-role semantics in current contracts.

**Strategic coherence — The shared fallback assistant has no domain contract** (FR-011–014, FR-022, FR-031–038)

The PRD defines personal-assistant ownership but not the no-owner shared fallback, its limited capabilities, memory boundary, lifecycle, or routing role.

Fix: Add requirements stating that the shared fallback has no personal owner, is household-scoped, handles only household-safe capabilities, cannot access unrestricted personal memory, and yields to a resolved personal assistant when policy allows.

**Strategic coherence — Teen and child privacy is implementation-defined** (§4.3–4.4; FR-035/037; FR-072–075)

An undefined household-policy exception can weaken teen privacy, adult-only language in FR-037 leaves youth memory exposed to interpretation, and child profiles without accounts have no deterministic behavior.

Fix: Define youth privacy separately from administration, narrowly define shareable household-safe coordination facts, enforce youth resource authorization server-side, and specify behavior for child profiles without accounts or assistants.

**Done-ness clarity — Identity-confidence outcomes lack a normative decision table** (FR-032–034; NFR-003/014; §12)

The requirements name inputs and test states but omit the source-defined high/medium/low/multiple-person outcomes. Tests could cover every state while implementing incompatible disclosure behavior.

Fix: Specify confidence-state outcomes independently of signal implementation, including generic medium-confidence responses, fallback behavior, authenticated handoff, immediate removal on confidence drop, and ambient reset on timeout.

**Done-ness clarity — External-action authority and approvals are not executable contracts** (FR-051–060; FR-065/069; NFR-009/019)

Terms such as “meaningful,” “explicit limits,” and “applicable approval” do not define the authorized principal, scope, approver, re-check behavior, state transitions, duplicates, or revocation.

Fix: Define an action-policy contract and state machine for observe, suggest, prepare, confirm, and bounded autonomous action, including execution-time authorization/state checks, terminal states, idempotency, reversal, and mandatory activity classes.

**Strategic coherence — Milestone sequencing contradicts the required first cross-surface slice** (§9, lines 329-360)

Milestone B delivers only personal mobile, shared displays arrive in C, and tablet/desktop layouts are absent. The UX and rebuild plan require the first frontend slice to validate one registry across mobile, tablet, desktop, shared kitchen, and shared living-room surfaces.

Fix: Restore the mock-backed five-surface foundation slice before the live assistant slice, or explicitly justify the narrowing while retaining acceptance fixtures for every required surface context.

**Scope honesty — The initial release boundary cannot be reconstructed** (§5.1–5.2; §9)

The “initial usable product” is not tied to a milestone, and later-scope capabilities remain mixed into an untagged requirement catalog.

Fix: Name the first usable release, tag every FR/NFR with its required milestone, and distinguish contract/schema readiness from user-visible delivery.

**Scope honesty — Backup and recovery are committed while their data contract remains open** (§5.1, line 106; FR-079–083; NFR-010/011; §12)

The PRD does not identify which people, assistants, personality, conversations/topics, memories, integration settings, Home Assistant mappings, layouts, approvals, activity, credentials, and configuration survive a clean rebuild.

Fix: Define the authoritative and regenerable data inventory, credential treatment, export schema/versioning, compatibility and failure behavior, household RPO/RTO or equivalent guarantee, and clean-deployment restore test that re-verifies ownership and privacy.

### Medium (7)

**Decision-readiness — Success measures are not operationally measurable** (§3)

Terms such as “voluntarily use,” “recurring real needs,” “important,” and “normal use” lack targets, windows, baselines, and measurement methods.

Fix: Add definitions, targets, observation windows, instruments, and release relevance for primary measures and counter-metrics.

**Done-ness clarity — Performance and accessibility NFRs lack quantitative bounds** (NFR-012–019)

“Promptly,” “immediately,” “room-distance readability,” and “appropriately large” have no supported conditions or pass/fail thresholds.

Fix: Add p95 timing targets, maximum private-content removal latency, minimum target sizes, viewing-distance/type-size checks, and supported test conditions.

**Scope honesty — Kinward Control “foundations” conceal broad CRUD and editing scope** (§5.1, line 105; FR-071–076; §5.2, line 115)

The PRD does not distinguish read-only health, basic forms, full management, or deferred editing for each Control area.

Fix: Add an initial capability matrix by area and operation: read, create, update, delete, preview, or deferred.

**Downstream usability — Canonical vocabulary and policy predicates are undefined** (§4; §7)

The PRD alternates among person, user, household member, owner, participant, and audience and does not normatively define meaningful action, durable fact, observation, topic, privacy state, or identity confidence.

Fix: Add a normative glossary and domain relationship summary, with canonical domain terms and UI-only synonyms clearly separated.

**Downstream usability — Requirements lack source, journey, milestone, risk, and verification traceability** (§7–§9)

Clean IDs exist, but downstream authors cannot prove source coverage, detect orphan requirements, or identify the release and verification level without rereading all sources.

Fix: Add requirement metadata or a compact traceability table covering authoritative source, journey, target milestone, risk, and verification level.

**Reliability — Optional inference, memory, and knowledge degradation lacks a functional fallback contract** (FR-023–025; FR-062/063; NFR-007/008/012/015)

The PRD does not define boot and local behavior without model inference, or whether unavailable memory writes queue, fail visibly, remain local, or are discarded.

Fix: Define the provider-neutral degraded contract for boot, auth, onboarding, admin, local surfaces, unavailable retrieval/indexing, durable-write claims, health reporting, and recovery behavior.

**Integration safety — Home Assistant state freshness is unspecified during degradation** (FR-062–070; NFR-007/008/012/015)

Cached imported state can be displayed as current or used for an action when Home Assistant is unavailable.

Fix: Require availability/freshness metadata, prohibit current-state claims when stale, block actions that require unverifiable state, and avoid claiming completion without authority confirmation.

## Mechanical notes

- FR IDs are contiguous and unique from `FR-001` through `FR-083`.
- NFR IDs are contiguous and unique from `NFR-001` through `NFR-024`.
- Journey IDs are contiguous and unique from `UJ-1` through `UJ-7`.
- The PRD has no normative glossary, assumptions register, requirement-level milestone tags, or requirement-to-source/verification mapping.
- No `[ASSUMPTION]` or `[NOTE FOR PM]` markers are present despite unresolved product-policy decisions.

## Reviewer files

- `review-rubric.md`
- `review-adversarial-general.md`
