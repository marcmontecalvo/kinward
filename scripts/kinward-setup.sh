#!/usr/bin/env bash
# Interactive first-run wizard: choose optional peers (Honcho, LLM-Wiki, an HA
# dev/test container), bring the stack up, bootstrap the household, and mint a
# Home Assistant integration token. Run from a checkout of this repository:
#
#   scripts/kinward-setup.sh
#
# Or non-interactively:
#
#   scripts/kinward-setup.sh --non-interactive --household-name="The Smiths" \
#     --with-honcho --with-llm-wiki
#
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
cd "${ROOT}"

readonly ENV_FILE="${ROOT}/.env"
readonly VENDOR_DIR="${ROOT}/vendor"

# whiptail/dialog and `read` prompts must talk to the controlling terminal, not
# stdin - this script is commonly invoked via `curl ... | bash`, where stdin is
# the piped script itself, not the user's keyboard.
if [[ -e /dev/tty ]]; then
  readonly TTY=/dev/tty
else
  readonly TTY=/dev/stdin
fi

log()  { printf '==> %s\n' "$*"; }
warn() { printf '\033[33m==> %s\033[0m\n' "$*" >&2; }
fail() { printf '\033[31mkinward setup: FAIL: %s\033[0m\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage: scripts/kinward-setup.sh [options]

  --with-honcho / --without-honcho     Install Honcho (conversational memory).
  --with-llm-wiki / --without-llm-wiki Install LLM-Wiki (curated knowledge).
  --with-ha-dev                        Also start a local HA dev/test container.
                                        Skip this if you already run Home Assistant
                                        elsewhere, which is the common case.
  --household-name=NAME                Household name (skips the prompt).
  --fallback-assistant-name=NAME       Shared fallback assistant name (default: Kinward).
  --non-interactive                    Never prompt; fail if a required value is missing.
  -h, --help                           Show this help.
USAGE
}

WITH_HONCHO=""
WITH_LLM_WIKI=""
WITH_HA="no"
HOUSEHOLD_NAME=""
FALLBACK_NAME=""
NONINTERACTIVE=false

for arg in "$@"; do
  case "${arg}" in
    --with-honcho) WITH_HONCHO=yes ;;
    --without-honcho) WITH_HONCHO=no ;;
    --with-llm-wiki) WITH_LLM_WIKI=yes ;;
    --without-llm-wiki) WITH_LLM_WIKI=no ;;
    --with-ha-dev) WITH_HA=yes ;;
    --household-name=*) HOUSEHOLD_NAME="${arg#*=}" ;;
    --fallback-assistant-name=*) FALLBACK_NAME="${arg#*=}" ;;
    --non-interactive) NONINTERACTIVE=true ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown option '${arg}' (see --help)" ;;
  esac
done

command -v docker >/dev/null 2>&1 || fail "docker is required. Run scripts/get-kinward.sh first, or install Docker manually."
docker compose version >/dev/null 2>&1 || fail "the Docker Compose plugin is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v git >/dev/null 2>&1 || fail "git is required."
command -v python3 >/dev/null 2>&1 || fail "python3 is required (used to build/parse setup API requests)."
docker info >/dev/null 2>&1 || fail "the Docker daemon is unreachable. Is it running, and can this user access it without sudo?"

ask() {
  local prompt="$1" default="${2:-}" reply
  read -r -p "${prompt}${default:+ [${default}]}: " reply <"${TTY}" || true
  printf '%s' "${reply:-${default}}"
}

ask_secret() {
  local prompt="$1" reply
  read -rsp "${prompt}: " reply <"${TTY}" || true
  printf '\n' >&2
  printf '%s' "${reply}"
}

ask_yn() {
  local prompt="$1" default="${2:-yes}" reply hint
  hint="y/N"; [[ "${default}" == yes ]] && hint="Y/n"
  while true; do
    read -r -p "${prompt} [${hint}]: " reply <"${TTY}" || true
    reply="${reply:-${default}}"
    case "${reply,,}" in
      y|yes) printf 'yes'; return 0 ;;
      n|no) printf 'no'; return 0 ;;
    esac
  done
}

