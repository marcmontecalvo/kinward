# Adversarial PRD Review (Re-Review): Kinward Assistant Experience

## Review Basis

Re-review of the current 965-line PRD (`_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md`) against only the four authoritative sources:

- `_bmad-output/planning-artifacts/product-brief-Kinward-Assistant-Experience.md`
- `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md`
- `docs/pivot/single-household-pivot-and-rebuild-plan.md`
- `docs/pivot/salvage-matrix.md`

`docs/pivot/migration-status.md` is not authoritative and was not used. The prior adversarial review was used only to disposition prior findings; resolved issues are not repeated as current findings. The revisions that addressed the prior high-severity findings were attacked on their merits.

## Verdict

**Materially improved but not yet ready for architecture or epic decomposition.** All seven prior high-severity findings were structurally addressed, and five prior focus areas are fully resolved. However, the group-mode fix introduces a `selected-share` exception that its own audience caveat makes unsafe, the privacy-classification taxonomy is now internally inconsistent across Sections 7, 8, and 10, and the new decision registers assign due dates that postdate Milestone A work that depends on them. One more focused revision pass should close the document.

## Severity Counts

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 2 |
| Medium | 10 |
| Low | 4 |
| **Total** | **16** |

## Current Findings

### 1. High: The group-state `selected-share` exception is unsatisfiable under the rule's own audience caveat and reopens the disclosure risk the fix was meant to close

**Exact current PRD lines:** 392 (Section 10), 328 (`selected-share` definition), 248 (Section 6.2 group test)

