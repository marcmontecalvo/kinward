# ADR-002: Privacy Boundary for Cross-Person Assistant Access

**Status:** Proposed
**Date:** 2026-07-16

## Context

Today Kinward recognizes exactly two categories of assistant access:

1. **Owner access** - a person talking to their own primary assistant gets full
   access to that assistant's private memory/knowledge about them (their own
   facts, their own conversation history).
2. **Fallback/shared access** - an unmapped HA user or a shared display talks
   to Home Assistant's own built-in agent (or the household fallback
   assistant), which has zero private memory access and only ever sees
   household-shared context (epics.md Story 2.5).

The product direction is for a household to have multiple personal
assistants per person (see ADR/epics work on relaxing the one-assistant-per-
person constraint), with any person able to directly address *another*
person's assistant - e.g. Marc says "hey Calopex" to Lisa's assistant. This is
a genuinely new third category that fits neither existing bucket:

- It is not owner access - Marc doesn't own Calopex.
- It is not anonymous/fallback access either - Marc is a known, mapped
  household member; Calopex should presumably recognize him as *Marc*, not
  treat him as an anonymous visitor the way an unmapped user is treated today.

Without an explicit rule, "any person can address any assistant" risks one of
two failure modes:

- **Silent over-disclosure**: Calopex, talking to Marc, surfaces something
  private about Lisa (a memory recalled from Lisa's own sessions, a personal
  fact from the knowledge store) because the code path doesn't distinguish
  "talking to my owner" from "talking to someone else."
- **Silent under-usefulness**: to avoid the above, Calopex refuses to have
  *any* useful context when talking to Marc, defeating the purpose of
  allowing the interaction at all.

Both are bad, and nothing in the codebase today has an explicit answer to
which is correct. Building "any person -> any assistant" without deciding
this first means guessing at a privacy policy inside implementation code -
exactly what cross-cutting rule 6 (no private-body leakage) and Story 3.3
(role and privacy are separate, explicit axes) say not to do.

This also directly affects the knowledge store, not just conversational
memory: whatever boundary governs Honcho recall must govern `search_facts`/
`propose_fact` the same way, or the two providers will silently drift apart.

## Decision (proposed)

Define exactly what an assistant is allowed to know, remember, and say when
addressed by someone other than its owner, as a single explicit, testable
authorization boundary - not scattered heuristics - satisfying:

- **One rule, two callers.** The same boundary check gates both Honcho
  recall and knowledge-store search/propose. No provider-specific privacy
  logic that can drift.
- **Fails closed by default.** An interaction with no explicit authorization
  reveals nothing private, matching every other fail-closed pattern already
  in the codebase (unmapped HA users, cross-person topic access, admin
  invariant checks).
- **Owner-controllable, not just an engineering default.** "How much can
  other people learn from talking to my assistant" is the owner's decision
  to make, not a hardcoded constant - this mirrors Story 3.3's existing
  principle that privacy authorization is a separate, explicit axis from
  role.

### Option A: Household-shared-only by default, isolated per-pair sessions

When person X talks to assistant B (owned by person Y, X != Y):

- **Memory (Honcho):** use the session already keyed by `(X, B)` - this falls
  out of the existing `session_id(person_id, assistant_id)` design for free.
  It is structurally isolated from B's session with its actual owner Y
  (different `person_id` in the pair -> different session). Recall only
  searches within the `(X, B)` session's own history; there is no
  cross-session recall into `(Y, B)`'s history. **No new code needed for
  this half** - it's what the current session keying already gives you.
- **Knowledge (llm_wiki):** when B is talking to X, `search_facts` only
  returns facts where `privacy == "household"` - never `"personal"` or
  `"sensitive"` facts belonging to Y. **This does require a code change**:
  the privacy filter must key off *who this conversation is with*, not just
  which assistant/person owns the fact.
- **Net effect:** talking to someone else's assistant is like talking to a
  housemate's friend - it remembers what the two of you have discussed
  together and knows general household facts, but never leaks the owner's
  personal life.

Tradeoff: simple, safe by default, ships with no per-owner configuration.
Downside: may feel less "smart" than an owner might want - e.g. if Lisa is
fine with Calopex telling Marc her Monday schedule, this default says no
unless that fact is explicitly marked household-visible.

### Option B: Owner-configurable disclosure grants, checked at the same boundary

Add an explicit, owner-controlled grant: something like
`(assistant_id, granted_to_person_id_or_null_for_anyone, scope)`, where
`scope` might be `"schedule"`, `"household_facts"`, or a named fact category.
Before returning any private-classified memory/fact to a non-owner caller,
check whether an active grant covers `(this assistant, this caller, this
category)`; if not, fall back to Option A's household-only default.

This is Option A's default *plus* an explicit, revocable, inspectable grant
an owner can turn on for specific people/topics - it directly generalizes
Story 3.3's existing "teen private disclosure... exact owner-authorized,
privacy-filtered exception" pattern from parent-of-teen to any two adults. It
also gives a natural hook for an admin-approval-gated future: the same grant
shape models "who is allowed to learn what from whom," which is exactly what
Epic 6's meaningful-action approval will need for assistant-to-assistant
delegation later.

Tradeoff: real product surface (an owner-facing UI/API to manage grants) and
more code, but it's the only option where Lisa can actually decide "yes,
Calopex can tell Marc my Monday schedule" instead of living with a hardcoded
rule.

### Option C: Open by default, single household-wide restriction toggle

Default to full disclosure (assistant B tells X everything it would tell Y),
with one household-level "restrict cross-person assistant access to
household-shared facts only" toggle admins can flip.

Tradeoff: least engineering effort, matches an "everyone here trusts each
other" framing, but violates fail-closed-by-default and risks a bad surprise
the first time it happens, with no prior chance to have configured
otherwise. Not recommended as a default even if an "open household" toggle
is offered later - default-closed is safer, and Option A already provides
useful default behavior (household facts) with zero configuration.

## Recommendation

Ship Option A now as the baseline for cross-person assistant access - safe
default, no new product surface, and it falls out of the existing session-
keying design almost for free. Shape the knowledge-store check so it reads
as "no active grant -> household-only," so Option B's grant table can be
added later as a pure addition, not a rework.

## Open questions for review

- Does "household-shared" facts-only feel right as the *default* ceiling, or
  should some categories (e.g. calendar/schedule) be treated as
  household-visible by default even when marked personal, given the
  household-coordination use case in the original ask?
- Should the assistant *tell* the non-owner caller when it's withholding
  something ("I can't share that - ask Lisa directly"), or stay silent about
  the omission? Silent omission is safer against over-disclosure through
  inference but may read as evasive.
- Where should Option B's grants live and who can manage them - self-service
  by the owner only, or also admin-visible/revocable?
