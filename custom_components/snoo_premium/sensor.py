"""Sensors for the Snoo Premium integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from python_snoo.containers import SnooData, SnooStates

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    StateType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SnooConfigEntry, SnooCoordinator
from .entity import SnooDescriptionEntity


@dataclass(frozen=True, kw_only=True)
class SnooSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[SnooData, SnooCoordinator], StateType]
    extra_attrs_fn: Callable[[SnooCoordinator], dict[str, Any]] | None = None


def _format_duration(seconds: int) -> str | None:
    """Format seconds as H:MM:SS."""
    if seconds <= 0:
        return None
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _history_attrs(coord: SnooCoordinator) -> dict[str, Any]:
    """Build extra attributes for the session log sensor."""
    history = coord.session_history
    if not history:
        return {"sessions": [], "total_sessions": 0}

    # Summary stats
    durations = [s["duration_seconds"] for s in history]
    total = sum(durations)
    avg = total // len(durations) if durations else 0

    # Last 10 sessions for the attribute (full log is in storage)
    recent = history[-10:]

    return {
        "total_sessions": len(history),
        "total_sleep_seconds": total,
        "total_sleep": _format_duration(total) or "0:00:00",
        "average_session_seconds": avg,
        "average_session": _format_duration(avg) or "0:00:00",
        "recent_sessions": recent,
    }


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
    # Live session duration — only has a value while a session is active
    SnooSensorEntityDescription(
        key="session_duration",
        translation_key="session_duration",
        value_fn=lambda _, coord: _format_duration(coord.session_duration_seconds),
        icon="mdi:timer-outline",
    ),
    # Persists the duration of the most recently completed session
    SnooSensorEntityDescription(
        key="last_session_duration",
        translation_key="last_session_duration",
        value_fn=lambda _, coord: _format_duration(
            coord.last_session_duration_seconds
        ),
        icon="mdi:timer-check-outline",
    ),
    # Timestamp when the current (or most recent) session started
    SnooSensorEntityDescription(
        key="session_start",
        translation_key="session_start",
        value_fn=lambda _, coord: coord.session_start_time,
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:sleep",
    ),
    # Timestamp when the most recent session ended
    SnooSensorEntityDescription(
        key="session_end",
        translation_key="session_end",
        value_fn=lambda _, coord: coord.session_end_time,
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:sleep-off",
    ),
    # Rolling session log — state is the total session count,
    # attributes contain stats and the last 10 sessions
    SnooSensorEntityDescription(
        key="session_log",
        translation_key="session_log",
        value_fn=lambda _, coord: len(coord.session_history),
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:chart-timeline-variant",
        extra_attrs_fn=_history_attrs,
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_attrs_fn is not None:
            return self.entity_description.extra_attrs_fn(self.coordinator)
        return None