random_secret() {
  local bytes="${1:-24}"
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex "${bytes}"
  else
    head -c "${bytes}" /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

set_env() {
  local key="$1" value="$2"
  touch "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    awk -v k="${key}" -v v="${value}" 'BEGIN{FS=OFS="="} $1==k{$0=k"="v} {print}' "${ENV_FILE}" >"${tmp}"
    mv "${tmp}" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${key}" "${value}" >>"${ENV_FILE}"
  fi
}

get_env() {
  local key="$1" default="${2:-}"
  [[ -f "${ENV_FILE}" ]] || { printf '%s' "${default}"; return; }
  local value
  value="$(grep "^${key}=" "${ENV_FILE}" 2>/dev/null | tail -n1 | cut -d= -f2-)"
  printf '%s' "${value:-${default}}"
}

clone_vendor() {
  local name="$1" url="$2"
  mkdir -p "${VENDOR_DIR}"
  if [[ -d "${VENDOR_DIR}/${name}/.git" ]]; then
    log "Updating vendored ${name}..."
    git -C "${VENDOR_DIR}/${name}" pull --ff-only --quiet || warn "could not fast-forward ${name}; using the existing checkout"
  else
    log "Cloning ${name} into vendor/${name}..."
    git clone --depth 1 --quiet "${url}" "${VENDOR_DIR}/${name}"
  fi
}

# ---------------------------------------------------------------------------
# Component selection
# ---------------------------------------------------------------------------

if [[ -z "${WITH_HONCHO}" || -z "${WITH_LLM_WIKI}" ]]; then
  if [[ "${NONINTERACTIVE}" == true ]]; then
    WITH_HONCHO="${WITH_HONCHO:-no}"
    WITH_LLM_WIKI="${WITH_LLM_WIKI:-no}"
  elif command -v whiptail >/dev/null 2>&1; then
    selection="$(whiptail --title "Kinward setup" --checklist \
      "Select components to install alongside Kinward (space to toggle, enter to confirm):" \
      16 78 3 \
      honcho "Honcho - conversational memory" ON \
      llm-wiki "LLM-Wiki - curated household knowledge" ON \
      ha-dev "Home Assistant dev/test container (skip if you already run HA)" OFF \
      3>&1 1>&2 2>&3 <"${TTY}" >"${TTY}")" || fail "setup cancelled"
    [[ "${selection}" == *honcho* ]] && WITH_HONCHO=yes || WITH_HONCHO="${WITH_HONCHO:-no}"
    [[ "${selection}" == *llm-wiki* ]] && WITH_LLM_WIKI=yes || WITH_LLM_WIKI="${WITH_LLM_WIKI:-no}"
    [[ "${selection}" == *ha-dev* ]] && WITH_HA=yes || WITH_HA="${WITH_HA:-no}"
  else
    warn "whiptail is not installed; falling back to plain prompts (Debian/Ubuntu: apt-get install -y whiptail)."
    [[ -z "${WITH_HONCHO}" ]] && WITH_HONCHO="$(ask_yn "Install Honcho (conversational memory)?" yes)"
    [[ -z "${WITH_LLM_WIKI}" ]] && WITH_LLM_WIKI="$(ask_yn "Install LLM-Wiki (curated household knowledge)?" yes)"
    [[ "${WITH_HA}" == no ]] && WITH_HA="$(ask_yn "Also start a local Home Assistant dev/test container? (skip if you already run HA)" no)"
  fi
fi

COMPOSE_FILES=(-f compose.yaml)
COMPOSE_PROFILES=()

if [[ "${WITH_HONCHO}" == yes ]]; then
  clone_vendor honcho https://github.com/plastic-labs/honcho.git
  COMPOSE_FILES+=(-f compose.honcho.yaml)
  COMPOSE_PROFILES+=(--profile honcho)

  log "Honcho needs an LLM provider for memory extraction, summarization, and dialectic chat."
  provider="$(get_env KINWARD_HONCHO_LLM_PROVIDER "")"
  if [[ -z "${provider}" ]]; then
    provider="$(ask "LLM provider for Honcho (openai/anthropic/gemini)" openai)"
  fi
  case "${provider}" in
    openai) honcho_key_var=KINWARD_HONCHO_LLM_OPENAI_API_KEY ;;
    anthropic) honcho_key_var=KINWARD_HONCHO_LLM_ANTHROPIC_API_KEY ;;
    gemini) honcho_key_var=KINWARD_HONCHO_LLM_GEMINI_API_KEY ;;
    *) fail "unknown Honcho LLM provider '${provider}' (expected openai, anthropic, or gemini)" ;;
  esac
  existing_key="$(get_env "${honcho_key_var}" "")"
  if [[ -n "${existing_key}" ]]; then
    log "Reusing the ${provider} API key already stored in .env."
  else
    api_key="$(ask_secret "API key for ${provider} (used by Honcho only)")"
    [[ -n "${api_key}" ]] || fail "Honcho will not start without an LLM provider API key."
    set_env "${honcho_key_var}" "${api_key}"
  fi
  set_env KINWARD_HONCHO_LLM_PROVIDER "${provider}"
  [[ -n "$(get_env KINWARD_HONCHO_POSTGRES_PASSWORD)" ]] || set_env KINWARD_HONCHO_POSTGRES_PASSWORD "$(random_secret 24)"
  set_env KINWARD_HONCHO_URL "http://honcho-api:8000"
  set_env KINWARD_MEMORY_BACKEND "honcho"
