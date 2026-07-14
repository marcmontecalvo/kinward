# Validation Report — Kinward Assistant Experience

- **PRD:** `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md`
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-13T19:22:23+00:00
- **Grade:** Fair (near Good — up from 9 high findings to 2; zero rubric highs)

## Overall verdict

The revision genuinely closes every high-severity defect from the prior review: the non-authoritative migration-status source is gone, Milestone A is evidence-gated against the salvage-matrix acceptance rule, the five-context mock-backed frontend-foundation gate restores the authoritative cross-surface validation shape, both decision registers carry owners/status/due/affected-IDs/safe-interim behavior, the Milestone C/D proactivity split is executed cleanly, post-restore account access is contracted, and Section 17.4 provides complete per-requirement traceability that survived mechanical verification with zero errors. Four rubric dimensions are now strong and none is thin.

The adversarial pass is what holds the grade at Fair: two new high-severity defects emerged from the fixes themselves. The group-state `selected-share` exception is unsatisfiable under the same rule's "presence detection is never proof" caveat and reopens the disclosure risk the group-mode fix was meant to close, and the privacy-class taxonomy is now internally inconsistent across Sections 7, 8, and 10 (`private-to-child`/`shared-with-guardians`/`teen` do not map to Section 8.1's six-class enumeration). It also flags decision-register due dates that postdate Milestone A work depending on them, and a member (non-administrator) post-restore access gap. One more focused revision pass should close the document.

## Dimension verdicts

- Decision-readiness — strong
- Substance over theater — adequate
- Strategic coherence — strong
- Done-ness clarity — adequate
- Scope honesty — adequate
- Downstream usability — strong
- Shape fit — strong

## Findings by severity

### Critical (0)

No critical findings.

### High (2)

**[Adversarial] — Group-state `selected-share` exception is unsatisfiable under its own audience caveat** (lines 392, 328, 248)
Line 392 permits rendering "a `selected-share` that is valid for every detected audience member" while stating "presence detection is never treated as proof that every audience member is known." The permission is either dead text or will be implemented against detected presence and disclose selected-share content (which originates from private data) to undetected people — recreating the group-mode leak the fix was meant to eliminate. Section 6.2's zero-disclosure group test cannot be authored against a self-contradictory rule.
Fix: In `group` state permit `household-shared` rendering only and route `selected-share`/private content through private-device handoff, or require every detected person to hold a currently `verified` session plus explicit surface-policy opt-in, with any unverified presence downgrading to household-shared. State that an explicit sharing act reclassifies the shared statement per Section 8.2.

