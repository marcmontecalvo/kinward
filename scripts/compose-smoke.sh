#!/usr/bin/env bash
set -Eeuo pipefail

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PROJECT="kinward-smoke-$$"
readonly FAILURE_PROJECT="${PROJECT}-migration-failure"
readonly EXAMPLE_PROJECT="${PROJECT}-example-env"
readonly API_PORT="${KINWARD_SMOKE_PORT:-18080}"
readonly TMP_DIR="$(mktemp -d)"
readonly OVERRIDE_FILE="${TMP_DIR}/migration-failure.yaml"
readonly EXAMPLE_ENV_FILE="${TMP_DIR}/example.env"

export KINWARD_API_PORT="${API_PORT}"
export KINWARD_DATABASE_URL="sqlite+aiosqlite:////data/kinward.db"
export KINWARD_MODEL_PROVIDER="none"
export KINWARD_MEMORY_BACKEND="none"
export KINWARD_KNOWLEDGE_BACKEND="none"
export KINWARD_CALENDAR_PROVIDER="none"
export KINWARD_HONCHO_URL=""
export KINWARD_LLM_WIKI_URL=""
export KINWARD_HOME_ASSISTANT_URL=""
export KINWARD_HOME_ASSISTANT_TOKEN=""

COMPOSE=(docker compose --env-file /dev/null --project-directory "${ROOT}" -f "${ROOT}/compose.yaml" -p "${PROJECT}")
FAILURE_COMPOSE=(docker compose --env-file /dev/null --project-directory "${ROOT}" -f "${ROOT}/compose.yaml" -f "${OVERRIDE_FILE}" -p "${FAILURE_PROJECT}")
EXAMPLE_COMPOSE=(env -u KINWARD_DATABASE_URL -u KINWARD_API_PORT docker compose --env-file "${EXAMPLE_ENV_FILE}" --project-directory "${ROOT}" -f "${ROOT}/compose.yaml" -p "${EXAMPLE_PROJECT}")

