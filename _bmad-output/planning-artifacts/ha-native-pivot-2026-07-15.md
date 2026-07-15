---
title: "Kinward Home Assistant Native Pivot"
status: approved-direction
created: 2026-07-15
supersedes:
  - sprint-change-proposal-2026-07-15.md
  - standalone five-surface frontend plan
homeAssistantBaseline: 2026.7.2
---

# Kinward Home Assistant Native Pivot

## Decision

Kinward will use Home Assistant as its committed user-interface shell for the first usable household release.

Kinward remains an independently testable backend and domain application. Home Assistant becomes the presentation, interaction, device-state, dashboard, mobile, and voice host through a custom integration and a shipped dashboard configuration.

The standalone `apps/web` experience, Kinward-owned five-surface renderer, card registry, layout resolver, design-token system, drag-and-drop layout editor, and standalone PWA are removed from committed scope. Existing code may remain temporarily for reference until deleted safely, but no new product capability may depend on it.

## Why this is the correct reset

- Kinward is currently for one real household, not a general SaaS product.
- Home Assistant is already authoritative for areas, devices, entities, state, services, dashboards, mobile access, notifications, and Assist voice pipelines.
- Voice will be a primary interaction surface.
- Very little Kinward-specific frontend capability has been completed.
- The existing frontend plan duplicates mature Home Assistant capabilities before Kinward's unique household intelligence has been proven.
- The valuable completed work is primarily backend foundation, policy, household bootstrap, privacy filtering, schemas, deployment, and test infrastructure.

## Product boundary

### Home Assistant owns

- Browser and mobile application shell
- Authentication for HA-hosted interaction
- Dashboard navigation and responsive rendering
- Areas, devices, entities, current physical state, and service invocation
- Built-in cards and supported dashboard editing
- Companion applications and notifications
- Assist pipelines, speech-to-text, text-to-speech, wake-word routing, and conversation-agent selection
- Ordinary technical administration of the Home Assistant installation

### Kinward owns

- Single-household domain model
- People, relationships, account binding, privacy class, and household authority
- Personal and household assistants
- Conversation topics and continuity
- Context assembly and provider-neutral orchestration
- Personal memory and household-shared knowledge policy
- Proactive prioritization, briefings, household coordination, approvals, and meaningful-action state machines
- Calendar and communication adapters
- Home Assistant action policy and reconciliation
- Activity, audit, backup, restore, deletion, and recovery contracts
- Plain-language household semantics exposed through HA entities, actions, events, conversation responses, and optional custom cards

## Supported HA extension model

The first implementation uses only documented Home Assistant extension points:

1. A custom integration under `custom_components/kinward`.
2. UI config flow for connection and household setup.
3. Standard entities where a standard entity model is useful.
4. Integration actions for explicit Kinward commands.
5. A `ConversationEntity` for Kinward Assist participation.
6. Integration-owned events and/or WebSocket commands only where entity state is insufficient.
7. A shipped dashboard using built-in cards first.
8. Optional custom cards only after a concrete limitation is demonstrated.
9. A custom panel only for administration that cannot be represented safely through ordinary HA configuration flows.

Kinward will not fork Home Assistant frontend, import HA internal frontend components into a standalone application, or attempt to execute arbitrary HACS cards outside Home Assistant.

## Home Assistant compatibility baseline

- Development target: Home Assistant Core `2026.7.2`.
- Minimum supported version for the first household trial: `2026.7.0` unless implementation proves that `2026.7.2` is required.
- CI must test the pinned target version and must not use an unbounded `latest` dependency.
- Monthly HA upgrades require compatibility validation before the supported target is raised.
- The integration manifest must declare an explicit version and required integration metadata.

## Initial user-visible slice

The first usable slice must be installable and useful without custom frontend code.

### Dashboard

A dashboard named **Kinward** contains one initial view using built-in Home Assistant cards:

- Household heading
- Person status pills or person/entity tiles for each configured household member
- Current household status
- Today's calendar summary
- Kinward briefing text
- Items requiring attention
- Kinward conversation card or Assist entry point
- Integration health and last refresh state

The exact initial card set may use Mushroom or another HACS dependency only if already installed in the target household. The distributable default must use core Home Assistant cards and degrade cleanly when optional HACS cards are absent.

### Initial entities

The first slice should expose a deliberately small set:

