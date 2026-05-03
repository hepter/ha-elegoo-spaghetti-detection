"""Home Assistant integration for Elegoo spaghetti detection."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CONFIG_ENTRY,
    CONF_DETECTOR,
    CONF_FORCE,
    CONF_IMAGE_URL,
    CONF_OBICO_AUTH_TOKEN,
    CONF_OBICO_HOST,
    DOMAIN,
    PLATFORMS,
    REQUIRED_CONFIG_KEYS,
    RUNTIME_ML_LOCK,
    RUNTIME_BY_DETECTOR,
    RUNTIME_DATA,
    SERVICE_PREDICT,
    SERVICE_RESET_STATE,
    SERVICE_RUN_DETECTION,
)
from .runtime import SpaghettiDetectorRuntime

LOGGER = logging.getLogger(__package__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

PREDICT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OBICO_HOST): str,
        vol.Required(CONF_OBICO_AUTH_TOKEN): str,
        vol.Required(CONF_IMAGE_URL): str,
    }
)

DETECTOR_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFIG_ENTRY): str,
        vol.Optional(CONF_DETECTOR): str,
        vol.Optional(CONF_FORCE, default=True): bool,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up global services for Elegoo spaghetti detection."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(RUNTIME_DATA, {})
    hass.data[DOMAIN].setdefault(RUNTIME_BY_DETECTOR, {})
    hass.data[DOMAIN].setdefault(RUNTIME_ML_LOCK, asyncio.Lock())

    async def predict_handler(call: ServiceCall) -> ServiceResponse:
        """Run the Obico ML model for a raw image URL."""
        result = await _async_predict_raw(
            hass,
            call.data[CONF_OBICO_HOST],
            call.data[CONF_OBICO_AUTH_TOKEN],
            call.data[CONF_IMAGE_URL],
        )
        return {"result": result}

    async def run_detection_handler(call: ServiceCall) -> ServiceResponse:
        """Run one detection against the configured detector."""
        runtime = _runtime_from_call(hass, call)
        return await runtime.async_run_detection(manual=bool(call.data[CONF_FORCE]))

    async def reset_handler(call: ServiceCall) -> None:
        """Reset detector state."""
        runtime = _runtime_from_call(hass, call)
        runtime.reset()

    hass.services.async_register(
        DOMAIN,
        SERVICE_PREDICT,
        predict_handler,
        schema=PREDICT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_DETECTION,
        run_detection_handler,
        schema=DETECTOR_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_STATE,
        reset_handler,
        schema=DETECTOR_SERVICE_SCHEMA,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one spaghetti detector."""
    missing = sorted(
        key
        for key in REQUIRED_CONFIG_KEYS
        if key not in entry.data and key not in entry.options
    )
    if missing:
        LOGGER.error(
            "Config entry %s is incomplete and must be removed and recreated. Missing: %s",
            entry.title,
            ", ".join(missing),
        )
        return False

    runtime = SpaghettiDetectorRuntime(hass, entry)
    hass.data[DOMAIN][RUNTIME_DATA][entry.entry_id] = runtime
    hass.data[DOMAIN][RUNTIME_BY_DETECTOR][runtime.detector_id] = runtime
    await runtime.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one spaghetti detector."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    runtime = hass.data[DOMAIN][RUNTIME_DATA].pop(entry.entry_id, None)
    if runtime is not None:
        hass.data[DOMAIN][RUNTIME_BY_DETECTOR].pop(runtime.detector_id, None)
        await runtime.async_unload()
    return unload_ok


async def _async_predict_raw(
    hass: HomeAssistant,
    obico_host: str,
    obico_auth_token: str,
    image_url: str,
) -> dict[str, Any]:
    """Call Obico ML directly."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"{obico_host.rstrip('/')}/p/",
            params={"img": image_url},
            headers={"Authorization": f"Bearer {obico_auth_token}"},
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            response.raise_for_status()
            result = await response.json()
            if not isinstance(result, dict):
                return {"detections": []}
            return result
    except (aiohttp.ClientError, TimeoutError) as err:
        LOGGER.warning("Obico ML request failed: %s", err)
        return {"detections": []}


def _runtime_from_call(
    hass: HomeAssistant,
    call: ServiceCall,
) -> SpaghettiDetectorRuntime:
    """Resolve a runtime from a service call."""
    runtime: SpaghettiDetectorRuntime | None = None
    if config_entry_id := call.data.get(CONF_CONFIG_ENTRY):
        runtime = hass.data[DOMAIN][RUNTIME_DATA].get(config_entry_id)
    elif detector := call.data.get(CONF_DETECTOR):
        runtime = hass.data[DOMAIN][RUNTIME_BY_DETECTOR].get(detector)

    if runtime is None:
        raise HomeAssistantError("Unknown Elegoo spaghetti detector")
    return runtime
