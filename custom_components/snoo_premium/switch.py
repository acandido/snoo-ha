"""Switch entities for the Snoo Premium integration."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from python_snoo.containers import SnooData, SnooDevice
from python_snoo.exceptions import SnooCommandException
from python_snoo.snoo import Snoo

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DOMAIN,
    SETTING_CAR_RIDE_MODE,
    SETTING_MOTION_LIMITER,
    SETTING_WEANING,
)
from .coordinator import SnooConfigEntry, SnooCoordinator
from .entity import SnooDescriptionEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SnooSwitchEntityDescription(SwitchEntityDescription):
    value_fn: Callable[[SnooData, SnooCoordinator], bool | None]
    set_value_fn: Callable[..., Awaitable[None]]
    is_settings_entity: bool = False


async def _set_hold(
    snoo: Snoo, device: SnooDevice, data: SnooData, state: bool
) -> None:
    await snoo.set_level(device, data.state_machine.level, state)


async def _set_sticky_white_noise(
    snoo: Snoo, device: SnooDevice, _data: SnooData, state: bool
) -> None:
    await snoo.set_sticky_white_noise(device, state)


async def _set_motion_limiter(coordinator: SnooCoordinator, state: bool) -> None:
    await coordinator.update_setting(SETTING_MOTION_LIMITER, state)


async def _set_car_ride_mode(coordinator: SnooCoordinator, state: bool) -> None:
    await coordinator.update_setting(SETTING_CAR_RIDE_MODE, state)


async def _set_weaning(coordinator: SnooCoordinator, state: bool) -> None:
    await coordinator.update_setting(SETTING_WEANING, state)


SWITCH_DESCRIPTIONS: list[SnooSwitchEntityDescription] = [
    SnooSwitchEntityDescription(
        key="hold",
        translation_key="hold",
        value_fn=lambda data, _: data.state_machine.hold == "on",
        set_value_fn=_set_hold,
        icon="mdi:lock",
    ),
    SnooSwitchEntityDescription(
        key="sticky_white_noise",
        translation_key="sticky_white_noise",
        value_fn=lambda data, _: data.state_machine.sticky_white_noise == "on",
        set_value_fn=_set_sticky_white_noise,
        icon="mdi:music-note",
    ),
    SnooSwitchEntityDescription(
        key="motion_limiter",
        translation_key="motion_limiter",
        value_fn=lambda _, coord: coord.baby_settings.get(
            SETTING_MOTION_LIMITER
        ),
        set_value_fn=_set_motion_limiter,
        icon="mdi:speedometer-slow",
        is_settings_entity=True,
    ),
    SnooSwitchEntityDescription(
        key="car_ride_mode",
        translation_key="car_ride_mode",
        value_fn=lambda _, coord: coord.baby_settings.get(
            SETTING_CAR_RIDE_MODE
        ),
        set_value_fn=_set_car_ride_mode,
        icon="mdi:car",
        is_settings_entity=True,
    ),
    SnooSwitchEntityDescription(
        key="weaning",
        translation_key="weaning",
        value_fn=lambda _, coord: coord.baby_settings.get(SETTING_WEANING),
        set_value_fn=_set_weaning,
        icon="mdi:baby-carriage",
        is_settings_entity=True,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SnooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        SnooSwitch(coordinator, description)
        for coordinator in entry.runtime_data.values()
        for description in SWITCH_DESCRIPTIONS
    )


class SnooSwitch(SnooDescriptionEntity, SwitchEntity):
    entity_description: SnooSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(
            self.coordinator.data, self.coordinator
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            if self.entity_description.is_settings_entity:
                await self.entity_description.set_value_fn(
                    self.coordinator, True
                )
            else:
                await self.entity_description.set_value_fn(
                    self.coordinator.snoo,
                    self.coordinator.device,
                    self.coordinator.data,
                    True,
                )
        except SnooCommandException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="switch_on_failed",
                translation_placeholders={"name": str(self.name)},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            if self.entity_description.is_settings_entity:
                await self.entity_description.set_value_fn(
                    self.coordinator, False
                )
            else:
                await self.entity_description.set_value_fn(
                    self.coordinator.snoo,
                    self.coordinator.device,
                    self.coordinator.data,
                    False,
                )
        except SnooCommandException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="switch_off_failed",
                translation_placeholders={"name": str(self.name)},
            ) from err
