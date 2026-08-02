"""Sensor platform for the i-ON40 Alarm Panel."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import Ion40Coordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Ion40Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            Ion40DisplaySensor(coordinator, entry),
            Ion40AlarmStatusSensor(coordinator, entry),
        ]
    )


class Ion40EntityBase(CoordinatorEntity[Ion40Coordinator]):
    """Shared device info for all entities from this integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Ion40Coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
        )


class Ion40DisplaySensor(Ion40EntityBase, SensorEntity):
    """Shows the current keypad display text."""

    _attr_name = "Display"
    _attr_icon = "mdi:television-guide"

    def __init__(self, coordinator: Ion40Coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_display"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None:
            return None
        # Truncate to HA's 255-char state limit; full text is in attributes.
        return self.coordinator.data.display_text[:255]

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return {"lines": self.coordinator.data.lines}


class Ion40AlarmStatusSensor(Ion40EntityBase, SensorEntity):
    """Shows the overall alarm status derived from the nav key colour."""

    _attr_name = "Alarm Status"
    _attr_icon = "mdi:shield-home"
    _attr_device_class = "enum"
    _attr_options = ["ok", "alarm", "unknown"]

    def __init__(self, coordinator: Ion40Coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_alarm_status"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.alarm_status

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return {
            "nav_color": self.coordinator.data.nav_color,
            "led_bitmask": self.coordinator.data.led_bitmask,
        }
