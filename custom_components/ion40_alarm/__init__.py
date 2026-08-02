"""The i-ON40 Alarm Panel integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PanelError, Ion40PanelClient
from .const import (
    ATTR_DELAY,
    ATTR_KEY,
    ATTR_KEYS,
    CONF_SCAN_INTERVAL,
    CONF_UID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    PLATFORMS,
    SERVICE_SEND_KEY,
    SERVICE_SEND_KEYS,
    VALID_KEYS,
)
from .coordinator import Ion40Coordinator

_LOGGER = logging.getLogger(__name__)

SEND_KEY_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required(ATTR_KEY): vol.In(VALID_KEYS),
    }
)

SEND_KEYS_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required(ATTR_KEYS): [vol.In(VALID_KEYS)],
        vol.Optional(ATTR_DELAY, default=0.3): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=5)
        ),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    session = async_get_clientsession(hass)
    client = Ion40PanelClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_UID],
    )

    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = Ion40Coordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=entry.title,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in (SERVICE_SEND_KEY, SERVICE_SEND_KEYS):
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
    return unload_ok


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> Ion40Coordinator:
    coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
    if coordinator is None:
        raise HomeAssistantError(f"Unknown ion40_alarm entry_id: {entry_id}")
    return coordinator


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the send_key / send_keys services once."""

    if hass.services.has_service(DOMAIN, SERVICE_SEND_KEY):
        return

    async def handle_send_key(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        try:
            state = await coordinator.client.async_send_key(call.data[ATTR_KEY])
        except PanelError as err:
            raise HomeAssistantError(str(err)) from err
        coordinator.async_set_updated_data(state)

    async def handle_send_keys(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        try:
            state = await coordinator.client.async_send_keys(
                call.data[ATTR_KEYS], call.data.get(ATTR_DELAY, 0.3)
            )
        except PanelError as err:
            raise HomeAssistantError(str(err)) from err
        if state is not None:
            coordinator.async_set_updated_data(state)

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_KEY, handle_send_key, schema=SEND_KEY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_KEYS, handle_send_keys, schema=SEND_KEYS_SCHEMA
    )
