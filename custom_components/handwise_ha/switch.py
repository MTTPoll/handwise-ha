"""Switch platform for Handwise MGC01 settings."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HandwiseGenieDataUpdateCoordinator


def _enabled(value: Any) -> bool:
    """Return true for common enabled/on values."""
    return value in (1, "1", True, "true", "on", "enabled")


@dataclass(frozen=True, kw_only=True)
class HandwiseSwitchDescription(SwitchEntityDescription):
    """Describes a Handwise MGC01 switch setting."""


SWITCHES: tuple[HandwiseSwitchDescription, ...] = (
    HandwiseSwitchDescription(
        key="rain_detection_enabled",
        translation_key="rain_detection_enabled",
        name="Rain detection",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise MGC01 switch entities from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        HandwiseSwitchEntity(coordinator, description)
        for coordinator in coordinators
        for description in SWITCHES
    )


class HandwiseSwitchEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], SwitchEntity
):
    """Handwise MGC01 switch entity."""

    entity_description: HandwiseSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HandwiseGenieDataUpdateCoordinator,
        description: HandwiseSwitchDescription,
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

    @property
    def is_on(self) -> bool:
        """Return current switch value."""
        if self.entity_description.key == "rain_detection_enabled":
            return _enabled(self.coordinator.reported_state.get("rainer_ctl"))
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return compact attributes."""
        return {
            "serial_number": self.coordinator.client.serial_number,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        if self.entity_description.key == "rain_detection_enabled":
            continue_time = self.coordinator.reported_state.get("mow_delay_time")
            if not isinstance(continue_time, int) or continue_time <= 0:
                continue_time = 180
            await self.coordinator.client.async_publish_service_command(
                cmd="ctl_rainer",
                data={
                    "switch": 1,
                    "continue_time": continue_time * 60,
                },
            )
        await self.coordinator.client.async_request_all_properties()
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        if self.entity_description.key == "rain_detection_enabled":
            continue_time = self.coordinator.reported_state.get("mow_delay_time")
            if not isinstance(continue_time, int) or continue_time <= 0:
                continue_time = 180
            await self.coordinator.client.async_publish_service_command(
                cmd="ctl_rainer",
                data={
                    "switch": 0,
                    "continue_time": continue_time * 60,
                },
            )
        await self.coordinator.client.async_request_all_properties()
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
