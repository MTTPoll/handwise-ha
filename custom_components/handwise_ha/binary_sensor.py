"""Binary sensor platform for Handwise MGC01."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
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


def _mode(data: dict[str, Any]) -> str | None:
    """Return MGC01 mode as lowercase string."""
    value = data.get("mode")
    if isinstance(value, str):
        return value.lower()
    return None


def _is_connected(data: dict[str, Any]) -> bool:
    """Return whether the mower is online."""
    return _enabled(data.get("online"))


def _is_charging(data: dict[str, Any]) -> bool:
    """Return whether the mower is charging or docked."""
    return _mode(data) in {"charge", "charging", "charge_start"}


def _is_rain_detection_enabled(data: dict[str, Any]) -> bool:
    """Return whether rain detection is enabled.

    No device_class is used here so Home Assistant shows On/Off instead of
    moisture-specific states like Wet/Dry.
    """
    return _enabled(data.get("rainer_ctl"))


def _has_error(data: dict[str, Any]) -> bool:
    """Return whether the mower reports an error code."""
    value = data.get("err_code")
    if isinstance(value, int):
        return value != 0
    return False


def _safety_triggered(data: dict[str, Any]) -> bool:
    """Return whether safety trigger is active."""
    return _enabled(data.get("safety_trigger"))


@dataclass(frozen=True, kw_only=True)
class HandwiseBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Handwise MGC01 binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS: tuple[HandwiseBinarySensorDescription, ...] = (
    HandwiseBinarySensorDescription(
        key="connection",
        translation_key="connection",
        name="Connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=_is_connected,
    ),
    HandwiseBinarySensorDescription(
        key="charging",
        translation_key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=_is_charging,
    ),
    HandwiseBinarySensorDescription(
        key="rain_detection",
        translation_key="rain_detection",
        name="Rain detection",
        value_fn=_is_rain_detection_enabled,
    ),
    HandwiseBinarySensorDescription(
        key="error",
        translation_key="error",
        name="Error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=_has_error,
    ),
    HandwiseBinarySensorDescription(
        key="safety_trigger",
        translation_key="safety_trigger",
        name="Safety trigger",
        value_fn=_safety_triggered,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise MGC01 binary sensors from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        HandwiseBinarySensorEntity(coordinator, description)
        for coordinator in coordinators
        for description in BINARY_SENSORS
    )


class HandwiseBinarySensorEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], BinarySensorEntity
):
    """Handwise MGC01 binary sensor entity."""

    entity_description: HandwiseBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HandwiseGenieDataUpdateCoordinator,
        description: HandwiseBinarySensorDescription,
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
        """Return current binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.reported_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return compact attributes."""
        return {
            "serial_number": self.coordinator.client.serial_number,
        }
