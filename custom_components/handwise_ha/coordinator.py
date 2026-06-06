"""Data coordinator for Handwise MGC01."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    HandwiseBoundDevice,
    HandwiseCloudApiClient,
    HandwiseGenieApiError,
    HandwiseShadowApiClient,
)
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)


class HandwiseGenieDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch and cache Handwise shadow state."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        account_client: HandwiseCloudApiClient,
        client: HandwiseShadowApiClient,
        device: HandwiseBoundDevice,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.account_client = account_client
        self.client = client
        self.device = device
        self._area_definition: dict[str, Any] = {}
        self._last_area_time: str | None = None

    @property
    def reported_state(self) -> dict[str, Any]:
        """Return the latest reported state."""
        return self.data if isinstance(self.data, dict) else {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest state from the cloud endpoint."""
        try:
            await self.client.async_ensure_temporary_credentials(self.account_client)
            property_state = await self.client.async_get_shadow_reported_state()
            _LOGGER.debug("ANTHBOT PROPERTY STATE: %s", property_state)
            try:
                service_state = await self.client.async_get_service_reported_state()
                _LOGGER.debug("ANTHBOT SERVICE STATE: %s", service_state)
            except HandwiseGenieApiError:
                service_state = {}

            area_time = property_state.get("area_time")
            if not isinstance(area_time, str):
                area_time = None
            should_refresh_area = not self._area_definition or (
                area_time is not None and area_time != self._last_area_time
            )
            if should_refresh_area:
                try:
                    self._area_definition = (
                        await self.account_client.async_get_device_area_definition(
                            self.client.serial_number
                        )
                    )
                    self._last_area_time = area_time
                except HandwiseGenieApiError:
                    if not self._area_definition:
                        self._area_definition = {}

            merged_state = dict(property_state)
            merged_state["_service_reported"] = service_state
            merged_state["_area_definition"] = self._area_definition
            return merged_state
        except HandwiseGenieApiError as err:
            raise UpdateFailed(str(err)) from err
