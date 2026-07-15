---
status: complete
completedAt: "2026-07-11"
documentType: "BMAD UX Design Specification"
replaces:
  - "routine-centric Homefront primary UX direction"
---

# UX Design Specification: Kinward Assistant Experience

**Author:** Marc Montecalvo  
**Date:** 2026-07-11

## Executive Summary

Kinward is a private household AI environment in which each person has one or more personal assistants. The assistants remember their users, understand durable household context, interact through personal and shared surfaces, and coordinate calendars, email, school, work, home devices, and household responsibilities.

The UX must feel like a trusted intelligence layer that inhabits household devices rather than an application the household must operate. The primary UX is not a morning-routine command center. Homefront-style routine construction, alarm chains, and checklist-heavy dashboards are rejected.

## Core Experience

A person expresses an intent once. Kinward resolves identity, context, permissions, privacy, and the appropriate surface. The assistant answers, prepares, acts, coordinates, or requests approval, then confirms the outcome in the least disruptive form.

### Critical success moments

- A thought begins on one surface and continues on another without restating context.
- A shared speaker recognizes that private details belong on the user’s phone.
- A school or calendar change is surfaced without a manually authored routine.
- A user delegates an outcome and Kinward coordinates the follow-through.
- A non-technical household member never needs to understand cards, entities, integrations, or automations.
- An administrator can modify a surface without changing application code.
- Voice succeeds without reading screen-length answers aloud.

### Experience principles

1. Design for relationship and delegation, not command entry.
2. Show what matters now, not everything known.
3. Use durable context instead of manual routines.
4. Keep personal surfaces private and continuous.
5. Keep shared surfaces ambient and conservative.
6. Treat voice as a distinct interaction model.
7. Use cards as presentation primitives, not the product metaphor.
8. Provide polished defaults before customization.
9. Keep advanced control separate.
10. Prefer silence when intervention is not useful.
11. Make uncertainty visible.
12. Make actions understandable and reversible.

## Desired Emotional Response

Users should feel personally supported, calmly informed, relieved of follow-through burden, respected rather than monitored, and confident that they remain in control.

Avoid surveillance, parental nagging, notification fatigue, setup exhaustion, dashboard overwhelm, chatbot emptiness, brittle automation, and ambiguity about whether an action happened.

## Information Architecture

Kinward has two top-level experience families.

### Assistant Experience

Used every day:

- Now.
- Briefing.
- Continue.
- Ask.
- Topics and projects.
- Household context.
- Approvals.
- Results.
- Personal settings.

### Kinward Control

Used by administrators and advanced users:

- Household.
- People.
- Assistants.
- Permissions.
- Memory.
- Integrations.
- Rooms and devices.
- Surfaces.
- Cards and layouts.
- Proactivity.
- Activity.
- System health.
- Advanced configuration.

The two experiences must not share the same default navigation or density.

## Surface Context

Every rendered experience receives a surface context:

```yaml
surface:
  class: personal-mobile | personal-tablet | personal-desktop | shared-display | voice
  owner: user-id | household
  room: optional-room-id
  privacy: private | shared | public
  interaction:
    touch: true
    keyboard: false
    voice: true
  distance: handheld | desk | room
```

Surface context controls available cards, density, type scale, touch size, personal-data visibility, layout selection, response length, navigation, edit controls, and handoff behavior.

# Experience by Surface

## Personal Mobile

The mobile experience is the user’s private pocket presence.

### Default structure

1. Assistant presence and greeting.
2. **Now** card.
3. Quiet briefing.
4. Continue topics.
5. Persistent assistant input.
6. Minimal bottom navigation.

### Now

One dominant current-context item such as:

- Leave in 18 minutes.
- A meeting changed.
- A response is required.
- Pick up medication nearby.
- Nothing needs attention.

It must explain why it matters and provide one primary action. It may disappear when nothing is useful.

### Quiet briefing

Contains prioritized meaning, not a notification feed:

- Calendar changes.
- Important email.
- School updates.
- Household exceptions.
- Completed assistant actions.
- Pending approvals.

Show three items by default and group the rest.

### Continue

Shows active topics rather than raw chat sessions: trips, projects, school papers, maintenance, birthdays, and other ongoing contexts. Topics may contain conversation, structured artifacts, decisions, related email/calendar data, and assistant actions.

### Input

