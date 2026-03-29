"""Sensors for the Snoo Premium integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from python_snoo.containers import SnooData, SnooStates

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    StateType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SnooConfigEntry, SnooCoordinator
from .entity import SnooDescriptionEntity


@dataclass(frozen=True, kw_only=True)
class SnooSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[SnooData, SnooCoordinator], StateType]


def _format_duration(coordinator: SnooCoordinator) -> str | None:
    """Format session duration as HH:MM:SS."""
    secs = coordinator.session_duration_seconds
    if secs <= 0:
        return None
    h, remainder = divmod(secs, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}:{m:02d}:{s:02d}"


SENSOR_DESCRIPTIONS: list[SnooSensorEntityDescription] = [
    SnooSensorEntityDescription(
        key="state",
        translation_key="state",
        value_fn=lambda data, _: data.state_machine.state.name,
        device_class=SensorDeviceClass.ENUM,
        options=[e.name for e in SnooStates],
    ),
    SnooSensorEntityDescription(
        key="time_left",
        translation_key="time_left",
        value_fn=lambda data, _: data.state_machine.time_left_timestamp,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SnooSensorEntityDescription(
        key="session_duration",
        translation_key="session_duration",
        value_fn=lambda _, coord: _format_duration(coord),
        icon="mdi:timer-outline",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SnooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        SnooSensor(coordinator, description)
        for coordinator in entry.runtime_data.values()
        for description in SENSOR_DESCRIPTIONS
    )


class SnooSensor(SnooDescriptionEntity, SensorEntity):
    entity_description: SnooSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(
            self.coordinator.data, self.coordinator
        )
