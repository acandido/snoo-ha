"""The Snoo Premium integration."""
from __future__ import annotations

import asyncio
import logging

from python_snoo.exceptions import InvalidSnooAuth, SnooAuthException, SnooDeviceError
from python_snoo.snoo import Snoo

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SnooSettingsAPI
from .coordinator import SnooConfigEntry, SnooCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SnooConfigEntry) -> bool:
    """Set up Snoo Premium from a config entry."""
    session = async_get_clientsession(hass)
    snoo = Snoo(
        email=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        clientsession=session,
    )
    try:
        await snoo.authorize()
    except (SnooAuthException, InvalidSnooAuth) as ex:
        raise ConfigEntryNotReady from ex

    try:
        devices = await snoo.get_devices()
    except SnooDeviceError as ex:
        raise ConfigEntryNotReady from ex

    # Get baby IDs for settings API
    baby_id = None
    try:
        babies = await snoo.get_babies()
        if babies:
            baby_id = babies[0]._id
    except Exception:
        _LOGGER.warning("Could not fetch baby data; premium settings will be unavailable")

    settings_api = SnooSettingsAPI(session)
    coordinators: dict[str, SnooCoordinator] = {}
    tasks = []
    for device in devices:
        coordinator = SnooCoordinator(
            hass, entry, device, snoo, settings_api, baby_id
        )
        coordinators[device.serialNumber] = coordinator
        tasks.append(coordinator.setup())
    await asyncio.gather(*tasks)

    entry.runtime_data = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SnooConfigEntry) -> bool:
    """Unload a config entry."""
    disconnects = await asyncio.gather(
        *(
            coordinator.snoo.disconnect()
            for coordinator in entry.runtime_data.values()
        ),
        return_exceptions=True,
    )
    for disconnect in disconnects:
        if isinstance(disconnect, Exception):
            _LOGGER.warning("Failed to disconnect: %s", disconnect)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
