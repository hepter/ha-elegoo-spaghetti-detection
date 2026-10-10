"""Switches for Elegoo spaghetti detection."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INSTANCE_ID, DOMAIN, RUNTIME_DATA
from .entity import SpaghettiDetectorEntity
from .runtime import SpaghettiDetectorRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up switches."""
    runtime = hass.data[DOMAIN][RUNTIME_DATA][entry.entry_id]
    async_add_entities([DetectorEnabledSwitch(entry, runtime)])


class DetectorEnabledSwitch(SpaghettiDetectorEntity, RestoreEntity, SwitchEntity):
    """Switch to pause and resume scheduled detection.

    Turning the switch off leaves the detector configured but stops the
    scheduled checks, so no snapshots are taken and no ML requests are sent.
    Manual actions (the Test button and the run_detection service with
    force enabled) keep working.
    """

    _attr_name = "Scheduled detection"

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: SpaghettiDetectorRuntime,
    ) -> None:
        super().__init__(entry, runtime, "detection_enabled")
        self.entity_id = f"switch.{entry.data[CONF_INSTANCE_ID]}_detection_enabled"

    async def async_added_to_hass(self) -> None:
        """Restore the paused state after a Home Assistant restart."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.runtime.set_enabled(last_state.state == STATE_ON)

    @property
    def icon(self) -> str:
        """Return an icon that reflects the current state."""
        return "mdi:motion-play-outline" if self.is_on else "mdi:motion-pause-outline"

    @property
    def is_on(self) -> bool:
        """Return whether scheduled detection is enabled."""
        return self.runtime.enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Resume scheduled detection."""
        self.runtime.set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Pause scheduled detection."""
        self.runtime.set_enabled(False)
