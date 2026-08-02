"""Binary sensor platform: one per zone LED (A-D)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ZONES
from .coordinator import Ion40Coordinator
from .sensor import Ion40EntityBase


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Ion40Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [Ion40ZoneBinarySensor(coordinator, entry, zone) for zone in ZONES]
    )


class Ion40ZoneBinarySensor(Ion40EntityBase, BinarySensorEntity):
    """
    Represents one zone's LED state, decoded from the 2-bit field in
    the vkleds bitmask (bits 0-1 = zone A, 2-3 = zone B, 4-5 = C, 6-7 = D).

    NOTE: the exact meaning of the 4 possible 2-bit values (0-3) per zone
    was not specified. This entity treats any non-zero value as "on"
    (zone active/triggered/faulted) and exposes the raw 0-3 value as an
    attribute so you can refine the on/off logic once you've observed
    real values from your panel.
    """

    _attr_icon = "mdi:shield-alert"

    def __init__(
        self, coordinator: Ion40Coordinator, entry: ConfigEntry, zone: str
    ) -> None:
        super().__init__(coordinator, entry)
        self._zone = zone
        self._attr_name = f"Zone {zone}"
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone.lower()}"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.zones.get(self._zone)
        if value is None:
            return None
        return value != 0

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return {"raw_value": self.coordinator.data.zones.get(self._zone)}
