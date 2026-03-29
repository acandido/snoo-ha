"""Direct API calls to Happiest Baby for premium settings."""
from __future__ import annotations

import logging

import aiohttp

from .const import BABY_API_BASE, SESSION_API_BASE

_LOGGER = logging.getLogger(__name__)


class SnooSettingsAPI:
    """Wrapper for Happiest Baby REST API settings that python-snoo doesn't support."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "authorization": f"Bearer {token}",
            "accept": "application/json",
            "content-type": "application/json",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.12.0",
        }

    async def get_baby_settings(self, token: str, baby_id: str) -> dict:
        """Get full baby data including settings."""
        url = f"{BABY_API_BASE}/{baby_id}"
        async with self._session.get(url, headers=self._headers(token)) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("settings", {})

    async def update_baby_settings(self, token: str, baby_id: str, settings: dict) -> dict:
        """Update baby settings via PUT to the baby endpoint.

        The Happiest Baby app sends a PUT with the full baby object including
        modified settings. We PATCH just the settings field.
        """
        url = f"{BABY_API_BASE}/{baby_id}"
        # First get current baby data
        async with self._session.get(url, headers=self._headers(token)) as resp:
            resp.raise_for_status()
            baby_data = await resp.json()

        # Merge new settings into existing
        current_settings = baby_data.get("settings", {})
        current_settings.update(settings)
        baby_data["settings"] = current_settings

        # PUT the full baby object back
        async with self._session.put(
            url, headers=self._headers(token), json=baby_data
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("settings", {})

    async def get_session_history(
        self, token: str, baby_id: str, start_time: str, end_time: str
    ) -> list[dict]:
        """Get Snoo sleep session history.

        Uses the sessions endpoint: /ss/v2/babies/{baby_id}/sessions
        start_time/end_time should be ISO format strings.
        """
        url = f"{SESSION_API_BASE}/{baby_id}/sessions"
        params = {
            "startTime": start_time,
            "endTime": end_time,
        }
        try:
            async with self._session.get(
                url, headers=self._headers(token), params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict):
                        return data.get("sessions", [])
                    return data if isinstance(data, list) else []
                _LOGGER.debug(
                    "Session history request returned %s", resp.status
                )
                return []
        except Exception:
            _LOGGER.debug("Failed to fetch session history", exc_info=True)
            return []
