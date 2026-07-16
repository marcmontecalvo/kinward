# Operational Household Context (v0 heuristic)

`docs/adr/ADR-002-cross-principal-assistant-access-boundary.md` Section 3 describes
"operational household context": resolving follow-up references such as "turn that light back
off" or "cancel the timer" regardless of who issued the original command or which voice node
hears the follow-up. This document is the concrete v0 implementation of that section -
`services/kinward/src/kinward/application/operational_context.py`.

## What this is - and isn't

This is a **live heuristic**, not durable memory. It is separate from:

- Honcho conversational memory (`memory-and-knowledge.md`) - nothing here is written to or read
  from a person's conversational history.
- The raw HA entity-state dump already folded into the system prompt for LLM grounding
  (`model-provider.md`'s "Conversation grounding" section) - that lists every entity's current
  state; this picks out one specific "most recently changed" candidate.

An earlier design for this section proposed a persistent `recent_actions`/`active_timers`
database store with its own migration and retention/lifecycle metadata. That was deliberately
**not built**: build the smallest thing that could work first, prove it out in real household
use, and only add Kinward-side persistence if testing shows Home Assistant's own state can't
support reliable cross-node lookup. This doc and its module are that smaller v0.

## How it works

`resolve_recent_device` and `resolve_recent_timer`
(`services/kinward/src/kinward/application/operational_context.py`) share one algorithm
(`_resolve_recent_entity`):

1. Filter the household's current HA entity states (already fetched once per conversation turn
   for prompt grounding - not re-fetched) to the eligible domains/states:
   - Devices: `light`/`switch`, states `on`/`off`, within a 5-minute recency cutoff
     (`RECENT_DEVICE_CUTOFF_MINUTES`).
   - Timers: `timer` domain, state `active`, **no recency cutoff** - a 30-minute timer is still
     "the" timer to cancel long after 5 minutes have passed; "currently active" is the filter,
     not recency.
2. If a `device_id` was supplied, resolve its area via Home Assistant's own template engine
   (`{{ area_id(device_id) }}`) and narrow the candidate pool to entities in that area
   (`{{ area_entities(area_id) | join(',') }}`). An **empty** area intersection never wipes out a
   real household-wide match - it just means "nothing changed in this room recently," not
   "nothing changed anywhere."
3. Sort the remaining candidates by `last_changed` descending and return the most recent one.
   Ties are broken by whichever the sort emits first - there is no separate "ambiguous" outcome
   in this v0 (the ADR's fuller ranking-tier/ambiguity design is deferred, see below).
4. No eligible, non-stale candidate anywhere -> `NoEntityCandidate()`. The backend never invents
   an entity or timer.

Only `resolve_area_for_device`/`entities_in_area` call out to Home Assistant (via
`HomeAssistantClient.render_template`, a thin wrapper around `POST /api/template`); everything
else is plain Python filtering/sorting over an already-fetched states list.

## Accepted limitation

`last_changed` proves an entity's state changed - it does not prove Kinward caused the change.
An automation, physical switch, another HA user, or an integration could all become the newest
candidate. HA restarts or entity-reload behavior can also affect timestamps. This is acceptable
for v0 given the short recency cutoff (devices), current-area preference, and "no candidate"
fallback - it is a provisional heuristic, not durable operational memory.

## Why no persistence, migration, or lifecycle entries exist yet

There are no new database tables, Alembic migrations, or `domain/lifecycle.py` entries for this
feature - everything is computed live from Home Assistant on each request. The trigger for
building real Kinward-side persistence (the `recent_actions`/`active_timers` store from the
ADR's fuller design) is **demonstrated failure in household testing** - for example: cross-node
follow-ups repeatedly resolving to the wrong entity, HA restarts breaking timestamp-based
matching, or timers whose HA-side representation can't support reliable cross-node lookup. Until
real usage shows that gap, adding a parallel Kinward-side store would be unvalidated complexity.

## Why area resolution calls Home Assistant instead of a Kinward registry client

Kinward has no entity/device/area-registry client of its own, and does not need one: Home
Assistant already knows this and exposes it through its own Jinja template engine
(`area_id()`/`area_entities()`), which is a small, well-established part of HA's public template
API. Two single-expression template calls are the entire HA-facing surface this feature adds;
everything else (domain/state/recency filtering, sorting) is ordinary, directly unit-tested
Python over data Kinward already has.

**This is also this feature's main untested edge**: HA's actual Jinja template environment
(with its custom globals like `area_id`/`area_entities`) cannot be executed inside Kinward's own
Python test suite. `tests/test_operational_context.py` verifies the request/response plumbing
(`render_template` sends the right body, parses the right text back) and the pure-Python
filtering/sorting logic, but the two template expressions themselves are only as trustworthy as
a live-HA smoke test proves - see `docs/ha-native/household-trial.md`.

## Configuration

`RECENT_DEVICE_CUTOFF_MINUTES`, `RECENT_DEVICE_DOMAINS`, `RECENT_DEVICE_ELIGIBLE_STATES`,
`RECENT_TIMER_DOMAINS`, and `RECENT_TIMER_ELIGIBLE_STATES` are plain module constants in
`operational_context.py`, not `Settings`/`ProviderSettingsRecord` fields - matching
`application/conversation.py`'s own `MAX_HOME_STATE_ENTITIES`/`MEMORY_RECALL_LIMIT` style. These
are algorithm-tuning knobs with no admin-facing configuration story in the ADR (unlike
`Settings.setup_authorization_ttl_seconds`, which is a real security control). Promote them to
runtime configuration only if real household testing shows they need per-household tuning.

## Conversation grounding

`application/conversation.py`'s `handle_conversation_request` now accepts a `device_id`
(threaded from Home Assistant's `ConversationInput.device_id` through
`custom_components/kinward/conversation.py` -> `api.py` -> the backend's
`/api/v1/integration/conversation` endpoint). When Home Assistant is configured, it calls
`resolve_recent_device`/`resolve_recent_timer` once per turn (reusing the same `states()` fetch
already used for home-state grounding) and folds a resolved match into the system prompt, e.g.:

```text
Most recently changed light/switch: light.office is on (changed 2026-07-16T12:09:00+00:00).
Currently active timer: timer.kitchen.
```

## What remains out of scope

- **No actual device control or timer cancellation.** Kinward's LLM layer
  (`llm/contracts.py`) has no tool-calling/function-calling support at all yet, and
  `HomeAssistantClient.call_service()` still has zero call sites (Epic 7 Story 7.3, unchanged
  by this work). This resolver only lets the model *describe* recent state/timers in a reply -
  it cannot yet act on them.
- **No tiered ranking or ambiguity handling** from the ADR's fuller design (current-room >
  current-assistant > household-window for devices; ringing > only-active > room >
  household-manageable for timers). v0 is a single most-recently-changed-wins heuristic.
- **No authorization check for timer cancellation** - moot for now since no cancellation call
  site exists yet, but also matches product intent: any household member may reference or
  manage a household timer.
