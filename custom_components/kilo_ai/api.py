"""Client for the Kilo AI Gateway (OpenAI-compatible API)."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are an assistant embedded in Home Assistant. Answer concisely and use "
    "metric units unless asked otherwise."
)


class KiloGatewayError(Exception):
    """Raised when the Kilo AI Gateway returns an error."""


class KiloGatewayClient:
    """Minimal async client for chat completions and model listing."""

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        api_key: str,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self._hass = hass
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def async_validate(self) -> None:
        """Verify the credentials by listing models."""
        await self.async_list_models()

    async def async_list_models(self) -> list[str]:
        session = async_get_clientsession(self._hass)
        url = f"{self._base_url}/models"
        try:
            async with session.get(
                url, headers=self._headers(), timeout=DEFAULT_TIMEOUT
            ) as response:
                if response.status != 200:
                    raise KiloGatewayError(
                        f"Model list failed ({response.status}): {await response.text()}"
                    )
                payload = await response.json()
        except aiohttp.ClientError as err:
            raise KiloGatewayError(f"Cannot reach Kilo AI Gateway: {err}") from err

        return [item["id"] for item in payload.get("data", []) if "id" in item]

    async def async_ask(
        self,
        prompt: str,
        context: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the response payload."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}
        ]
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE if temperature is None else temperature,
            "stream": False,
        }

        session = async_get_clientsession(self._hass)
        url = f"{self._base_url}/chat/completions"
        try:
            async with session.post(
                url, headers=self._headers(), json=body, timeout=DEFAULT_TIMEOUT
            ) as response:
                if response.status != 200:
                    raise KiloGatewayError(
                        f"Chat completion failed ({response.status}): {await response.text()}"
                    )
                payload = await response.json()
        except aiohttp.ClientError as err:
            raise KiloGatewayError(f"Cannot reach Kilo AI Gateway: {err}") from err

        return _parse_completion(payload)


def _parse_completion(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices") or []
    if not choices:
        raise KiloGatewayError("Kilo AI Gateway returned no choices")

    message = choices[0].get("message") or {}
    usage = payload.get("usage") or {}
    return {
        "response": message.get("content") or "",
        "model": payload.get("model") or DEFAULT_MODEL,
        "finish_reason": choices[0].get("finish_reason"),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
    }


__all__ = ["KiloGatewayClient", "KiloGatewayError"]
