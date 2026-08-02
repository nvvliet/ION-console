"""Coordinator that polls the alarm panel on a schedule."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PanelError, PanelState, Ion40PanelClient

_LOGGER = logging.getLogger(__name__)


class Ion40Coordinator(DataUpdateCoordinator[PanelState]):
    """Fetches PanelState from the client on an interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Ion40PanelClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="ion40_alarm",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> PanelState:
        try:
            return await self.client.async_get_state()
        except PanelError as err:
            raise UpdateFailed(str(err)) from err
