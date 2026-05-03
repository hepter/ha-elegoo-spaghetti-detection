"""Config flow for Elegoo spaghetti detection."""

from __future__ import annotations

from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify
import voluptuous as vol

from .const import (
    CONF_ACTIVE_PRINT_STATES,
    CONF_CAMERA,
    CONF_CHAMBER_LIGHT,
    CONF_COOLDOWN_SECONDS,
    CONF_DETECTION_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_HOME_ASSISTANT_HOST,
    CONF_INSTANCE_ID,
    CONF_LIGHT_CONTROL_MODE,
    CONF_LIGHT_SETTLE_SECONDS,
    CONF_OBICO_AUTH_TOKEN,
    CONF_OBICO_HOST,
    CONF_PRINT_STATUS_SENSOR,
    CONF_RUN_WITHOUT_PRINTING,
    CONF_SENSITIVITY,
    CONF_SNAPSHOT_URL,
    CONF_WARNING_THRESHOLD,
    DEFAULT_ACTIVE_PRINT_STATES,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_DETECTION_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_HOME_ASSISTANT_HOST,
    DEFAULT_INSTANCE_ID,
    DEFAULT_LIGHT_CONTROL_MODE,
    DEFAULT_LIGHT_SETTLE_SECONDS,
    DEFAULT_NAME,
    DEFAULT_OBICO_AUTH_TOKEN,
    DEFAULT_OBICO_HOST,
    DEFAULT_SENSITIVITY,
    DEFAULT_WARNING_THRESHOLD,
    DOMAIN,
    LIGHT_CONTROL_LEAVE_ON,
    LIGHT_CONTROL_OFF,
    LIGHT_CONTROL_RESTORE,
)


OPTIONAL_ENTITY_FIELDS: tuple[tuple[str, str | list[str]], ...] = (
    (CONF_PRINT_STATUS_SENSOR, ["sensor", "binary_sensor"]),
    (CONF_CHAMBER_LIGHT, "light"),
)


def _entry_values(entry: ConfigEntry) -> dict[str, Any]:
    """Return config entry data with options overriding editable settings."""
    return {**entry.data, **entry.options}


def _default_value(defaults: dict[str, Any], key: str, fallback: Any) -> Any:
    """Return a form default without leaking None into selectors."""
    value = defaults.get(key)
    return fallback if value is None else value


def _optional_marker(key: str, defaults: dict[str, Any]) -> vol.Optional:
    """Return an optional voluptuous marker with an existing default if present."""
    if defaults.get(key):
        return vol.Optional(key, default=defaults[key])
    return vol.Optional(key)


def _light_control_mode(defaults: dict[str, Any]) -> str:
    """Return the default light-control mode for setup/options forms."""
    mode = defaults.get(CONF_LIGHT_CONTROL_MODE)
    if mode in {LIGHT_CONTROL_OFF, LIGHT_CONTROL_LEAVE_ON, LIGHT_CONTROL_RESTORE}:
        return mode
    return DEFAULT_LIGHT_CONTROL_MODE


