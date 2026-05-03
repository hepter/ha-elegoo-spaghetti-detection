"""Base entities for Elegoo spaghetti detection."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN
from .runtime import SpaghettiDetectorRuntime


class SpaghettiDetectorEntity(Entity):
    """Base entity for a detector runtime."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: SpaghettiDetectorRuntime,
        key: str,
    ) -> None:
        self.entry = entry
        self.runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Elegoo",
            model="Spaghetti detection",
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime updates."""
        self.async_on_remove(
            self.runtime.async_add_listener(self.async_write_ha_state)
        )
