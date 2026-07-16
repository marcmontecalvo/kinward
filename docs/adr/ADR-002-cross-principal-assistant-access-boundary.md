# ADR-002: Privacy Boundary for Cross-Person Assistant Access

**Status:** Proposed
**Date:** 2026-07-16

## Context

Kinward supports personal AI assistants that may be addressed by more than one
household member.

For example:

- Marc owns AI Bob.
- Lisa owns AI Joe.
- Marc normally speaks to AI Bob.
- Lisa may also be allowed to speak to AI Bob when she needs access to a tool
  connected to Bob, such as Marc's calendar.

Cross-person assistant access does not mean that household members receive
access to one another's conversational memories.

When Lisa speaks to AI Bob, the useful purpose is generally to:

- Ask about Marc's availability.
- Schedule something on Marc's calendar.
- Request a change to something Marc owns.
- Use a household tool available through Bob.
- Continue a recent household action, such as turning a light back off or
  cancelling a timer.

Kinward therefore needs to distinguish between:

1. Personal assistant conversational memory.
2. Shared assistant conversational memory.
3. Short-lived operational household context.
4. Deterministic permissions for connected tools.
5. Actions that require approval from another person.

The system should remain simple enough to test in a real household before
introducing a general-purpose authorization framework.

The following principles apply:

- Conversational memory boundaries remain peer-based.
- Access to an assistant does not grant access to another person's peer memory.
- Tool access is separate from conversational memory access.
- Privacy-sensitive behavior must be deterministic wherever practical.
- The AI should not decide whether another person's protected data or resources
  may be disclosed or modified.
- V0 should prefer understandable toggles and approvals over granular permission
  matrices.
- The model should remain extensible as real household usage reveals additional
  requirements.

## Decision

### 1. Personal assistant memory

Personal assistants will use separate conversational memory for each
person-assistant peer relationship.

For example:

```text
Marc <-> AI Bob
Lisa <-> AI Bob
Marc <-> AI Joe
Lisa <-> AI Joe
```

When Lisa talks to AI Bob:

- Bob uses the Lisa-Bob peer memory.
- Bob may remember previous conversations that Lisa had with Bob.
- Bob does not retrieve conversational memories from the Marc-Bob peer.
- Information learned in the Lisa-Bob peer is not automatically copied into the
  Marc-Bob peer.
- Bob's ownership by Marc does not give Lisa access to Marc's conversations with
  Bob.
- Bob's ownership by Marc does not give Marc automatic access to Lisa's
  conversations with Bob.

The peer is selected from the authenticated caller and the addressed assistant:

```text
peer_id = (person_id, assistant_id)
```

This is an architectural invariant rather than a configurable permission.

Cross-person access to an assistant only determines whether the caller may start
or continue their own peer relationship with that assistant. It never merges
peer memories or changes which conversational memory is active.

Assistant persona, voice, name, and general behavior may remain consistent
across peers. Private facts and conversation history must not cross between
peers merely to make the assistant appear consistent.

#### V0 assistant access configuration

Each personal assistant will have a simple access setting:

```yaml
access:
  mode: owner_only | household | allowlist
  allowed_person_ids: []
```

Examples:

```yaml
assistant:
  id: ai-bob
  owner_person_id: marc
  access:
    mode: allowlist
    allowed_person_ids:
      - lisa
```

```yaml
assistant:
  id: calopex
  owner_person_id: marc
  access:
    mode: owner_only
```

The modes mean:

- `owner_only`: only the assistant's owner may address it.
- `household`: any authenticated household member may address it.
- `allowlist`: only the owner and specifically selected household members may
  address it.

The default for a newly created personal assistant will be `owner_only`.

This setting controls access to the assistant, not access to every tool attached
to it. Tool permissions are handled separately.

### 2. Shared assistant memory

Household-shared conversational memory is deferred until V2.

A future shared assistant may use a household-scoped peer such as:

```text
Household <-> Shared Assistant
```

That assistant could remember conversations from multiple household members in
one intentionally shared memory space.

V0 will not implement this behavior.

The Home Assistant fallback agent or household fallback assistant may serve
multiple users, but it will not have a durable shared Honcho conversational
memory in V0.

This distinction is important because shared conversational memory introduces
additional questions that are not required for the first usable release,
including:

