"""Sensors for Elegoo spaghetti detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_INSTANCE_ID, DOMAIN, RUNTIME_DATA
from .entity import SpaghettiDetectorEntity


@dataclass(frozen=True, kw_only=True)
class DetectorSensorDescription(SensorEntityDescription):
    """Detector sensor description."""

    value_fn: Any


SENSORS: tuple[DetectorSensorDescription, ...] = (
    DetectorSensorDescription(
        key="confidence",
        name="Confidence",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda runtime: round(runtime.confidence * 100, 1),
    ),
    DetectorSensorDescription(
        key="raw_score",
        name="Raw Score",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda runtime: round(runtime.raw_score, 4),
    ),
    DetectorSensorDescription(
        key="detections",
        name="Detection Count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda runtime: runtime.detection_count,
    ),
    DetectorSensorDescription(
        key="status",
        name="Status",
        value_fn=lambda runtime: runtime.status,
    ),
    DetectorSensorDescription(
        key="last_error",
        name="Last Error",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda runtime: runtime.last_error or "none",
    ),
    DetectorSensorDescription(
        key="last_run",
        name="Last Run",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda runtime: runtime.last_run,
    ),
    DetectorSensorDescription(
        key="next_run",
        name="Next Run",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda runtime: runtime.next_run,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up sensors."""
    runtime = hass.data[DOMAIN][RUNTIME_DATA][entry.entry_id]
    async_add_entities(
        DetectorSensor(entry, runtime, description) for description in SENSORS
    )


class DetectorSensor(SpaghettiDetectorEntity, SensorEntity):
    """Detector sensor."""

    entity_description: DetectorSensorDescription

    def __init__(
        self,
        entry: ConfigEntry,
        runtime,
        description: DetectorSensorDescription,
    ) -> None:
        super().__init__(entry, runtime, description.key)
        self.entity_description = description
        self.entity_id = f"sensor.{entry.data[CONF_INSTANCE_ID]}_{description.key}"

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.runtime)
