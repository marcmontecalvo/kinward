from __future__ import annotations

from datetime import timedelta

DOMAIN = "kinward"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"

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

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)
REQUEST_TIMEOUT_SECONDS = 10

CONTRACT_VERSION = "v1"