def _schema(
    defaults: dict[str, Any] | None = None,
    *,
    include_identity: bool,
) -> vol.Schema:
    """Return detector setup/options schema."""
    defaults = defaults or {}
    data_schema: dict[Any, Any] = {}

    if include_identity:
        data_schema[
            vol.Required(
                CONF_NAME,
                default=_default_value(defaults, CONF_NAME, DEFAULT_NAME),
            )
        ] = str
        data_schema[
            vol.Required(
                CONF_INSTANCE_ID,
                default=_default_value(
                    defaults,
                    CONF_INSTANCE_ID,
                    DEFAULT_INSTANCE_ID,
                ),
            )
        ] = str

    data_schema[
        vol.Required(
            CONF_HOME_ASSISTANT_HOST,
            default=_default_value(
                defaults,
                CONF_HOME_ASSISTANT_HOST,
                DEFAULT_HOME_ASSISTANT_HOST,
            ),
        )
    ] = str
    data_schema[
        vol.Required(
            CONF_OBICO_HOST,
            default=_default_value(defaults, CONF_OBICO_HOST, DEFAULT_OBICO_HOST),
        )
    ] = str
    data_schema[
        vol.Required(
            CONF_OBICO_AUTH_TOKEN,
            default=_default_value(
                defaults,
                CONF_OBICO_AUTH_TOKEN,
                DEFAULT_OBICO_AUTH_TOKEN,
            ),
        )
    ] = str

    camera_marker = (
        vol.Required(CONF_CAMERA, default=defaults[CONF_CAMERA])
        if defaults.get(CONF_CAMERA)
        else vol.Required(CONF_CAMERA)
    )
    data_schema[camera_marker] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="camera")
    )

    data_schema[
        vol.Optional(
            CONF_SNAPSHOT_URL,
            default=_default_value(defaults, CONF_SNAPSHOT_URL, ""),
        )
    ] = str

    for key, domain in OPTIONAL_ENTITY_FIELDS:
        data_schema[_optional_marker(key, defaults)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=domain)
        )

    data_schema[
        vol.Required(
            CONF_ACTIVE_PRINT_STATES,
            default=_default_value(
                defaults,
                CONF_ACTIVE_PRINT_STATES,
                DEFAULT_ACTIVE_PRINT_STATES,
            ),
        )
    ] = str
    data_schema[
        vol.Required(
            CONF_LIGHT_CONTROL_MODE,
            default=_light_control_mode(defaults),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"label": "Do not control light", "value": LIGHT_CONTROL_OFF},
                {
                    "label": "Turn on before detection and leave on",
                    "value": LIGHT_CONTROL_LEAVE_ON,
                },
                {
                    "label": "Restore previous state after detection",
                    "value": LIGHT_CONTROL_RESTORE,
                },
            ],
            mode="dropdown",
        )
    )
    data_schema[
        vol.Required(
            CONF_LIGHT_SETTLE_SECONDS,
            default=_default_value(
                defaults,
                CONF_LIGHT_SETTLE_SECONDS,
                DEFAULT_LIGHT_SETTLE_SECONDS,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=30,
            step=1,
            mode="box",
            unit_of_measurement="s",
        )
    )
    data_schema[
        vol.Required(
            CONF_RUN_WITHOUT_PRINTING,
            default=_default_value(defaults, CONF_RUN_WITHOUT_PRINTING, False),
        )
    ] = selector.BooleanSelector()
    data_schema[
        vol.Required(
            CONF_DETECTION_INTERVAL,
            default=_default_value(
                defaults,
                CONF_DETECTION_INTERVAL,
                DEFAULT_DETECTION_INTERVAL,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=3600,
            step=5,
            mode="box",
            unit_of_measurement="s",
        )
    )
    data_schema[
        vol.Required(
            CONF_SENSITIVITY,
            default=_default_value(defaults, CONF_SENSITIVITY, DEFAULT_SENSITIVITY),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"label": "High sensitivity", "value": "high"},
                {"label": "Normal sensitivity", "value": "normal"},
                {"label": "Low sensitivity", "value": "low"},
                {"label": "Custom thresholds", "value": "custom"},
            ],
            mode="dropdown",
        )
    )
    data_schema[
        vol.Required(
            CONF_WARNING_THRESHOLD,
            default=_default_value(
                defaults,
                CONF_WARNING_THRESHOLD,
                DEFAULT_WARNING_THRESHOLD,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode="box")
    )
    data_schema[
        vol.Required(
            CONF_FAILURE_THRESHOLD,
            default=_default_value(
                defaults,
                CONF_FAILURE_THRESHOLD,
                DEFAULT_FAILURE_THRESHOLD,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode="box")
    )
    data_schema[
        vol.Required(
            CONF_COOLDOWN_SECONDS,
            default=_default_value(
                defaults,
                CONF_COOLDOWN_SECONDS,
                DEFAULT_COOLDOWN_SECONDS,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=3600,
            step=5,
            mode="box",
            unit_of_measurement="s",
        )
    )

    return vol.Schema(data_schema)


def _build_image_url(
    hass,
    data: dict[str, Any],
) -> str | None:
    """Build the image URL that the ML server will fetch during checks."""
    if snapshot_url := data.get(CONF_SNAPSHOT_URL):
        return snapshot_url

    state = hass.states.get(data[CONF_CAMERA])
    if state is None:
        return None
    entity_picture = state.attributes.get("entity_picture")
    if not entity_picture:
        return None
    return f"{data[CONF_HOME_ASSISTANT_HOST].rstrip('/')}{entity_picture}"


def _validate_thresholds(data: dict[str, Any]) -> dict[str, str]:
    """Validate threshold fields."""
    if float(data[CONF_WARNING_THRESHOLD]) > float(data[CONF_FAILURE_THRESHOLD]):
        return {CONF_WARNING_THRESHOLD: "warning_above_failure"}
    return {}


def _camera_in_use(
    entries: list[ConfigEntry],
    camera: str,
    *,
    exclude_entry_id: str | None = None,
) -> bool:
    """Return whether a camera is already used by a detector."""
    return any(
        entry.entry_id != exclude_entry_id
        and _entry_values(entry).get(CONF_CAMERA) == camera
        for entry in entries
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elegoo spaghetti detection."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure one detector target."""
        errors: dict[str, str] = {}
        form_defaults = self._defaults_from_existing_entry()

        if user_input is not None:
            data = dict(user_input)
            data[CONF_INSTANCE_ID] = slugify(data[CONF_INSTANCE_ID])
            errors.update(_validate_thresholds(data))

            if not data[CONF_INSTANCE_ID]:
                errors[CONF_INSTANCE_ID] = "invalid_instance_id"
            elif self._instance_id_exists(data[CONF_INSTANCE_ID]):
                errors[CONF_INSTANCE_ID] = "instance_id_exists"
            elif not errors:
                await self.async_set_unique_id(data[CONF_CAMERA])
                self._abort_if_unique_id_configured()

            if not errors:
                errors.update(await self._async_validate_backend(data))

            if not errors:
                name = data.pop(CONF_NAME)
                return self.async_create_entry(title=name, data=data)

            form_defaults = {**form_defaults, **data}

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(form_defaults, include_identity=True),
            errors=errors,
        )

    def _defaults_from_existing_entry(self) -> dict[str, Any]:
        """Use the first existing detector to reduce repeated server entry."""
        for entry in self._async_current_entries():
            values = _entry_values(entry)
            defaults = {
                CONF_HOME_ASSISTANT_HOST: values.get(CONF_HOME_ASSISTANT_HOST),
                CONF_OBICO_HOST: values.get(CONF_OBICO_HOST),
                CONF_OBICO_AUTH_TOKEN: values.get(CONF_OBICO_AUTH_TOKEN),
                CONF_DETECTION_INTERVAL: values.get(CONF_DETECTION_INTERVAL),
                CONF_LIGHT_CONTROL_MODE: values.get(CONF_LIGHT_CONTROL_MODE),
                CONF_LIGHT_SETTLE_SECONDS: values.get(CONF_LIGHT_SETTLE_SECONDS),
                CONF_SENSITIVITY: values.get(CONF_SENSITIVITY),
                CONF_WARNING_THRESHOLD: values.get(CONF_WARNING_THRESHOLD),
                CONF_FAILURE_THRESHOLD: values.get(CONF_FAILURE_THRESHOLD),
                CONF_COOLDOWN_SECONDS: values.get(CONF_COOLDOWN_SECONDS),
            }
            return {key: value for key, value in defaults.items() if value is not None}
        return {CONF_HOME_ASSISTANT_HOST: self._home_assistant_url_default()}

    def _home_assistant_url_default(self) -> str:
        """Return the best available HA URL for the ML server to fetch images."""
        return (
            getattr(self.hass.config, "internal_url", None)
            or getattr(self.hass.config, "external_url", None)
            or DEFAULT_HOME_ASSISTANT_HOST
        )

    def _instance_id_exists(self, instance_id: str) -> bool:
        """Return whether an entity prefix is already used."""
        return any(
            entry.data.get(CONF_INSTANCE_ID) == instance_id
            for entry in self._async_current_entries()
        )

    def _camera_exists(self, camera: str) -> bool:
        """Return whether a camera is already used by another detector."""
        return _camera_in_use(self._async_current_entries(), camera)

    async def _async_validate_backend(self, data: dict[str, Any]) -> dict[str, str]:
        """Validate ML health and whether it can fetch the configured image."""
        return await _async_validate_backend(self.hass, data)


class OptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle detector options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage detector options."""
        errors: dict[str, str] = {}
        defaults = _entry_values(self.config_entry)

        if user_input is not None:
            data = dict(user_input)
            errors.update(_validate_thresholds(data))

            if _camera_in_use(
                self.hass.config_entries.async_entries(DOMAIN),
                data[CONF_CAMERA],
                exclude_entry_id=self.config_entry.entry_id,
            ):
                errors[CONF_CAMERA] = "already_configured"

            if not errors:
                errors.update(await _async_validate_backend(self.hass, data))

            if not errors:
                return self.async_create_entry(data=data)

            defaults = {**defaults, **data}

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults, include_identity=False),
            errors=errors,
        )


async def _async_validate_backend(hass, data: dict[str, Any]) -> dict[str, str]:
    """Return form errors for backend/camera connectivity problems."""
    image_url = _build_image_url(hass, data)
    if not image_url:
        return {CONF_CAMERA: "camera_image_unavailable"}

    session = async_get_clientsession(hass)
    obico_host = data[CONF_OBICO_HOST].rstrip("/")
    token = data[CONF_OBICO_AUTH_TOKEN]
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with session.get(
            f"{obico_host}/hc/",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status >= 400:
                return {CONF_OBICO_HOST: "ml_health_failed"}
    except (aiohttp.ClientError, TimeoutError):
        return {CONF_OBICO_HOST: "ml_health_failed"}

    try:
        async with session.get(
            f"{obico_host}/debug/image",
            params={"img": image_url},
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            if response.status == 401:
                return {CONF_OBICO_AUTH_TOKEN: "ml_auth_failed"}
            if response.status >= 400:
                return {CONF_CAMERA: "ml_image_fetch_failed"}
    except (aiohttp.ClientError, TimeoutError):
        return {CONF_CAMERA: "ml_image_fetch_failed"}

    return {}
