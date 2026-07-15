from __future__ import annotations

from datetime import timedelta

DOMAIN = "kinward"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)
REQUEST_TIMEOUT_SECONDS = 10

CONTRACT_VERSION = "v1"
