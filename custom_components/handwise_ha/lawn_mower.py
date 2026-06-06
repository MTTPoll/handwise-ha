"""Lawn mower platform for Handwise MGC01."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HandwiseGenieDataUpdateCoordinator


_MOWING_RAW_STATUSES: frozenset[str] = frozenset(
    {
        "globalmowing",
        "zonemowing",
        "pointmowing",
        "bordermowing",
        "regionmowing",
        "nestmowing",
        "position",
        "resume_point",
        "gototarget",
        "mapping",
    }
)

_DOCKED_RAW_STATUSES: frozenset[str] = frozenset(
    {"charge", "charging", "charge_start", "idle", "sleep", "shutdown"}
)

_RETURNING_RAW_STATUSES: frozenset[str] = frozenset({"backtodock"})
_PAUSED_RAW_STATUSES: frozenset[str] = frozenset({"pause"})


def _raw_robot_status(data: dict[str, Any]) -> str | None:
    """Return raw MGC01 status from shadow payload."""
    mode = data.get("mode")
    if isinstance(mode, str):
        return mode.lower()
    return None


def _activity_from_state(data: dict[str, Any]) -> LawnMowerActivity | None:
    """Map raw shadow state to a Home Assistant LawnMowerActivity."""
    raw = _raw_robot_status(data)

    if raw is None:
        return None
    if raw in _MOWING_RAW_STATUSES:
        return LawnMowerActivity.MOWING
    if raw in _RETURNING_RAW_STATUSES:
        return LawnMowerActivity.RETURNING
    if raw in _PAUSED_RAW_STATUSES:
        return LawnMowerActivity.PAUSED
    if raw in _DOCKED_RAW_STATUSES:
        return LawnMowerActivity.DOCKED

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise lawn mower entities from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        HandwiseLawnMowerEntity(coordinator) for coordinator in coordinators
    )


class HandwiseLawnMowerEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], LawnMowerEntity
):
    """Handwise lawn mower entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.DOCK
    )

    def __init__(self, coordinator: HandwiseGenieDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.serial_number}_lawn_mower"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.client.serial_number)},
            manufacturer="Handwise",
            model=coordinator.device.model,
            name=coordinator.device.alias,
        )

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return current mower activity."""
        return _activity_from_state(self.coordinator.reported_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        state = self.coordinator.reported_state
        return {
            "serial_number": self.coordinator.client.serial_number,
            "robot_status_raw": _raw_robot_status(state),
        }

    async def _async_sync_after_command(self) -> None:
        """Refresh shadow state after issuing a command."""
        await self.coordinator.client.async_request_all_properties()
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_start_mowing(self) -> None:
        """Start or resume mowing."""
        await self.coordinator.client.async_publish_service_command(
            cmd="app_state", data=1
        )
        await self.coordinator.client.async_publish_service_command(
            cmd="mow_start", data=1
        )
        await self._async_sync_after_command()

    async def async_pause(self) -> None:
        """Pause the mower."""
        await self.coordinator.client.async_publish_service_command(
            cmd="mow_pause", data=1
        )
        await self._async_sync_after_command()

    async def async_dock(self) -> None:
        """Send the mower back to its dock."""
        await self.coordinator.client.async_publish_service_command(
            cmd="charge_start", data=1
        )
        await self._async_sync_after_command()
