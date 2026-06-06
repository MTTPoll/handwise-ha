"""Button platform for Handwise MGC01 mower actions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HandwiseGenieDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HandwiseButtonDescription(ButtonEntityDescription):
    """Describes a Handwise mower action button."""


BUTTONS: tuple[HandwiseButtonDescription, ...] = (
    HandwiseButtonDescription(
        key="start_full_mow",
        translation_key="start_full_mow",
        name="Start mowing",
    ),
    HandwiseButtonDescription(
        key="pause_mow",
        translation_key="pause_mow",
        name="Pause mowing",
    ),
    HandwiseButtonDescription(
        key="return_to_dock",
        translation_key="return_to_dock",
        name="Return to dock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise buttons from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        HandwiseButtonEntity(coordinator, description)
        for coordinator in coordinators
        for description in BUTTONS
    )


class HandwiseButtonEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], ButtonEntity
):
    """Handwise action button entity."""

    entity_description: HandwiseButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HandwiseGenieDataUpdateCoordinator,
        description: HandwiseButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.client.serial_number}_{self.entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.client.serial_number)},
            manufacturer="Handwise",
            model=coordinator.device.model,
            name=coordinator.device.alias,
        )

    async def async_press(self) -> None:
        """Run the button action."""
        key = self.entity_description.key

        if key == "start_full_mow":
            await self.coordinator.client.async_publish_service_command(
                cmd="app_state", data=1
            )
            await self.coordinator.client.async_publish_service_command(
                cmd="mow_start", data=1
            )

        elif key == "pause_mow":
            await self.coordinator.client.async_publish_service_command(
                cmd="mow_pause", data=1
            )

        elif key == "return_to_dock":
            await self.coordinator.client.async_publish_service_command(
                cmd="charge_start", data=1
            )

        await self.coordinator.client.async_request_all_properties()
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
