# Epic 5: Briefings, Calendar Awareness, and Proactive Attention

## Goal

Use Home Assistant calendar entities, dashboards, Assist, and notifications to surface meaningful calendar changes and current household context without recreating a generic notification feed.

Kinward should continuously maintain a useful briefing that can be viewed in Home Assistant or summarized verbally by a Kinward assistant. In v0, Home Assistant remains the calendar authority and Kinward accepts Home Assistant's existing calendar visibility model.

---

## Scope Decisions

### v0

- Use Home Assistant calendar entities directly.
- Accept Home Assistant's existing all-or-nothing calendar visibility model.
- Do not invent calendar ownership, per-person visibility, or edit controls that Home Assistant does not provide.
- Use the Home Assistant calendar state as the source available to Kinward.
- Recompute briefing and attention state when Home Assistant reports calendar changes.
- Expose a continuously current Briefings Card in the Kinward Home Assistant dashboard.
- Allow assistants to use the same briefing information when answering questions such as:
  - "What does the morning look like?"
  - "What is happening today?"
  - "Anything I need to know?"
- Allow Home Assistant push notifications for supported meaningful changes after significance filtering and deduplication.
- Leave additional delivery methods such as email, announcements, or custom mobile notification flows to Home Assistant automations.

### v1

- Add direct Google Calendar and Microsoft Outlook calendar connections.
- Create a Kinward-controlled Home Assistant calendar dashboard or calendar surface.
- Add real per-person view and edit permissions.
- Preserve provider-native calendar identity, change versions, attendee state, and mutation capabilities.
- Prefer provider push notifications or webhook-style change delivery where supported.
- Use polling only as a fallback, with a configurable refresh interval such as one or five minutes.

---

## Core Concepts

### Attention item

An attention item is a durable record that a meaningful calendar condition may need notice or action, such as a cancellation, time change, location change, overlap, or RSVP requirement.

### Attention state

Attention state tracks the lifecycle of an attention item.

Supported states:

- `active`
- `acknowledged`
- `dismissed`
- `resolved`
- `expired`
- `superseded`

State behavior:

- **Acknowledged:** The user has seen the item. It remains visible but is de-emphasized until resolved.
- **Dismissed:** The item is hidden unless the underlying event changes materially again.
- **Resolved:** Kinward automatically detects that the issue no longer exists and closes it.
- **Expired:** The item is no longer relevant because its useful time window has passed.
- **Superseded:** A newer meaningful change replaces the prior item.

Users should not be required to manually resolve calendar issues.

An item may reappear only when:

- the underlying event changes materially,
- the issue returns after being resolved,
- or the deadline or impact materially worsens.

---

## Meaningful Calendar Changes

Kinward creates or updates attention items for all of the following:

- Event cancellations
- Meaningful time changes
- Meaningful location changes
- Calendar overlaps
- RSVP or response requirements

All supported change types may produce Home Assistant push notifications after significance filtering, privacy checks, interruption policy, and deduplication.

### Significance thresholds

#### Time changes

- Treat a change of **five minutes or more** as meaningful.
- Ignore changes smaller than five minutes as likely calendar churn.

#### Location changes

- Treat any actual location change as meaningful.
- Ignore formatting-only differences such as:
  - capitalization,
  - punctuation,
  - whitespace,
  - common address abbreviation differences,
  - equivalent normalized addresses.

#### Overlaps

- Treat any overlap of **five minutes or more** as meaningful.
- Also detect back-to-back events when:
  - locations differ,
  - and there is no travel buffer between them.

Travel-time estimation is not required for v0. The initial rule only needs to recognize that different locations with no buffer may require attention.

#### RSVP requirements

Create an attention item when:

- the calendar reports that a response is required,
- the invitation remains unanswered,
- and the event is still upcoming.

---

## Deduplication and Change Handling

Kinward must not create a new attention item every time Home Assistant refreshes the same calendar state.

Required behavior:

- Repeated observation of the same change updates the existing attention item.
- Each logical calendar condition has one active attention item.
- A materially different change may supersede the existing item.
- A dismissed item remains dismissed unless a new meaningful change occurs.
- A resolved issue may create a new active item if it later returns.
- Notification delivery is tracked separately so the same change is not repeatedly pushed.