Supports text, voice, camera, screenshot, file, current-screen context, and optional quick modes such as Ask, Do, Remember, and Explain.

### Navigation

Recommended: Home, Calendar, Topics, Household, You. Assistant input remains globally available.

## Personal Tablet

The tablet supports planning, exploration, cooking, homework, family coordination, and richer collaboration.

- Multi-column adaptive canvas.
- Split view.
- Expand cards into workspaces.
- Pin useful generated cards.
- Drag and reorder where authorized.
- Direct manipulation of timelines, comparisons, and plans.

The user may enter layout edit mode to add, remove, resize, reorder, configure, preview, and reset cards. The experience must remain polished without customization.

## Personal Desktop

The desktop supports deep personal and household work.

- Persistent navigation rail.
- Main adaptive canvas.
- Assistant input across the bottom or side.
- Topic and workspace navigation.
- Optional inspector.
- Kinward Control access for authorized users.

A topic workspace may include conversation, timeline, documents, email summaries, calendar proposals, decisions, tasks, people, assistant progress, and final artifacts.

The optional inspector shows source context, assumptions, permissions, memory used, planned actions, history, and undo only when requested or required for trust.

## Shared Household Display

The shared display is an ambient household surface, not a large personal dashboard.

### Default state

- Time and weather.
- What is happening.
- Room-appropriate primary card.
- House status.
- Up next.
- Active media or timers.
- Assistant invocation affordance.

### Privacy

Default to household-safe information. Personal information appears only when identity confidence, room policy, other-present-person policy, and user preferences allow it. Otherwise Kinward summarizes generically, addresses the person without details, sends private content to a personal device, or asks to continue privately.

### Room profiles

**Kitchen:** dinner, recipes, timers, groceries, who will be home, activities, music, lights, and appliances.

**Living room:** media, family schedule, visitors, doorbell, shared planning, photos, and house status.

**Entryway:** departures, weather, traffic, equipment, medications, security, deliveries, and anything at risk.

**Bedroom:** tomorrow, sleep/wake context, quiet controls, and personal information only under strict identity rules.

### Interaction

- Large touch targets.
- Readable at room distance.
- Minimal navigation depth.
- Automatic return to ambient state.
- Voice and touch may combine.
- Personal sessions time out.
- Private content disappears when confidence drops.

## Voice-Only

Voice responses must be brief, interruptible, contextual, identity-aware, and privacy-aware.

Rules:

- Do not read long lists.
- Do not repeat commands unless ambiguity requires it.
- Support interruption, correction, and follow-up.
- Distinguish “I’m doing it” from “It is done.”
- Transfer rich details to the right screen.
- Avoid private details on shared endpoints.
- Use consistent earcons for listening, acting, completion, uncertainty, and error.

Voice states: idle, wake detected, listening, understanding, acting, awaiting approval, completed, uncertain, error, and privacy handoff.

## Kinward Control

Kinward Control is a distinct administrative experience.

Primary navigation:

- Overview.
- People.
- Assistants.
- Memory and privacy.
- Permissions and approvals.
- Integrations.
- Rooms and devices.
- Surfaces.
- Cards.
- Layouts.
- Proactivity.
- Activity.
- System health.
- Settings.
- Advanced.

The Surface Manager supports surface assignment, room assignment, default layouts, preview as user, preview privacy states, card editing, configuration editing, restore defaults, import, and export.

Activity is a plain-language household journal showing what happened, who requested it, which assistant acted, why it was allowed, which service was used, whether it succeeded, and whether it can be undone.

# Modular Component System

## Card Registry

Every card definition declares:

- Type and version.
- Title and description.
- Category.
- Supported surfaces.
- Default, minimum, and maximum size.
- Capabilities.
- Privacy level.
- Configuration and data schemas.
- Renderer.
- Optional editor.

Initial card categories include Now, Briefing, Schedule, Timeline, Priority, Continue, Topic, People, Presence, Weather, House Status, Device Control, Media, Timer, Camera, Task List, Notes, Approval, Assistant Progress, Activity, Email Summary, Calendar Proposal, Comparison, Decision, Recipe, School, Work, Transportation, Delivery, Energy, System Health, Text, Button, Shortcut, Stack, Conditional, and Spacer.

## Layout Registry

Layouts are declarative arrangements of card instances.

