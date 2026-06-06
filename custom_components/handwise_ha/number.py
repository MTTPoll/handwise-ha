"""Number platform for Handwise MGC01 settings."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HandwiseGenieDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HandwiseNumberDescription(NumberEntityDescription):
    """Describes a Handwise MGC01 number setting."""

    getter: Callable[[dict[str, Any]], float | int | None]


NUMBERS: tuple[HandwiseNumberDescription, ...] = (
    HandwiseNumberDescription(
        key="mow_height_setting",
        translation_key="mow_height_setting",
        name="Mow height",
        native_min_value=30,
        native_max_value=70,
        native_step=5,
        native_unit_of_measurement="mm",
        mode=NumberMode.SLIDER,
        getter=lambda data: data.get("cutter_height"),
    ),
    HandwiseNumberDescription(
        key="rain_wait_time_setting",
        translation_key="rain_wait_time_setting",
        name="Rain wait time",
        native_min_value=0,
        native_max_value=8,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        mode=NumberMode.SLIDER,
        getter=lambda data: (
            data.get("mow_delay_time") / 60
            if isinstance(data.get("mow_delay_time"), (int, float))
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise MGC01 number entities from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        HandwiseNumberEntity(coordinator, description)
        for coordinator in coordinators
        for description in NUMBERS
    )


class HandwiseNumberEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], NumberEntity
):
    """Handwise MGC01 number entity."""

    entity_description: HandwiseNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HandwiseGenieDataUpdateCoordinator,
        description: HandwiseNumberDescription,
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
    def native_value(self) -> float | None:
        """Return current number value."""
        value = self.entity_description.getter(self.coordinator.reported_state)
        if isinstance(value, (int, float)):
            return float(value)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return compact attributes."""
        return {
            "serial_number": self.coordinator.client.serial_number,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set value on mower."""
        int_value = int(round(value))
        key = self.entity_description.key

        if key == "mow_height_setting":
            if int_value < 30 or int_value > 70 or int_value % 5 != 0:
                raise ValueError("Mow height must be 30..70 in 5 mm steps")
            await self.coordinator.client.async_publish_service_command(
                cmd="param_set",
                data={"cutter_height": int_value, "rid_switch": 0},
            )

        elif key == "rain_wait_time_setting":
            if int_value < 0 or int_value > 8:
                raise ValueError("Rain wait time must be 0..8 hours")
            rain_enabled = 1 if self.coordinator.reported_state.get("rainer_ctl") in (1, True, "1") else 0
            await self.coordinator.client.async_publish_service_command(
                cmd="ctl_rainer",
                data={
                    "switch": rain_enabled,
                    "continue_time": int_value * 3600,
                },
            )

        await self.coordinator.client.async_request_all_properties()
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
