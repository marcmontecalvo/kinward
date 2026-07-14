# Validation Report — Kinward Assistant Experience

- **PRD:** `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md`
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-13T23:23:59Z
- **Grade:** Excellent

## Overall verdict

This is an unusually disciplined chain-top PRD. It carries a clear thesis (durable context over routines, private-by-default, relationship-first), backs it with 86 FRs and 37 NFRs that are mostly testable, exposes every open decision in two registers (AD/PD) with safe interim behavior, and traces every requirement to a source, milestone, invariant, verification method, and owner — the brownfield salvage rule is even encoded into the Milestone A exit gate. What holds it back from pristine is a localized downstream-usability gap (three of nine user journeys lack the named protagonists the PRD's own Section 5 header promises) and a thesis-critical but under-bounded proactive-level selection rule (FR-046) that no decision register owns. No contradictions were found; no dimension is broken.

The grade is Excellent under the rubric rule (all seven dimensions strong or adequate, zero high or critical findings); it borders Good solely because the two medium findings sit in dimensions (done-ness, downstream usability) that matter most for a chain-top PRD. No additional reviewers were dispatched (`finalize_reviewers` resolves empty; nested model calls unavailable, so the sequential fallback was used).

## Dimension verdicts

- Decision-readiness — strong
- Substance over theater — strong
- Strategic coherence — strong
- Done-ness clarity — adequate
- Scope honesty — strong
- Downstream usability — adequate
- Shape fit — strong

## Findings by severity

### Critical (0)

None.

### High (0)

None.

### Medium (2)

**Done-ness clarity — FR-046 proactive-level selection lacks testable thresholds and an owning decision** (§13.6, FR-046)
"Least disruptive level consistent with timing, consequence, confidence, and policy" names four factors but no rule for combining them, no thresholds separating ambient from briefing from nudge, and no entry in the Section 18 or 19 registers that owns the selection algorithm. The thesis ("most successful assistance should happen quietly") rests on this requirement. The gap is bounded for Milestone C (only ambient/briefing are enabled per FR-045, and 6.1/6.4 measure outcome quality post-hoc), but bites hard at Milestone D when nudge/interruption/autonomous levels activate and 6.5's "fewer than 20% dismissed as irrelevant" / "fewer than 5% reversed" need a deterministic selector to test against.
Fix: Either add an AD (Architect, due Milestone D start) defining the level-selection inputs, thresholds, and tie-break rule with a `privacy-test`/`unit` verification gate, or add acceptance criteria to FR-046 stating the minimum decision inputs and the "must not exceed" level given each input combination — and link it from FR-046 and 6.5.

**Downstream usability — Three user journeys lack named protagonists** (§5 UJ-4, UJ-7, UJ-8)
UJ-4 ("A connected calendar adds an early-release event associated with a child profile"), UJ-7 ("A child account asks for homework help"), and UJ-8 ("The memory provider or Home Assistant is offline") have no named person. Section 5's header promises fictional test personas and the rubric (chain-top, consumer, meaningful UX) treats named protagonists as load-bearing. UJ-7 is the most impactful miss: child-to-guardian approval routing, age-appropriate tone, and "not automatically copied into guardian memory" all benefit from a named child protagonist with inline age/family context.
Fix: Give UJ-4 and UJ-7 a named child protagonist (and a named adult recipient where relevant) with one line of inline family/age context, mirroring UJ-1/UJ-2/UJ-5/UJ-6/UJ-9. UJ-8 may stay protagonist-free if the PRD explicitly marks operational/failure journeys as exempt from the named-protagonist rule.

### Low (3)

**Downstream usability — Glossary does not cover all domain nouns used as FR subjects** (§3)
"Now", "Briefing", "Continue", "Activity", and "Kinward Control" are defined behaviorally (§12.4, §12.3, FR-053, FR-068) but not in Section 3, so a reader pulling a single FR out of context must hunt for the definition. Usage is consistent across FRs, UJs, and SM definitions — this is an indexing gap, not drift.
Fix: Add five short glossary entries in §3 pointing to their behavioral definitions, or rename the §3 heading to "Core product concepts" and add a "See also" note listing the behaviorally-defined terms.

**Done-ness clarity — "Relevant" is unbounded in two thesis-adjacent FRs** (§13.6 FR-048, §13.8 FR-063)
FR-048's "relevant exceptions" and FR-063's "relevant state and actions" leave "relevant" to the implementer. FR-045 narrows FR-048 to calendar-change exceptions for C (mitigating), and FR-063's "without requiring entity IDs or service syntax" is testable on its own, but the word "relevant" itself is not.
Fix: Replace "relevant" with a defined scope (e.g. "exceptions derived from connected calendar, household-transportation, and confirmed-fact sources" for FR-048) or link an owning PD that defines the initial category set per milestone.

**Decision-readiness — AD-13 / PD-05 overlap on activity retention** (§18 AD-13, §19 PD-05)
AD-13 ("Activity retention and append-protection strategy", Architect) and PD-05 ("Default retention periods for … activity, and approvals", Product owner) both cover activity retention with the same interim ("retain all … no pruning / no automatic deletion"). The concerns are distinct (append-protection vs. retention period) but the affected-requirement overlap (FR-082) and interim duplication could let a story pick the wrong owner.
Fix: Add a one-line cross-reference in each entry naming the other as the complementary concern, or split the activity-retention scope between them explicitly.

## Mechanical notes

- Glossary coverage: five domain nouns used as FR subjects (Now, Briefing, Continue, Activity, Kinward Control) are absent from Section 3 but defined behaviorally elsewhere and used consistently — indexing gap, not drift.
- ID continuity: clean across FR-001–086, NFR-001–037, UJ-1–9, AD-01–15, PD-01–07, INV-1–11; no duplicates, no gaps, no deprecated-without-superseder entries.
- Cross-references: ten FR→Section spot-checks (§4.1.1, §4.1.2, §6.5, §7, §8.2, §9.2, §10, §11, §12.1, §12.4) all resolve.
- Assumptions Index roundtrip: no `[ASSUMPTION]` tags and no Assumptions Index present. The PRD substitutes the AD/PD decision registers with explicit "safe interim behavior"; the function is served, the literal convention and its roundtrip are dropped. A one-line note in §18 or §20 stating that open AD/PD entries stand in for the Assumptions Index would close the loop.
- UJ protagonist naming: 6 of 9 UJs name a protagonist (Alex, Jordan); UJ-4, UJ-7, UJ-8 do not (see Medium finding in Downstream usability).
- Required sections for stakes: all present and appropriate to a chain-top, privacy-critical, single-household PRD.

## Reviewer files

- `review-rubric.md`
