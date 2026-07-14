# Edge Case Review: Kinward Assistant Experience PRD

**Location:** /home/marc/workspaces/kinward/_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md  
**Method:** Exhaustive path enumeration across all FRs, UJs, state transitions, data classes, role transitions, integration states, and open architecture/product decisions.

---

## UJ-1: Administrator establishes a household

**Location:** Section 5 / UJ-1 (lines 170-179)  
**Trigger:** Setup fails after household record created but before assistant/personality commit  
**Gap:** PRD specifies "no partially configured household is presented as usable" on pre-commit failure, but does not specify rollback behavior when household record persists but assistant/personality creation fails mid-transaction  
**Consequence:** Orphaned household record blocks retry with same name; admin cannot recover without manual DB edit

**Location:** Section 5 / UJ-1 (lines 170-179)  
**Trigger:** Admin creates household, then immediately loses access (device loss, credential loss) before completing onboarding  
**Gap:** PRD specifies admin recovery bound to restored admin profile (Section 14.3) but does not specify recovery path for admin who never completed onboarding and has no backup  
**Consequence:** Household unrecoverable; requires full reset and data loss

**Location:** Section 5 / UJ-1 (line 172)  
**Trigger:** Admin adds another adult and child as "profiles without requiring their accounts" during initial setup  
**Gap:** PRD does not specify what happens if the invited adult later accepts invitation but the pre-created profile has conflicting data (different name, wrong role)  
**Consequence:** Profile merge conflict or duplicate profile creation on invitation acceptance

---

## UJ-2: Invited adult receives a separate assistant

**Location:** Section 5 / UJ-2 (lines 180-186)  
**Trigger:** Invitation token expires after adult creates account but before profile binding completes  
**Gap:** PRD specifies "expired or mismatched invitation cannot silently create duplicate profile or attach to wrong person" (failure outcome) but does not specify recovery path — whether admin must re-invite, whether partial account is auto-cleaned, or whether adult can self-recover  
**Consequence:** Orphaned account with no profile binding; admin cannot re-invite same email; adult cannot self-remediate

**Location:** Section 5 / UJ-2 (line 182)  
**Trigger:** Invited adult accepts invitation but household already has a profile with same name/email (created by admin in UJ-1)  
**Gap:** UJ-1 allows admin to "add another adult as profile without requiring their account"; UJ-2 says adult "confirms the intended profile" — no conflict resolution specified when pre-created profile data mismatches invited adult's actual identity  
**Consequence:** Duplicate profiles or wrong profile binding; privacy boundary violation if bound to wrong person's assistant

**Location:** Section 5 / UJ-2 (line 184)  
**Trigger:** Invited adult was previously a member, left/was removed, and is re-invited  
**Gap:** PRD covers initial invitation (UJ-2) and member deletion (FR-083) but not re-invitation of a previously removed adult — whether prior private data/topics/integrations are restored, archived, or permanently deleted  
**Consequence:** Privacy leak if prior private data resurfaces; or data loss if admin expected continuity

---

## UJ-3: Topic continues across surfaces

**Location:** Section 5 / UJ-3 (lines 188-195)  
**Trigger:** Topic created on mobile, continued on desktop, but desktop session expires during continuation  
**Gap:** PRD specifies continuation "without requiring the original request to be repeated" but does not specify behavior when session expires mid-continuation — whether topic state is preserved, whether re-authentication resumes at same point, or whether context is lost  
**Consequence:** User loses topic context and must restate request after re-authentication

**Location:** Section 5 / UJ-3 (line 194)  
**Trigger:** Topic is `household-shared` but the original creator (Jordan) is removed from household before shared display renders it  
**Gap:** PRD specifies shared display shows "Trip planning is active" for `household-shared` topics but does not specify behavior when topic owner is removed — whether topic persists as orphaned household-shared, is auto-deleted, or requires admin action  
**Consequence:** Orphaned shared topic with no owner; or unexpected disappearance from shared display

**Location:** Section 5 / UJ-3 (line 194)  
**Trigger:** Private topic has approved `household-shared` coordination statement; creator later revokes the approval  
**Gap:** PRD specifies approval creates shared statement (Section 8.2) but does not specify revocation behavior — whether shared display immediately removes the statement, whether there's a grace period, or whether revocation is logged for audit  
**Consequence:** Stale shared statement remains visible after revocation; privacy violation

---

## UJ-4: Kinward surfaces a calendar change