- Whether every household member may inspect or delete shared memories.
- Whether children and adults share the same memory space.
- How private disclosures made accidentally to the shared assistant are
  corrected.
- Whether shared memory can be used by personal assistants.
- How shared assistant history is exported, restored, or deleted.

These questions will be decided after Kinward has real usage data.

V0 will instead solve immediate cross-user continuity requirements through
structured operational household context.

### 3. Operational household context

Kinward will maintain structured, short-lived operational context shared across
authorized users, assistants, rooms, and voice nodes where appropriate.

This context is separate from Honcho conversational memory and is intended to
resolve references to recent or active household operations, including:

- The most recently controlled light, device, area, scene, or media player.
- Active and recently created timers.
- The device, room, person, and assistant associated with an action.
- Pending confirmations or approval requests.
- Recent tool actions needed to interpret follow-up commands.

This enables interactions such as:

- "Turn on the office light," followed later by "Turn that light back off."
- One household member creating a timer and another asking to cancel it.
- A command beginning on one voice node and being continued through another.
- "Pause it" referring to the media player most recently controlled in the
  current room.
- "Add five minutes" referring to the active timer most relevant to the room or
  recent interaction.

Home Assistant does not currently provide this kind of persistent, cross-user
and cross-voice-node operational context natively.

Home Assistant can preserve conversational context through a `conversation_id`
while a conversation remains active and while the participating integration
continues using that identifier. This does not provide a durable,
household-wide operational state after the conversation ends.

Home Assistant voice nodes and integrations may also keep limited local or
session-specific context. This can explain behavior where an immediate
follow-up such as "turn it back off" succeeds while a request made a minute
later, through another node, or after the conversation closes does not.

Kinward must therefore provide its own operational context layer.

Operational context will be stored as structured application state rather than
asking the language model to reconstruct prior actions from conversational
memory.

Example:

```yaml
recent_actions:
  - action_id: action-123
    domain: light
    service: turn_on
    entity_ids:
      - light.office
    area_id: office
    requested_by_person_id: marc
    assistant_id: ai-bob
    voice_node_id: office-voice
    occurred_at: 2026-07-16T12:05:00-04:00
    expires_at: 2026-07-16T12:15:00-04:00
```

```yaml
active_timers:
  - timer_id: timer-456
    label: null
    duration_seconds: 1800
    created_by_person_id: marc
    assistant_id: ai-bob
    origin_area_id: kitchen
    origin_voice_node_id: kitchen-voice
    created_at: 2026-07-16T12:10:00-04:00
    state: active
```

The physical voice node is an input and output surface. It is not the sole owner
of the action or timer.

A timer may carry metadata about:

- Who created it.
- Which assistant created it.
- Which room or node received the request.
- Where it should announce.
- Whether it is personal, room-scoped, or household-manageable.

The timer itself must remain available to Kinward regardless of which voice node
receives the follow-up request.

#### Deterministic reference resolution

The AI may interpret that a user intends to control a light or timer, but the
backend must resolve the actual resource from structured state.

For lights and devices, Kinward should prefer:

1. The most recent matching action in the current room.
2. The most recent matching action performed through the current assistant.
3. The most recent matching household action within a limited time window.
4. A clarification request when no sufficiently strong match exists.

For timers, Kinward should prefer:

1. A timer currently ringing.
2. The only active timer.
3. The most recent active timer in the current room.
4. The most recent active household-manageable timer.
5. A clarification request when more than one plausible timer remains.

The backend must not allow the model to invent an entity, timer, room, or prior
action.

Operational context must have explicit retention limits. Old context should
expire rather than remain indefinitely available as accidental long-term
memory.

Initial retention periods may be conservative and adjusted through household
testing.

#### Existing community work

Community projects demonstrate related approaches but do not appear to provide
a directly reusable implementation of Kinward's required operational context
model.

Examples include:

- Home Mind, which adds persistent semantic memory to a Home Assistant
  conversation agent. This is closer to long-term conversational recall than
  deterministic tracking of recent tool actions.
- Friday/ZenOS-AI, which explores contextual memory, entity-state snapshots, and
  event-driven summaries around Home Assistant. Its architecture may provide
  useful design references, but it is a broader agent framework rather than a
  drop-in operational-context component.
- External Home Assistant agents such as OpenClaw and Mylo, which combine
  persistent agent memory with Home Assistant tool access. These reinforce that
  persistent context is usually implemented outside Home Assistant's native
  conversation layer.

