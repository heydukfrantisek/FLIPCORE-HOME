"""Kilo AI integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_MODEL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import KiloGatewayClient, KiloGatewayError
from .const import CONF_BASE_URL, CONF_CONTEXT, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR]

ATTR_PROMPT = "prompt"
ATTR_CONTEXT = "context"
ATTR_MAX_TOKENS = "max_tokens"
ATTR_TEMPERATURE = "temperature"

SERVICE_ASK = "ask"
SERVICE_LIST_MODELS = "list_models"

ASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_CONTEXT): cv.string,
        vol.Optional(ATTR_MAX_TOKENS): cv.positive_int,
        vol.Optional(ATTR_TEMPERATURE): vol.Coerce(float),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = KiloGatewayClient(
        hass,
        base_url=entry.data[CONF_BASE_URL],
        api_key=entry.data[CONF_API_KEY],
        model=entry.data[CONF_MODEL],
    )

    try:
        await client.async_validate()
    except KiloGatewayError as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        _async_remove_services(hass)
    return unloaded


def _async_register_services(hass: HomeAssistant) -> None:
    async def handle_ask(call: ServiceCall) -> dict[str, Any]:
        client: KiloGatewayClient = _client_from_call(hass, call)
        return await client.async_ask(
            prompt=call.data[ATTR_PROMPT],
            context=call.data.get(ATTR_CONTEXT),
            max_tokens=call.data.get(ATTR_MAX_TOKENS),
            temperature=call.data.get(ATTR_TEMPERATURE),
        )

    async def handle_list_models(call: ServiceCall) -> dict[str, Any]:
        client: KiloGatewayClient = _client_from_call(hass, call)
        return {"models": await client.async_list_models()}

    hass.services.async_register(
        DOMAIN,
        SERVICE_ASK,
        handle_ask,
        schema=ASK_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_MODELS,
        handle_list_models,
        supports_response=SupportsResponse.ONLY,
    )


def _async_remove_services(hass: HomeAssistant) -> None:
    for service in (SERVICE_ASK, SERVICE_LIST_MODELS):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)


def _client_from_call(hass: HomeAssistant, call: ServiceCall) -> KiloGatewayClient:
    entry_id = call.data.get(CONF_CONTEXT)
    if entry_id is None:
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise KiloGatewayError("Kilo AI is not configured")
        return entries[0].runtime_data
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        raise KiloGatewayError(f"Unknown Kilo AI config entry: {entry_id}")
    return entry.runtime_data
