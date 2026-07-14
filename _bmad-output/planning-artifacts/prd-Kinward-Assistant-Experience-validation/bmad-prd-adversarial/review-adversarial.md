# Adversarial PRD Review — Kinward Assistant Experience

## Gate verdict

The PRD is not ready to be handed to UX, architecture, and epic/story creation without correction. It establishes strong privacy, action, and lifecycle policies, but several requirements use undefined subjective thresholds that will produce divergent implementations and untestable acceptance; multiple success metrics lack sampling or evidence contracts; and at least one source contradiction narrows a product-brief guarantee into a weaker PRD requirement. The release-boundary and milestone-content descriptions omit a mutation capability that FR-060 and UJ-6 place in the same milestone, which will mislead epic decomposition. These are PRD-level fixes that do not require prescribing architecture, but they must be resolved before downstream work consumes the requirements.

## Findings

### FR-023 narrows the product brief's confirmation requirement and uses undefined subjective categories

Priority: P1

Confidence: high

Evidence: Product brief §Progressive Context Building: "Assistants may learn naturally but must request confirmation before promoting observations into durable context." PRD FR-023 (Milestone C): "Consequential, sensitive, or behavior-changing observations require confirmation before becoming durable facts." FR-022 (Milestone C): "Kinward shall distinguish confirmed facts, inferred observations, transient context, and household-shared facts."

Failure mode: The brief requires confirmation unconditionally — all observations promoted to durable context need confirmation. FR-023 narrows this to only "consequential, sensitive, or behavior-changing observations," implying that non-consequential observations may become durable facts without confirmation. An implementer reading FR-023 alone could allow inferred observations to become durable facts without confirmation, contradicting the brief. Additionally, "consequential," "sensitive," and "behavior-changing" are undefined; one implementation could treat all observations as consequential (matching the brief) while another treats none as consequential, producing divergent durable-fact behavior and no objective test oracle for FR-023.

Fix: Align FR-023 with the brief by requiring confirmation for all observations promoted to durable facts. If the narrowing is intentional, justify it explicitly against the brief and define the three categories with objective criteria. Add a PD if the category boundary is a product decision.

### Success metrics lack sampling or evidence contracts

Priority: P1

Confidence: high

Evidence: Section 6.1: "At least 70% of sampled assistant sessions produce a response, topic update, useful explanation, or permitted action without developer repair" and "At least 80% of sampled cross-surface topic continuations resume without restating the initial request." Section 6.2: "At least 95% of sampled meaningful external actions contain complete requester, assistant, represented person, authority, approval, integration, result, and reversibility records." Section 6.5: "Fewer than 20% of proactive nudges are dismissed as irrelevant during the Milestone D measurement window." Section 16 Milestone C exit gate: "all Section 6.1 through 6.4 conditions are measurable."

Failure mode: "Sampled" is used without defining sample size, sampling methodology, population criteria, or who collects and adjudicates the evidence. "70% of sampled sessions" is satisfiable by any sample size — 3 of 4 sessions passes. Two implementers could produce wildly different evidence for the same metric. The Milestone C exit gate cannot be adjudicated because "measurable" has no sampling definition. The Section 6.5 "measurement window" is undefined in duration and scope. The zero-tolerance metrics in 6.2 and 6.4 ("Zero actions are reported complete when the provider returned failure..." and "Zero private items remain visible...") use "zero" without stating whether all pilot events are checked or only sampled, leaving the verification method ambiguous.

Fix: For each sampled metric, define minimum sample size, sampling method (random/consecutive/all), the population window (the 30-day pilot), and who adjudicates subjective terms ("useful," "acted upon," "left undisputed," "complete"). For zero-tolerance metrics, state explicitly that all relevant events in the pilot are checked, not sampled.

### FR-083 person deletion dispositions are undefined for shared and household data

Priority: P1

Confidence: high

Evidence: FR-083 (Milestone C): "Deleting a person shall require an explicit disposition for owned assistants, topics, facts, integration connections, shared contributions, and required audit records." Section 7.2: "An adult may explicitly share a fact, topic summary, calendar, or action outcome with the household or selected people. Sharing does not transfer ownership of the underlying private source." Section 8.2: "Deleting or revoking access to source data must invalidate or remove derived data where the product can identify the dependency."