Relevant references:

- Home Assistant follow-up conversation discussion:
  https://community.home-assistant.io/t/voice-assistant-follow-up-responses/695081
- Home Mind discussion:
  https://www.reddit.com/r/homeassistant/comments/1qyo0d7/home_mind_a_conversation_agent_for_ha_with/
- ZenOS-AI:
  https://github.com/nathan-curtis/zenos-ai
- OpenClaw Home Assistant integration:
  https://github.com/ddrayne/openclaw-homeassistant

For V0, Kinward will implement only the minimum operational context required
for:

- Lights and switches.
- Timers.
- Media control.
- Room and area references.
- Recent tool actions.
- Pending approvals.

The implementation must remain replaceable as household testing reveals the
actual retention periods, ranking rules, and scope boundaries needed.

### 4. Tool permissions

Connected tools will use deterministic permissions that are separate from
assistant access and conversational memory.

Three different questions must be evaluated independently:

```text
1. May Lisa address AI Bob?
2. Which conversational memory peer is active?
3. What may AI Bob's connected tool do when Lisa is the caller?
```

For the example above:

- The assistant access setting may allow Lisa to talk to AI Bob.
- The Lisa-Bob peer memory is selected automatically.
- Bob's calendar connection determines which calendar operations Lisa may
  request.

Tool permissions must be expressed as concrete capabilities implemented by
code. They must not depend on the AI deciding whether an operation feels
appropriate.

Each connected tool may define its own small capability set.

Example calendar permissions:

```yaml
tool:
  type: calendar
  connection_owner_person_id: marc

  cross_person_permissions:
    read_availability: true
    read_non_private_event_details: true
    create_events: true
    modify_events: approval_required
    delete_events: approval_required
```

Example Home Assistant permissions:

```yaml
tool:
  type: home_assistant

  cross_person_permissions:
    control_lights: true
    control_switches: true
    control_media: true
    manage_household_timers: true
    control_locks: false
    control_alarm_system: false
```

The initial implementation does not need one universal capability schema for
every future integration. Each tool adapter may expose a typed set of
capabilities appropriate to that tool.

The permission result must be one of:

```text
allow
approval_required
deny
```

The language model may request an operation, but the tool adapter must validate
the operation and enforce its configured result before execution.

#### Calendar reads

Calendar event privacy will use the event's explicit private status.

For a non-private event, full event details may be returned when
`read_non_private_event_details` is allowed.

For an event marked private, a non-owner caller may receive only the minimum
availability information:

- The date.
- The start time.
- The end time.
- The fact that the owner is busy or unavailable.

The following fields must not be disclosed:

- Title.
- Description.
- Location.
- Attendees.
- Meeting links.
- Attachments.
- Notes.
- Organizer details when those details reveal the event's purpose.
- Any other field that could reveal why the time is reserved.

An allowed response may be:

```text
Marc is unavailable Monday from 2:00 PM until 3:00 PM.
```

It must not be:

```text
Marc has a private medical appointment Monday at 2:00 PM.
```

The system should avoid confirming more than is required to answer the
availability question.

The event's private marker is the deterministic privacy boundary for V0.
Kinward will not attempt to infer whether an event title or description is
sensitive.

#### Calendar creation

A connected calendar may allow selected people to create new events.

For example, Lisa may ask AI Bob:

```text
Schedule dinner with me on Marc's calendar tomorrow at 6:00 PM.
```

If the requested time is free and the tool permits cross-person event creation,
Bob may create the event.

Calendar creation permissions should be configurable when the user connects the
calendar or later in the tool's settings.

V0 does not require separate permission settings for every calendar field.
The adapter may use a safe, predefined event-creation contract.

#### Home Assistant tools

Routine household device control may be permitted to all authorized household
members because those resources are generally shared.

Examples include:

- Turning lights and switches on or off.
- Activating scenes.
- Controlling shared media players.
- Creating and cancelling household timers.
- Querying ordinary environmental sensors.
- Adjusting commonly shared climate controls within configured limits.

Higher-risk Home Assistant operations should remain independently disabled or
approval-gated.

Examples include:

- Unlocking doors.
- Opening garage doors.
- Disarming an alarm.
- Disabling cameras.
- Changing security automations.
- Exposing private presence or location information.
- Controlling devices marked as restricted.