---

## Briefing Behavior

The briefing is a continuously current projection of calendar state and active attention items. It is not a separate source of truth.

The briefing should include:

- Important upcoming events
- Active cancellations
- Meaningful time changes
- Meaningful location changes
- Calendar overlaps
- RSVP requirements
- Recently resolved changes when still useful
- An explicit useful empty state when nothing requires attention

The briefing should prioritize:

1. Required action
2. Urgency
3. Consequence if ignored
4. Recency
5. Confidence
6. Household relevance

The briefing must remain concise enough to glance at in Home Assistant and concise enough for a spoken assistant summary.

---

## Home Assistant Presentation

### Briefings Card

The default Kinward Home Assistant dashboard includes a Briefings Card that remains current throughout the day.

The card should:

- refresh when the underlying Kinward briefing entity updates,
- display the most important current items first,
- show an explicit empty state,
- distinguish active, acknowledged, and recently resolved items,
- avoid exposing large nested payloads in entity attributes,
- remain usable with built-in Home Assistant cards,
- remain truthful when calendar data is stale or unavailable.

Kinward should not implement a separate polling schedule for the card in v0. Home Assistant entity updates should drive the card refresh.

The practical refresh delay is limited by how quickly Home Assistant receives the upstream calendar change.

### Assistant access

Kinward assistants may use the same briefing data to answer spoken or typed questions about the day, morning, evening, schedule, conflicts, or upcoming obligations.

The assistant may summarize only the structured briefing and calendar information available through the authorized Kinward request. It must not independently invent calendar conflicts or importance.

### Notifications

All supported meaningful change types may produce Home Assistant push notifications.

Notification policy must:

- deduplicate repeated delivery,
- respect quiet periods,
- avoid repeated notifications for the same unchanged item,
- avoid notifying from stale calendar state,
- update or supersede prior attention rather than creating noise,
- leave email, announcements, and other delivery channels to Home Assistant automations.

---

## Story 5.1: Read Home Assistant Calendar Entities

As a household member,  
I want Kinward to read the calendars already available in Home Assistant,  
So that calendar awareness works without adding new provider connections in v0.

### Acceptance criteria

- Kinward reads configured Home Assistant calendar entities through a provider-neutral calendar adapter.
- Home Assistant remains authoritative for which calendars and events are available.
- Kinward does not add calendar ownership, per-person visibility, or edit controls in v0.
- Calendar entities can be enabled or disabled for Kinward independently.
- Event observations retain:
  - Home Assistant calendar entity identity,
  - event identity when available,
  - observed time,
  - start and end time,
  - title,
  - location,
  - status,
  - attendee or RSVP information when exposed,
  - freshness.
- Unavailable, stale, disabled, and configuration-error states remain distinct.
- Calendar content is bounded and sanitized before entering logs, entity state, prompts, or activity records.
- Kinward responds to Home Assistant calendar updates without requiring its own dashboard polling schedule.

---

## Story 5.2: Detect Meaningful Calendar Changes

As a household member,  
I want Kinward to recognize meaningful calendar changes,  
So that I do not need to manually compare calendar versions.

### Acceptance criteria

- Kinward detects:
  - cancellations,
  - time changes,
  - location changes,
  - overlaps,
  - RSVP requirements.
- Time changes smaller than five minutes are ignored.
- Location comparisons normalize formatting-only differences.
- Overlaps shorter than five minutes are ignored.
- Back-to-back events at different locations with no travel buffer are treated as a possible conflict.
- Repeated synchronization of unchanged calendar state does not create duplicate changes.
- Stale calendar state cannot support a claim that a change is current.
- Change detection remains deterministic and testable.
- An LLM does not decide whether a meaningful change occurred.

---

## Story 5.3: Create and Maintain Attention Items

As a household member,  
I want meaningful calendar conditions tracked consistently,  
So that Kinward can show, notify, dismiss, and resolve them without losing state.

### Acceptance criteria

- A meaningful calendar condition creates one durable attention item.
- Attention items support:
  - active,
  - acknowledged,
  - dismissed,
  - resolved,
  - expired,
  - superseded states.