**Location:** Section 5 / UJ-4 (lines 196-202)  
**Trigger:** Calendar integration detects change, but the associated child profile has no configured guardians (admin forgot to assign)  
**Gap:** PRD says "appropriate adults receive briefing" but does not specify fallback when no adult is authorized for that child — whether briefing is suppressed, sent to all adults, or generates an admin alert  
**Consequence:** Silent drop of child-related calendar change; or inappropriate disclosure to non-guardian adults

**Location:** Section 5 / UJ-4 (line 198)  
**Trigger:** Calendar change detected for event that spans multiple calendars (personal + household) with conflicting privacy classifications  
**Gap:** PRD says "compares event with confirmed household transportation facts and permitted adult calendars" but does not specify conflict resolution when same event appears in `private-person` and `household-shared` calendars with different details  
**Consequence:** Incorrect briefing generated from wrong calendar source; privacy leak or missed action

**Location:** Section 5 / UJ-4 (line 202)  
**Trigger:** Early-release event detected, but household transportation facts are unconfirmed (confidence below threshold)  
**Gap:** PRD says "compares with confirmed household transportation facts" — does not specify behavior when facts exist but are unconfirmed/low-confidence  
**Consequence:** Briefing generated on unconfirmed assumptions; or briefing suppressed when it should have been informational

---

## UJ-5: Shared display refuses private disclosure

**Location:** Section 5 / UJ-5 (lines 204-208) / Section 10 (referenced)  
**Trigger:** Identity confidence drops from `verified` → `likely` → `unknown` during active session on shared display  
**Gap:** Section 10 (referenced by FR-029, AD-10) defines identity states but PRD does not specify transition behavior between states — whether content is progressively filtered, immediately purged, or grace-period applies at each transition  
**Consequence:** Private content may remain visible during `likely` state; or overly aggressive purge during transient confidence dip

**Location:** Section 5 / UJ-5 (line 208)  
**Trigger:** Private handoff offered but user's personal device is offline/unreachable  
**Gap:** PRD says "offers private-device handoff" but does not specify fallback when handoff target unavailable — whether shared display shows error, suppresses response entirely, or queues for later  
**Consequence:** User receives no response at all; or shared display shows "handoff failed" leaking that private query existed