fail() {
  printf 'compose smoke: FAIL: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  if [[ -f "${OVERRIDE_FILE}" ]]; then
    "${FAILURE_COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  if [[ -f "${EXAMPLE_ENV_FILE}" ]]; then
    "${EXAMPLE_COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

wait_for_state() {
  local service="$1"
  local expected="$2"
  local attempts="${3:-30}"
  local compose_name="${4:-COMPOSE}"
  local -n compose_ref="${compose_name}"
  local container_id state
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    container_id="$("${compose_ref[@]}" ps -aq "${service}")"
    if [[ -n "${container_id}" ]]; then
      state="$(docker inspect --format '{{.State.Status}}' "${container_id}")"
      if [[ "${state}" == "${expected}" ]]; then
        return 0
      fi
    fi
    sleep 2
  done
  fail "${service} did not reach state ${expected}"
}

wait_for_healthy() {
  local service="$1"
  local attempts="${2:-45}"
  local compose_name="${3:-COMPOSE}"
  local -n compose_ref="${compose_name}"
  local container_id health
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    container_id="$("${compose_ref[@]}" ps -q "${service}")"
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

default_services="$("${COMPOSE[@]}" config --services | sort)"
expected_default=$'api\nmigrate\nworker'
[[ "${default_services}" == "${expected_default}" ]] || fail "default service inventory was: ${default_services//$'\n'/, }"
for forbidden in postgres redis model memory knowledge calendar home-assistant observability; do
  if grep -qx "${forbidden}" <<<"${default_services}"; then
    fail "default inventory unexpectedly contains ${forbidden}"
  fi
done

profile_services="$("${COMPOSE[@]}" --profile postgres config --services | sort)"
expected_profile=$'api\nmigrate\npostgres\nworker'
[[ "${profile_services}" == "${expected_profile}" ]] || fail "PostgreSQL profile inventory was: ${profile_services//$'\n'/, }"
if grep -q 'redis' <<<"${profile_services}"; then
  fail "Redis is present in the PostgreSQL profile"
fi

printf '%s\n' \
  'services:' \
  '  migrate:' \
  '    command: ["sh", "-c", "exit 23"]' >"${OVERRIDE_FILE}"

"${COMPOSE[@]}" build

set +e
"${FAILURE_COMPOSE[@]}" up --detach --no-build >/dev/null 2>&1
failure_up_status=$?
set -e
[[ "${failure_up_status}" -ne 0 ]] || fail "injected migration failure unexpectedly reported success"
failure_migrate_id="$("${FAILURE_COMPOSE[@]}" ps -aq migrate)"
[[ -n "${failure_migrate_id}" ]] || fail "injected migration container was not created"
failure_exit="$(docker inspect --format '{{.State.ExitCode}}' "${failure_migrate_id}")"
[[ "${failure_exit}" == "23" ]] || fail "injected migration exited with ${failure_exit}, expected 23"
failure_running="$("${FAILURE_COMPOSE[@]}" ps --status running --services)"
if grep -Eq '^(api|worker)$' <<<"${failure_running}"; then
  fail "API or worker ran after migration failure"
fi
"${FAILURE_COMPOSE[@]}" down --volumes --remove-orphans >/dev/null

"${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
"${COMPOSE[@]}" up --build --detach

wait_for_state migrate exited
migrate_id="$("${COMPOSE[@]}" ps -aq migrate)"
migrate_exit="$(docker inspect --format '{{.State.ExitCode}}' "${migrate_id}")"
[[ "${migrate_exit}" == "0" ]] || fail "migration exited with ${migrate_exit}"
migrate_started_at="$(docker inspect --format '{{.State.StartedAt}}' "${migrate_id}")"

wait_for_healthy worker
wait_for_healthy api

curl --fail --silent --show-error "http://127.0.0.1:${API_PORT}/api/v1/health" >"${TMP_DIR}/health.json" || fail "API health is unreachable"
setup_status="$(curl --fail --silent --show-error "http://127.0.0.1:${API_PORT}/api/v1/setup/status")" || fail "versioned setup status route is unreachable"
[[ "${setup_status}" == '{"configured":false,"bootstrap_available":false}' ]] || fail "clean deployment setup status was unexpected"
if ! python3 - "${TMP_DIR}/health.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as health_file:
    health = json.load(health_file)
assert health["status"] == "healthy"
assert all(component["state"] == "healthy" for component in health["core"].values())
assert all(
    capability["state"] == "intentionally-disabled"
    for capability in health["capabilities"].values()
)
PY
then
  fail "health contract did not report healthy core and intentionally disabled providers"
fi

for service in api worker; do
  service_id="$("${COMPOSE[@]}" ps -q "${service}")"
  pid_one_command="$(docker inspect --format '{{json .Config.Cmd}}' "${service_id}")"
  if grep -qi alembic <<<"${pid_one_command}"; then
    fail "${service} startup command runs Alembic"
  fi
done

"${COMPOSE[@]}" run --rm --no-deps migrate
migrate_started_after_rerun="$(docker inspect --format '{{.State.StartedAt}}' "${migrate_id}")"
[[ "${migrate_started_after_rerun}" == "${migrate_started_at}" ]] || fail "one-shot migration service was restarted"

revision_before="$("${COMPOSE[@]}" exec -T api python -c "import sqlite3; print(sqlite3.connect('/data/kinward.db').execute('SELECT version_num FROM alembic_version').fetchone()[0])")"
[[ "${revision_before}" == "004_conversation_topics" ]] || fail "unexpected schema revision before restart"
"${COMPOSE[@]}" restart api worker
wait_for_healthy worker
wait_for_healthy api
curl --fail --silent --show-error "http://127.0.0.1:${API_PORT}/api/v1/health" >"${TMP_DIR}/health-after-restart.json" || fail "health did not recover after restart"
grep -q '"status":"healthy"' "${TMP_DIR}/health-after-restart.json" || fail "core was not healthy after restart"

migrate_started_after_restart="$(docker inspect --format '{{.State.StartedAt}}' "${migrate_id}")"
[[ "${migrate_started_after_restart}" == "${migrate_started_at}" ]] || fail "API/worker restart reran migration service"
revision_after="$("${COMPOSE[@]}" exec -T api python -c "import sqlite3; print(sqlite3.connect('/data/kinward.db').execute('SELECT version_num FROM alembic_version').fetchone()[0])")"
[[ "${revision_after}" == "${revision_before}" ]] || fail "schema revision changed during API/worker restart"

"${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null
cp "${ROOT}/.env.example" "${EXAMPLE_ENV_FILE}"
"${EXAMPLE_COMPOSE[@]}" up --detach --no-build
wait_for_state migrate exited 30 EXAMPLE_COMPOSE
wait_for_healthy worker 45 EXAMPLE_COMPOSE
wait_for_healthy api 45 EXAMPLE_COMPOSE
example_database_url="$("${EXAMPLE_COMPOSE[@]}" exec -T worker python -c "from kinward.config import get_settings; print(get_settings().database_url)")"
[[ "${example_database_url}" == "sqlite+aiosqlite:////data/kinward.db" ]] || fail "copied .env.example did not select the shared SQLite path"
example_revision="$("${EXAMPLE_COMPOSE[@]}" exec -T worker python -c "import sqlite3; print(sqlite3.connect('/data/kinward.db').execute('SELECT version_num FROM alembic_version').fetchone()[0])")"
[[ "${example_revision}" == "004_conversation_topics" ]] || fail "copied .env.example did not expose the migrated shared schema"

printf 'compose smoke: PASS (migration, health, copied example env, inventory, failure gating, idempotency, restart, cleanup)\n'
