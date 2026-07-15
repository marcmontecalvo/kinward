# Kinward for Home Assistant

A Home Assistant custom integration that exposes household-shared Kinward state
through ordinary Home Assistant entities and a core-card dashboard, instead of
a standalone Kinward frontend. See
[`docs/ha-native/household-trial.md`](../../docs/ha-native/household-trial.md)
for a step-by-step household trial covering everything below end to end.

## What this preview does and does not do

- Exposes backend availability, household adult/child counts, and placeholder
  briefing/attention/next-event entities (these report an honest
  `intentionally-disabled` / `not-yet-implemented` state - Epic 5's real
  briefing/calendar/attention pipeline isn't built yet).
- `conversation.kinward` resolves whichever Home Assistant user is actually
  talking to an account-bearing Kinward profile (via the integration's Options
  flow - "Configure" on the integration's device page). A mapped request gets
  a real, persisted, multi-turn topic - but since no model provider is
  configured in this deployment, every reply is still a truthful "no model
  configured" capability report rather than a generated answer. An unmapped
  HA user or a shared display is handed off entirely to Home Assistant's own
  built-in Assist agent instead - never a Kinward-generated reply, and never
  another person's private context (epics.md Story 2.5).
- Cancelling a request always reports "already terminal" today - every turn
  completes synchronously in the same call that creates it, so there's never
  an in-flight turn for a separate cancel call to actually interrupt
  (epics.md Story 2.3). The endpoint is the real interface future async/model
  work will give teeth to.
- Topics can be listed, renamed, archived/reopened, inspected, and deleted as
  backend capability (`GET`/`PATCH`/`DELETE /api/v1/integration/topics`) -
  epics.md Story 2.4. There's no HA entity/service exposing this yet (the
  story permits backend-only capability with "first HA UI exposes only a
  subset"). Reclassifying a topic's privacy class (e.g. sharing a private
  topic to the household) is deliberately not implemented - that's real,
  unbuilt access-control design, not a label flip.
- Does not manage Home Assistant `person.*` or `calendar.*` entities - those
  remain fully HA's own, and the dashboard below only references them.

## Install (development)

`custom_components/kinward` is bind-mounted into the `homeassistant` dev
container automatically - see the repository root [`README.md`](../../README.md#home-assistant-development)
for `docker compose --profile ha up`. There is no manual copy step for local
development.

For a Home Assistant instance outside this repository's Docker Compose setup,
copy this directory to that instance's `config/custom_components/kinward/`.

## Configure

1. In Home Assistant, go to **Settings -> Devices & Services -> Add
   Integration**, and search for "Kinward".
2. Enter the backend URL (`http://api:8000` from inside the `ha` compose
   profile's network, or wherever the Kinward backend is reachable) and an
   integration token.
3. Generate a token first if you don't have one - see the root README's
   "Home Assistant development" section for the `kinward.cli
   create-integration-token` command.

The config flow distinguishes an unreachable backend, a rejected token, an
incompatible API contract version, and a backend with no household set up yet.

## Map Home Assistant users to Kinward profiles

On the integration's card under **Settings -> Devices & Services**, click
**Configure** to open the Options flow. Each active, non-system Home Assistant
user is presented one at a time - choose the Kinward profile they are, or
"Not mapped". Only account-bearing profiles can be chosen (today that's just
the household's bootstrap administrator, until Epic 3's invitation flow adds
accounts for everyone else). The mapping itself lives on the Kinward backend,
not in Home Assistant's local storage, so it can be inspected/audited there
independently of this UI.

## Dashboard

Import [`kinward-dashboard.yaml`](kinward-dashboard.yaml): **Settings ->
Dashboards -> Add Dashboard -> New dashboard from scratch**, then the
dashboard's three-dot menu -> **Edit Dashboard** -> three-dot menu -> **Raw
configuration editor**, and paste the file's contents. Replace every
`person.replace_with_*` and `calendar.replace_with_*` placeholder with this
household's real entity IDs - never commit real entity IDs or names to source
control.

## Services

`kinward.refresh` re-polls the backend immediately instead of waiting for the
next scheduled update (there is no backend "generate a briefing" action yet).

## Diagnostics

Download diagnostics from the integration's device page to get a redacted
snapshot (the integration token is never included) useful for filing an
issue.
