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

list_models() {
  # $1 = base_url, $2 = api_key (may be empty). Prints one model id per line.
  local base_url="$1" api_key="$2"
  local -a auth_header=()
  [[ -n "${api_key}" ]] && auth_header=(-H "Authorization: Bearer ${api_key}")
  curl -fsS "${auth_header[@]}" "${base_url%/}/models" 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
items = data.get("data", data) if isinstance(data, dict) else data
if not isinstance(items, list):
    sys.exit(1)
for item in items:
    if isinstance(item, dict) and item.get("id"):
        print(item["id"])
' 2>/dev/null
}

pick_model() {
  # $1 = base_url, $2 = api_key, $3 = purpose label for prompts. Echoes the chosen model id on stdout.
  local base_url="$1" api_key="$2" purpose="$3" models
  models="$(list_models "${base_url}" "${api_key}")"
  if [[ -z "${models}" ]]; then
    warn "could not list models from ${base_url%/}/models; enter the ${purpose} model id manually."
    ask "Model id for ${purpose}"
    return
  fi
  warn "Models available at ${base_url}:"
  local i=1 line
  while IFS= read -r line; do
    printf '  %d) %s\n' "${i}" "${line}" >&2
    i=$((i + 1))
  done <<<"${models}"
  local choice selected
  while true; do
    choice="$(ask "Pick the ${purpose} model (number, or paste a model id not listed)" "1")"
    if [[ "${choice}" =~ ^[0-9]+$ ]]; then
      selected="$(sed -n "${choice}p" <<<"${models}")"
      if [[ -n "${selected}" ]]; then
        printf '%s' "${selected}"
        return
      fi
      warn "no model at position ${choice}; try again."
    else
      printf '%s' "${choice}"
      return
    fi
  done
}

probe_embedding_dimension() {
  # $1 = base_url, $2 = api_key, $3 = model id. Echoes the vector length on success, nothing on failure.
  local base_url="$1" api_key="$2" model="$3"
  local -a auth_header=()
  [[ -n "${api_key}" ]] && auth_header=(-H "Authorization: Bearer ${api_key}")
  local body
  body="$(python3 -c 'import json, sys; print(json.dumps({"model": sys.argv[1], "input": "kinward-dimension-probe"}))' "${model}")"
  curl -fsS "${auth_header[@]}" -H "Content-Type: application/json" -X POST "${base_url%/}/embeddings" -d "${body}" 2>/dev/null \
    | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(len(data["data"][0]["embedding"]))
except (ValueError, KeyError, IndexError, TypeError):
    sys.exit(1)
' 2>/dev/null
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

  log "Honcho needs an LLM provider for memory extraction, summarization, dreaming, and dialectic chat."
  provider="$(get_env KINWARD_HONCHO_LLM_PROVIDER "")"
  if [[ -z "${provider}" ]]; then
    provider="$(ask "LLM provider for Honcho (openai/anthropic/gemini/local)" openai)"
  fi

  case "${provider}" in
    openai|anthropic|gemini)
      case "${provider}" in
        openai) honcho_key_var=KINWARD_HONCHO_LLM_OPENAI_API_KEY ;;
        anthropic) honcho_key_var=KINWARD_HONCHO_LLM_ANTHROPIC_API_KEY ;;
        gemini) honcho_key_var=KINWARD_HONCHO_LLM_GEMINI_API_KEY ;;
      esac
      existing_key="$(get_env "${honcho_key_var}" "")"
      if [[ -n "${existing_key}" ]]; then
        log "Reusing the ${provider} API key already stored in .env."
      else
        api_key="$(ask_secret "API key for ${provider} (used by Honcho only)")"
        [[ -n "${api_key}" ]] || fail "Honcho will not start without an LLM provider API key."
        set_env "${honcho_key_var}" "${api_key}"
      fi
      ;;
    local)
      log "Local/self-hosted LLM (any OpenAI-compatible server: vLLM, Ollama, LiteLLM, LM Studio, ...)."
      chat_base_url="$(get_env KINWARD_HONCHO_CHAT_BASE_URL "")"
      [[ -n "${chat_base_url}" ]] || chat_base_url="$(ask "Base URL for chat/inference (OpenAI-compatible, e.g. http://10.0.0.5:8000/v1)")"
      [[ -n "${chat_base_url}" ]] || fail "a base URL is required for a local LLM provider"
      chat_api_key="$(ask_secret "API key for ${chat_base_url} (blank if your server does not require one)")"

      chat_model="$(pick_model "${chat_base_url}" "${chat_api_key}" "chat/inference")"
      [[ -n "${chat_model}" ]] || fail "a chat model id is required"

      if [[ "$(ask_yn "Use the same URL for embeddings?" yes)" == yes ]]; then
        embedding_base_url="${chat_base_url}"
        embedding_api_key="${chat_api_key}"
      else
        embedding_base_url="$(ask "Base URL for embeddings (OpenAI-compatible)" "${chat_base_url}")"
        embedding_api_key="$(ask_secret "API key for ${embedding_base_url} (blank if not required)")"
      fi
      embedding_model="$(pick_model "${embedding_base_url}" "${embedding_api_key}" "embedding")"
      [[ -n "${embedding_model}" ]] || fail "an embedding model id is required"

      if [[ "${embedding_api_key}" != "${chat_api_key}" ]]; then
        warn "the embedding endpoint's API key differs from the chat endpoint's; this wizard only wires"
        warn "one shared key (LLM_OPENAI_API_KEY) for both. Edit vendor/honcho/.env after setup if they"
        warn "truly need different credentials."
      fi

      log "Probing ${embedding_model} to detect its output vector dimension..."
      embedding_dim="$(probe_embedding_dimension "${embedding_base_url}" "${embedding_api_key}" "${embedding_model}")"
      if [[ -z "${embedding_dim}" ]]; then
        warn "could not auto-detect the embedding dimension by calling ${embedding_base_url%/}/embeddings."
        embedding_dim="$(ask "Embedding vector dimension for ${embedding_model}" "1536")"
      else
        log "Detected a ${embedding_dim}-dimension embedding vector from ${embedding_model}."
      fi
      [[ "${embedding_dim}" =~ ^[0-9]+$ ]] || fail "embedding dimension must be a number, got '${embedding_dim}'"

      existing_dim="$(get_env KINWARD_HONCHO_EMBEDDING_DIMENSIONS "")"
      if [[ -n "${existing_dim}" && "${existing_dim}" != "${embedding_dim}" ]]; then
        warn "Honcho's pgvector schema was previously configured for dimension ${existing_dim}; it will be"
        warn "re-adjusted to ${embedding_dim} by honcho-configure-embeddings on next startup. That step"
        warn "refuses to run if any embeddings have already been written (dimension is otherwise immutable"
        warn "for the life of a deployment - see Honcho's changing-embeddings docs)."
      fi

      set_env KINWARD_HONCHO_CHAT_BASE_URL "${chat_base_url}"
      set_env KINWARD_HONCHO_CHAT_MODEL "${chat_model}"
      set_env KINWARD_HONCHO_EMBEDDING_BASE_URL "${embedding_base_url}"
      set_env KINWARD_HONCHO_EMBEDDING_MODEL "${embedding_model}"
      set_env KINWARD_HONCHO_EMBEDDING_DIMENSIONS "${embedding_dim}"
      set_env KINWARD_HONCHO_LLM_OPENAI_API_KEY "${chat_api_key:-local-no-key-required}"
      ;;
    *) fail "unknown Honcho LLM provider '${provider}' (expected openai, anthropic, gemini, or local)" ;;
  esac

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
# Kinward's own conversation model - separate from Honcho's memory pipeline.
# Without this, assistants have no model to actually reply with until an
# admin visits the Kinward integration's Options screen in Home Assistant.
# ---------------------------------------------------------------------------

