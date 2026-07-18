#!/usr/bin/env bash
# Static validation for the optional Honcho/LLM-Wiki compose fragments.
#
# Does not pull or start anything - just proves the fragments parse, merge
# cleanly with compose.yaml, and expose the expected services only behind
# their profiles.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
readonly COMPOSE=(docker compose --env-file /dev/null --project-directory "${ROOT}" \
  -f "${ROOT}/compose.yaml" -f "${ROOT}/compose.honcho.yaml" -f "${ROOT}/compose.llmwiki.yaml")

fail() {
  printf 'optional-peers smoke: FAIL: %s\n' "$*" >&2
  exit 1
}

command -v docker >/dev/null || fail "docker is required"

export KINWARD_HONCHO_POSTGRES_PASSWORD=placeholder
export KINWARD_LLM_WIKI_UI_PASSWORD=placeholder

default_services="$("${COMPOSE[@]}" config --services | sort)"
for forbidden in honcho-db honcho-redis honcho-api honcho-deriver honcho-configure-embeddings llm-wiki; do
  if grep -qx "${forbidden}" <<<"${default_services}"; then
    fail "${forbidden} appears without an active profile"
  fi
done

honcho_services="$("${COMPOSE[@]}" --profile honcho config --services | sort)"
for expected in honcho-db honcho-redis honcho-api honcho-deriver honcho-configure-embeddings; do
  grep -qx "${expected}" <<<"${honcho_services}" || fail "honcho profile is missing ${expected}"
done

wiki_services="$("${COMPOSE[@]}" --profile llm-wiki config --services | sort)"
grep -qx "llm-wiki" <<<"${wiki_services}" || fail "llm-wiki profile is missing the llm-wiki service"

printf 'optional-peers smoke: PASS (default inventory unaffected, honcho profile, llm-wiki profile)\n'
