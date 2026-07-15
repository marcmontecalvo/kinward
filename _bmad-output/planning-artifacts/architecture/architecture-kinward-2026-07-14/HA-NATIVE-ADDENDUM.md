---
title: "Kinward Architecture Addendum: Home Assistant Native UI"
status: authoritative-addendum
created: 2026-07-15
homeAssistantBaseline: 2026.7.2
---

# Home Assistant Native Architecture Addendum

This addendum overrides frontend and surface architecture in the existing architecture package where the two conflict. Backend domain, application, persistence, policy, action, provider, activity, backup, restore, and operational decisions remain authoritative.

## Replaced architecture

The following are retired from committed scope:

- standalone Kinward Assistant Experience web shell;
- five Kinward-owned surface implementations;
- Kinward card and layout registries as presentation architecture;
- Kinward-owned responsive shell, PWA, and layout persistence;
- design-token and primitive-system enforcement as a release gate;
- separate everyday and Kinward Control web route shells.

## New frontend boundary

```text
Home Assistant 2026.7.2
  ├─ dashboards and core cards
  ├─ Companion apps
  ├─ Assist pipelines
  ├─ areas/devices/entities/services
  └─ Kinward custom integration adapter
          ├─ config/options/reauth flows
          ├─ coordinator/client
          ├─ safe standard entities
          ├─ integration actions/events
          ├─ ConversationEntity
          └─ optional WebSocket commands
                    │
                    ▼
Kinward versioned backend API
  ├─ identity/profile mapping
  ├─ household and assistant domain
  ├─ privacy and authority policy
  ├─ topics/conversation/context
  ├─ memory and knowledge
  ├─ calendar and coordination
  ├─ meaningful actions/reconciliation
  ├─ activity/health/diagnostics
  └─ backup/restore/deletion/recovery
```

## Adapter rules

- `custom_components/kinward` is an outer adapter and depends on versioned Kinward API contracts.
- HA entities and actions may call only application-level Kinward commands and queries.
- The integration contains no independent household authority or privacy policy.
- HA user identity must be mapped explicitly to a Kinward profile before private operations.
- Mapping and authorization are re-evaluated for each protected operation.
- Home Assistant administrator status is not Kinward household authority.
- Entity state is public to the authorized HA instance and potentially retained by recorder/logbook; therefore it must be compact and safe.
- Private bodies and rich records use authorization-checked request paths and must not be persisted in HA state.
- The integration must use bounded timeouts, safe retries, explicit availability, and coordinator-driven refresh rather than unbounded per-entity calls.
- Config entry unload/reload and backend disconnect must leave entities unavailable rather than stale-current.

## Voice boundary

- Kinward participates in Assist through a `ConversationEntity`.
- HA owns speech transport, wake word, STT, TTS, pipeline selection, and device routing.
- Kinward owns the conversation request lifecycle, context authorization, assistant ownership, topic continuity, action proposals, cancellation, and terminal outcome.
- HA conversation IDs may be associated with Kinward topics but never replace Kinward authorization or persistence.

## Home Assistant physical-state boundary

- HA is authoritative for areas, devices, entities, services, and observed state.
- Kinward stores stable references and policy metadata, not a competing device registry.
- A service/action call result means submitted.
- Completion requires a fresh matching HA observation under the existing meaningful-action contract.
- Missing, stale, unavailable, or contradictory observations produce unknown or failed outcomes as defined by policy.

## UI delivery stages

### Stage 1: core-card dashboard

A shipped dashboard uses only supported core cards and the small safe entity set. This is the release path for the first household trial.

### Stage 2: evidence-gated custom cards

A custom card is allowed only when a demonstrated daily-use need cannot be met safely with core cards. It must remain a thin client and must not depend on private HA frontend internals.

### Stage 3: evidence-gated custom panel or strategy

A custom panel or dashboard strategy requires a separate decision record based on observed household use. Neither is a prerequisite for backend or Assist milestones.

## Deployment implications

- Kinward and HA remain separate deployables and failure domains.
- The repository may provide a pinned HA development/test profile but does not own the household's production HA lifecycle.
- Kinward backend production ingress and authentication remain explicit; local-network trust alone is insufficient.
- Optional providers remain separate from both HA and Kinward core readiness.
- No HACS dependency is required for the default distributable experience.

## Testing implications

Remove standalone five-surface visual gates from required validation. Replace them with:

- integration manifest/config-flow tests;
- setup, reload, unload, reauth, duplicate-entry, and unavailable-backend tests;
- entity-state safety and recorder/logbook exposure review;
- HA-user-to-Kinward-profile authorization matrix;
- conversation entity lifecycle and error tests;
- action submission and fresh-observation reconciliation tests;
- core-card dashboard import/render smoke checks where practical;
- compatibility tests against pinned HA 2026.7.2;
- existing backend privacy, domain, persistence, action, backup, and public-safety suites.

## Deferred decisions

- Custom dashboard strategy
- Custom Kinward cards
- Kinward custom administration panel
- Remote access topology beyond the current household deployment
- Standalone Kinward clients
- Distribution through HACS or an official HA integration submission