Kinward will begin with a small set of explicit Home Assistant capabilities and
expand them based on real household use.

#### Configuration surface

V0 may present tool permissions as a small set of toggles rather than a complex
policy editor.

For example:

```text
Allow selected household members to:
[x] Check my availability
[x] See details of non-private events
[x] Add new events
[x] Request changes to existing events
[ ] Directly change existing events
[ ] Delete events
```

The goal is to make the expected behavior understandable during onboarding and
when connecting a tool.

### 5. Approval-required actions

An operation that changes another person's existing resource may be converted
into a pending approval request rather than immediately executed.

For example, Lisa may ask AI Bob:

```text
Can you move Marc's dentist appointment to Friday afternoon?
```

AI Bob may:

1. Identify the intended event without disclosing protected details to Lisa.
2. Determine whether the requested change is technically possible.
3. Find a suitable proposed time when requested.
4. Create a pending action.
5. Notify Marc.
6. Wait for Marc to approve or deny it.
7. Execute the change only after approval.

The AI does not decide whether Marc should accept the request.

Example pending action:

```yaml
pending_action:
  id: approval-789
  type: calendar.reschedule
  requested_by_person_id: lisa
  affected_person_id: marc
  assistant_id: ai-bob
  tool_connection_id: marc-primary-calendar
  target_resource_id: event-123
  proposed_changes:
    start: 2026-07-17T15:00:00-04:00
    end: 2026-07-17T16:00:00-04:00
  status: pending
  created_at: 2026-07-16T12:30:00-04:00
  expires_at: 2026-07-17T12:30:00-04:00
```

Marc may receive a Home Assistant push notification or dashboard prompt:

```text
Lisa asked AI Bob to move "Dentist appointment"
from Thursday at 2:00 PM to Friday at 3:00 PM.

[Approve] [Deny] [Review]
```

The notification shown to the resource owner may contain the event details that
the owner is authorized to see. The requesting person should receive only an
appropriate status response.

For example:

```text
I sent Marc a request to approve the change.
```

After approval:

```text
Marc approved the request, and the event was moved.
```

After denial:

```text
Marc declined the requested change.
```

No explanation for the denial is required.

#### Initial approval-required operations

For V0 or V0.5, approval should be used for cross-person operations such as:

- Rescheduling an existing calendar event.
- Deleting or cancelling an existing calendar event.
- Modifying an existing event's attendees.
- Changing an existing event's title, location, or details.
- Replacing an existing commitment with a new one.
- Other changes where the affected resource clearly belongs to another person.

Additional Home Assistant actions may later use the same mechanism, including:

- Unlocking a restricted door.
- Opening a garage door for another person.
- Disabling a security device.
- Changing a protected automation.
- Performing an action with a meaningful safety, privacy, or financial impact.

#### Approval lifecycle

A pending action must include:

- The requester.
- The affected person.
- The assistant used.
- The connected tool.
- The specific proposed operation.
- The target resource.
- The proposed changes.
- The current status.
- Creation and expiration timestamps.

Valid states should include:

```text
pending
approved
denied
expired
cancelled
executed
failed
```

Approval must apply only to the specific proposed action.

If the proposed operation changes after approval, a new approval must be
requested.

Approval must be checked again immediately before execution to ensure:

- The approval is still valid.
- The request has not expired.
- The target resource still exists.
- The resource has not materially changed.
- The approving person is still authorized.
- The tool connection remains available.

Approvals must be one-time by default and must not silently create a permanent
permission.

Kinward may later allow users to convert repeated approvals into broader
permissions, but that is outside the initial decision.

## Resulting V0 model

The V0 access flow is:

```text
1. Authenticate the caller.
2. Resolve the addressed assistant.
3. Check whether the caller may access that assistant.
4. Select the caller-assistant peer memory.
5. Interpret the request.
6. Resolve recent references from operational household context.
7. Check the requested tool capability.
8. Allow, deny, or create an approval request.
9. Execute only after all required checks pass.
10. Record structured operational context for relevant follow-up commands.
```

## Consequences

### Positive

- Personal conversational memories remain cleanly isolated by peer.
- Cross-person assistant access remains useful without exposing the owner's
  conversation history.
- Home Assistant tools can behave consistently across users and voice nodes.
- Timers and recent device references no longer depend on which physical node
  heard the command.
