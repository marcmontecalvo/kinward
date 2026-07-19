from __future__ import annotations

from datetime import timedelta

DOMAIN = "kinward"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"
CONF_SETUP_AUTHORIZATION = "setup_authorization"

CONF_MODEL_PROVIDER = "model_provider"
CONF_MODEL_BASE_URL = "model_base_url"
CONF_MODEL_NAME = "model_name"
CONF_MODEL_API_KEY = "model_api_key"
CONF_MEMORY_BACKEND = "memory_backend"
CONF_HONCHO_URL = "honcho_url"
CONF_KNOWLEDGE_BACKEND = "knowledge_backend"
CONF_LLM_WIKI_URL = "llm_wiki_url"

MODEL_PROVIDERS = ["none", "openai", "openai-compatible", "anthropic"]
MEMORY_BACKENDS = ["none", "honcho"]
KNOWLEDGE_BACKENDS = ["none", "llm_wiki"]

CONF_MAX_ASSISTANTS_PER_PERSON = "max_assistants_per_person"
CONF_REQUIRE_ADMIN_APPROVAL_FOR_ASSISTANT_CREATION = "require_admin_approval_for_assistant_creation"

# 0 in the options-flow number selector means "no cap" - stored as `None` server-side.
NO_ASSISTANT_CAP = 0

# Epic 7 Story 7.3's CAPABILITY_SERVICE_ALLOWLIST keys (services/kinward/src/kinward/domain/
# tool_permission.py) - kept in sync manually since the options flow has no live schema fetch.
TOOL_POLICY_CAPABILITIES = [
    "control_lights",
    "control_switches",
    "manage_household_timers",
    "control_locks",
    "control_alarm_system",
]
TOOL_POLICY_VALUES = ["allow", "approval_required", "deny"]
TOOL_POLICY_DEFAULTS = {
    "control_lights": "allow",
    "control_switches": "allow",
    "manage_household_timers": "allow",
    "control_locks": "deny",
    "control_alarm_system": "deny",
}

CONF_RESOURCE_LABEL_ENTITY_ID = "resource_label_entity_id"
CONF_RESOURCE_LABEL_LABEL = "resource_label_label"

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)
REQUEST_TIMEOUT_SECONDS = 10

CONTRACT_VERSION = "v1"
