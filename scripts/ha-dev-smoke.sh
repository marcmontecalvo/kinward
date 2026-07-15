#!/usr/bin/env bash
set -Eeuo pipefail

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PROJECT="kinward-ha-smoke-$$"
readonly API_PORT="${KINWARD_SMOKE_PORT:-18081}"
readonly HA_PORT="${KINWARD_HA_SMOKE_PORT:-18123}"

export KINWARD_API_PORT="${API_PORT}"
export KINWARD_HA_PORT="${HA_PORT}"
export KINWARD_DATABASE_URL="sqlite+aiosqlite:////data/kinward.db"
export KINWARD_MODEL_PROVIDER="none"
export KINWARD_MEMORY_BACKEND="none"
export KINWARD_KNOWLEDGE_BACKEND="none"
export KINWARD_CALENDAR_PROVIDER="none"
export KINWARD_HONCHO_URL=""
export KINWARD_LLM_WIKI_URL=""
export KINWARD_HOME_ASSISTANT_URL=""
export KINWARD_HOME_ASSISTANT_TOKEN=""

COMPOSE=(docker compose --env-file /dev/null --project-directory "${ROOT}" -f "${ROOT}/compose.yaml" -p "${PROJECT}" --profile ha)

fail() {
  printf 'ha-dev smoke: FAIL: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_healthy() {
  local service="$1"
  local attempts="${2:-90}"
  local container_id health
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    container_id="$("${COMPOSE[@]}" ps -q "${service}")"
    if [[ -n "${container_id}" ]]; then
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "${container_id}")"
      if [[ "${health}" == "healthy" ]]; then
        return 0
      fi
      if [[ "$(docker inspect --format '{{.State.Status}}' "${container_id}")" == "exited" ]]; then
        fail "${service} exited before becoming healthy"
      fi
    fi
    sleep 2
  done
  fail "${service} did not become healthy"
}

command -v docker >/dev/null || fail "docker is required"
command -v curl >/dev/null || fail "curl is required"
docker info >/dev/null 2>&1 || fail "the Docker daemon is unavailable to this user"

ha_services="$("${COMPOSE[@]}" config --services | sort)"
grep -qx "homeassistant" <<<"${ha_services}" || fail "homeassistant is missing from the ha profile inventory"
grep -qx "api" <<<"${ha_services}" || fail "api is missing from the ha profile inventory"

"${COMPOSE[@]}" build
"${COMPOSE[@]}" up --detach

wait_for_healthy api
wait_for_healthy homeassistant

curl --fail --silent --show-error "http://127.0.0.1:${API_PORT}/api/v1/health" >/dev/null \
  || fail "Kinward API health is unreachable"
curl --fail --silent --show-error "http://127.0.0.1:${HA_PORT}/manifest.json" >/dev/null \
  || fail "Home Assistant is unreachable"

ha_container="$("${COMPOSE[@]}" ps -q homeassistant)"
docker exec "${ha_container}" test -f /config/custom_components/kinward/manifest.json \
  || fail "custom_components/kinward is not visible inside the homeassistant container"
docker exec "${ha_container}" python3 -c "
import json
with open('/config/custom_components/kinward/manifest.json', encoding='utf-8') as manifest_file:
    manifest = json.load(manifest_file)
assert manifest['domain'] == 'kinward'
assert manifest['config_flow'] is True
" || fail "mounted manifest.json is invalid"

docker exec "${ha_container}" python3 -c "
import yaml
with open('/config/custom_components/kinward/kinward-dashboard.yaml', encoding='utf-8') as dashboard_file:
    dashboard = yaml.safe_load(dashboard_file)
assert dashboard['title'] == 'Kinward'
assert dashboard['views'], 'dashboard has no views'
" || fail "kinward-dashboard.yaml did not parse as valid YAML"

default_services="$(docker compose --env-file /dev/null --project-directory "${ROOT}" -f "${ROOT}/compose.yaml" -p "${PROJECT}" config --services | sort)"
if grep -qx "homeassistant" <<<"${default_services}"; then
  fail "homeassistant unexpectedly appears in the default (non-ha-profile) inventory"
fi

printf 'ha-dev smoke: PASS (ha-profile inventory, health, mounted integration files, dashboard YAML)\n'