model_provider="$(get_env KINWARD_MODEL_PROVIDER "")"
model_base_url="$(get_env KINWARD_MODEL_BASE_URL "")"
model_name="$(get_env KINWARD_MODEL_NAME "")"
model_api_key="$(get_env KINWARD_MODEL_API_KEY "")"

if [[ -z "${model_provider}" ]]; then
  reused=no
  if [[ "${WITH_HONCHO}" == yes && "$(get_env KINWARD_HONCHO_LLM_PROVIDER)" == local ]]; then
    if [[ "$(ask_yn "Use the same local model you just configured for Honcho (${chat_model} @ ${chat_base_url}) for Kinward's own assistant conversations too?" yes)" == yes ]]; then
      model_provider="openai-compatible"
      model_base_url="${chat_base_url}"
      model_name="${chat_model}"
      model_api_key="${chat_api_key}"
      reused=yes
    fi
  fi
  if [[ "${reused}" == no ]]; then
    if [[ "$(ask_yn "Configure a conversation model for Kinward's own assistants now? (skip to leave this for the Kinward integration's Options screen in Home Assistant later)" yes)" == yes ]]; then
      model_provider="$(ask "Model provider (openai/anthropic/openai-compatible)" openai)"
      case "${model_provider}" in
        openai-compatible)
          model_base_url="$(ask "Base URL (OpenAI-compatible, e.g. http://10.0.0.5:8000/v1)")"
          [[ -n "${model_base_url}" ]] || fail "a base URL is required for the openai-compatible provider"
          model_api_key="$(ask_secret "API key for ${model_base_url} (blank if your server does not require one)")"
          model_name="$(pick_model "${model_base_url}" "${model_api_key}" "conversation")"
          ;;
        openai|anthropic)
          model_name="$(ask "Model name")"
          model_api_key="$(ask_secret "API key for ${model_provider}")"
          ;;
        *) fail "unknown model provider '${model_provider}' (expected openai, anthropic, or openai-compatible)" ;;
      esac
    else
      model_provider="none"
    fi
  fi
  set_env KINWARD_MODEL_PROVIDER "${model_provider}"
  [[ -n "${model_base_url}" ]] && set_env KINWARD_MODEL_BASE_URL "${model_base_url}"
  [[ -n "${model_name}" ]] && set_env KINWARD_MODEL_NAME "${model_name}"
  [[ -n "${model_api_key}" ]] && set_env KINWARD_MODEL_API_KEY "${model_api_key}"
