"""Button entities for the Snoo Premium integration."""
from __future__ import annotations

from python_snoo.exceptions import SnooCommandException

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import SnooConfigEntry
from .entity import SnooDescriptionEntity

BUTTON_DESCRIPTIONS: list[ButtonEntityDescription] = [
    ButtonEntityDescription(
        key="start_snoo",
        translation_key="start_snoo",
        icon="mdi:play",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SnooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        SnooButton(coordinator, description)
        for coordinator in entry.runtime_data.values()
        for description in BUTTON_DESCRIPTIONS
    )


class SnooButton(SnooDescriptionEntity, ButtonEntity):
    async def async_press(self) -> None:
        try:
            await self.coordinator.snoo.start_snoo(self.coordinator.device)
        except SnooCommandException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="start_failed",
                translation_placeholders={"name": str(self.name)},
            ) from err
