"""Sensor platform for the Kilo AI integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import KiloGatewayClient
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: KiloGatewayClient = entry.runtime_data
    async_add_entities([KiloAIModelSensor(client, entry)])


class KiloAIModelSensor(SensorEntity):
    """Exposes the active Kilo AI model."""

    _attr_should_poll = False
    _attr_icon = "mdi:brain"

    def __init__(self, client: KiloGatewayClient, entry: ConfigEntry) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_model"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Kilo AI",
            "manufacturer": "Kilo Code",
        }

    @property
    def native_value(self) -> str:
        return self._client.model

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "configured_model": self._client.model,
            "base_url": self._client.base_url,
        }
