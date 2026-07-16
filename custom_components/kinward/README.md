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
  talking to the Kinward person synced from that user's linked `person.*`
  entity - Kinward has no identity system of its own; see "Sync people from
  Home Assistant" below. A synced request gets a real, persisted, multi-turn
  topic - but since no model provider is configured in this deployment, every
  reply is still a truthful "no model configured" capability report rather
  than a generated answer. An unsynced HA user (no `person.*` entity links to
  them) or a shared display is handed off entirely to Home Assistant's own
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
incompatible API contract version, and a backend with no household set up
yet. Nothing further is asked - there's no separate admin-designation step
(see below).

## Sync people from Home Assistant

Kinward has no identity system of its own. Every ~60 seconds (the same poll
that refreshes the dashboard entities), the integration reads every Home
Assistant `person.*` entity and syncs it to the Kinward backend, keyed on that
person's stable Home Assistant registry id - not their name, and not their
linked login. A person with no login (e.g. a child) syncs in exactly the same
way as one with a login; only their `person.*` entity's `user_id` attribute
differs (absent vs. present). Renaming a person in Home Assistant, or turning
their login on or off later, never creates a duplicate Kinward profile and
never breaks `conversation.kinward`'s resolution of who's talking - both key
off the same stable id, not the name. Removing a person from Home Assistant
does not delete their Kinward profile or history; it only stops updating it.

Kinward also has no admin designation of its own: whoever is a Home Assistant
administrator is a Kinward administrator. Every sync pass looks up each
synced person's linked HA user (when they have one) and reconciles their
Kinward `role` to match that user's current admin flag - promoting or
demoting automatically as HA admin membership changes, with no action needed
in Kinward. Any number of people can hold the role at once; a household with
two HA admins has two Kinward admins. This is a coarse role only - it doesn't
by itself grant access to another adult's private data (that's privacy
classification, a separate axis - epics.md Story 3.3). Finer-grained
permissions than admin/member may be built later if actually needed.

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