fi

if [[ "${WITH_LLM_WIKI}" == yes ]]; then
  clone_vendor llm_wiki https://github.com/marcmontecalvo/llm_wiki.git
  COMPOSE_FILES+=(-f compose.llmwiki.yaml)
  COMPOSE_PROFILES+=(--profile llm-wiki)
  [[ -n "$(get_env KINWARD_LLM_WIKI_UI_PASSWORD)" ]] || set_env KINWARD_LLM_WIKI_UI_PASSWORD "$(random_secret 16)"
  set_env KINWARD_LLM_WIKI_URL "http://llm-wiki:3050"
  set_env KINWARD_KNOWLEDGE_BACKEND "llm_wiki"
fi

[[ "${WITH_HA}" == yes ]] && COMPOSE_PROFILES+=(--profile ha)

# ---------------------------------------------------------------------------
# Bring the stack up
# ---------------------------------------------------------------------------

API_PORT="$(get_env KINWARD_API_PORT 8000)"
readonly API_PORT
readonly BASE_URL="http://localhost:${API_PORT}"

wait_for_healthy() {
  local service="$1" attempts="${2:-60}" container_id health
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    container_id="$(docker compose --env-file "${ENV_FILE}" "${COMPOSE_FILES[@]}" ps -q "${service}" 2>/dev/null)"
    if [[ -n "${container_id}" ]]; then
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "${container_id}")"
      [[ "${health}" == "healthy" ]] && return 0
      [[ "${health}" == "missing" && "$(docker inspect --format '{{.State.Status}}' "${container_id}")" == "running" ]] && return 0
      if [[ "$(docker inspect --format '{{.State.Status}}' "${container_id}")" == "exited" ]]; then
        fail "${service} exited before becoming healthy - check: docker compose logs ${service}"
      fi
    fi
    sleep 2
  done
  fail "${service} did not become healthy in time - check: docker compose logs ${service}"
}

log "Generating a one-time household setup authorization..."
export KINWARD_SETUP_AUTHORIZATION
KINWARD_SETUP_AUTHORIZATION="$(random_secret 24)"

extras=""
[[ "${WITH_HONCHO}" == yes ]] && extras+=" + Honcho"
[[ "${WITH_LLM_WIKI}" == yes ]] && extras+=" + LLM-Wiki"
log "Building and starting Kinward${extras} (this can take a while on first run)..."
docker compose --env-file "${ENV_FILE}" "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILES[@]}" up --build -d

wait_for_healthy api
wait_for_healthy worker
[[ "${WITH_HONCHO}" == yes ]] && wait_for_healthy honcho-api 90
[[ "${WITH_HA}" == yes ]] && wait_for_healthy homeassistant 90

# ---------------------------------------------------------------------------
# Household bootstrap
# ---------------------------------------------------------------------------

setup_status="$(curl -fsS "${BASE_URL}/api/v1/setup/status")" || fail "the Kinward API is unreachable at ${BASE_URL}"
already_configured="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['configured'])" "${setup_status}")"

if [[ "${already_configured}" == "True" ]]; then
  log "A household is already configured on this deployment; skipping bootstrap."
else
  log "Let's set up your household."
  if [[ -z "${HOUSEHOLD_NAME}" ]]; then
    if [[ "${NONINTERACTIVE}" == true ]]; then
      fail "--household-name is required in non-interactive mode"
    fi
    HOUSEHOLD_NAME="$(ask "Household name" "")"
  fi
  [[ -n "${HOUSEHOLD_NAME}" ]] || fail "a household name is required"
  if [[ -z "${FALLBACK_NAME}" ]]; then
    if [[ "${NONINTERACTIVE}" == true ]]; then
      FALLBACK_NAME="Kinward"
    else
      FALLBACK_NAME="$(ask "Shared fallback assistant name" "Kinward")"
    fi
  fi

  csrf_token="$(random_secret 24)"
  idempotency_key="install-$(random_secret 8)"
  bootstrap_body="$(python3 - "${HOUSEHOLD_NAME}" "${FALLBACK_NAME}" "${csrf_token}" <<'PY'