**[Adversarial] — Privacy-class taxonomy internally inconsistent across Sections 7, 8, and 10** (lines 291, 306, 324–331, 392, 940)
Section 8.1 enumerates exactly six mandatory data classes, but Section 7.4 uses `private-to-child` (drift from `private-child`) and `shared-with-guardians` (not in the enumeration; PD-02's interim is keyed to it), and the `teen` class has no stated mapping — so the group-state prohibition, naming only `private-person` and `private-child`, does not literally cover teen private data. Privacy tests (FR-029/FR-032/NFR-003/NFR-004) cannot be written consistently against three divergent taxonomies.
Fix: One normative mapping — `private-to-child` = `private-child`; `shared-with-guardians` = a constrained `selected-share` naming the guardians; state which class teen private content uses; rephrase the group prohibition to close over the complete class set (e.g., "everything except `household-shared`"); align PD-02's wording.

### Medium (15)

**[Rubric / Substance] — Residual qualifier escape hatches** (§8.2 L337, §12.1 L440, FR-048 L555, NFR-016 L670)
Derived-data invalidation, already-submitted cancellation, "relevant exceptions," and "retry-bounded" still lack mandatory floors even though AD-07/AD-11/PD-04 own the designs.
Fix: One sentence each — dependency record at derivation time; cancellation terminal state per submission stage; relevance inputs and correction loop; declared retry limit and terminal user-visible status.

**[Rubric / Done-ness] — Pilot metrics lack reproducible measurement definitions** (§6.1–6.4, L240–264)
"Sampled," "left undisputed," etc. have targets but no event schema, denominator, sampling method, minimum N, or evaluator.
Fix: Add a metric dictionary for every percentage measure in 6.1–6.5.

**[Rubric / Done-ness] — NFR-024 has no objective pass condition** (L686)
The UX source gives no dimensions, distances, or protocol for room-distance readability and touch targets; the a11y-audit gate cannot execute.
Fix: State minimum touch-target size, per-room viewing distances, and type/contrast criteria, or add a register entry due before Milestone C.

**[Rubric / Scope] — "Basic Kinward Control" not an operation-level release boundary** (§4.2 L131, FR-068–FR-073)
"Manage" across nine resource areas doesn't identify mandatory Milestone C operations.
Fix: Milestone C Control capability matrix (resource × mandatory operation) with explicit deferrals.

**[Rubric / Downstream] — Teen policy has no end-to-end journey** (§7.3, UJ-1–UJ-9)
Epics can pass the automated-boundary bar while missing the lived teen experience.
Fix: Add a fictional teen journey (UJ-10) with success and refusal/handoff outcomes mapped to FR-032, NFR-004, and relevant action FRs.

**[Adversarial] — UJ-3 contradicts the Section 4.1.2 coordination-statement alternative** (L102–115 vs L194)
UJ-3 permits the generic shared item "only when the topic is household-shared," forbidding the approved-coordination-statement branch; "shared/unshared" is undefined for it.
Fix: Define "shared" for the slice as household-shared or having an approved Section 8.2 statement; amend UJ-3 to permit either.

**[Adversarial] — Decision-register due dates postdate dependent Milestone A work** (L711, L494, L772, L917–922)
Milestone A includes bootstrap account bindings, neutral contracts, and provider adapters, but AD-01/AD-02/AD-06 are due at Milestone B start; salvage requires contracts before migration.
Fix: Pull the contract-shaping parts of AD-01/AD-02/AD-06 to Milestone A start (or split A-scoped contract vs B-scoped mechanism decisions), or move the dependent content to B.

**[Adversarial] — Member post-restore access neither specified nor verified** (§14.3 L629–630, FR-085/086)
Members get one sentence with no required procedure; FR-086 never verifies member re-access, so INV-8 can pass with all non-admins locked out.
Fix: Documented member re-access procedure, credential supersession rule, and FR-086 verification for at least one non-administrator profile.

**[Adversarial] — Autonomous-authority machinery C/D scope ambiguous** (L408–419, L552, L559, L264–272)
FR-052 (C) requires every Section 11 rule including the `autonomous` grant contract while FR-045/§6.4 keep autonomous delivery disabled until D; build-disabled vs D-scope is undefined.
Fix: State that in Milestone C no `autonomous` grant can be created or activated ("always deny") and the mechanism plus §6.5 measurement ship in D.

**[Adversarial] — Guardian review contradicts PD-02; child account path undefined** (§7.4, FR-032, PD-02, UJ-7)
7.4's "necessary for care…" review lacks precedence, principal, and audit, contradicting PD-02's interim; FR-032 requires implementing Section 7 as written while PD-02 is open; no FR creates the child account UJ-7 uses.
Fix: Subordinate 7.4 to PD-02's resolution; add precedence/principal/minimum-disclosure/audit; add or explicitly defer a child-account binding FR.

**[Adversarial] — No grant/approval/revocation principal matrix for action authority** (§11, FR-053)
Who may grant, revoke, or approve — especially when actions affect another person — is undefined and unowned by any register entry.
Fix: Principal matrix with execution-time validation, or minimally a register entry with a safe interim.

**[Adversarial] — Inference-provider degradation under-defined** (L135, L159, L222–226)
No FR covers unconfigured/failed inference or the minimum capability for the "working assistant conversation path" gate.
Fix: FR mirroring FR-027/FR-067 for inference; define minimum pilot capability; extend UJ-8.

**[Adversarial] — Specialist assistants have no lifecycle or milestone** (§3.2, §9.1, FR-010, NFR-004)
NFR-004 tests a boundary no requirement brings into existence.
Fix: Assign a minimum lifecycle to a milestone or defer explicitly, preserving multi-assistant schema compatibility.

**[Adversarial] — Approvals and activity records omit "what information was used"** (L416, L560, L547)
Records identify actors/authority/results but not the privacy-filtered source categories or correctable facts relied on.
Fix: Require that provenance in prepared approvals and final activity records, excluding others' private data, secrets, prompts, hidden reasoning.

**[Adversarial] — "Exactly one household" lacks enforcement-path requirements** (FR-001, FR-076, INV-1)
No requirement rejects a second household on API/job/import/restore paths or prohibits tenant-routing fields.
Fix: Extend FR-001 to every boundary; prohibit tenant/entitlement/support-operator fields absent approved justification.

### Low (6)

**[Rubric] — "Measurable" vs "met" pilot gating undefined** (L236 vs L725). Fix: state that Milestone D entry requires the Milestone C pilot conditions met.
**[Rubric] — Actor vocabulary drift** (FR-008/009/015/016/024). Fix: normative actor-relationship paragraph plus UI-synonym declaration.
**[Adversarial] — `household-safe`/`system-safe`/`represented person`/`account binding` undefined** (L389 et al.). Fix: short normative definitions referenced from Sections 10, 11, 13, 14.
**[Adversarial] — Traceability Source column attributes PRD-original thresholds to sources** (L873–878, L817, L939). Fix: add a `PRD` source token for PRD-defined thresholds.
**[Adversarial] — Dangling "prior 10% target"; no document history** (L271, L743). Fix: add a history section or restate self-contained.
**[Adversarial] — Milestone D/E content lacks FR coverage; "—" legend misplaced** (L729, L735, L759). Fix: require a PRD revision issuing D/E requirements before decomposition; move the legend into 17.4.

## Prior-review disposition

All nine high-severity findings from the previous validation run were verified as structurally addressed. Rubric (12 prior findings): **6 resolved, 2 partially resolved, 4 still open** (the still-open items are the pre-existing mediums/lows: pilot metric dictionary, Kinward Control operations, teen journey, actor vocabulary). Adversarial (16 prior findings): **5 resolved, 8 partially resolved, 3 unresolved**. The two current high findings are residuals of the group-mode and shared-topic fixes interacting with the privacy taxonomy, not regressions of the resolved items.

## Mechanical notes

- FR IDs contiguous and unique `FR-001`–`FR-086`; NFR IDs `NFR-001`–`NFR-037`; journeys `UJ-1`–`UJ-9`; registers `AD-01`–`AD-15`, `PD-01`–`PD-07` — verified in both definitions and the Section 17.4 table with no gaps, duplicates, or dangling cross-references.
- Front matter lists exactly the four authoritative sources; all paths resolve; zero references to `docs/pivot/migration-status.md` remain.
- Every source-section citation in Section 17.4 resolves to a real section or salvage-matrix row; the 17.5 journey summary matches the table exactly.
- Public-repository safety: pass — fictional personas only; no real names, credentials, hostnames, or private data found.

## Reviewer files

- `review-rubric.md`
- `review-adversarial-general.md`
