"""Coordinator for the Snoo Premium integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from python_snoo.containers import BabyData, SnooData, SnooDevice
from python_snoo.snoo import Snoo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SnooSettingsAPI

type SnooConfigEntry = ConfigEntry[dict[str, "SnooCoordinator"]]

_LOGGER = logging.getLogger(__name__)


class SnooCoordinator(DataUpdateCoordinator[SnooData]):
    """Coordinator that manages real-time Snoo state and premium settings."""

    config_entry: SnooConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SnooConfigEntry,
        device: SnooDevice,
        snoo: Snoo,
        settings_api: SnooSettingsAPI,
        baby_id: str | None = None,
    ) -> None:
        super().__init__(
            hass,
            name=device.name,
            config_entry=entry,
            logger=_LOGGER,
        )
        self.device_unique_id = device.serialNumber
        self.device = device
        self.snoo = snoo
        self.settings_api = settings_api
        self.baby_id = baby_id
        self.baby_settings: dict = {}
        self.session_duration_seconds: int = 0

    @property
    def token(self) -> str:
        """Get the current AWS ID token for API calls."""
        return self.snoo.tokens.aws_id

    async def setup(self) -> None:
        """Subscribe to MQTT updates and fetch initial settings."""
        self.snoo.start_subscribe(self.device, self._handle_update)
        await self.snoo.get_status(self.device)
        await self.refresh_settings()

    def _handle_update(self, data: SnooData) -> None:
        """Handle real-time MQTT state updates and track session duration."""
        if data.state_machine.is_active_session:
            self.session_duration_seconds = (
                data.state_machine.since_session_start_ms // 1000
            )
        else:
            self.session_duration_seconds = 0
        self.async_set_updated_data(data)

    async def refresh_settings(self) -> None:
        """Fetch the latest baby/premium settings from the API."""
        if not self.baby_id:
            return
        try:
            self.baby_settings = await self.settings_api.get_baby_settings(
                self.token, self.baby_id
            )
        except Exception:
            _LOGGER.debug("Failed to refresh baby settings", exc_info=True)

    async def update_setting(self, key: str, value) -> None:
        """Update a single baby setting and refresh."""
        if not self.baby_id:
            return
        await self.settings_api.update_baby_settings(
            self.token, self.baby_id, {key: value}
        )
        await self.refresh_settings()
        self.async_set_updated_data(self.data)
