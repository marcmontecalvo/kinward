---
title: "HA-native household trial runbook"
status: manual-checklist
relatesTo: _bmad-output/planning-artifacts/epics.md (Story 1.7)
---

# Household trial: install and use the HA-native slice

This is a manual checklist for epics.md Story 1.7 ("Verify the same-day usable
slice"). It is intentionally not fully automated: the acceptance criteria
describe a human sitting down with a browser and a Companion app, not a CI
flow. `scripts/ha-dev-smoke.sh` automates everything around this trial that
*can* be automated safely (both containers healthy, the backend reachable,
the integration files mounted, the dashboard YAML valid) - run it first.

Record any defect or missing-UI observation inline under **Notes** as you go;
do not silently work around a problem to make a checkbox pass.

## 0. Prerequisites

- [ ] `bash scripts/ha-dev-smoke.sh` passes.
- [ ] A household exists (`POST /api/v1/setup/household` completed - see the
      root README's "Establish the household" section).
- [ ] An integration token exists: `docker compose exec api python -m
      kinward.cli create-integration-token --name "Household trial"`.

## 1. Install the integration on HA 2026.7.2

- [ ] Open <http://localhost:8123>, complete HA's own onboarding if this is a
      fresh `kinward-homeassistant` volume.
- [ ] **Settings -> Devices & Services -> Add Integration -> Kinward** appears
      and can be selected.

## 2. Configure a Kinward backend entry

- [ ] Enter `http://api:8000` and the token from step 0. The entry completes
      and is titled with the real household name - nothing else is asked.
- [ ] Repeating the same entry is rejected as already configured (duplicate
      protection).

## 3. Display at least one HA person state and one Kinward-produced summary

- [ ] At least one `person.*` entity exists in HA (create one under
      **Settings -> People** if this is a fresh instance) and shows a state.
- [ ] `sensor.kinward_household_status` shows the real adult/child counts.
- [ ] `binary_sensor.kinward_backend` is `on`.
- [ ] `sensor.kinward_people` exists; its state is the synced person count and
      its `people` attribute lists each person with `role` (`admin`/`member`).

## 4. Run refresh or briefing generation from HA

- [ ] **Developer Tools -> Actions**, call `kinward.refresh`. It completes
      without error and `sensor.kinward_household_status`'s `last_changed`
      (or `sensor.kinward_last_refresh`'s state) updates.

## 5. Confirm people sync automatically from Home Assistant

- [ ] Within one polling interval of adding the integration (step 2), every
      existing `person.*` entity appears as a synced Kinward person, visible
      either via `sensor.kinward_people`'s `people` attribute in
      **Developer Tools -> States** or `GET /api/v1/integration/people`.
- [ ] Add a second `person.*` entity in HA (with or without a linked login).
      Within one polling interval it also appears as a synced person, with no
      further configuration.
- [ ] Rename that person in HA. Confirm the synced Kinward profile's display
      name updates and no duplicate profile is created.
- [ ] Confirm the person linked to an HA admin user synced with Kinward
      `role: "admin"`, and any person linked to a non-admin (or no) user
      synced with `role: "member"` - there is no separate Kinward admin
      designation step. If more than one HA user is an admin, confirm more
      than one Kinward person shows `role: "admin"`. This is visible directly
      in `sensor.kinward_people`'s `people` attribute (also rendered as a
      table in the dashboard's "Household roster" view, step 8) - no API call
      needed to check who's an admin.
- [ ] In HA, toggle that user's admin flag off (**Settings -> People ->
      Users**), then re-poll. Confirm the synced person's Kinward role flips
      to `"member"` automatically, and back to `"admin"` if you toggle it on
      again.

## 6. Submit text requests through `conversation.kinward`

- [ ] **Developer Tools -> Actions**, call `conversation.process` targeting
      `conversation.kinward` as the **synced** HA user (one with a linked
      `person.*` entity, per step 5) with a short text request. It returns the
      truthful "no model configured" capability report and a
      `conversation_id`.
- [ ] Send a second request reusing that same `conversation_id`; confirm it's
      the same value in the response (the topic continued rather than a new
      one being created).
- [ ] Call `conversation.process` again as an HA user id with no synced
      `person.*` entity. Confirm the response comes from Home Assistant's own
      built-in Assist agent (e.g. ask it something HA's built-in agent can
      answer, like the time, or try a device-control phrase) rather than any
      Kinward-generated text - and that it never continues a synced person's
      private topic.
- [ ] Call `kinward.cli`-issued cancel: `POST
      /api/v1/integration/conversation/turns/{turnId}/cancel` for a turn
      created in this step. Confirm it reports `alreadyTerminal: true` with
      the turn's real outcome (expected - nothing is ever in-flight today).
- [ ] `GET /api/v1/integration/topics?haUserId=<synced HA user id>` lists the
      topic(s) from this step; `PATCH` a rename and an archive/reopen, then
      `DELETE` it and confirm a follow-up `GET` 404s.

## 7. Stop Kinward and verify truthful unavailable behavior

- [ ] `docker compose stop api`.
- [ ] Within one polling interval, `binary_sensor.kinward_backend` turns
      `off` and the other Kinward entities go `unavailable` - not stale data
      presented as current.
- [ ] `docker compose start api` and confirm entities recover.

## 8. Import and check the dashboard

- [ ] Import `custom_components/kinward/kinward-dashboard.yaml` (see that
      package's README) with the household's real `person.*`/`calendar.*`
      IDs substituted in.
- [ ] The dashboard renders correctly in the HA web UI and in the Companion
      app on at least one device.
- [ ] The "Household roster" view's People/Pets tables render (not "No people
      synced yet." once step 5 has run at least once).

## 9. Pet CRUD (admin-only, backend-only - no HA-side create/edit form yet)

Pets have no HA form to add or edit them (Epic 10's custom-card/panel gate
hasn't been triggered), so creation and edits go through the backend API
directly using the integration token and a synced admin's `ha_user_id`
(the same one visible in step 5's `sensor.kinward_people`). Reading the
result back is always visible in HA via `sensor.kinward_pets`.

- [ ] Create a pet:
      ```bash
      curl -s -X POST http://localhost:8000/api/v1/integration/pets \
        -H "Authorization: Bearer <integration token>" \
        -H "Content-Type: application/json" \
        -d '{"haUserId": "<admin ha_user_id>", "displayName": "Biscuit", "species": "Dog", "sharedFacts": ["Needs a walk every morning"]}'
      ```
      Returns `201` with the new pet's `id`. Within one polling interval,
      `sensor.kinward_pets` shows the updated count and the pet in its `pets`
      attribute (and the dashboard's Pets table).
- [ ] Update it: `PATCH /api/v1/integration/pets/{id}` with the same
      `haUserId` plus any of `displayName`/`species`/`sharedFacts`. Confirm
      the change is reflected after the next poll.
- [ ] Delete it: `DELETE /api/v1/integration/pets/{id}?haUserId=<admin ha_user_id>`
      returns `204`; confirm it disappears from `sensor.kinward_pets` after
      the next poll.
- [ ] Confirm a non-admin `haUserId` (or an unmapped one) gets `403
      admin_required` on create/update/delete, and that plain `GET /pets`
      needs only a valid integration token (no admin check) since pet facts
      are household-shared, not privacy-sensitive.

## Notes / defects observed

**2026-07-15 implementation trial** (driven directly against the HA REST API
against a real `--profile ha` stack - the same calls the frontend itself
makes for onboarding, config flow, states, actions, and `conversation.process`
- to verify backend behavior end to end before this was handed off for a
human pass). Steps 0-6 passed, including the config-flow error paths
(`cannot_connect`, `invalid_auth`), duplicate-entry rejection, the truthful
unavailable behavior on backend stop, and full recovery on restart.

One real defect was found and fixed during this pass: `ConversationEntity`
requires `supported_languages` implemented as an actual property (not just
set via `_attr_supported_languages`), and the entity needed `_attr_name =
None` to get the required `conversation.kinward` entity_id instead of
`conversation.kinward_kinward` (Home Assistant's `has_entity_name` naming
otherwise combines the device name with the entity's own name). Both are
fixed in `custom_components/kinward/conversation.py`.

**Not yet covered by this pass** - still needs a real human/browser/Companion
app trial: the config flow's and dashboard's actual visual rendering (step 1's
"appears and can be selected" and step 7's dashboard import/rendering).
Driving the REST API confirms the backend logic and entity behavior the UI
depends on, but not the frontend rendering itself.

**2026-07-16 Story 2.1/2.2 trial** (this time genuinely human/browser-driven,
against the household's real bootstrapped data, not a synthetic one): the
household operator opened the integration's Options flow in their own
browser, mapped their HA user to the admin Kinward profile, then ran
`conversation.process` twice via Developer Tools with the same
`conversation_id`. Server-side inspection (`ha_user_mappings`/`topics`/
`topic_turns` tables) confirmed the mapping, a single persisted topic, and
each turn recorded with `outcome="completed"` - continuity worked on the
first try, no defects found. Step 6's unmapped-denial path was left to the
operator as optional (already covered by backend unit tests
`test_conversation.py::test_unmapped_ha_user_fails_closed` and
`test_integration_api.py::test_conversation_reports_unmapped_users_truthfully`).

**2026-07-16 Story 2.3/2.4/2.5 trial** (REST-driven against the same real
household stack, using a long-lived access token the operator generated for
this pass). All verified with no defects:

- **2.5**: temporarily removed the mapping, called `conversation.process`
  asking "what time is it" - got a real answer ("6:00 PM") from Home
  Assistant's own built-in Assist agent, with its own unrelated
  `conversation_id`, confirming the delegation is real (not a Kinward
  response) and fully decoupled from Kinward topics. Restored the mapping
  afterward and confirmed the mapped path still worked identically to before
  (same truthful no-model response, `continue_conversation: true`).
- **2.3**: created a fresh turn, called its cancel endpoint - got
  `alreadyTerminal: true` with the turn's real recorded outcome, exactly as
  designed (nothing is ever in-flight today).
- **2.4**: full round-trip on a real topic - `GET` detail (including its
  turns), `PATCH` rename, `PATCH` archive, `PATCH` reopen, then `DELETE` on a
  different topic followed by a `GET` confirming 404. All worked on the
  first try against real household data, no synthetic fixtures needed.

`scripts/ha-dev-smoke.sh` and `scripts/compose-smoke.sh`'s first two legs
also passed post-migration (the `.env.example` leg collides with the live
household stack's own port 8000, same as the 2.1/2.2 pass - not a
regression).
