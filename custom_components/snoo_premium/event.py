"""Event entities for the Snoo Premium integration."""
from __future__ import annotations

from python_snoo.containers import SnooData, SnooEvents

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SnooConfigEntry
from .entity import SnooDescriptionEntity

EVENT_DESCRIPTIONS: list[EventEntityDescription] = [
    EventEntityDescription(
        key="event",
        translation_key="event",
        event_types=[e.name.lower() for e in SnooEvents],
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SnooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        SnooEvent(coordinator, description)
        for coordinator in entry.runtime_data.values()
        for description in EVENT_DESCRIPTIONS
    )


class SnooEvent(SnooDescriptionEntity, EventEntity):
    @callback
    def _handle_coordinator_update(self) -> None:
        data: SnooData = self.coordinator.data
        if data is not None:
            self._trigger_event(
                data.event.name.lower(),
                {"state": data.state_machine.state.name},
            )
            self.async_write_ha_state()
