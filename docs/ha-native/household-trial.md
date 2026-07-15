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
      and is titled with the real household name.
- [ ] Repeating the same entry is rejected as already configured (duplicate
      protection).

## 3. Display at least one HA person state and one Kinward-produced summary

- [ ] At least one `person.*` entity exists in HA (create one under
      **Settings -> People** if this is a fresh instance) and shows a state.
- [ ] `sensor.kinward_household_status` shows the real adult/child counts.
- [ ] `binary_sensor.kinward_backend` is `on`.

## 4. Run refresh or briefing generation from HA

- [ ] **Developer Tools -> Actions**, call `kinward.refresh`. It completes
      without error and `sensor.kinward_household_status`'s `last_changed`
      (or `sensor.kinward_last_refresh`'s state) updates.

## 5. Map a Home Assistant user to a Kinward profile

- [ ] On the integration's device page, click **Configure** to open the
      Options flow. Confirm it steps through each active HA user one at a
      time, showing their real name.
- [ ] Map the admin HA user to the household's admin Kinward profile; leave
      any other HA user "Not mapped".
- [ ] Re-opening **Configure** shows the mapping was saved (defaults reflect
      the previous choice).

## 6. Submit text requests through `conversation.kinward`

- [ ] **Developer Tools -> Actions**, call `conversation.process` targeting
      `conversation.kinward` as the **mapped** HA user with a short text
      request. It returns the truthful "no model configured" capability
      report and a `conversation_id`.
- [ ] Send a second request reusing that same `conversation_id`; confirm it's
      the same value in the response (the topic continued rather than a new
      one being created).
- [ ] Call `conversation.process` again as an **unmapped** HA user (or after
      removing the mapping in step 5). Confirm the response truthfully says
      this HA user isn't linked to a Kinward profile, and that no
      `conversation_id` suggesting a real topic is returned.

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