```yaml
layout:
  id: personal-mobile-default
  version: 1
  surface: personal-mobile
  grid:
    columns: 12
    gap: md
  cards:
    - id: now
      type: now
      span: 12
    - id: briefing
      type: briefing
      span: 12
    - id: continue
      type: continue
      span: 12
```

Layout selection order:

1. Explicit surface assignment.
2. User and surface override.
3. Room and surface override.
4. Household surface profile.
5. Product default.

Card visibility then evaluates identity, privacy, room, time, presence, data availability, preference, assistant priority, device capability, and household state.

## Layout Editing

### Basic mode

Add, remove, drag, resize, configure, duplicate, hide, preview, save, undo, and reset.

### Advanced mode

Human-editable declarative configuration with syntax highlighting, schema completion, validation, live preview, diff, version history, and restore.

Unknown or invalid cards render safe placeholders. Invalid configuration cannot replace the last valid version. Built-in defaults remain immutable.

## Generated Views

The assistant may create temporary views only from registered components. Generated views declare a title, purpose, card instances, layout hint, and persistence mode: ephemeral, topic, or pinned. Arbitrary generated React code is forbidden.

# Additional Interaction Primitives

## Context-Targeted Input

Any meaningful card or item can become the subject of the next command.

Examples:

- Select garage card → “Close this.”
- Select calendar conflict → “Move this to Friday.”
- Select email summary → “Reply that Tuesday works.”

The client passes a typed context reference instead of relying only on conversational inference.

## Explain-on-Hold

Long-press or open an item menu to show:

- Why it appeared.
- What changed.
- Which sources were used.
- What the assistant believes.
- Confidence or uncertainty.
- Relevant permissions.
- Available corrections.

Never expose hidden chain-of-thought, raw prompts, credentials, or secret values.

## Coordination Request

A privacy-filtered proposal card represents coordination between household members.

Example: “Lisa would prefer dinner at 6:30. Your calendar is clear.”

Actions: Accept, Decline, Counter, or Ask assistant to handle.

## Emergency Surface Mode

A shared display may replace its normal layout for a genuine household emergency. It must show what happened, what Kinward or Home Assistant already did, what someone must do now, and whether acknowledgement is required.

Infrastructure faults appear only when they affect household safety or functionality.

## Contextual Maintenance Recall

Device events may surface manuals, model and serial details, warranty, repair history, measurements, photos, contractor information, prior decisions, and relevant Home Assistant telemetry. Kinward summarizes meaning instead of presenting raw telemetry.

# Platform Capability Matrix

| Capability | Web/PWA | Native preferred/required |
|---|---:|---:|
| Personal mobile/tablet/desktop UI | Yes | No |
| Shared room display | Yes | No |
| Text interaction | Yes | No |
| Push-to-talk while open | Yes | No |
| Camera/file context | Yes | No |
| Context-targeted commands | Yes | No |
| Explain-on-hold | Yes | No |
| Drag/drop and declarative layouts | Yes | No |
| Emergency display mode | Yes | No |
| Install to home screen | Yes | No |
| Basic notifications | Partial | Preferred for reliability |
| Background wake word | No | Yes |
| Background microphone | No | Yes |
| Rich lock-screen widgets | Limited | Yes |
| System share sheet | Limited | Preferred |
| Background proximity | Limited | Yes |
| Bluetooth identity hints | No | Yes |
| Android Auto/CarPlay | No | Yes |
| System-wide screen context | No | Yes |

No native-only capability may block the core product. Complete and validate the web/PWA experience first. Android may be sideloaded later before any Play Store distribution.

# Visual Foundation

Kinward should feel calm, intelligent, personal, modern, restrained, and warm without becoming decorative.

Each assistant has a signature color field, subtle visual form, voice, motion cadence, optional emblem, typographic tone, and sound signature. Avoid default humanoid avatars.

Motion communicates attention, listening, understanding, acting, waiting, completion, and uncertainty. It must be subtle, functional, interruptible, and reduced when accessibility settings require it.

## Design-system contract

Kinward uses one versioned token system for color, typography, spacing, size, radius, border, elevation, opacity, layering, motion, focus, targets, and supported responsive thresholds. Primitive values are separated from semantic intent and surface-context expression. Application components consume semantic tokens; raw visual values outside the token boundary require an explicit, documented, lint-enforced exception.

