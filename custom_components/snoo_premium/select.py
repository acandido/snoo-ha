"""Select entities for the Snoo Premium integration."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from python_snoo.containers import SnooData, SnooDevice, SnooLevels
from python_snoo.exceptions import SnooCommandException
from python_snoo.snoo import Snoo

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DOMAIN,
    MINIMAL_LEVEL_1,
    MINIMAL_LEVEL_2,
    MINIMAL_LEVEL_BASELINE,
    RESPONSIVENESS_INCREASED,
    RESPONSIVENESS_NORMAL,
    SETTING_MINIMAL_LEVEL,
    SETTING_RESPONSIVENESS,
)
from .coordinator import SnooConfigEntry, SnooCoordinator
from .entity import SnooDescriptionEntity

_LOGGER = logging.getLogger(__name__)

# Maps for display name <-> API value
RESPONSIVENESS_MAP = {
    "Normal": RESPONSIVENESS_NORMAL,
    "Increased": RESPONSIVENESS_INCREASED,
}
RESPONSIVENESS_REVERSE = {v: k for k, v in RESPONSIVENESS_MAP.items()}

MINIMAL_LEVEL_MAP = {
    "Baseline": MINIMAL_LEVEL_BASELINE,
    "Level 1": MINIMAL_LEVEL_1,
    "Level 2": MINIMAL_LEVEL_2,
}
MINIMAL_LEVEL_REVERSE = {v: k for k, v in MINIMAL_LEVEL_MAP.items()}


@dataclass(frozen=True, kw_only=True)
class SnooSelectEntityDescription(SelectEntityDescription):
    value_fn: Callable[[SnooData, SnooCoordinator], str | None]
    set_value_fn: Callable[..., Awaitable[None]]
    is_settings_entity: bool = False


async def _set_intensity(
    snoo: Snoo, device: SnooDevice, option: str, **_kwargs
) -> None:
    await snoo.set_level(device, SnooLevels[option])


async def _set_responsiveness(coordinator: SnooCoordinator, option: str) -> None:
    api_val = RESPONSIVENESS_MAP.get(option, option)
    await coordinator.update_setting(SETTING_RESPONSIVENESS, api_val)


async def _set_minimal_level(coordinator: SnooCoordinator, option: str) -> None:
    api_val = MINIMAL_LEVEL_MAP.get(option, option)
    await coordinator.update_setting(SETTING_MINIMAL_LEVEL, api_val)


SELECT_DESCRIPTIONS: list[SnooSelectEntityDescription] = [
    SnooSelectEntityDescription(
        key="intensity",
        translation_key="intensity",
        value_fn=lambda data, _: data.state_machine.level.name
        if data.state_machine.level
        else None,
        set_value_fn=_set_intensity,
        options=[level.name for level in SnooLevels],
        icon="mdi:sine-wave",
    ),
    SnooSelectEntityDescription(
        key="responsiveness",
        translation_key="responsiveness",
        value_fn=lambda _, coord: RESPONSIVENESS_REVERSE.get(
            coord.baby_settings.get(SETTING_RESPONSIVENESS, ""), "Normal"
        ),
        set_value_fn=_set_responsiveness,
        options=list(RESPONSIVENESS_MAP.keys()),
        icon="mdi:ear-hearing",
        is_settings_entity=True,
    ),
    SnooSelectEntityDescription(
        key="motion_start_level",
        translation_key="motion_start_level",
        value_fn=lambda _, coord: MINIMAL_LEVEL_REVERSE.get(
            coord.baby_settings.get(SETTING_MINIMAL_LEVEL, ""), "Baseline"
        ),
        set_value_fn=_set_minimal_level,
        options=list(MINIMAL_LEVEL_MAP.keys()),
        icon="mdi:waves-arrow-up",
        is_settings_entity=True,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SnooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        SnooSelect(coordinator, description)
        for coordinator in entry.runtime_data.values()
        for description in SELECT_DESCRIPTIONS
    )


class SnooSelect(SnooDescriptionEntity, SelectEntity):
    entity_description: SnooSelectEntityDescription

    @property
    def current_option(self) -> str | None:
        return self.entity_description.value_fn(
            self.coordinator.data, self.coordinator
        )

    async def async_select_option(self, option: str) -> None:
        try:
            if self.entity_description.is_settings_entity:
                await self.entity_description.set_value_fn(
                    self.coordinator, option
                )
            else:
                await self.entity_description.set_value_fn(
                    self.coordinator.snoo,
                    self.coordinator.device,
                    option,
                )
        except SnooCommandException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="select_failed",
                translation_placeholders={
                    "name": str(self.name),
                    "option": option,
                },
            ) from err
