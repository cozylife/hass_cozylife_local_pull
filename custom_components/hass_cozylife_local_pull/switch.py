"""Switch platform for CozyLife Local Pull integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH_TYPE_CODE
from .tcp_client import CozyLifeDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch platform from a config entry."""
    _LOGGER.info("Setting up switch platform")

    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("Integration not initialized")
        return

    data = hass.data[DOMAIN][config_entry.entry_id]
    device_manager = data.get("device_manager")

    if not device_manager:
        return

    # Get all switch devices
    switch_devices = device_manager.get_devices_by_type(SWITCH_TYPE_CODE)

    switches = [CozyLifeSwitch(device) for device in switch_devices]

    async_add_entities(switches)
    _LOGGER.info(f"Added {len(switches)} switch entities")


class CozyLifeSwitch(SwitchEntity):
    """Representation of a CozyLife switch."""

    _attr_has_entity_name = True

    def __init__(self, device: CozyLifeDevice) -> None:
        """Initialize the switch."""
        self._device = device
        self._attr_unique_id = device.device_id
        self._attr_name = f"{device.device_model_name}"
        # Initialize to None, will be set on first update
        self._attr_is_on = None

        # Set device info to associate this entity with the device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            manufacturer="CozyLife",
            model=device.device_model_name,
            name=device.device_model_name,
        )

        _LOGGER.debug(f"Initialized switch {self._attr_unique_id}")

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._device.is_available

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        await super().async_added_to_hass()
        # Fetch initial state from device
        await self.async_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._device.async_control({"1": 255})
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._device.async_control({"1": 0})
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the switch state."""
        state = await self._device.async_query()
        if not state:
            _LOGGER.debug(f"Failed to query device {self._attr_unique_id}, device may be initializing")
            # Set sensible default on first query failure
            if self._attr_is_on is None:
                self._attr_is_on = False
            return

        if "1" in state:
            self._attr_is_on = state["1"] > 0
        else:
            if self._attr_is_on is None:
                self._attr_is_on = False
