"""Constants for the Kilo AI integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "kilo_ai"

CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "https://api.kilo.ai/api/gateway"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7

DEFAULT_TIMEOUT = 60
UPDATE_INTERVAL = timedelta(minutes=30)

ATTR_BASE_URL = CONF_BASE_URL
ATTR_API_KEY = "api_key"
ATTR_MODEL = "model"
