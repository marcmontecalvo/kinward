---
status: complete
completedAt: "2026-07-11"
documentType: "BMAD Product Brief"
replaces:
  - "routine-centric Homefront UI direction"
---

# Product Brief: Kinward Assistant Experience

**Author:** Marc Montecalvo  
**Date:** 2026-07-11

## Executive Summary

Kinward is a private, single-household AI platform that gives each household member one or more personal AI assistants. These assistants remember the people they serve, understand household context, connect to email, calendars, school, work, and smart-home systems, and coordinate without combining everyone’s private information into one shared brain.

Kinward must not feel like a smart-home dashboard with a chatbot attached, a task tracker, or a complex alarm clock. It should feel like trusted personal intelligences naturally available across phones, tablets, computers, shared displays, and voice-only room endpoints.

The defining experience is not a morning routine. Kinward understands durable facts—people, schools, grades, workplaces, calendars, sports, clubs, transportation, preferences, locations, devices, and responsibilities—and continuously interprets current reality. It quietly coordinates what matters, surfaces deviations and decisions, and avoids requiring household members to encode ordinary life as routines, alarms, checklists, or many small reminders.

Kinward is deployed through Docker for one household. It is not a SaaS control plane or commercial multi-tenant platform. It may later be released publicly as a source-available project for other households.

## Product Identity

### Category

Private household intelligence and personal assistant system.

### Core promise

Each person has a personal AI that knows them, helps them, and coordinates with the home without requiring them to operate the underlying systems.

### Product metaphor

A trusted personal intelligence layer that follows each person through the house and adapts to the surface currently available.

### Deployment model

- One household per deployment.
- Docker-based deployment.
- Household-owned data and configuration.
- Cloud inference and external integrations may be used where desired.
- No required per-house SaaS backend.
- Designed first for Marc’s family.
- Potential public source-available release later.

## Product Boundaries

Kinward is not:

- A coding assistant.
- A multi-tenant SaaS product.
- A generic chatbot.
- A calendar or task-management application.
- A morning-routine builder.
- A replacement for Home Assistant’s device registry or automation engine.
- A dashboard requiring ordinary users to understand entities, services, YAML, or integrations.

Kinward is:

- A personal assistant and companion for each household member.
- A household coordination layer.
- A context and memory layer.
- An adaptive interaction layer across personal and shared surfaces.
- A safe action layer over email, calendars, household services, and smart-home capabilities.
- A flexible card and layout system that renders the right information for the current person, room, surface, and moment.

## Product Thesis

The relationship between a person and their assistant is the product. Chat history, dashboards, routines, and device controls are supporting representations.

1. Durable context is more valuable than manually programmed routines.
2. Ordinary logistics should be inferred from known facts and current conditions.
3. Most successful assistance should happen quietly.
4. Shared surfaces must be privacy-conservative.
5. Personal surfaces preserve continuity, privacy, and deeper collaboration.
6. Voice is a first-class surface with its own interaction model.
7. Users delegate outcomes rather than construct workflows.
8. Technical control remains available without leaking into everyday use.
9. Modular cards and layouts allow deep customization without rebuilding the app.
10. Single-household deployment permits stronger personalization and simpler architecture.

## Target Users

### Household administrator

Creates the household, adds adults and children, optionally adds pets, manages integrations and permissions, and may customize layouts and advanced configuration.

### Adult household member

Needs private memory, email and calendar awareness, household coordination, planning, delegation, clear approvals, and minimal setup.

### Teen household member

Needs a respectful private assistant, school and activity support, age-appropriate autonomy, and privacy from parents and shared surfaces. The experience must not feel childish or parental.

### Child household member

May receive a simpler age-appropriate voice and visual experience with strong privacy and permission boundaries.

### Shared-surface participant

May be recognized or unknown. Receives household-safe information, general questions, timers, media, and allowed device control.

### Pets and guests

Pets may exist in the household model for care, appointments, and medication but do not receive accounts. Guests are not included during initial onboarding and, if supported later, receive temporary limited access.

## Initial Onboarding

### Administrator

1. Create account.
2. Name the house.
3. Add adults and children.
4. Optionally add pets.
5. Name the first personal assistant.
6. Complete a short personality and interaction interview.
7. Enter Kinward.

### Invited member

1. Accept email invitation.
2. Create account and confirm profile.
3. Name the first personal assistant.
4. Complete the personality and interaction interview.
5. Enter Kinward.

Initial onboarding must not require routines, detailed school or work setup, integrations, rooms, devices, food surveys, notification rules, or technical layout configuration.

## Progressive Context Building

Later targeted sessions gather useful context when relevant:

- **Work:** employer, role, schedule, location, commute, work email and calendar.
- **School:** school, grade, calendar, transportation, sports, clubs, team schedules, and school systems.
- **Personal:** email, calendar, food, allergies, hobbies, dislikes, important people, goals, and communication preferences.
- **Home:** Home Assistant, imported rooms and devices, responsibilities, media, security, and shared-display preferences.
- **Transportation:** vehicles, drivers, recurring routes, school pickup, parking, and charging.

