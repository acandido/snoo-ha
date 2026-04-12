"""Coordinator for the Snoo Premium integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from python_snoo.containers import SnooData, SnooDevice
from python_snoo.snoo import Snoo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SnooSettingsAPI

type SnooConfigEntry = ConfigEntry[dict[str, "SnooCoordinator"]]

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "snoo_premium_session"


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

        # Live session tracking
        self.session_duration_seconds: int = 0
        self._was_active: bool = False

        # Persistent session tracking — loaded from storage on setup
        self.session_start_time: datetime | None = None
        self.session_end_time: datetime | None = None
        self.last_session_duration_seconds: int = 0

        # HA file-based storage so values survive restarts
        self._store: Store = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}_{device.serialNumber}",
        )

    @property
    def token(self) -> str:
        """Get the current AWS ID token for API calls."""
        return self.snoo.tokens.aws_id

    async def setup(self) -> None:
        """Subscribe to MQTT updates and fetch initial settings."""
        await self._load_stored_session()
        self.snoo.start_subscribe(self.device, self._handle_update)
        await self.snoo.get_status(self.device)
        await self.refresh_settings()

    async def _load_stored_session(self) -> None:
        """Restore last session values from persistent storage."""
        stored = await self._store.async_load()
        if not stored:
            return
        self.last_session_duration_seconds = stored.get(
            "last_session_duration_seconds", 0
        )
        if ts := stored.get("session_start_time"):
            try:
                self.session_start_time = datetime.fromisoformat(ts)
            except ValueError:
                pass
        if ts := stored.get("session_end_time"):
            try:
                self.session_end_time = datetime.fromisoformat(ts)
            except ValueError:
                pass
        _LOGGER.debug("Restored session data from storage: %s", stored)

    async def _save_session_data(self) -> None:
        """Persist current session values to storage."""
        await self._store.async_save(
            {
                "last_session_duration_seconds": self.last_session_duration_seconds,
                "session_start_time": self.session_start_time.isoformat()
                if self.session_start_time
                else None,
                "session_end_time": self.session_end_time.isoformat()
                if self.session_end_time
                else None,
            }
        )

    def _handle_update(self, data: SnooData) -> None:
        """Handle real-time MQTT state updates and track session duration."""
        is_active = data.state_machine.is_active_session
        now = datetime.now(timezone.utc)

        if is_active:
            self.session_duration_seconds = (
                data.state_machine.since_session_start_ms // 1000
            )
            if not self._was_active:
                # New session started
                self.session_start_time = now
                self.session_end_time = None
                _LOGGER.debug("Snoo session started at %s", now.isoformat())
                self.hass.async_create_task(self._save_session_data())
        else:
            if self._was_active and self.session_duration_seconds > 0:
                # Session just ended — capture and persist
                self.last_session_duration_seconds = self.session_duration_seconds
                self.session_end_time = now
                _LOGGER.debug(
                    "Snoo session ended at %s (duration: %ds)",
                    now.isoformat(),
                    self.last_session_duration_seconds,
                )
                self.hass.async_create_task(self._save_session_data())
            self.session_duration_seconds = 0

        self._was_active = is_active
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
