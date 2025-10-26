# -*- coding: utf-8 -*-
"""Device manager for CozyLife Local Pull integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from .const import DOMAIN
from .tcp_client import CozyLifeDevice

_LOGGER = logging.getLogger(__name__)


class DeviceManager:
    """Manages devices and their registry entries."""

    def __init__(self, hass: HomeAssistant, config_entry_id: str) -> None:
        """Initialize the device manager."""
        self.hass = hass
        self.config_entry_id = config_entry_id
        self.devices: Dict[str, CozyLifeDevice] = {}
        self._device_registry: Optional[DeviceRegistry] = None
        self._entity_registry: Optional[EntityRegistry] = None

    async def async_setup(self) -> None:
        """Set up the device manager."""
        from homeassistant.helpers.device_registry import async_get as async_get_dev_reg
        from homeassistant.helpers.entity_registry import async_get as async_get_ent_reg

        self._device_registry = async_get_dev_reg(self.hass)
        self._entity_registry = async_get_ent_reg(self.hass)

    def add_device(self, device: CozyLifeDevice) -> None:
        """Add a device to the manager."""
        device_id = device.device_id
        if device_id not in self.devices:
            self.devices[device_id] = device
            _LOGGER.debug(f"Added device: {device_id} ({device.device_model_name})")
        else:
            _LOGGER.debug(f"Device already exists: {device_id}")

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the manager."""
        if device_id in self.devices:
            del self.devices[device_id]
            _LOGGER.debug(f"Removed device: {device_id}")

    def get_device(self, device_id: str) -> Optional[CozyLifeDevice]:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_devices_by_type(self, device_type: str) -> List[CozyLifeDevice]:
        """Get all devices of a specific type."""
        return [
            device
            for device in self.devices.values()
            if device.device_type_code == device_type
        ]

    def register_device(
        self,
        device: CozyLifeDevice,
        entity_type: str = "unknown",
    ) -> None:
        """Register a device in the device registry."""
        if not self._device_registry:
            _LOGGER.warning("Device registry not initialized")
            return

        try:
            self._device_registry.async_get_or_create(
                config_entry_id=self.config_entry_id,
                connections=set(),
                identifiers={(DOMAIN, device.device_id)},
                name=device.device_model_name,
                manufacturer="CozyLife",
                model=device.device_model_name,
                sw_version=getattr(device, "software_version", "Unknown"),
            )
            _LOGGER.debug(f"Registered device in device registry: {device.device_id}")
        except Exception as e:
            _LOGGER.error(f"Failed to register device {device.device_id}: {e}")

    def get_all_devices(self) -> List[CozyLifeDevice]:
        """Get all devices."""
        return list(self.devices.values())

    def get_device_count(self) -> int:
        """Get total device count."""
        return len(self.devices)

    def clear(self) -> None:
        """Clear all devices."""
        self.devices.clear()
