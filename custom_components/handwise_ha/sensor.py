"""Sensor platform for Handwise MGC01."""

from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfArea
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HandwiseGenieDataUpdateCoordinator


MOWER_STATUS_OPTIONS: list[str] = [
    "standby",
    "paused",
    "charging",
    "mowing",
    "returning_to_dock",
    "mapping",
    "positioning",
    "resuming",
    "sleeping",
    "ota_updating",
    "remote_control",
    "factory_mode",
    "camera_cleaning",
    "going_to_target",
    "shutdown",
    "unknown",
]


def _path_exists(data: dict[str, Any], *keys: str) -> bool:
    """Check if a nested path exists in the data dictionary."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return False
        if key not in current:
            return False
        current = current[key]
    return True


def _raw_robot_status(data: dict[str, Any]) -> str | None:
    """Return raw MGC01 status from shadow payload."""
    mode = data.get("mode")
    if isinstance(mode, str):
        return mode.lower()
    return None


def _general_mower_status(data: dict[str, Any]) -> str:
    """Map raw robot status to a Home Assistant friendly status."""
    raw = _raw_robot_status(data)
    if raw is None:
        return "unknown"

    if raw in {
        "globalmowing",
        "zonemowing",
        "pointmowing",
        "bordermowing",
        "regionmowing",
        "nestmowing",
    }:
        return "mowing"
    if raw in {"charge", "charging", "charge_start"}:
        return "charging"
    if raw == "backtodock":
        return "returning_to_dock"
    if raw == "idle":
        return "standby"
    if raw == "pause":
        return "paused"
    if raw == "mapping":
        return "mapping"
    if raw == "position":
        return "positioning"
    if raw == "resume_point":
        return "resuming"
    if raw == "sleep":
        return "sleeping"
    if raw == "ota":
        return "ota_updating"
    if raw == "remotectrl":
        return "remote_control"
    if raw == "factory":
        return "factory_mode"
    if raw == "camera_cleaning":
        return "camera_cleaning"
    if raw == "gototarget":
        return "going_to_target"
    if raw == "shutdown":
        return "shutdown"
    return "unknown"


def _curpath_decoded_length(data: dict[str, Any]) -> int | None:
    """Return decoded curpath byte length without using raw curpath as HA state."""
    curpath = data.get("curpath")
    if not isinstance(curpath, str) or not curpath:
        return None
    try:
        return len(base64.b64decode(curpath, validate=True))
    except Exception:
        return len(curpath)


def _pin_status(data: dict[str, Any]) -> str | None:
    """Return human readable PIN/security status."""
    value = data.get("pin_correct")
    if value in (1, "1", True, "true", "on"):
        return "Entsichert"
    if value in (0, "0", False, "false", "off"):
        return "Gesperrt"
    return None


def _firmware_value(data: dict[str, Any], key: str) -> str | None:
    """Return firmware sub-version."""
    fw_version = data.get("fw_version")
    if isinstance(fw_version, dict):
        value = fw_version.get(key)
        if isinstance(value, str):
            return value
    return None


@dataclass(frozen=True, kw_only=True)
class HandwiseSensorDescription(SensorEntityDescription):
    """Describes a Handwise sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[HandwiseSensorDescription, ...] = (
    HandwiseSensorDescription(
        key="mower_status",
        translation_key="mower_status",
        name="Mower status",
        device_class=SensorDeviceClass.ENUM,
        options=MOWER_STATUS_OPTIONS,
        value_fn=_general_mower_status,
    ),
    HandwiseSensorDescription(
        key="battery_level",
        translation_key="battery_level",
        name="Battery level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("elec"),
    ),
    HandwiseSensorDescription(
        key="cutting_height",
        translation_key="cutting_height",
        name="Cutting height",
        native_unit_of_measurement="mm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("cutter_height"),
    ),
    HandwiseSensorDescription(
        key="mowing_area",
        translation_key="mowing_area",
        name="Mowing area",
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        device_class=SensorDeviceClass.AREA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mowing_area"),
    ),
    HandwiseSensorDescription(
        key="mowing_progress",
        translation_key="mowing_progress",
        name="Mowing progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mowing_progress"),
    ),
    HandwiseSensorDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        name="WiFi signal",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("rssi"),
    ),
    HandwiseSensorDescription(
        key="error_code",
        translation_key="error_code",
        name="Error code",
        value_fn=lambda data: data.get("err_code"),
    ),
    HandwiseSensorDescription(
        key="event_code",
        translation_key="event_code",
        name="Event code",
        value_fn=lambda data: data.get("event_code"),
    ),
    HandwiseSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        name="IP address",
        value_fn=lambda data: data.get("sta_ip_addr"),
    ),
    HandwiseSensorDescription(
        key="mode",
        translation_key="mode",
        name="Mode",
        value_fn=lambda data: data.get("mode"),
    ),
    HandwiseSensorDescription(
        key="pin_status",
        translation_key="pin_status",
        name="PIN status",
        value_fn=_pin_status,
    ),
    HandwiseSensorDescription(
        key="rain_effect",
        translation_key="rain_effect",
        name="Rain effect",
        value_fn=lambda data: data.get("rainer_effect"),
    ),
    HandwiseSensorDescription(
        key="mow_delay_time",
        translation_key="mow_delay_time",
        name="Rain wait time",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mow_delay_time"),
    ),
    HandwiseSensorDescription(
        key="current_mow_passes",
        translation_key="current_mow_passes",
        name="Current mow passes",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("cur_mow_times"),
    ),
    HandwiseSensorDescription(
        key="map_time",
        translation_key="map_time",
        name="Map time",
        value_fn=lambda data: data.get("maptime"),
    ),
    HandwiseSensorDescription(
        key="last_path_update",
        translation_key="last_path_update",
        name="Last path update",
        value_fn=lambda data: data.get("update_his_path"),
    ),
    HandwiseSensorDescription(
        key="current_path_data",
        translation_key="current_path_data",
        name="Current path data",
        native_unit_of_measurement="B",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_curpath_decoded_length,
    ),
    HandwiseSensorDescription(
        key="firmware_ui_board",
        translation_key="firmware_ui_board",
        name="UI board firmware",
        value_fn=lambda data: _firmware_value(data, "ui_board"),
    ),
    HandwiseSensorDescription(
        key="firmware_motor_board",
        translation_key="firmware_motor_board",
        name="Motor board firmware",
        value_fn=lambda data: _firmware_value(data, "motor_board"),
    ),
    HandwiseSensorDescription(
        key="firmware_charger_station",
        translation_key="firmware_charger_station",
        name="Charger station firmware",
        value_fn=lambda data: _firmware_value(data, "charger_station"),
    ),
    HandwiseSensorDescription(
        key="firmware_position_board",
        translation_key="firmware_position_board",
        name="Position board firmware",
        value_fn=lambda data: _firmware_value(data, "pos_board"),
    ),
)