Failure mode: "Explicit disposition" does not enumerate allowed disposition options. For `household-shared` contributions created by the deleted person, one implementer could delete them (causing household data loss for remaining members who depend on shared facts), another could transfer ownership to the administrator (potentially granting access the administrator shouldn't have to data originally created by a different person), and another could anonymize provenance. None of these is constrained. Since person deletion is irreversible and affects household-shared data, the undefined dispositions risk data loss or privacy exposure. There is also no constraint on what happens to `selected-share` items the deleted person created for named recipients — those could be orphaned or silently destroyed.

Fix: Define allowed disposition options per data class: `private-person` data is deleted; `household-shared` contributions are retained with household ownership and anonymized or transferred provenance (not deleted); `selected-share` items are either transferred to the recipient or deleted with notification. At minimum, constrain that `household-shared` data contributed by a deleted person must not be silently destroyed.

### Section 11 approval expiry uses undefined "materially" threshold

Priority: P1

Confidence: high

Evidence: Section 11: "Approval expires when its prepared mutation expires, source state changes materially, identity changes, or authority is revoked." UJ-6: "If source state changed, approval expires and the assistant prepares a new proposal instead of applying stale intent." Section 11 also states: "A prepared mutation includes target, changed fields, source version or freshness marker, expected result, expiration, and reversibility status." FR-058 (Milestone C): "Detected changes shall retain provider event identity, observed version, observed time, and affected account."

Failure mode: "Materially" is undefined. UJ-6 says unconditionally "If source state changed, approval expires," but Section 11 qualifies it with "materially." For a calendar mutation, an implementer could treat only time/date changes as material (allowing stale attendee or location changes to pass approved) or treat any field change as material (over-invalidating). Since the prepared mutation includes a "source version or freshness marker," the mechanism to detect changes exists, but the threshold for when a version change triggers expiry is undefined. This produces divergent stale-intent prevention behavior and untestable acceptance for UJ-6.

Fix: Define "materially" as any change to any field included in the prepared mutation, or provide a per-action-category materiality rule. Alternatively, align Section 11 with UJ-6 by stating that any detected source version change expires the approval, removing the "materially" qualifier.

### FR-045 proactive briefing delivery and Section 12.4 briefing area create ambiguity for non-calendar exceptions at Milestone C

Priority: P2

Confidence: medium

Evidence: FR-045 (Milestone C): "Ambient and briefing delivery for calendar-change exceptions — including evaluation, suppression, deduplication, explanation, category-level correction, and metric instrumentation — shall be operational in Milestone C. Nudge, interruption, and autonomous-action delivery are Milestone D scope." Section 12.4 (Milestone C via FR-038): "A briefing item must include: concise meaning, why it matters, source category, recency, affected person or household scope, required action if any, and correction or dismissal control." FR-048 (Milestone C): "Kinward shall detect relevant exceptions without requiring routine definitions." PD-04 interim: "Calendar-change briefing is the only enabled proactive category."

Failure mode: "Briefing" is used both as a UI area (Section 12.4, which can contain any relevant item including completed actions and pending approvals) and as a proactive delivery level (FR-045, restricted to calendar-change exceptions at Milestone C). FR-048 requires detecting non-calendar exceptions at Milestone C, but it is unclear whether detected non-calendar exceptions can appear in the briefing UI area. One implementation could place all detected exceptions in the briefing area; another could restrict it to calendar-change exceptions per FR-045's delivery-level restriction. This produces divergent Milestone C behavior and untestable acceptance for FR-048 (what is the observable outcome of detecting a non-calendar exception if it cannot be delivered?).

Fix: Distinguish the briefing UI area (Section 12.4) from the proactive delivery mechanism (FR-045). State that at Milestone C the briefing area may contain calendar-change exceptions, completed assistant actions, and pending approvals, while non-calendar exception proactive delivery (nudge, interruption) is deferred to Milestone D. Alternatively, define which exception categories populate the briefing area at Milestone C.

### Section 4.2 release boundary describes calendar as "read-capable" but FR-060 and UJ-6 require mutations at Milestone C

Priority: P2

Confidence: medium

Evidence: Section 4.2 (first usable household release): "one read-capable calendar integration with change detection." FR-060 (Milestone C): "Calendar mutations shall implement Section 11 and reconcile unknown provider results before retry." UJ-6: "Alex asks Kinward to change a calendar appointment" — Section 17.5 maps UJ-6 to FR-060 at Milestone C. Section 4.3 (Later scope) lists "email reading and sending" as later scope but does not list calendar mutations.

Failure mode: Section 4.2 is the release scope definition that epic/story creators will read first. By listing only "read-capable calendar integration with change detection" and not mentioning mutations, a reader could conclude calendar mutations are later scope — especially given the parallel structure where Section 4.3 explicitly defers "email reading and sending." This would cause epic decomposition to miss FR-060 and UJ-6 at Milestone C, blocking downstream work. The Milestone C content description (Section 16) likewise says "calendar change detection" without mentioning mutations.

Fix: Add "calendar mutation with approval, reconciliation, and activity records" to Section 4.2's calendar item, or add a clarifying note that "read-capable" does not exclude the mutation capabilities required by FR-060 and UJ-6. Update the Milestone C content description in Section 16 to mention calendar mutations.

### FR-065 "when confirmation is expected" has no oracle; AD-09 interim does not cover post-action confirmation

Priority: P2

Confidence: medium

Evidence: FR-065 (Milestone C): "A successful service call without confirmed resulting state shall not be described as confirmed physical completion when confirmation is expected." AD-09 (Due: Milestone C start): "Home Assistant freshness and availability model (observed timestamps or version markers, stale presentation, reconnection refresh, per-action current-state rules)" — safe interim: "Cached Home Assistant state is presented as stale; actions requiring current state are blocked on stale data." INV-5: "No fabricated facts, state, or completion claims; uncertainty stays visible."

Failure mode: FR-065's "when confirmation is expected" is undefined — no rule states which Home Assistant actions require post-action state confirmation. An implementer could decide confirmation is never expected and always report actions as completed, which would contradict INV-5. AD-09's scope ("per-action current-state rules") could address this, but its safe interim only covers pre-action staleness ("actions requiring current state are blocked on stale data"), not post-action confirmation. If AD-09 is accepted as open at Milestone C with its current interim, FR-065 is vacuously satisfiable (never expect confirmation), silently weakening INV-5.

Fix: Define which Home Assistant action categories require post-action state confirmation (e.g., locks, covers, climate, switches where the service call return does not include resulting state), or state a default rule: confirmation is expected for any action whose service call response does not include the resulting state. Extend AD-09's interim to cover post-action confirmation: "Actions without confirmed resulting state are reported as `unknown`, not `completed`."

### "Required audit retention" is undefined for user-initiated deletion

Priority: P2

Confidence: medium

Evidence: FR-024 (Milestone C): "Users shall inspect, correct, reclassify, and delete durable facts about themselves, subject to required audit retention." Section 12.3: "delete it subject to required audit retention." FR-083: "Deleting a person shall require an explicit disposition for... required audit records." AD-13 (Due: Milestone C start): "Activity retention and append-protection strategy" — interim: "Retain all activity with no pruning until resolved." PD-05 interim: "Retain all data with no automatic deletion."

Failure mode: "Required audit retention" is referenced as a constraint on user-initiated deletion (FR-024, Section 12.3) but is never defined. AD-13 covers activity retention (interim: retain everything), but it is unclear whether "required audit retention" blocks deletion of the fact itself or only retains an audit log entry recording the deletion event. One implementation could block all user-initiated fact deletions (interpreting AD-13's "retain all" as blocking); another could delete the fact and retain only an audit entry. This produces divergent deletion behavior and untestable acceptance for FR-024 — a test cannot determine whether deletion should succeed or be blocked.

Fix: Define "required audit retention" as retaining an audit log entry (recording the deletion event, timestamp, and actor) without blocking deletion of the underlying durable fact. Alternatively, explicitly state that user-initiated deletion is blocked while AD-13 is unresolved, and that audit retention applies to activity records only, not to the durable fact being deleted.

### Section 8.2 derived data invalidation has a dependency-tracking loophole for internally stored derived data

Priority: P2

Confidence: medium

Evidence: Section 8.2: "Deleting or revoking access to source data must invalidate or remove derived data where the product can identify the dependency." FR-026 (Milestone C): "Derived data shall enforce Section 8.2." AD-07 (Due: Milestone C start): "Invalidation and deletion behavior for externally stored derived data" — interim: "Mark references inaccessible and disclose the limitation." Section 8.1: "An explicit privacy-filtered transformation is a new, separately reviewable item... it does not reclassify or expose its private source."

Failure mode: Section 8.2's invalidation requirement is conditional on "where the product can identify the dependency." There is no requirement for the product to track dependencies between source data and internally stored derived data (summaries, embeddings, inferences stored in personal memory). An implementation could simply not track dependencies and claim "cannot identify the dependency" for all internally stored derived data, silently skipping invalidation when a source fact is deleted or revoked. AD-07 only covers externally stored derived data. For internally stored derived data, the loophole is unconstrained, and a deleted private fact's content could persist indefinitely in derived summaries or embeddings without invalidation.

Fix: Add a requirement that internally stored derived data must track source dependencies (linkage to source fact IDs and data classes) so that Section 8.2's invalidation condition is actionable. Alternatively, state that derived data whose source dependencies cannot be tracked must inherit the most restrictive data class of all possible source inputs indefinitely and must be deleted when any candidate source is deleted.

### Child and teen action approval routing and approval-request content are undefined

Priority: P2

Confidence: medium

Evidence: Section 7.3 (Teen): "Money, transportation, appointments, account security, message sending, and actions affecting another person require confirmation or authorized-adult approval by default." Section 7.4 (Child): "External-state actions require authorized-adult approval unless a narrow category is explicitly pre-authorized." UJ-7: "Message sending is blocked or routed to authorized-adult approval. The child's ordinary conversation is not automatically copied into guardian memory." Section 7.1 defines the administrator role; Sections 7.1–7.6 define no "guardian" role. FR-052 (Milestone C): "External actions shall implement every authority rule in Section 11." Section 11: "A prepared mutation includes target, changed fields, source version or freshness marker, expected result, expiration, and reversibility status."

Failure mode: "Authorized-adult approval" does not define which adult(s) receive the approval request for a minor's action. In a household with two adults, one implementation could route to any administrator, another to all adults, another to a designated guardian — but "guardian" is not a defined role. More critically, there is no constraint on what information the approval request contains at Milestone C. The prepared mutation (Section 11) includes "changed fields" and "target," which for a child's message-sending action would include the message content and recipient. This could expose the child's private message content to the approving adult via the approval mechanism, even though UJ-7 only prohibits copying into "guardian memory" (not into approval requests). FR-050 (minimum-information coordination requests) is Milestone D and does not cover Milestone C approval requests.

Fix: Define approval routing for minor actions: e.g., "approval requests for a minor's action are routed to all household adults or a designated guardian." Add a constraint that approval requests for minor actions must contain only minimum-necessary information (action category, target integration, and consequence) and must not include the minor's private conversation or message content unless explicitly required for the approval decision.

### Section 9.2 coordination statement fields do not satisfy Section 9.1 delegation record requirements

Priority: P2

Confidence: medium

Evidence: Section 9.1: "Assistants may exchange information only through an explicit delegation record containing purpose, permitted data, expiry, and recipient." Section 9.2: "A personal assistant may send the fallback assistant only a minimum-necessary, privacy-filtered coordination statement. The statement must carry provenance, sharing class, purpose, and expiry."

Failure mode: A coordination statement (Section 9.2) carries "provenance, sharing class, purpose, and expiry" but not "permitted data" or "recipient" as required by Section 9.1's delegation record. Either (a) a coordination statement is a delegation record but is missing two required fields (non-compliance with Section 9.1), or (b) it is a separate mechanism outside the delegation record framework, creating an information channel not covered by Section 9.1's constraint. The "permitted data" field is particularly important for privacy enforcement — without it, the coordination statement does not declare what data the fallback assistant is permitted to use from the statement. An implementer could either add the missing fields (diverging from the stated required fields in Section 9.2) or treat coordination statements as exempt from delegation record rules (creating an unregulated channel between personal and household assistants).

Fix: Align the coordination statement's required fields with the delegation record's: add "permitted data" (the privacy-filtered statement content itself) and "recipient" (explicitly the household fallback assistant). Alternatively, state that a coordination statement is a restricted form of delegation record where "permitted data" is the statement content and "recipient" is implicitly the household fallback assistant, satisfying Section 9.1.

## Areas challenged with no finding

1. **Shared-surface identity state machine (Section 10):** The five states (`unknown`, `candidate`, `verified`, `group`, `expired`), their permitted data classes, the `group`-state categorical prohibition of all non-`household-shared` data, the transition rules removing private content on downgrade, the no-private-caching rule, and the 10-minute session-expiry maximum are internally consistent and produce testable privacy boundaries.

2. **External-action authority hierarchy (Section 11):** The `observe`/`suggest`/`prepare`/`confirm`/`autonomous` levels, default-to-observe for new integrations, the `confirm`-only-on-exact-mutation rule, the unknown-result-as-not-completed rule, and the approval-expiry triggers (except the "materially" threshold in the finding above) are well-specified and enforceable.

3. **Backup and restore contract (Section 14):** The included/excluded/portable classification of authentication artifacts, atomic-restore-or-stop rule, post-restore token invalidation, member re-access procedure with duplicate-profile prevention, and post-restore verification scope are thorough and internally consistent with UJ-9.

4. **Data classification system (Section 8.1):** The six data classes (`private-person`, `private-child`, `selected-share`, `household-shared`, `surface-ephemeral`, `system-operational`), the derived-data inheritance rule (most restrictive class unless privacy-filtered transformation), and the data-minimization principle provide a clear, enforceable privacy model.
