---
title: "HA-Native Implementation Reset"
status: partially-implemented
created: 2026-07-15
homeAssistantBaseline: 2026.7.2
---

# HA-Native Implementation Reset

## Stop work

Stop all implementation against the retired standalone UI plan, including incomplete Story 1.6 work. Do not extend the design-token system, primitives, five-surface shells, card renderers, layout resolver, PWA behavior, or visual regression gates.

## Preserve before deletion

Before removing frontend code, run a focused salvage review and preserve only:

- backend/API behavior accidentally implemented alongside UI work;
- household bootstrap and schema code;
- policy-filtering and forbidden-field tests that exercise backend boundaries;
- accessibility or tooling improvements useful outside the retired UI;
- synthetic fixtures that remain useful and public-safe;
- deployment and CI work unrelated to `apps/web`.

Do not preserve a component merely because it exists. No compatibility layer is required for unreleased standalone UI code.

## Same-day implementation sequence

### 1. Development runtime

- Add a pinned Home Assistant `2026.7.2` development service/profile.
- Persist HA configuration in an ignored local volume.
- Document startup, reset, and integration-copy/install commands.
- Keep Kinward core healthy when HA is absent and HA healthy when optional Kinward providers are absent.

### 2. Integration skeleton

Create `custom_components/kinward` with:

- `manifest.json`
- `__init__.py`
- `const.py`
- `config_flow.py`
- `coordinator.py`
- typed backend client module
- `sensor.py`
- `binary_sensor.py`
- `conversation.py`
- `services.yaml` or current action-description equivalent where required
- translations/strings
- diagnostics redaction

Use current HA integration conventions. Avoid deprecated setup patterns and direct blocking I/O in the event loop.

### 3. Backend contract

Implement or confirm a minimal versioned contract for:

- health/capability status;
- household-safe summary;
- briefing summary;
- attention count;
- next household event;
- refresh/briefing command;
- conversation request and truthful terminal response.

The HA integration must not scrape the retired web UI or import frontend schemas as its API contract.

### 4. Initial entities

Expose only the bounded initial entity set from revised Epic 1. Entity attributes must be reviewed for recorder/logbook privacy and size.

### 5. Dashboard

Ship an importable dashboard YAML or storage-compatible documented configuration using core cards only. Prefer simple sections, headings, tile cards, entity cards, calendar, markdown, and Assist/conversation access available in HA 2026.7.2.

Use existing HA `person.*` entities for household status. Provide placeholders/mapping instructions rather than hard-coded real household names or entity IDs.

### 6. Trial verification

Verify:

- integration setup through UI;
- reload/unload;
- backend stop/start;
- stale/unavailable behavior;
- dashboard on desktop and Companion app;
- one refresh/briefing action;
- one text conversation request;
- no private bodies in entity states, attributes, logs, diagnostics, or HA history;
- no role-derived disclosure through HA administrator status.

## Follow-on order

After the household trial, address defects before adding presentation features. Then implement HA user/profile mapping, the full conversation lifecycle, topic continuity, calendar awareness, and action reconciliation in the order defined by revised `epics.md`.

## Explicit non-goals

- polished custom cards;
- HACS packaging;
- official Home Assistant integration submission;
- voice satellite hardware changes.

## Implementation status (2026-07-16)

Steps 1-6 of the same-day sequence above are implemented, matching epics.md
Stories 1.3-1.7: the pinned HA 2026.7.2 dev profile, `custom_components/kinward`
(manifest, config flow, coordinator, initial entities, `services.yaml`), the
backend's `/api/v1/integration` contract with hashed service tokens, an
importable core-card dashboard, and `scripts/ha-dev-smoke.sh` plus
`docs/ha-native/household-trial.md` for verification. The trial's backend/API
behavior was exercised end to end against a real HA container; a human
browser/Companion-app pass through the dashboard and config-flow UI itself is
still open (see that runbook's Notes section).

**2026-07-16 update**: epics.md Stories 2.1 and 2.2 are also implemented -
an Options-flow-driven HA-user-to-Kinward-profile mapping (backend-authoritative,
fail-closed on missing/removed-account mappings) and a real `conversation.kinward`
lifecycle with persisted topics/turns and multi-turn continuity, verified live
by the household operator against their own bootstrapped data (see the runbook's
2026-07-16 trial note). Stories 2.3 (cancellation), 2.4 (cross-client topic
continuity UI), and 2.5 (fallback-assistant boundary) remain open, as does
`AccountRecord` state modeling (active/disabled/locked) needed for the fuller
fail-closed behavior Story 2.1 describes.

Story 2.1 (HA-user-to-Kinward-profile mapping) and Story 2.2 (the real
`conversation.kinward` lifecycle) are explicitly deferred - `conversation.kinward`
exists but only returns a truthful "not implemented yet" placeholder, and the
integration token used above is household-level only, not per-person.