def _sensor_path_for_description(description: HandwiseSensorDescription) -> list[str] | None:
    """Return the data path for conditional entity creation."""
    path_map: dict[str, list[str]] = {
        "mower_status": ["mode"],
        "battery_level": ["elec"],
        "cutting_height": ["cutter_height"],
        "mowing_area": ["mowing_area"],
        "mowing_progress": ["mowing_progress"],
        "wifi_signal": ["rssi"],
        "error_code": ["err_code"],
        "event_code": ["event_code"],
        "ip_address": ["sta_ip_addr"],
        "mode": ["mode"],
        "pin_status": ["pin_correct"],
        "rain_effect": ["rainer_effect"],
        "mow_delay_time": ["mow_delay_time"],
        "current_mow_passes": ["cur_mow_times"],
        "map_time": ["maptime"],
        "last_path_update": ["update_his_path"],
        "current_path_data": ["curpath"],
        "firmware_ui_board": ["fw_version", "ui_board"],
        "firmware_motor_board": ["fw_version", "motor_board"],
        "firmware_charger_station": ["fw_version", "charger_station"],
        "firmware_position_board": ["fw_version", "pos_board"],
    }
    return path_map.get(description.key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Handwise sensors from config entry."""
    coordinators: list[HandwiseGenieDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities_to_add: list[HandwiseSensorEntity] = []
    for coordinator in coordinators:
        state = coordinator.reported_state
        for description in SENSORS:
            path = _sensor_path_for_description(description)
            if path is not None and not _path_exists(state, *path):
                continue
            entities_to_add.append(HandwiseSensorEntity(coordinator, description))

    async_add_entities(entities_to_add)


class HandwiseSensorEntity(
    CoordinatorEntity[HandwiseGenieDataUpdateCoordinator], SensorEntity
):
    """Handwise sensor entity."""

    entity_description: HandwiseSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HandwiseGenieDataUpdateCoordinator,
        description: HandwiseSensorDescription,
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
    def native_value(self) -> Any:
        """Return current sensor value."""
        return self.entity_description.value_fn(self.coordinator.reported_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return compact extra state attributes."""
        state = self.coordinator.reported_state
        key = self.entity_description.key

        attributes: dict[str, Any] = {
            "serial_number": self.coordinator.client.serial_number,
        }

        if key == "mower_status":
            attributes["robot_status_raw"] = _raw_robot_status(state)

        elif key == "current_path_data":
            curpath = state.get("curpath")
            attributes.update(
                {
                    "curpath_raw": curpath,
                    "curpath_raw_length": (
                        len(curpath) if isinstance(curpath, str) else None
                    ),
                    "curpath_decoded_bytes": _curpath_decoded_length(state),
                }
            )

        return attributes