Sessions are optional, short, conversational, and explain their benefit. Assistants may learn naturally but must request confirmation before promoting observations into durable context.

## Core Experiences

1. **Glance:** See what matters without initiating a conversation.
2. **Summon:** Ask a quick question or give a short command.
3. **Collaborate:** Work through a decision or plan using conversation and structured components.
4. **Delegate:** Give the assistant an outcome and allow coordinated follow-through.
5. **Ambient stewardship:** The assistant notices useful exceptions and acts or informs without unnecessary interruption.

## Experience by Surface

- **Personal mobile:** private pocket presence, Now, quiet briefing, active topics, approvals, and assistant input.
- **Personal tablet:** richer planning, family timelines, cooking, homework, comparisons, and flexible multi-column workspaces.
- **Personal desktop:** research, review, deep planning, topic workspaces, and optional Kinward Control.
- **Shared display:** ambient household information, room-appropriate controls, privacy-conservative behavior, timers, media, arrivals, security, and household status.
- **Voice-only endpoint:** brief, interruptible, identity-aware responses with complex detail transferred to a screen.
- **Kinward Control:** separate administrator experience for people, assistants, memory, permissions, integrations, surfaces, layouts, activity, and system health.

## Modular Interface Strategy

Kinward uses a registry-driven card and layout system inspired by Home Assistant dashboards.

- Cards can be added, removed, reordered, resized, and configured.
- Layouts adapt by surface class, room, person, and privacy state.
- Defaults remain polished and automatic.
- Advanced users may edit declarative configuration.
- Layouts can eventually be imported, exported, versioned, and shared.
- Generated temporary workspaces use the same registered components.
- Invalid configuration must never replace the last valid layout.

YAML compatibility is desirable but should not be selected until schema validation and round-trip editing are proven.

## Assistant Model

Each user has at least one personal assistant with a name, voice, personality, interaction preferences, personal memory, permissions, visual signature, and relationship continuity.

A user may also create specialist or temporary assistants. The primary assistant remains the default router so users are not forced to select an assistant for every request.

A shared assistant may handle general questions, timers, shared calendars, announcements, groceries, media, and allowed device control. It must not become a combined repository of private household memory.

## Identity and Privacy

Identity confidence may use voice recognition, nearby personal devices, room occupancy, recent continuity, explicit selection, and optional visual recognition.

- High confidence: personal response within surface policy.
- Medium confidence: generic response and private-device handoff.
- Low confidence: ask identity or use the household fallback.
- Multiple people: group context and no private-memory disclosure.

## Proactivity and Trust

Proactive delivery levels:

1. Ambient.
2. Briefing.
3. Nudge.
4. Interruption.
5. Authorized autonomous action.

Action authority progresses through observe, suggest, prepare, act with confirmation, and act autonomously within explicit limits.

Every meaningful action should make clear what happened, why, which assistant acted, on whose behalf, what information was used, whether approval was required, and whether the action can be undone.

## Client Delivery Strategy

Kinward is web/PWA first.

Web/PWA supports the primary mobile, tablet, desktop, shared-display, Kinward Control, push-to-talk, camera/file context, context-targeted commands, explain-on-hold, emergency display takeover, and layout editing experiences.

Native Android is deferred for capabilities that require deeper operating-system integration:

- Background wake word and microphone.
- Foreground assistant service.
- Rich lock-screen widgets and notification actions.
- Share-sheet capture.
- Background proximity and Bluetooth signals.
- Biometrics.
- Android Auto.
- System-level assistant integration.
- System-wide screen context.

The household uses Android, so a future native client may be sideloaded before Play Store distribution. Native Android must be a thin platform client using the same APIs, privacy rules, card schemas, and surface definitions. iOS is later and must not constrain the initial implementation.

## Success Measures

- Household members voluntarily use their assistants.
- Repeated parent follow-up decreases.
- Meaningful schedule or household changes are caught.
- Personal and shared surfaces are trusted.
- Voice interactions complete cleanly.
- Non-technical users do not need administrator help for normal use.
- The interface does not revolve around reminders, routines, or checklists.

Desired reactions include: “I only had to say it once,” “It already knew,” “It told me only when it mattered,” and “I can change everything, but my family doesn’t need to.”

## Strategic Decisions

1. Kinward is designed first for one household.
2. SaaS and control-plane direction is retired.
3. Morning routines are not the primary workflow.
4. Durable context replaces manual routine construction.
5. Personal assistants are primary; shared AI is a limited fallback.
6. Chat is not the default home screen.
7. Experiences are defined independently by surface.
8. Kinward Control is separate from normal assistant use.
9. The UI begins with modular cards and declarative layouts.
10. Non-technical simplicity and technical flexibility must coexist.