- Calendar privacy is enforced by deterministic event metadata.
- Another person's existing resources cannot be modified without their consent.
- The model is simple enough to test during V0 household use.
- Future permissions can be added without first building a universal policy
  engine.
- The AI interprets requests but does not make final authorization decisions.

### Negative

- Kinward must build and maintain its own operational context store.
- Different tool adapters will initially have different capability schemas.
- Approval workflows require notifications, persistence, expiration, and
  execution handling.
- Private calendar events still reveal busy time.
- Some ambiguous follow-up commands will require clarification.
- V0 will not support durable shared household conversational memory.

### Accepted limitations

- Tool permissions will initially be coarse.
- V0 will not support permissions tied to individual conversational memories.
- V0 will not use the AI to infer whether unmarked data is sensitive.
- V0 will not attempt to define every future cross-person tool interaction.
- V0 will not implement shared assistant conversational memory.
- Permission defaults and operational-context retention periods may change after
  real household testing.

## Deferred work

The following are explicitly deferred:

- Household-shared conversational memory.
- Per-memory or per-fact disclosure controls.
- General-purpose authorization policies covering every integration.
- Automatic AI classification of private information.
- Direct cross-person modification of existing resources without approval.
- Permanent permission grants derived from repeated approvals.
- Complex guardian, child, and teen delegation rules beyond existing product
  requirements.
- Assistant-to-assistant delegation.
- General emergency-access policy.
- Long-term learning from operational household context.

## Implementation guidance

The implementation should preserve three separate concepts:

```text
assistant_access_policy
peer_memory_selector
tool_capability_policy
```

Operational context and approvals should remain separate persisted services:

```text
operational_context_store
pending_action_store
```

A tool call must receive an explicit execution context:

```yaml
execution_context:
  caller_person_id: lisa
  assistant_id: ai-bob
  assistant_owner_person_id: marc
  peer_id:
    person_id: lisa
    assistant_id: ai-bob
  source:
    type: home_assistant_voice
    area_id: kitchen
    device_id: kitchen-voice
  requested_capability: calendar.modify_event
```

The tool adapter, not the language model, returns:

```text
allow
approval_required
deny
```

No tool adapter may infer authorization only from the assistant ID or tool
connection owner. It must evaluate the authenticated caller and the requested
capability.

## Test requirements

At minimum, automated tests must verify:

### Personal assistant memory

- Lisa speaking to AI Bob selects the Lisa-Bob peer.
- Marc speaking to AI Bob selects the Marc-Bob peer.
- Lisa cannot recall Marc-Bob conversational history.
- Marc cannot recall Lisa-Bob conversational history.
- Denied callers cannot create a new peer by addressing the assistant.
- Assistant access changes do not merge existing peer memories.

### Operational context

- A light turned on through one voice node can be turned back off through
  another authorized voice node.
- A timer created by one household member can be cancelled by another when the
  timer is household-manageable.
- Expired recent-action context is not used.
- Ambiguous references produce a clarification request.
- The backend never invents an entity or timer when no candidate exists.
- Operational context is not written into long-term Honcho memory by default.

### Calendar permissions

- Private events disclose only busy time to authorized non-owner callers.
- Private event titles, descriptions, locations, and attendees are withheld.
- Non-private event details are returned only when the capability is enabled.
- Event creation succeeds only when explicitly allowed.
- A caller who may access the assistant but not the calendar receives a denial.
- The language model cannot bypass the calendar adapter's permission decision.

### Approvals

- Cross-person event modification creates a pending action.
- No modification occurs before approval.
- The affected owner can approve or deny the action.
- Approval applies only to the exact proposed change.
- Expired approval cannot be executed.
- A materially changed event requires a new approval.
- A denied request cannot be executed.
- Execution failure is reported without marking the action successful.
- The requester receives status without receiving protected event details.

## Open questions

The following questions do not block the V0 decision and should be answered
through implementation and household testing:

- How long should recent light, media, and room references remain active?
- Should timers default to room scope, person scope, or household scope?
- Which Home Assistant domains should initially be treated as routine shared
  controls?
- Which Home Assistant actions should require approval instead of being denied?
- Should event creation on another person's calendar require approval by
  default, or be an onboarding toggle?
- How should pending requests appear in Home Assistant dashboards in addition to
  push notifications?
- When should repeated clarification or approval patterns be offered back to the
  owner as a suggested setting change?
