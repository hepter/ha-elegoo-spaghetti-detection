"""Buttons for Elegoo spaghetti detection."""

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_INSTANCE_ID, DOMAIN, RUNTIME_DATA
from .entity import SpaghettiDetectorEntity
from .runtime import SpaghettiDetectorRuntime


@dataclass(frozen=True, kw_only=True)
class DetectorButtonDescription(ButtonEntityDescription):
    """Detector button description."""

    press_fn: Callable[[SpaghettiDetectorRuntime], Awaitable[None]]


async def _run_detection(runtime: SpaghettiDetectorRuntime) -> None:
    """Run one manual detection."""
    await runtime.async_run_detection(manual=True)


async def _reset_state(runtime: SpaghettiDetectorRuntime) -> None:
    """Reset detection state."""
    runtime.reset()


BUTTONS: tuple[DetectorButtonDescription, ...] = (
    DetectorButtonDescription(
        key="test_spaghetti_detection",
        name="Test Spaghetti Detection",
        icon="mdi:camera-iris",
        press_fn=_run_detection,
    ),
    DetectorButtonDescription(
        key="reset_detection_state",
        name="Reset Detection State",
        icon="mdi:restart",
        press_fn=_reset_state,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up buttons."""
    runtime = hass.data[DOMAIN][RUNTIME_DATA][entry.entry_id]
    async_add_entities(
        DetectorButton(entry, runtime, description) for description in BUTTONS
    )


class DetectorButton(SpaghettiDetectorEntity, ButtonEntity):
    """Detector action button."""

    entity_description: DetectorButtonDescription

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: SpaghettiDetectorRuntime,
        description: DetectorButtonDescription,
    ) -> None:
        super().__init__(entry, runtime, description.key)
        self.entity_description = description
        self.entity_id = f"button.{entry.data[CONF_INSTANCE_ID]}_{description.key}"

    async def async_press(self) -> None:
        """Handle button press."""
        await self.entity_description.press_fn(self.runtime)