**Impact:** Line 392 categorically prohibits `private-person` and `private-child` disclosure in `group` state and prohibits "anything derived from private memory," but simultaneously permits rendering "a `selected-share` that is valid for every detected audience member." The same sentence then states "presence detection is never treated as proof that every audience member is known." If detection can never establish the audience, no `selected-share` can ever be proven valid for every audience member — the permission is either dead text or, in practice, will be implemented against detected presence and disclose selected-share content (which originates from a person's private data, per line 287) to undetected people. This recreates exactly the group-mode leak the revision was written to eliminate, and Section 6.2's zero-disclosure group test cannot be authored deterministically against a self-contradictory rule.

**Concrete fix:** In `group` state, permit `household-shared` rendering only; route `selected-share` and all private content through private-device handoff. If a group-visible selected-share is genuinely wanted, require that every detected person holds a currently `verified` session on that surface and that the surface policy explicitly opts in — and state that any unverified or additional presence downgrades to household-shared only. Also resolve the overlap between "anything derived from private memory" and `selected-share` (state that an explicit sharing act reclassifies the shared statement, per Section 8.2, and only the reclassified statement may render).

**Authoritative basis:** Product brief §Identity and Privacy ("Multiple people: group context and no private-memory disclosure"); UX spec §Shared Household Display Privacy (default to household-safe; send private content to a personal device) and §Anti-Patterns ("Shared displays exposing personal email or calendars").

### 2. High: The privacy-classification taxonomy is internally inconsistent across Sections 7, 8, and 10

**Exact current PRD lines:** 291 (`teen` privacy class), 306 (`private-to-child` / `shared-with-guardians`), 324-331 (Section 8.1 data-class enumeration), 392 (group prohibition names only `private-person` and `private-child`), 940 (PD-02 interim keyed to `shared-with-guardians`)

**Impact:** Section 8.1 mandates that "every stored or transmitted item must have an effective data class" and enumerates exactly six classes. Section 7.4 then mandates that every child durable fact be classified `private-to-child`, `shared-with-guardians`, or `household-shared` — `private-to-child` is a naming drift from 8.1's `private-child`, and `shared-with-guardians` does not exist in the enumeration at all, yet PD-02's safe interim behavior is keyed to that nonexistent class. Section 7.3 declares a `teen` privacy class with no stated mapping to any 8.1 data class; consequently the group-state categorical prohibition (line 392), which names only `private-person` and `private-child`, does not literally cover teen private data if teen content is its own class. FR-032, FR-029, NFR-003, and NFR-004 all require automated tests over these classes; the tests cannot be written consistently against three divergent taxonomies, and a story-level "reasonable interpretation" here is a privacy defect waiting to happen.

**Concrete fix:** Establish one normative mapping: either extend Section 8.1 or state explicitly that `private-to-child` is the same class as `private-child`, that `shared-with-guardians` is a constrained `selected-share` whose named recipients are the guardians, and which data class teen private content uses (e.g., `private-person`). Update line 392 to close over the complete class set (or phrase the prohibition as "everything except `household-shared`"), and align PD-02's interim wording to the canonical class names.

**Authoritative basis:** Product brief §Identity and Privacy, §Teen household member, §Child household member; UX spec acceptance criterion 14 and anti-pattern "One family AI containing all private memory."

### 3. Medium: UJ-3's shared-display outcome contradicts the coordination-statement alternative introduced in Section 4.1.2

**Exact current PRD lines:** 102, 110, 113, 115 (Section 4.1.2), 194 (UJ-3 shared-display outcome)

**Impact:** Section 4.1.2 now allows the shared fixture topic to be either explicitly `household-shared` **or** a `private-person` topic "represented by a separately reviewable, minimum-necessary household-safe coordination statement explicitly approved for sharing" (consistent with Section 8.2). UJ-3 still states the household display may show a generic item "only when the topic is household-shared," which forbids the second branch outright. Additionally, steps 5, 7, and 8 and line 115 use "the explicitly shared topic" and "unshared" without defining that an approved coordination statement makes a topic "shared" for slice purposes — under the alternative branch, both fixture topics are `private-person`, and "unshared" is distinguishable only by the presence of an approved statement, which no requirement defines. Story authors can read the slice two contradictory ways.

**Concrete fix:** Define "shared" for the slice as: the topic is `household-shared`, or a coordination statement derived from it has been explicitly approved for household sharing per Section 8.2 — and "unshared" as neither. Amend UJ-3's shared-display outcome to permit the generic item when either condition holds and to state that the rendered payload contains only the topic's household-safe representation or the approved statement.

**Authoritative basis:** Product brief §Product Thesis 4 (shared surfaces privacy-conservative); UX spec §Shared Household Display Privacy ("summarizes generically") and §Coordination Request (privacy-filtered proposal is a legitimate shared representation).

### 4. Medium: Decision-register due dates postdate the Milestone A work that depends on them

**Exact current PRD lines:** 711 (Milestone A content), 494 and 772 (FR-002 at Milestone A), 917 (AD-01 due Milestone B start), 918 (AD-02), 922 (AD-06)

**Impact:** Milestone A's content includes the bootstrap API (FR-002 creates household, administrator profile, **account binding**, and first assistant, and Section 17.4 gates FR-002 at Milestone A) plus "neutral memory/knowledge contracts" and "provider adapters." Yet AD-01 (authentication, session, invitation, and recovery mechanism — which determines what an account binding is), AD-02 (model-provider contract), and AD-06 (storage split among Kinward, Honcho, and LLM-Wiki) are due only at "Milestone B start." Milestone A therefore either implements bindings, contracts, and adapters ahead of their governing decisions — inviting rework or a de facto decision made inside a story, which Section 19 explicitly forbids — or the traceability milestone assignments are wrong. The salvage acceptance rule requires contracts to be defined *before* a subsystem migrates, so adapter salvage in A under undecided contracts also strains the Milestone A exit gate.

**Concrete fix:** Pull AD-01 (at least the account-binding shape), AD-02 (at least the adapter contract surface), and AD-06 forward to "Milestone A start," or split each into an A-scoped contract decision and a B-scoped mechanism decision; alternatively move FR-002's account-binding element and provider-adapter acceptance into Milestone B and shrink Milestone A content accordingly.

**Authoritative basis:** Salvage matrix §Acceptance rule item 3 ("Required contracts are defined in Kinward" before migration); rebuild plan §Execution Order (Phase 1 skeleton and Phase 2 salvage precede Phase 4 household foundation, but salvage still presupposes approved contracts).

### 5. Medium: Member (non-administrator) post-restore access is neither specified nor verified

**Exact current PRD lines:** 629-630 (Section 14.3), 645 (FR-085), 646 (FR-086), 598 (excluded reusable secrets), 232 (UJ-9)

**Impact:** The new account-access contract gives the administrator a documented secure recovery procedure (FR-085) and verifies it (FR-086), but members get one sentence — "Members re-establish authentication against their existing restored profiles" — with no required procedure. All pre-restore invitations are invalid, reusable authentication secrets are excluded, and the portable list's recovery-material example is scoped to the administrator. The only implied member path is a *new* invitation, which Section 14.3 neither authorizes nor constrains: binding a member's new account to their existing profile is not "a different person's profile," so the no-rebinding rule doesn't govern it, and nothing defines supersession of the profile's prior orphaned account record. FR-086 verifies binding integrity and admin recovery but never verifies that any member can actually regain access, so INV-8 ("recoverable from its own backups, including account access") can pass verification while every non-admin is locked out.

**Concrete fix:** Require a documented member re-access procedure (post-restore invitation to the existing profile, or portable member recovery material where the architecture declares it safe), define supersession/invalidation of a profile's prior account credentials when a new binding is established, and extend FR-086 to verify member re-access for at least one non-administrator profile.

**Authoritative basis:** Product brief §Deployment model (household-owned data and configuration; no SaaS backend to fall back on); rebuild plan §Database reset (preserve people and assistants through explicit export/import).

### 6. Medium: Whether `autonomous` authority machinery is Milestone C or D scope is left ambiguous

**Exact current PRD lines:** 408 and 419 (Section 11 `autonomous` rules), 552 (FR-045), 559 (FR-052 at Milestone C per line 822), 264 (Section 6.4 zero-autonomous counter-metric), 268-272 (Section 6.5)

**Impact:** FR-052 (Milestone C) requires implementing "every authority rule in Section 11," which includes the full `autonomous` grant contract (named bounded policy, limits, review date, revocation). FR-045 and Section 6.4 simultaneously mandate that autonomous-action delivery remain disabled until Milestone D, and Section 6.5's reversal metric gates D. The PRD never states whether Milestone C must build the autonomous grant/policy/revocation mechanism (disabled) or whether the mechanism itself is D scope and FR-052 is satisfied vacuously in C because no autonomous grants can exist. This is the same class of C/D scope ambiguity the revision set out to eliminate for proactivity, left open on the action-authority side; epic teams will split it inconsistently.

**Concrete fix:** State explicitly in FR-052 or Section 16 that during Milestone C no `autonomous` grant can be created or activated, that Section 11's autonomous rules are enforced as "always deny," and that the grant mechanism, controls, and Section 6.5 measurement ship in Milestone D.

**Authoritative basis:** Product brief §Proactivity and Trust (authority progresses through observe → … → act autonomously within explicit limits — a progression, not a single release).

### 7. Medium: Guardian review of child data remains contradictory between Section 7.4 and PD-02, and the child account path is still undefined

**Exact current PRD lines:** 307 (Section 7.4 review sentence), 306, 533 (FR-032, Milestone C), 940 (PD-02), 217-220 (UJ-7 "A child account")

**Impact:** Section 7.4 still grants administrators review of child facts and activity "necessary for care, safety, school, transportation, health, and household responsibilities" without defining precedence over `private-to-child`, who decides necessity, or what audit trail exceptional access produces. PD-02's interim behavior ("no guardian-review implementation until resolved; only `shared-with-guardians` facts visible") is a good containment, but it contradicts the plain text of 7.4, and FR-032 (Milestone C) requires implementing "Section 7" as written and covering it with automated tests — an unimplementable instruction while PD-02 is open, and PD-02 covers only default categories, not the necessity/audit questions. Separately, UJ-7 depends on a child *account*, and no FR defines child account creation or binding distinct from adult invitation (FR-003 covers profiles; FR-005/006 cover invitations generically).

**Concrete fix:** Rewrite 7.4's review sentence to subordinate it to PD-02's resolution ("Administrators may review only facts and activity in guardian-visible categories established under PD-02"), add precedence, necessity-decision principal, minimum-necessary disclosure, and append-protected audit for any exceptional access, and either add a child-account onboarding/binding FR or explicitly defer child accounts (and re-scope UJ-7 to a profile-plus-supervised-device model) for Milestone C.

**Authoritative basis:** Product brief §Child household member (strong privacy and permission boundaries); UX spec §Desired Emotional Response ("respected rather than monitored") and §Child guidance against presenting hidden monitoring as privacy.

### 8. Medium: Action authority still has no grant/approval/revocation principal matrix

**Exact current PRD lines:** 410-422 (Section 11 requirements), 414 (capability maxima "per person, action category, and integration"), 560 (FR-053 "authority basis")

**Impact:** Carried from the prior review and not addressed by the revisions or either decision register: the PRD never states who may grant or revoke a capability maximum or bounded autonomy (adult, administrator, guardian, represented person, integration owner), or who is an eligible approver when an action affects another person. Recording an "authority basis" in the activity record does not establish that the basis was valid, and no AD/PD entry owns this gap, so it will be decided silently inside stories — exactly what Section 19's closing rule forbids.

**Concrete fix:** Add a grant/approval/revocation matrix keyed by privacy class, represented person, action category, affected person, and integration ownership; require execution-time validation that grantor and approver still hold authority; or, minimally, add a register entry with owner, due milestone, and a safe interim behavior (e.g., "only the affected person's own adult account may grant, and any action affecting another person requires that person's approval").

**Authoritative basis:** Product brief §Proactivity and Trust (every meaningful action must make clear whether approval was required and on whose behalf it acted); UX spec §Kinward Control (Permissions and approvals) and §Activity ("why it was allowed").

### 9. Medium: Inference-provider degradation is still less defined than memory and Home Assistant degradation

**Exact current PRD lines:** 135 ("working assistant conversation path"), 159 (exclusion of mandatory cloud inference), 222-226 (UJ-8 names only memory and Home Assistant), 702 (NFR-034 includes model health), 918 (AD-02 interim)

**Impact:** Carried and only partially mitigated by AD-02's interim ("requests terminate visibly on provider failure"). No FR defines behavior when no model provider is configured at all, whether accepted requests fail or remain pending on outage, or the minimum configured inference capability required for the Milestone C "working assistant conversation path" gate. FR-027 and FR-067 give memory and Home Assistant explicit degradation requirements; the model capability — the one dependency the whole product needs — has none, leaving either a hidden mandatory dependency or an undefined release gate.

**Concrete fix:** Add an FR mirroring FR-027/FR-067 for the inference capability: absent/unavailable/rate-limited/mid-stream-failure behavior, unsubmitted actions remain unsubmitted, no fabricated output, health and recovery guidance names the capability; and define the minimum configured inference capability required to enter the Milestone C pilot. Extend UJ-8 (or add a journey) to cover the inference-provider-down case.

**Authoritative basis:** Product brief §Deployment model (cloud inference "may be used where desired") and §Product Boundaries; rebuild plan §Architecture Direction (boot without optional peers, report degraded capability clearly).

### 10. Medium: Specialist assistants still have no lifecycle requirement or milestone

**Exact current PRD lines:** 53-55 (Section 3.2), 345-351 (Section 9.1), 505 (FR-010), 655 (NFR-004), Sections 4.3 and 16 (no lifecycle entry)

**Impact:** Carried, unchanged. The PRD defines specialists, bounds their access, and requires tests over the specialist boundary (NFR-004, Milestone C), but no FR lets an owner create, select, retire, or delete one and no milestone or explicit deferral covers the lifecycle — so NFR-004 requires testing a boundary no requirement ever brings into existence, and architecture must guess assistant cardinality and retirement semantics.

**Concrete fix:** Either assign a minimum specialist lifecycle (create, invoke, retire; no implicit private-memory merge on retirement or router change) to a named milestone, or add it to Section 4.3 later scope explicitly and scope NFR-004's specialist coverage to the contract level until then, while requiring schema compatibility for multiple owner-bound assistants now.

**Authoritative basis:** Product brief §Assistant Model ("A user may also create specialist or temporary assistants"); salvage matrix (Personal assistants: "verify multiple assistants per user"); rebuild plan §Likely Salvage ("Multiple assistants per user").

### 11. Medium: Prepared approvals and activity records still omit "what information was used"

**Exact current PRD lines:** 416 (prepared mutation contents), 560 (FR-053 record fields), 547 (FR-043)

**Impact:** Carried, unchanged. The brief requires every meaningful action to make clear "what information was used." FR-053's activity record lists actors, authority, approval, integration, results, and undo — but not the privacy-filtered source categories or user-correctable facts the action relied on, and FR-043 applies to surfaced items generally rather than requiring the approval or final action record to retain provenance. A user cannot identify that an action was based on a stale or wrong fact, undermining the correction loop the product depends on.

**Concrete fix:** Require prepared approvals (Section 11) and final activity records (FR-053) to include privacy-filtered source categories and referenced user-correctable facts, excluding another person's private data, secrets, prompts, and hidden reasoning.

**Authoritative basis:** Product brief §Proactivity and Trust ("what information was used"); UX spec §Explain-on-Hold and §Activity.

### 12. Medium: "Exactly one household" still lacks enforcement-path requirements

**Exact current PRD lines:** 493 (FR-001), 636 (FR-076), 747 (INV-1)

**Impact:** Carried, partially improved: INV-1 now makes single-household a governing invariant that epics must preserve, and FR-076 protects restore-over-existing-state. But no requirement rejects creation of a second household through APIs, background jobs, imports, or restore-to-populated-deployment, and nothing prohibits tenant-routing or commercial-role fields in current Kinward contracts. A nominally single-household UI over a latent multi-tenant core would satisfy every literal FR.

**Concrete fix:** Extend FR-001 (or add an FR) to require rejection of a second household on every persistence, service, job, import, and restore path, and prohibit tenant-ID, tenant-routing, entitlement, and support-operator fields in Kinward contracts absent an approved non-tenancy justification.

**Authoritative basis:** Rebuild plan §Infrastructure simplification ("Remove tenant IDs, control-plane services, support access…"); salvage matrix (Control plane / Tenant identity / Billing: "Do not copy"); product brief §Strategic Decisions 1-2.

### 13. Low: Security-significant vocabulary is still partially implementation-defined

**Exact current PRD lines:** 389 (`system-safe`), 59/102/110/208 and elsewhere (`household-safe`), 560 (`represented person`), 494 (`account binding`)

**Impact:** Carried remainder of the prior glossary finding (the sharpest piece is Finding 2 above). `household-safe` and `system-safe` gate rendering decisions in Section 10 and the live slice, and `represented person` and `account binding` gate activity and restore semantics, yet none is normatively defined; stories can define them locally and diverge.

**Concrete fix:** Add short normative definitions to Section 3 or 8 — `household-safe` (classified `household-shared` or an approved Section 8.2 transformation), `system-safe` (subset of `system-operational` free of personal content), `represented person`, `account binding` — and reference them from Sections 10, 11, 13, and 14.

**Authoritative basis:** Rebuild plan §Contract reset (define current contracts in household language); product brief §Identity and Privacy.

### 14. Low: The traceability table's Source column attributes PRD-original values to source sections that do not contain them

**Exact current PRD lines:** 873-878 (NFR-017–NFR-022 cited to UX sections), 817 (FR-047 cited to Brief §Proactivity and Trust), 939 (PD-01's 10-minute default)

**Impact:** The numeric thresholds (2 s/4 s load, 500 ms acceptance, 250 ms/1 s privacy removal, 3-per-day interruption cap, 10-minute timeout) appear nowhere in the cited sources — they are legitimate PRD-level decisions, but the table presents them as sourced. An acceptance audit of Section 17.4 against the sources will fail on these rows, and the table's authority claim (line 897) is weakened.

**Concrete fix:** Mark such rows as "PRD-defined threshold; theme from <source §>" (or add a `PRD` source token) so the table distinguishes sourced requirements from PRD-original quantifications.

**Authoritative basis:** Rebuild plan §Product and planning reset (authoritative current documents); Section 17.4's own claim of source traceability.

### 15. Low: Section 6.5 references a "prior 10% target" that exists in no source or recorded history

**Exact current PRD lines:** 271, 743 (Section 17.1 history requirement)

**Impact:** "The prior 10% target is a post-pilot optimization goal" is a dangling reference to a superseded draft. Section 17.1 requires material changes to be recorded in the document history, but the PRD contains no history section, so the reference is unverifiable and the 17.1 governance rule is currently unmeetable.

**Concrete fix:** Either add a document-history section recording the 20%/10% change (and other material revisions), or restate the sentence self-contained ("a 10% dismissal rate is the post-pilot optimization goal").

**Authoritative basis:** Section 17.1's own governance rule; no source defines either figure.

### 16. Low: Milestone D/E content has no requirement coverage, and the "—" legend is misplaced

**Exact current PRD lines:** 729 (email, layout editing), 735 (voice), 909 (bidirectional mapping rule), 759 (legend inside Section 17.2)

**Impact:** Email has zero FRs; layout editing has none beyond registry validity (FR-040/041); voice has none — while Section 17.5 demands bidirectional epic mapping for every requirement. This is tolerable for later milestones only if the PRD says these will receive requirements before D/E decomposition; today it is silent, so D epics would decompose from narrative content alone, which line 909 forbids. Cosmetically, the "—" Invariant-column legend sits in Section 17.2 (invariants) but describes the 17.4 table.

**Concrete fix:** Add one sentence to Section 16 or 17 stating that Milestone D/E content items without FR coverage require a PRD revision issuing requirements before their epic decomposition; move the "—" legend note into Section 17.4.

**Authoritative basis:** Rebuild plan §BMAD and Ringer (BMAD produces authoritative PRD before epics/stories); Section 17.5's own rule.

## Prior-Findings Disposition

| # | Prior finding (severity) | Disposition | Current basis |
|---|---|---|---|
| 1 | Non-authoritative migration-status in source set (High) | **Resolved** | Frontmatter lines 6-10 list only the four sources; `migration-status` appears nowhere in the PRD; line 713 states status reports "carry no product authority" |
| 2 | "Accepted foundation" unsupported completion claim (High) | **Resolved** | Milestone A (lines 709-713) is now an evidence-gated foundation baseline requiring all six salvage-matrix acceptance checks per retained subsystem, including adapters and infrastructure |
| 3 | First slice contradicts cross-surface foundation and order (High) | **Resolved** | Section 4.1.1 (lines 81-91) adds a mock-backed gate across all five contexts with the eight-capability set from one card/layout registry; FR-035 (line 539) and Milestone A/B gates (lines 711, 719) bind it; live-slice narrowing is now explicit and bounded |
| 4 | Shared-topic milestone can force private-existence disclosure (High) | **Partially resolved** | Dual shared/private fixtures with absence-is-sufficient rule added (lines 102-115); residual: UJ-3 (line 194) contradicts the coordination-statement branch and "shared/unshared" is undefined for that branch → current Finding 3 |
| 5 | Group mode permits private disclosure (High) | **Partially resolved** | Categorical prohibition added (line 392); residual: the new `selected-share` exception is unsafe/unsatisfiable under the same rule's audience caveat → current Finding 1 |
| 6 | Milestone C gate depends on Milestone D proactivity (High) | **Partially resolved** | C/D split executed cleanly across Sections 6.4/6.5, FR-045/047/050/051, and Section 16; residual: autonomous-authority *mechanism* scope (FR-052 vs FR-045) still ambiguous → current Finding 6 |
| 7 | No safe post-restore account-access contract (High) | **Partially resolved** | Section 14.3, FR-084–FR-086, and UJ-9 define portability, admin recovery, token invalidation, and no-rebinding; residual: member re-access has no required procedure or verification → current Finding 5 |
| 8 | One-household not enforced across creation paths (Medium) | **Partially resolved** | INV-1 (line 747) and FR-076 added; enforcement-path and field-prohibition requirements still absent → current Finding 12 |
| 9 | Child privacy vs guardian-review exception (Medium) | **Partially resolved** | PD-02 (line 940) adds a safe interim and closed default; Section 7.4 precedence/necessity/audit and the child-account path remain → current Finding 7 |
| 10 | Action authority lacks principal matrix (Medium) | **Unresolved** | No change; no register entry owns it → current Finding 8 |
| 11 | Inference-provider degradation under-defined (Medium) | **Partially resolved** | AD-02 interim (line 918) and NFR-034 model health; no FR for unconfigured/failed inference or minimum pilot capability → current Finding 9 |
| 12 | Home Assistant freshness contract missing (Medium) | **Resolved** | AD-09 (line 925) requires exactly the freshness/availability model (timestamps, stale presentation, reconnection refresh, per-action rules) with a safe blocking interim |
| 13 | Specialist assistants have no lifecycle/milestone (Medium) | **Unresolved** | No change → current Finding 10 |
| 14 | Action explanations omit information used (Medium) | **Unresolved** | FR-053 (line 560) unchanged in this respect → current Finding 11 |
| 15 | Glossary leaves security terms implementation-defined (Medium) | **Partially resolved** | Section 3 concepts and Section 8.1 classes help; taxonomy contradiction (current Finding 2) and undefined `household-safe`/`system-safe`/`represented person`/`account binding` remain → current Finding 13 |
| 16 | Journey coverage not usable as bidirectional traceability (Medium) | **Resolved** | Section 17.4 per-requirement table (source, journey, milestone, invariant, verification, owner) plus 17.5 bidirectional preservation rule; UJ-7 supplemented; residual Source-column overreach is a new Low (current Finding 14) |

### Disposition Counts

| Disposition | Count |
|---|---:|
| Resolved | 5 |
| Partially resolved | 8 |
| Unresolved | 3 |