import json, sys
household_name, fallback_name, csrf_token = sys.argv[1:4]
print(json.dumps({
    "household_name": household_name,
    "fallback_assistant_name": fallback_name,
    "pets": [],
    "csrf_token": csrf_token,
}))
PY
)"

  bootstrap_response="$(curl -fsS -X POST "${BASE_URL}/api/v1/setup/household" \
    -H "X-Setup-Authorization: ${KINWARD_SETUP_AUTHORIZATION}" \
    -H "Idempotency-Key: ${idempotency_key}" \
    -H "X-CSRF-Token: ${csrf_token}" \
    -H "Content-Type: application/json" \
    -d "${bootstrap_body}")" || fail "household bootstrap failed - check: docker compose logs api"
  fallback_assistant_id="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['fallback_assistant_id'])" "${bootstrap_response}")"
  log "Household '${HOUSEHOLD_NAME}' created (fallback assistant: ${FALLBACK_NAME}, id ${fallback_assistant_id})."
fi

log "Clearing the one-time setup authorization from the running containers..."
unset KINWARD_SETUP_AUTHORIZATION
docker compose --env-file "${ENV_FILE}" "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILES[@]}" up -d --no-build api worker
wait_for_healthy api
wait_for_healthy worker

# ---------------------------------------------------------------------------
# Integration token + provider wiring
# ---------------------------------------------------------------------------

log "Minting a Home Assistant integration token..."
token_output="$(docker compose --env-file "${ENV_FILE}" "${COMPOSE_FILES[@]}" exec -T api \
  python -m kinward.cli create-integration-token --name "Home Assistant")" \
  || fail "could not mint an integration token - check: docker compose logs api"
integration_token="$(printf '%s\n' "${token_output}" | awk -F': ' '/^  token:/{print $2}')"
[[ -n "${integration_token}" ]] || fail "token minting succeeded but the token could not be parsed from CLI output"

if [[ "${WITH_HONCHO}" == yes || "${WITH_LLM_WIKI}" == yes ]]; then
  log "Pointing Kinward's provider settings at the peers you installed..."
  provider_body="$(python3 - "${WITH_HONCHO}" "${WITH_LLM_WIKI}" <<'PY'
import json, sys
with_honcho, with_wiki = sys.argv[1] == "yes", sys.argv[2] == "yes"
body = {}
if with_honcho:
    body["memoryBackend"] = "honcho"
    body["honchoUrl"] = "http://honcho-api:8000"
if with_wiki:
    body["knowledgeBackend"] = "llm_wiki"
    body["llmWikiUrl"] = "http://llm-wiki:3050"
print(json.dumps(body))
PY
)"
  curl -fsS -X PATCH "${BASE_URL}/api/v1/integration/settings/providers" \
    -H "Authorization: Bearer ${integration_token}" \
    -H "Content-Type: application/json" \
    -d "${provider_body}" >/dev/null \
    || warn "could not set provider settings automatically - set them from the Kinward integration's Options in Home Assistant instead."
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

cat <<SUMMARY

Kinward is running.

  API:                ${BASE_URL}
  Integration token:   ${integration_token}
    (shown once - store it now. Re-issue with:
     docker compose exec api python -m kinward.cli create-integration-token --name "<label>")

Next step - connect Home Assistant:
  1. Install custom_components/kinward in your Home Assistant config
     (see custom_components/kinward/README.md for HACS/manual instructions).
  2. In Home Assistant: Settings -> Devices & Services -> Add Integration -> Kinward.
  3. Backend URL: ${BASE_URL}   (use a LAN-reachable host/IP if HA runs elsewhere)
     Token: the value printed above
SUMMARY

if [[ "${WITH_HONCHO}" == yes ]]; then
  echo "  Honcho:    http://localhost:$(get_env KINWARD_HONCHO_PORT 8001) (internal: honcho-api:8000)"
fi
if [[ "${WITH_LLM_WIKI}" == yes ]]; then
  echo "  LLM-Wiki:  http://localhost:$(get_env KINWARD_LLM_WIKI_PORT 3050)"
fi
if [[ "${WITH_HA}" == yes ]]; then
  echo "  HA (dev):  http://localhost:$(get_env KINWARD_HA_PORT 8123)"
fi
echo