- `conversation.kinward`
- `sensor.kinward_household_status`
- `sensor.kinward_briefing`
- `sensor.kinward_attention_count`
- `sensor.kinward_next_household_event`
- `binary_sensor.kinward_backend_available`
- one diagnostic/update timestamp sensor where useful

Person presence should reuse authoritative HA `person.*` entities rather than duplicate presence inside Kinward. Kinward may associate its profiles with HA person entities through configuration.

### Initial actions

- `kinward.refresh`
- `kinward.generate_briefing`
- `kinward.acknowledge_attention_item`
- `kinward.ask`

Actions must use current Home Assistant action conventions and selectors where applicable.

## Salvage disposition for Stories 1.1–1.6

| Story | Disposition | Notes |
| --- | --- | --- |
| 1.1 | Keep and revalidate | Repository, runtime, database, API, worker, and deployment foundation remain useful. |
| 1.2 | Keep | Atomic household bootstrap and single-household invariants remain authoritative. |
| 1.3 | Partial salvage | Keep backend policy-filtered view-model work where reusable; remove standalone surface renderer requirements. |
| 1.4 | Retire frontend portion | Layout resolver and Kinward-owned layout persistence are no longer product requirements. Preserve only generally useful validation code after explicit review. |
| 1.5 | Replace | Five-surface frontend verification is replaced by HA integration, dashboard, Assist, mobile, and policy-bound integration tests. |
| 1.6 | Cancel as obsolete | The Kinward-owned visual foundation is no longer required. HA owns visual design and responsive shells. |

Completed artifacts remain historical implementation evidence. They must not be treated as active requirements when they conflict with this pivot.

## Immediate implementation order

1. Remove Story 1.6 as a blocker and mark it superseded.
2. Add a development HA instance pinned to `2026.7.2` to the local compose/profile workflow.
3. Create the Kinward custom integration manifest and UI config flow.
4. Connect the integration to the existing Kinward backend health endpoint.
5. Expose the initial diagnostic and household entities.
6. Add the Kinward conversation entity using a minimal backend request path.
7. Ship an importable core-card dashboard.
8. Add tests for setup, reconnect, unavailable backend, entity freshness, action authorization, and conversation errors.
9. Install in the target household and use it before expanding the dashboard.

## End-of-day acceptance target

The target household can:

- install or copy the Kinward custom integration into Home Assistant 2026.7.2;
- configure the Kinward backend URL through the HA UI;
- see Kinward integration health;
- view a Kinward dashboard built from core cards;
- see existing HA person status alongside at least one Kinward-produced household summary;
- invoke one refresh or briefing action;
- submit one text request through the Kinward conversation entity or a temporary action-driven fallback;
- observe truthful unavailable/error behavior when the Kinward backend is stopped.

This target intentionally excludes polished custom cards, full onboarding, proactive delivery, complex approvals, mobile-native code, and broad backend completion.

## Architectural guardrails

- HA user identity is an input to Kinward access decisions, not a replacement for Kinward's person/profile policy model.
- The integration must map an HA user to at most one Kinward account-bearing profile and fail closed when mapping is absent or ambiguous.
- HA administrator status does not grant access to another adult's private Kinward data.
- Entity attributes must not contain private conversation bodies, secrets, large payloads, or data that would leak through HA history/logbook.
- Rich private data should be returned only through authorization-checked requests and should not be persisted in HA state.
- Service-call success remains `submitted`; Kinward may report `completed` only after the required fresh confirming observation.
- Kinward must continue to operate without optional model, memory, knowledge, calendar, or communication providers and report each capability separately.
- Backend APIs remain provider-neutral and independently testable.

## Deferred UI work

The following require evidence from real household usage before implementation:

- Custom Kinward cards
- Custom dashboard strategy
- Kinward administration panel
- Generated temporary dashboards
- User-controlled dashboard composition beyond normal HA capabilities
- A standalone Kinward web or mobile client
- Support for running HACS cards outside HA

## Documentation disposition

The PRD, architecture, UX specification, epics, and sprint artifacts must be updated so that:

- Home Assistant is the committed UI shell.
- Standalone frontend requirements are removed or explicitly deferred.
- All backend, policy, privacy, memory, action, provider, backup, restore, and household requirements are preserved unless separately changed.
- Acceptance criteria reference HA entities, actions, dashboards, Assist, config flow, and documented extension APIs rather than Kinward-owned routes and renderers.
- Historical artifacts are labeled superseded rather than silently deleted when they contain reusable evidence.