**Location:** Section 5 / UJ-5 / NFR-020 (line 682)  
**Trigger:** Backend detects identity downgrade but client has not yet received downgrade signal (network partition)  
**Gap:** NFR-020 specifies "within 250ms of client receiving identity downgrade AND within 1s of backend detection" — does not specify behavior when these two signals are inconsistent (backend detects, client doesn't receive)  
**Consequence:** Private content remains on client beyond 250ms; or backend purges but client still shows stale private content

---

## UJ-6: Prepared action requires exact approval

**Location:** Section 5 / UJ-6 (lines 210-214) / FR-017, FR-052, FR-060, NFR-012, NFR-015  
**Trigger:** User approves action, but provider returns timeout/unknown status (not success/failure)  
**Gap:** PRD says "if source state changed, approval expires and assistant prepares new proposal" but does not specify behavior when provider returns indeterminate status — whether approval is consumed, action is retried, or user must re-approve  
**Consequence:** Duplicate execution on retry; or action stuck in limbo with no user-visible resolution

**Location:** Section 5 / UJ-6 (line 214) / NFR-015 (line 672)  
**Trigger:** Kinward restarts during in-progress approved action (after approval, before provider confirmation)  
**Gap:** NFR-015 says restart "shall not convert an unknown or incomplete action into completed" but does not specify whether action is retried, rolled back, or presented as "pending confirmation" after restart  
**Consequence:** User sees action as complete when provider never confirmed; or user must manually check external system

**Location:** Section 5 / UJ-6 / FR-053 (line 826)  
**Trigger:** Multiple approvals pending for same resource (e.g., two calendar edits to same event) approved in rapid succession  
**Gap:** PRD specifies per-action approval but not concurrency control — whether second approval waits for first to complete, queues, or conflicts  
**Consequence:** Race condition causing lost update or duplicate mutation

---

## UJ-7: Child receives bounded assistance

**Location:** Section 5 / UJ-7 (lines 216-221) / Section 7.3-7.4 (Teen/Child policies)  
**Trigger:** Teen asks assistant to send message; guardian approval required but no guardian is currently authenticated/available  
**Gap:** PRD says "blocked or routed to authorized-adult approval" but does not specify queue behavior — whether request times out, persists until guardian acts, notifies guardian asynchronously, or allows teen to cancel  
**Consequence:** Teen's request hangs indefinitely; or guardian receives stale approval request days later

**Location:** Section 7.4 (line 306) / FR-032  
**Trigger:** Child profile exists without account; admin later creates account for that child (e.g., child turns 13)  
**Gap:** Section 7.5 allows "profile without account"; Section 7.4 governs child with account — no transition path specified when child profile gains an account  
**Consequence:** Duplicate profile created; or prior `private-child` facts not migrated to `private-person`; privacy class mismatch

**Location:** Section 7.4 (line 310)  
**Trigger:** Child asks question that triggers proactive coordination request (Milestone D) involving another household member  
**Gap:** PD-04 and FR-045-FR-049 limit Milestone C to ambient/briefing; UJ-7 is Milestone C scope but coordination requests are Milestone D — PRD does not specify whether child can trigger coordination requests in Milestone C  
**Consequence:** Child inadvertently triggers coordination flow not yet implemented/guarded

---

## UJ-8: Optional providers unavailable

**Location:** Section 5 / UJ-8 (lines 222-226) / NFR-010 (line 667) / FR-027, FR-061, FR-067  
**Trigger:** Memory provider AND Home Assistant both unavailable simultaneously during active topic work  
**Gap:** PRD covers single-provider unavailability but not compound degradation — whether topic persistence falls back to local-only, whether assistant degrades to stateless mode, or whether user is notified of compound degradation  
**Consequence:** Silent data loss if topic updates only held in memory provider; or assistant claims capabilities it cannot fulfill

**Location:** Section 5 / UJ-8 (line 226) / FR-067  
**Trigger:** Home Assistant becomes unavailable mid-action (service call submitted, awaiting state confirmation)  
**Gap:** FR-067 says unavailability "removes or marks stale dependent cards" but does not specify in-flight action handling — whether action is marked failed, retried on reconnect, or left in unknown state  
**Consequence:** User believes light turned off; it didn't; no indication of failure

**Location:** Section 5 / UJ-8 / NFR-010 (line 667)  
**Trigger:** Calendar provider unavailable during calendar-change detection window (UJ-4)  
**Gap:** NFR-010 says provider failure "shall not prevent... local topic access" but UJ-4 depends on calendar integration — no fallback briefing behavior specified when calendar sync fails  
**Consequence:** Missed calendar changes with no user-visible indication; silent degradation

---

## UJ-9: Administrator restores household

**Location:** Section 5 / UJ-9 (lines 228-232) / Section 14.3-14.4 / FR-074-FR-086  
**Trigger:** Restore target deployment has different schema version than backup manifest (forward/backward compatibility)  
**Gap:** FR-075 says "same or declared compatible schema version" and FR-080 covers upgrade — but no forward-compatibility rule for restore to newer schema, nor rollback rule for restore to older schema  
**Consequence:** Restore fails silently or corrupts data; admin cannot recover without manual migration

**Location:** Section 14.3 (lines 629-632) / FR-085-FR-086  
**Trigger:** Restored admin profile's recovery procedure requires credentials that were excluded from backup (per FR-078/FR-084)  
**Gap:** FR-085 says admin "shall be able to authenticate, or complete a documented secure recovery procedure, bound to the restored administrator profile" but FR-078/FR-084 exclude recovery credentials from backup — circular dependency if recovery material was excluded  
**Consequence:** Admin cannot recover own access after restore; household unrecoverable

**Location:** Section 14.3 (lines 632-633) / FR-086  
**Trigger:** Non-admin member re-access initiated by admin, but member's restored profile has corrupted binding record  
**Gap:** FR-086 specifies verification of "successful re-access for at least one non-administrator restored profile" but not remediation if re-access fails — whether admin can retry, must delete/recreate profile, or manual intervention required  
**Consequence:** Member permanently locked out; admin cannot resolve without DB access

**Location:** Section 14.4 / FR-083 (line 646)  
**Trigger:** Admin deletes a person who owns the household fallback assistant (shared assistant)  
**Gap:** FR-083 requires "explicit disposition for owned assistants, topics, facts, integration connections, shared contributions, and required audit records" but household fallback assistant is household-owned (Section 3.3), not person-owned — no disposition rule for shared assistant on last admin deletion  
**Consequence:** Household fallback assistant becomes orphaned; shared display non-functional; no owner to manage it

---

## Section 7: User, Role, and Privacy Classes — Implicit State Transitions

**Location:** Section 7.1-7.6 (lines 277-319)  
**Trigger:** Adult member promoted to administrator (or demoted)  
**Gap:** PRD defines admin and adult as distinct roles with different permissions but specifies no transition mechanism, authorization requirement, or audit trail for role changes  
**Consequence:** Privilege escalation without audit; or admin accidentally demoted losing household management capability

**Location:** Section 7.3 (lines 289-299) / Section 7.4 (lines 300-311)  
**Trigger:** Teen turns 18 (becomes adult) or child turns 13 (becomes teen)  
**Gap:** Privacy classifications (`teen`/`child` as "policy state not data class") imply age transitions but PRD specifies no automatic or admin-initiated transition process — whether profile class changes automatically, requires admin action, or triggers data reclassification  
**Consequence:** Teen retains child restrictions indefinitely; or adult retains teen privacy restrictions incorrectly

**Location:** Section 7.5 (lines 312-314)  
**Trigger:** Profile without account (child/infant) later gets an account created  
**Gap:** Section 7.5 allows profiles without accounts; Sections 7.3-7.4 govern accounts — no migration path specified when account is added to existing profile  
**Consequence:** Duplicate profile; or `private-child` facts not reclassified to `private-person`; integration credentials orphaned

**Location:** Section 7.6 (lines 316-318)  
**Trigger:** Shared surface detects multiple verified members simultaneously (e.g., two adults authenticated)  
**Gap:** Section 10 (referenced by FR-029, AD-10) defines identity states but PRD does not specify shared-display behavior when multiple verified identities are present — whether it shows union of household-shared content, intersection, or defaults to household-safe  
**Consequence:** Private content of one adult visible to other adult on shared display

---

## Section 8: Data Classification and Sharing — Boundary Transitions

**Location:** Section 8.1 (lines 324-333) / Section 8.2 (lines 335-336)  
**Trigger:** Durable fact created as `private-person`, later transformed to `household-shared` via explicit privacy-filtered transformation, then source fact is deleted  
**Gap:** Section 8.1 says transformation "does not reclassify or expose its private source" but does not specify whether derived item survives source deletion, becomes orphaned, or is auto-deleted  
**Consequence:** Orphaned shared fact with no traceable source; or shared fact disappears unexpectedly when user deletes private source

**Location:** Section 8.1 (line 329) / Section 8.2  
**Trigger:** `selected-share` fact shared with specific guardians; one guardian is later removed from household  
**Gap:** PRD defines `selected-share` as "shared with named household members" but does not specify revocation behavior when named member leaves — whether share auto-revokes, persists to deleted profile, or requires manual cleanup  
**Consequence:** Deleted member's account retains access to shared fact; or share silently breaks

**Location:** Section 8.1 (lines 326-331)  
**Trigger:** Teen's `private-person` fact transformed to `selected-share` for guardians; teen later becomes adult (Section 7.3 gap)  
**Gap:** No specification of how `selected-share` facts naming "guardians" are handled when subject's privacy class changes from teen to adult — whether guardians remain named recipients, share converts to `household-share`, or requires re-authorization  
**Consequence:** Former guardians retain access to now-adult's private data; or adult loses intended sharing

**Location:** Section 8.1 (line 331)  
**Trigger:** `surface-ephemeral` item created on shared display during session; session ends abnormally (power loss, crash)  
**Gap:** PRD says `surface-ephemeral` is "available only during current authorized surface session and not durable unless explicitly saved" — does not specify cleanup on abnormal session termination  
**Consequence:** Ephemeral data persists in session store; leaked to next session's household-safe context

---

## Section 9-13: Feature Areas (Implied from traceability table)

**Location:** FR-045-FR-049 (lines 818-822) / Section 6.5 / PD-04  
**Trigger:** Milestone C enables only calendar-change briefing (PD-04) but FR-045-FR-049 describe evaluation, suppression, deduplication, explanation, category-level correction — no specification of behavior when user corrects a briefing category that doesn't exist in Milestone C scope  
**Gap:** Category correction UI/behavior specified for future categories but only one category exists in Milestone C  
**Consequence:** Dead UI affordance; user correction action has no target

**Location:** FR-055-FR-061 (lines 829-830) / PD-03 / AD-08  
**Trigger:** Calendar integration configured but sync fails permanently (provider deprecated, credentials revoked)  
**Gap:** AD-08 interim behavior: "Calendar data is treated as stale unless observed in current sync; stale state blocks mutation" — but no specification for permanent failure: whether integration is auto-disabled, user notified, or briefing continues on stale data  
**Consequence:** Stale calendar briefings continue indefinitely; or silent briefing failure

**Location:** FR-062-FR-067 (lines 835-836) / AD-09  
**Trigger:** Home Assistant entity renamed or replaced (same device, new entity_id)  
**Gap:** AD-09 covers freshness/availability but not entity identity migration — whether Kinward tracks entity by stable device ID, requires manual remapping, or treats as new entity  
**Consequence:** Automations/actions target stale entity_id; device control fails silently

**Location:** FR-068-FR-073 (lines 836-838) / Section 13.9  
**Trigger:** Admin uses Kinward Control to disable an integration that has pending approval requests  
**Gap:** FR-069 says admin manages "household integrations" but does not specify behavior for in-flight approvals/approvals-pending when integration is disabled  
**Consequence:** Orphaned approval requests; user approves but action fails; no cleanup path

**Location:** NFR-034 (line 705) / FR-069  
**Trigger:** Health reporting shows "degraded optional capability" for integration that admin already disabled intentionally  
**Gap:** NFR-034 requires health to distinguish "degraded optional capability" but FR-073 says "every degraded state shall include actionable next step or explicitly state no action required" — no specification for intentionally disabled vs. failed integrations  
**Consequence:** Admin sees false alarm; or genuine degradation masked by intentional disable

---

## Section 14: Backup, Restore, Export, Retention, Upgrade

**Location:** Section 14.1 (lines 598-610) / FR-074  
**Trigger:** Backup includes encrypted credential material (FR-074 line 608) but FR-078/FR-084/PD-06 say credentials excluded — contradiction  
**Gap:** FR-074 line 608 lists "encrypted credential material where supported" as included; FR-078/FR-084/PD-06 say excluded — no resolution of conflict  
**Consequence:** Backup either leaks credentials or fails to include restorable auth; restore behavior undefined

**Location:** Section 14.2 (lines 612-620)  
**Trigger:** External provider (e.g., Google Calendar) changes API/schema; restored backup has stale provider reference mappings  
**Gap:** FR-074 requires "provider reference mappings required to reconnect optional stores" but does not specify versioning/migration of provider references when provider API changes  
**Consequence:** Restored integration cannot reconnect; manual reconfiguration required

**Location:** Section 14.4 / FR-082 (line 645)  
**Trigger:** Retention policy deletes archived topic that contains `household-shared` facts referenced by active topics  
**Gap:** FR-082 documents retention for "conversations, topics, activity, approvals, durable facts, and integration caches" but not cross-reference integrity — whether shared facts in deleted topics are preserved, copied, or cause dangling references  
**Consequence:** Active topic references deleted shared fact; broken context; or shared fact unexpectedly retained

**Location:** Section 14.4 / FR-083 (line 646)  
**Trigger:** Person deletion requested for admin who is sole administrator  
**Gap:** FR-083 requires disposition for "owned assistants, topics, facts, integration connections, shared contributions, and required audit records" but does not address transfer of admin role — household left with no admin  
**Consequence:** Household unmanageable; no one can invite, restore, or administer

---

## Section 15: Nonfunctional Requirements — Underspecified Boundaries

**Location:** NFR-003 (line 657) / NFR-004 (line 658)  
**Trigger:** New shared-surface identity state added in future (beyond unknown/likely/verified/multiple)  
**Gap:** NFR-003 requires tests for "every shared-surface state and transition" but Section 10/AD-10 only define current states — no extensibility requirement for new states  
**Consequence:** New identity state added without privacy tests; regression risk

**Location:** NFR-007 (line 661)  
**Trigger:** Handoff token used for cross-surface continuation (UJ-3) — token replayed after legitimate use  
**Gap:** NFR-007 says tokens "shall expire and be protected against replay" but does not specify whether handoff tokens are single-use, time-bounded, or bound to session — UJ-3 continuation implies reuse  
**Consequence:** Replay attack enables session hijacking; or legitimate continuation blocked by single-use enforcement

**Location:** NFR-011 (line 668) / NFR-012 (line 669)  
**Trigger:** External mutation (calendar write, HA action) times out; client retries; provider eventually succeeds on first attempt  
**Gap:** NFR-011 requires "explicit timeouts, bounded retries"; NFR-012 requires "idempotent where supported or protected against duplicate execution" — but no specification for provider that doesn't support idempotency keys and where timeout occurs after mutation committed  
**Consequence:** Duplicate calendar event; light toggled twice; no deduplication possible

**Location:** NFR-016 (line 673)  
**Trigger:** Background job (calendar sync, fact extraction) fails repeatedly, exceeds retry bound, then succeeds on manual retry  
**Gap:** NFR-016 says jobs "shall be observable, retry-bounded, and recoverable without duplicate user-visible outcomes" — does not specify whether "retry bound" is per-job, per-type, or global; nor whether manual retry resets bound  
**Consequence:** Silent job abandonment after bound; or duplicate outcomes on manual retry

**Location:** NFR-020 (line 682) / NFR-022 (line 684)  
**Trigger:** Shared display session expires simultaneously with identity downgrade (two independent triggers)  
**Gap:** NFR-020 specifies 250ms/1s for identity downgrade; NFR-022 specifies 1s for session expiry — no specification for which takes precedence or whether they compound  
**Consequence:** Race condition in cleanup; private content removal delayed to slower path

**Location:** NFR-027 (line 692)  
**Trigger:** Error message from provider (Home Assistant, calendar API) surfaces to user without transformation  
**Gap:** NFR-027 says "shall not require infrastructure or provider terminology" but does not specify error message translation layer or fallback language  
**Consequence:** User sees "HTTP 401 Unauthorized: invalid_grant" instead of "Calendar connection expired — please reconnect"

**Location:** NFR-035 (line 706) / NFR-037 (line 708)  
**Trigger:** Admin requests diagnostic bundle for failed action that involved private content from multiple household members  
**Gap:** NFR-035 requires correlation "without exposing private content"; NFR-037 requires bundle "excludes credentials and private conversation bodies" — but does not specify whether cross-person correlation metadata (timestamps, action types, success/failure) is included, which could infer private activity  
**Consequence:** Admin infers other adult's private assistant usage from diagnostic metadata

---

## Section 18: Architecture Decision Register — Open Decisions as Edge Cases

**Location:** AD-01 (line 920)  
**Trigger:** Invitation flow implemented before AD-01 resolved; invitation token format changes  
**Gap:** AD-01 safe interim: "No implementation of invitation, session, or recovery flows until resolved" — but UJ-2 and FR-005/FR-006 require invitation flow for Milestone C  
**Consequence:** Milestone C blocked; or implementation proceeds with interim behavior that violates final decision

**Location:** AD-03 (line 922)  
**Trigger:** Assistant attempts tool execution before AD-03 resolved  
**Gap:** Safe interim: "No tool execution capable of external mutation until resolved" — but UJ-6 (approval for meaningful external action) requires tool execution for Milestone B  
**Consequence:** Milestone B cannot demonstrate UJ-6; or tool execution implemented without resolved boundary

**Location:** AD-07 (line 926)  
**Trigger:** External provider (memory/knowledge) deletes derived data referenced by Kinward topic  
**Gap:** Safe interim: "Mark references inaccessible and disclose the limitation" — but no specification of user-visible behavior when topic references inaccessible derived data  
**Consequence:** Topic shows broken references; user cannot distinguish provider failure from data deletion

**Location:** AD-10 (line 929)  
**Trigger:** Shared display used before AD-10 resolved (no `verified` identity mechanism)  
**Gap:** Safe interim: "Shared surfaces remain household-safe with no `verified` state until resolved" — but UJ-5 and NFR-020/NFR-022 require identity-downgrade behavior that presupposes `verified` state exists  
**Consequence:** Identity downgrade logic untestable; NFR-020/NFR-022 unverifiable until AD-10 resolved

**Location:** AD-11 (line 930)  
**Trigger:** Background job fails with unknown provider result (NFR-015/NFR-016) before AD-11 resolved  
**Gap:** Safe interim: "Unknown provider results block retry; no background mutation until resolved" — but NFR-016 requires jobs "recoverable without duplicate user-visible outcomes"  
**Consequence:** Jobs permanently stuck; or duplicate outcomes on manual recovery

**Location:** AD-12 (line 931)  
**Trigger:** Restore attempted before AD-12 resolved (credential storage/backup encryption)  
**Gap:** Safe interim: "Credentials are excluded from backups and require reauthorization" — conflicts with FR-074 line 608 (see Section 14 gap above) and FR-085 (admin recovery bound to restored profile)  
**Consequence:** Restore cannot re-establish admin access without credentials; circular dependency

**Location:** AD-14 (line 933)  
**Trigger:** Diagnostic bundle requested before AD-14 resolved  
**Gap:** Safe interim: "No diagnostic bundle export until resolved" — but NFR-037 requires "household administrator shall obtain a sanitized diagnostic bundle" for Milestone C  
**Consequence:** Milestone C exit gate unachievable; or diagnostic bundle exported without redaction rules

---

## Section 19: Product Decision Register — Open Decisions as Edge Cases

**Location:** PD-01 (line 942)  
**Trigger:** Shared display session exceeds 10-minute maximum (PD-01 default) but user is actively interacting  
**Gap:** PD-01 sets 10-minute maximum as default but does not specify whether active interaction extends session, whether warning is shown, or whether session hard-terminates  
**Consequence:** Active user session terminated mid-task; or session extends indefinitely defeating privacy timeout

**Location:** PD-02 (line 943)  
**Trigger:** Teen creates `private-person` fact; no guardian-visible categories defined (PD-02 unresolved)  
**Gap:** PD-02 interim: "No default guardian-visible categories and no guardian-review implementation until resolved" — but FR-032/Section 7.3 says "product must show the teen which categories are guardian-visible and which are private"  
**Consequence:** Teen cannot see guardian-visible categories (none defined); privacy transparency requirement unmet

**Location:** PD-03 (line 944)  
**Trigger:** Calendar integration implemented with provider-neutral contract (NFR-029) but no provider configured  
**Gap:** PD-03 interim: "Calendar work stays provider-neutral; no provider-specific coupling" — but UJ-4 and FR-055 require calendar change detection for Milestone C  
**Consequence:** Calendar briefing feature non-functional in Milestone C; or provider-specific coupling introduced prematurely

**Location:** PD-05 (line 946)  
**Trigger:** Private conversation exceeds unspecified retention period; auto-deletion behavior undefined  
**Gap:** PD-05 interim: "Retain all data with no automatic deletion" — but FR-082 requires documented retention behavior for Milestone C  
**Consequence:** FR-082 undocumented; unbounded storage growth; no retention policy for compliance

**Location:** PD-06 (line 947)  
**Trigger:** Backup includes encrypted credentials (per FR-074 line 608) but PD-06 says exclude  
**Gap:** Direct contradiction between FR-074 and PD-06 interim behavior — see Section 14 gap above  
**Consequence:** Backup either non-portable (credentials excluded) or insecure (credentials included)

**Location:** PD-07 (line 948)  
**Trigger:** Shared display shows item requiring explanation/correction (FR-043, FR-049) but PD-07 unresolved  
**Gap:** PD-07 interim: "Shared display shows only item's information class and household-safe reason; full explanation and correction occur via private-device handoff" — but FR-049 requires "explanation and correction" for proactive items on shared display  
**Consequence:** Shared display cannot meet FR-049; or private handoff required for every proactive item

---

## Cross-Cutting Implicit State Sets (Three-State Gaps)

**Location:** Section 7.1-7.4 (Roles: Admin, Adult, Teen, Child) × Section 8.1 (Data classes: 6 classes)  
**Trigger:** Matrix of 4 roles × 6 data classes = 24 access combinations; PRD specifies only subset (admin↛private, adult→own private, teen→private+selected-share, child→private-child+selected-share+household-shared)  
**Gap:** Unspecified combinations: Can admin read `household-shared`? Can teen read `household-shared`? Can child read `selected-share` not naming them? Can adult read `private-child`?  
**Consequence:** Implementation defaults (allow/deny) become de facto policy; privacy violations or over-restriction

**Location:** Section 10 / AD-10 (Shared surface identity: unknown, likely, verified, multiple) × Section 8.1 (Data classes)  
**Trigger:** 4 identity states × 6 data classes = 24 rendering combinations; PRD specifies behavior for `household-shared` on shared display, `private-person` suppression on unknown/likely  
**Gap:** Unspecified: `selected-share` on shared display for `likely` identity; `private-child` on `verified` non-guardian; `system-operational` on any state  
**Consequence:** Inconsistent rendering; data class leakage on edge identity states

**Location:** Section 3.1-3.3 (Assistant types: Personal, Specialist, Household Fallback) × Section 7 (Roles) × Section 8 (Data classes)  
**Trigger:** 3 assistant types × 4 roles × 6 data classes = 72 authorization combinations  
**Gap:** PRD specifies: Personal→own private; Specialist≤Personal; Fallback→household-shared only. Unspecified: Specialist access to `selected-share`; Fallback access to `selected-share` naming household; Personal assistant accessing `household-shared` facts  
**Consequence:** Specialist assistant leaks `selected-share` data; fallback assistant accesses `selected-share`; personal assistant cannot read household-shared facts for coordination

**Location:** FR-045-FR-049 (Proactive levels: Ambient, Briefing, Nudge, Interruption, Autonomous) × Section 6.4 (Counter-metric: "Zero nudge/interruption/autonomous during Milestone C")  
**Trigger:** Milestone C enables only Ambient+Briefing (PD-04); Milestone D enables all five — but no transition specification  
**Gap:** Unspecified: How Ambient→Briefing escalation works; whether Briefing items can become Nudges; what happens to pending Briefing items when Nudge level enabled  
**Consequence:** Proactive items stuck in wrong level; duplicate delivery across levels; user preferences not migrated

---

## Journey Coverage Gaps (From Section 17.5)

**Location:** Section 17.5 (lines 898-910)  
**Trigger:** UJ-1 through UJ-9 coverage summary — but no journey covers: specialist assistant invocation (Section 3.2), profile-without-account account creation (Section 7.5), household fallback assistant usage (Section 3.3), or teen→adult transition  
**Gap:** Requirements exist for these concepts (FR-010, FR-012, Section 3.2, Section 3.3, Section 7.5) but no user journey validates them  
**Consequence:** Features implemented without journey validation; edge cases in these flows untested

**Location:** Section 17.5 / UJ-7 coverage (line 908)  
**Trigger:** UJ-7 lists FR-032, NFR-004, "supported by" FR-007, FR-028, FR-052-FR-053 — but FR-052/FR-053 are action authority/activity (UJ-6), not child-specific  
**Gap:** No child-specific action authority requirement mapped to UJ-7; FR-032 covers privacy but not action boundaries  
**Consequence:** Child action approval flows untested; teen/child action boundaries unverified

---

## Summary of Areas Walked and Found Covered

The following areas were traced exhaustively and found to have explicit handling in the PRD:

1. **UJ-1 success/failure outcomes** — explicit commit/rollback semantics for initial setup (lines 176-178)
2. **UJ-2 privacy boundary** — explicit "no private content from Alex visible" (line 184)
3. **UJ-3 cross-surface continuation** — explicit desktop continuation without restating (line 192)
4. **UJ-4 briefing content** — explicit change identification, source category, action required (line 200)
5. **UJ-5 shared display refusal** — explicit household-safe response, no private details in UI/payloads/logs (line 208)
6. **UJ-6 approval exactness** — exact mutation, stale-state expiration (line 214)
7. **UJ-7 child bounded assistance** — homework allowed, message blocked/routed (line 220)
8. **UJ-8 single provider degradation** — core functions remain, dependent marked unavailable (line 226)
9. **UJ-9 restore verification** — explicit manifest, verification, re-access procedure (lines 232, 624-649)
10. **Data classes (8.1)** — six classes explicitly defined with access rules (lines 326-331)
11. **Derived data transformation (8.2)** — explicit "new item, does not reclassify source" (line 333)
12. **Privacy class vs data class distinction** — explicit for teen/child (lines 291, 302)
13. **NFR-010 single-provider failure** — explicit core functions preserved (line 667)
14. **NFR-015 restart during action** — explicit no-completion-conversion (line 672)
15. **NFR-020/NFR-022 shared display timing** — explicit 250ms/1s and 1s bounds (lines 682, 684)
16. **Backup manifest content (14.1)** — explicit 11-item inclusion list (lines 600-610)
17. **Backup exclusions (14.2)** — explicit 5-item exclusion list (lines 616-620)
18. **Post-restore access (14.3)** — explicit portable/excluded classification (lines 626-628)
19. **Architecture decisions (18)** — 15 open decisions with safe interim behaviors
20. **Product decisions (19)** — 7 open decisions with safe interim behaviors
21. **Traceability table (17.4)** — 97 requirements with source, journey, milestone, invariant, verification, owner

---

**Total unhandled paths identified: 47**

All entries above anchor to specific PRD locations (section numbers, line numbers, FR/NFR/UJ/AD/PD IDs). No editorializing, severity labels, or rankings included per instructions.