Reusable semantic primitives own presentation and accessibility mechanics for surfaces, layout, typography, panels/card frames, actions, status, navigation, composer, lists, assistant presence, privacy cues, and empty or unavailable states. Feature and card renderers own meaning, content structure, and typed intents. They do not create independent visual systems.

Each registered card has one semantic renderer contract with intentional treatments for personal mobile, personal tablet, personal desktop, shared kitchen, and shared living room. These treatments adapt structure, hierarchy, density, interaction, and viewing distance; they are not recolored copies and must not become forty unrelated implementations.

## Surface art direction

- **Personal mobile:** intimate pocket presence, one dominant moment, calm vertical rhythm, persistent input, and minimal bottom navigation; never a compressed dashboard grid.
- **Personal tablet:** tactile planning canvas with deliberate multi-column composition and touch-and-keyboard affordances.
- **Personal desktop:** focused workspace with persistent navigation, continuity, adaptive canvas, and input; never enlarged mobile.
- **Shared kitchen:** active, glanceable, task-proximate, touch/voice compatible, and readable while people move through the room.
- **Shared living room:** ambient, quiet, distance-first, socially shared, and visually calm rather than a wall-mounted personal dashboard.

All five remain recognizably Kinward through shared typography, assistant presence, state language, interaction principles, and semantic tokens. Difference follows surface purpose rather than arbitrary skins.

## Visual approval

The frontend foundation advances through four rendered-visual gates: a direction gallery; a representative slice on personal mobile, personal desktop, and shared living room; the complete eight-card set across all five surfaces; and final polish covering responsive and non-happy states. The product owner reviews visual output only. Implementation, token compliance, accessibility, and source quality remain the implementation agent's responsibility.

Reject generic glass dashboards, undifferentiated card grids, enlarged-mobile desktop, wall-mounted personal dashboards, novelty motion, decorative status ambiguity, and one-off component styling outside the primitive system.

# Accessibility

Target WCAG 2.2 AA with keyboard access, screen-reader semantics, large touch targets, reduced motion, high contrast, text scaling, captions, non-color status indicators, clear focus, shared-display distance readability, and timeout warnings for private sessions.

Cognitive accessibility requires one dominant decision at a time, plain household language, visible action state, limited notification density, preserved context, and the ability to request simpler explanations.

# Content Design

Family-facing language uses people, assistants, home, topics, what matters, what changed, what I handled, approvals, activity, privacy, and connected services.

Admin-only language may use cards, layouts, integrations, entities, services, policies, logs, schemas, and configuration.

Tone is direct, calm, brief by default, personalized by assistant settings, never falsely certain, never infantilizing to teens, never therapeutic by default, and never nagging.

# Initial Cross-Surface Vertical Slice

The first implementation slice should render the same capability set across mobile, tablet, desktop, shared kitchen, and shared living-room surfaces:

- Assistant Presence.
- Now.
- Briefing.
- Continue.
- Schedule.
- House Status.
- Approval.
- Assistant Input.

This validates the surface, privacy, card, and layout architecture before expanding the card library.

# UX Acceptance Criteria

1. Mobile provides useful context without opening chat.
2. Tablet and desktop render distinct layouts from one card registry.
3. Shared displays show household-safe information by default.
4. Private content can hand off to a personal surface.
5. Voice responses remain brief and screen-independent.
6. An administrator can add, remove, reorder, and resize cards.
7. Declarative layouts can be inspected and edited.
8. Invalid configuration cannot break the active surface.
9. Users receive value without creating a routine.
10. School and activity context can drive assistance automatically.
11. Chat is available but not the only representation.
12. Kinward Control is visually and navigationally distinct.
13. Multiple assistants do not require constant manual selection.
14. Shared assistants cannot casually access personal memory.
15. Every meaningful action has an understandable outcome and activity record.

# Anti-Patterns

Do not build:

- A morning-routine builder as the primary experience.
- A notification feed disguised as a briefing.
- A generic chatbot landing page.
- A Home Assistant dashboard clone.
- A context-free grid of cards.
- One dashboard reused unchanged across all surfaces.
- Shared displays exposing personal email or calendars.
- Childlike teen experiences.
- Arbitrary AI-generated components.
- An advanced editor without validation and rollback.
- Technical concepts in normal household navigation.
- One family AI containing all private memory.
- A system requiring Home Assistant for basic value.
- A system claiming completion before verification.