- Acknowledged items remain visible but de-emphasized.
- Dismissed items remain hidden unless a materially new change occurs.
- Kinward automatically resolves items when the underlying issue no longer exists.
- Items may reappear only when:
  - a materially new change occurs,
  - a resolved issue returns,
  - or the deadline or impact materially worsens.
- Repeated syncs update the existing item rather than creating duplicates.
- New changes may supersede prior items while preserving history.
- Users are not required to manually resolve calendar attention items.
- Attention state remains separate from notification delivery state.

---

## Story 5.4: Generate the Continuously Current Briefing

As a household member,  
I want a current briefing available throughout the day,  
So that I can glance at what matters or ask my assistant for a summary.

### Acceptance criteria

- Kinward maintains a current briefing projection from calendar state and active attention items.
- The briefing includes important upcoming events and supported meaningful changes.
- Required action and urgent items appear before informational items.
- The briefing supports a concise Home Assistant representation.
- The same structured briefing can be used by Assist for verbal or typed summaries.
- The briefing exposes an explicit useful empty state.
- The briefing is recomputed when relevant calendar or attention state changes.
- The briefing is not stored as a second independent source of truth.
- If an LLM is used for wording, it receives policy-filtered structured facts only.
- A deterministic fallback summary exists when no model is available.
- The assistant does not independently decide whether an event is important or conflicting.

---

## Story 5.5: Expose the Briefing Through Home Assistant

As a household member,  
I want the briefing visible in the Kinward Home Assistant dashboard,  
So that I can understand the day without opening a separate application.

### Acceptance criteria

- The default Kinward dashboard includes a Briefings Card using built-in Home Assistant cards.
- The card updates when the Kinward briefing entity updates.
- No separate dashboard polling loop is required.
- The card shows the highest-priority items first.
- Active, acknowledged, and recently resolved items are distinguishable.
- The card provides an explicit empty state.
- Entity state and attributes remain bounded and safe for Home Assistant recorder and logbook exposure.
- Calendar freshness and degraded state are visible.
- The dashboard remains truthful when Kinward or calendar sources are unavailable.
- Kinward Assist requests can access the same briefing information.

---

## Story 5.6: Deliver Deduplicated Home Assistant Notifications

As a household member,  
I want meaningful calendar changes pushed through Home Assistant when appropriate,  
So that important changes can reach me without creating repeated noise.

### Acceptance criteria

- Cancellations, meaningful time changes, meaningful location changes, overlaps, and RSVP requirements are eligible for push notification.
- Notification delivery occurs only after:
  - significance filtering,
  - deduplication,
  - freshness validation,
  - quiet-period evaluation,
  - interruption-policy evaluation.
- The same unchanged attention item is not repeatedly pushed.
- A materially changed or worsened item may generate a new notification.
- Dismissed items do not generate another notification unless they materially change.
- Notification failure does not change the truth or lifecycle state of the attention item.
- Home Assistant notifications are an adapter; Kinward decides what is eligible to be delivered.
- Email, announcements, and additional delivery methods remain Home Assistant automation concerns in v0.

---

## v0 Completion Slice

Epic 5 v0 is complete when the following end-to-end scenario works:

1. Home Assistant exposes a configured calendar entity.
2. An event changes by at least five minutes, changes location, is cancelled, overlaps another event, or requires RSVP.
3. Kinward receives the updated Home Assistant calendar state.
4. Kinward detects the meaningful change once.
5. Kinward creates or updates one attention item.
6. The Briefings Card updates without manual refresh.
7. A Kinward assistant can verbally summarize the same information.
8. A deduplicated Home Assistant push notification may be delivered.
9. Repeated calendar refreshes do not create duplicate items or notifications.
10. The attention item resolves automatically when the underlying condition no longer exists.

---

## Explicitly Deferred Beyond v0

- Direct Google Calendar integration
- Direct Microsoft Outlook calendar integration
- Provider-native push notifications and change tokens
- Kinward-controlled per-person calendar visibility
- Kinward-controlled per-person calendar editing
- Calendar mutation flows
- Cross-person calendar approval flows
- Travel-time provider integration
- Detailed transportation assignment
- Custom Kinward calendar dashboard or frontend card
- Email delivery implemented directly by Kinward
- Repeated escalation or emergency notification behavior
