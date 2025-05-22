"""Platform for switch integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN,
    SWITCH_TYPE_CODE,
    LIGHT_TYPE_CODE,
    LIGHT_DPID,
    SWITCH,
    WORK_MODE,
    TEMP,
    BRIGHT,
    HUE,
    SAT,
)
from .tcp_client import tcp_client

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the switch platform via YAML discovery."""
    _LOGGER.debug("Setting up switch platform")
    
    if discovery_info is None:
        return

    domain_data = hass.data.get(DOMAIN, {})
    tcp_clients = domain_data.get('tcp_client', [])
    
    switches = []
    for client in tcp_clients:
        if SWITCH_TYPE_CODE == client.device_type_code:
            switches.append(CozyLifeSwitch(client))
    
    async_add_entities(switches)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform via config entry."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    tcp_clients = domain_data.get('tcp_client', [])
    
    switches = []
    for client in tcp_clients:
        if SWITCH_TYPE_CODE == client.device_type_code:
            switches.append(CozyLifeSwitch(client))
    
    async_add_entities(switches)


class CozyLifeSwitch(SwitchEntity):
    """Representation of a CozyLife Switch."""
    
    def __init__(self, tcp_client: tcp_client) -> None:
        """Initialize the switch."""
        _LOGGER.debug("Initializing CozyLife Switch")
        self._tcp_client = tcp_client
        self._attr_unique_id = tcp_client.device_id
        self._attr_name = f"{tcp_client.device_model_name} {tcp_client.device_id[-4:]}"
        self._refresh_state()
    
    def _refresh_state(self) -> None:
        """Query device and update state."""
        try:
            self._state = self._tcp_client.query()
            self._attr_is_on = self._state.get('1', 0) != 0
            _LOGGER.debug("Switch state refreshed: %s", self._attr_is_on)
        except Exception as err:
            _LOGGER.error("Error refreshing switch state: %s", err)
    
    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return True
    
    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        self._refresh_state()
        return self._attr_is_on
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on switch with kwargs: %s", kwargs)
        
        try:
            self._tcp_client.control({'1': 255})
            self._attr_is_on = True
            await self.hass.async_add_executor_job(self._refresh_state)
        except Exception as err:
            _LOGGER.error("Error turning on switch: %s", err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off switch")
        
        try:
            self._tcp_client.control({'1': 0})
            self._attr_is_on = False
            await self.hass.async_add_executor_job(self._refresh_state)
        except Exception as err:
            _LOGGER.error("Error turning off switch: %s", err)