fi

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

wait_for_exit_success() {
  local service="$1" attempts="${2:-60}" container_id status
  local error_hint="${3:-check: docker compose logs ${service}}"
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    container_id="$(docker compose --env-file "${ENV_FILE}" "${COMPOSE_FILES[@]}" ps -aq "${service}" 2>/dev/null)"
    if [[ -n "${container_id}" ]]; then
      status="$(docker inspect --format '{{.State.Status}}' "${container_id}")"
      if [[ "${status}" == "exited" ]]; then
        [[ "$(docker inspect --format '{{.State.ExitCode}}' "${container_id}")" == "0" ]] && return 0
        fail "${error_hint}"
      fi
    fi
    sleep 2
  done
  fail "${service} did not finish in time - check: docker compose logs ${service}"
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

if [[ "${WITH_HONCHO}" == yes ]]; then
  log "Applying Honcho's database migrations and pgvector dimension..."
  wait_for_exit_success honcho-configure-embeddings 60 \
    "honcho-configure-embeddings failed - check: docker compose logs honcho-configure-embeddings (a common cause is the embedding dimension changing on a deployment that already has embeddings written; see the warning above, or wipe the honcho volumes with 'docker compose ... down --volumes' for a clean local dev reset)"
  wait_for_healthy honcho-api 90
fi
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

if [[ "${WITH_HONCHO}" == yes || "${WITH_LLM_WIKI}" == yes || ( -n "${model_provider}" && "${model_provider}" != none ) ]]; then
  log "Pointing Kinward's provider settings at what you configured..."
  provider_body="$(python3 - "${WITH_HONCHO}" "${WITH_LLM_WIKI}" "${model_provider}" "${model_base_url}" "${model_name}" "${model_api_key}" <<'PY'
import json, sys
with_honcho, with_wiki, model_provider, model_base_url, model_name, model_api_key = (
    sys.argv[1] == "yes",
    sys.argv[2] == "yes",
    sys.argv[3],
    sys.argv[4],
    sys.argv[5],
    sys.argv[6],
)
body = {}
if with_honcho:
    body["memoryBackend"] = "honcho"
    body["honchoUrl"] = "http://honcho-api:8000"
if with_wiki:
    body["knowledgeBackend"] = "llm_wiki"
    body["llmWikiUrl"] = "http://llm-wiki:3050"
if model_provider and model_provider != "none":
    body["modelProvider"] = model_provider
    if model_base_url:
        body["modelBaseUrl"] = model_base_url
    if model_name:
        body["modelName"] = model_name
    if model_api_key:
        body["modelApiKey"] = model_api_key
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

if [[ -n "${model_provider}" && "${model_provider}" != none ]]; then
  echo "  Conversation model: ${model_provider} - $(get_env KINWARD_MODEL_NAME)${model_base_url:+ @ ${model_base_url}}"
else
  echo "  Conversation model: none set - configure one from the Kinward integration's Options in Home Assistant, or assistants have nothing to reply with."
fi
if [[ "${WITH_HONCHO}" == yes ]]; then
  echo "  Honcho:    http://localhost:$(get_env KINWARD_HONCHO_PORT 8001) (internal: honcho-api:8000)"
  if [[ "$(get_env KINWARD_HONCHO_LLM_PROVIDER)" == local ]]; then
    echo "             chat model:      $(get_env KINWARD_HONCHO_CHAT_MODEL) @ $(get_env KINWARD_HONCHO_CHAT_BASE_URL)"
    echo "             embedding model: $(get_env KINWARD_HONCHO_EMBEDDING_MODEL) @ $(get_env KINWARD_HONCHO_EMBEDDING_BASE_URL) (dim $(get_env KINWARD_HONCHO_EMBEDDING_DIMENSIONS))"
  fi
fi
if [[ "${WITH_LLM_WIKI}" == yes ]]; then
  echo "  LLM-Wiki:  http://localhost:$(get_env KINWARD_LLM_WIKI_PORT 3050)"
fi
if [[ "${WITH_HA}" == yes ]]; then
  echo "  HA (dev):  http://localhost:$(get_env KINWARD_HA_PORT 8123)"
fi
echo
