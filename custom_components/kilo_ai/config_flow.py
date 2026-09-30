"""Config flow for the Kilo AI integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_MODEL
from homeassistant.core import callback

from .api import KiloGatewayClient, KiloGatewayError
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DEFAULT_MODEL, DOMAIN

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_MODEL, default=DEFAULT_MODEL): str,
    }
)


async def _async_fetch_models(
    hass: Any, base_url: str, api_key: str
) -> tuple[list[str] | None, str | None]:
    client = KiloGatewayClient(hass, base_url=base_url, api_key=api_key)
    try:
        return await client.async_list_models(), None
    except KiloGatewayError as err:
        return None, str(err)


class KiloAIFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle the Kilo AI config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        suggested = user_input or {}

        if user_input is not None:
            models, error = await _async_fetch_models(
                self.hass, user_input[CONF_BASE_URL], user_input[CONF_API_KEY]
            )
            if error is None:
                return self.async_create_entry(
                    title=f"Kilo AI ({user_input[CONF_MODEL]})",
                    data={
                        CONF_BASE_URL: user_input[CONF_BASE_URL].rstrip("/"),
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_MODEL: user_input[CONF_MODEL],
                    },
                    options={"models": models},
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, suggested),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        errors: dict[str, str] = {}

        if user_input is not None:
            models, error = await _async_fetch_models(
                self.hass, user_input[CONF_BASE_URL], user_input[CONF_API_KEY]
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        CONF_BASE_URL: user_input[CONF_BASE_URL].rstrip("/"),
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_MODEL: user_input[CONF_MODEL],
                    },
                    options={"models": models},
                )
            errors["base"] = "cannot_connect"

        suggested = user_input or dict(entry.data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, suggested),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> KiloAIOptionsFlowHandler:
        return KiloAIOptionsFlowHandler()


class KiloAIOptionsFlowHandler(OptionsFlow):
    """Handle the Kilo AI options (model selection)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        models: list[str] = list(self.config_entry.options.get("models") or [])
        current = self.config_entry.data[CONF_MODEL]
        if not models:
            models = [current]

        if user_input is not None:
            return self.async_create_entry(
                title="", data={"models": models, CONF_MODEL: user_input[CONF_MODEL]}
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_MODEL, default=current): vol.In(models)}
            ),
        )
