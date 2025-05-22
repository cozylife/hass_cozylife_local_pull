"""Platform for light integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_HS,
    COLOR_MODE_ONOFF,
    COLOR_MODE_RGB,
    COLOR_MODE_UNKNOWN,
    FLASH_LONG,
    FLASH_SHORT,
    LightEntity,
)
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
    """Set up the light platform via YAML discovery."""
    _LOGGER.debug(
        "Setting up light platform: config=%s, discovery_info=%s",
        config, discovery_info
    )
    
    if discovery_info is None:
        return

    domain_data = hass.data.get(DOMAIN, {})
    tcp_clients = domain_data.get('tcp_client', [])
    
    lights = []
    for client in tcp_clients:
        if LIGHT_TYPE_CODE == client.device_type_code:
            lights.append(CozyLifeLight(client))
    
    async_add_entities(lights)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform via config entry."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    tcp_clients = domain_data.get('tcp_client', [])
    
    lights = []
    for client in tcp_clients:
        if LIGHT_TYPE_CODE == client.device_type_code:
            lights.append(CozyLifeLight(client))
    
    async_add_entities(lights)


class CozyLifeLight(LightEntity):
    """Representation of a CozyLife Light."""
    
    def __init__(self, tcp_client: tcp_client) -> None:
        """Initialize the light."""
        _LOGGER.debug("Initializing CozyLife Light")
        self._tcp_client = tcp_client
        self._attr_unique_id = tcp_client.device_id
        self._attr_name = f"{tcp_client.device_model_name} {tcp_client.device_id[-4:]}"
        
        # Initialize supported color modes
        self._attr_supported_color_modes = {COLOR_MODE_BRIGHTNESS, COLOR_MODE_ONOFF}
        self._attr_color_mode = COLOR_MODE_BRIGHTNESS
        
        _LOGGER.debug(
            "Before color mode setup - ID: %s, color_mode: %s, supported_modes: %s, dpid: %s",
            self._attr_unique_id, self._attr_color_mode, 
            self._attr_supported_color_modes, tcp_client.dpid
        )
        
        # Check for color temperature support
        if 3 in tcp_client.dpid:
            self._attr_color_mode = COLOR_MODE_COLOR_TEMP
            self._attr_supported_color_modes.add(COLOR_MODE_COLOR_TEMP)
        
        # Check for HS color support
        if 5 in tcp_client.dpid or 6 in tcp_client.dpid:
            self._attr_color_mode = COLOR_MODE_HS
            self._attr_supported_color_modes.add(COLOR_MODE_HS)
        
        _LOGGER.debug(
            "After color mode setup - ID: %s, color_mode: %s, supported_modes: %s",
            self._attr_unique_id, self._attr_color_mode, self._attr_supported_color_modes
        )
        
        self._refresh_state()
    
    def _refresh_state(self) -> None:
        """Query device and update state attributes."""
        try:
            self._state = self._tcp_client.query()
            _LOGGER.debug("Device state: %s", self._state)
            
            self._attr_is_on = self._state.get('1', 0) > 0
            
            if '4' in self._state:
                self._attr_brightness = int(self._state['4'] / 4)
            
            if '5' in self._state and '6' in self._state:
                self._attr_hs_color = (
                    int(self._state['5']), 
                    int(self._state['6'] / 10)
                )
            
            if '3' in self._state:
                self._attr_color_temp = 500 - int(self._state['3'] / 2)
                
        except Exception as err:
            _LOGGER.error("Error refreshing state: %s", err)
    
    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return True
    
    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        self._refresh_state()
        return self._attr_is_on
    
    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        self._refresh_state()
        return getattr(self, '_attr_brightness', None)
    
    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue and saturation color value [float, float]."""
        self._refresh_state()
        return getattr(self, '_attr_hs_color', None)
    
    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return getattr(self, '_attr_color_temp', None)
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        _LOGGER.debug("Turning on light with kwargs: %s", kwargs)
        
        payload = {'1': 255, '2': 0}
        
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            payload['4'] = brightness * 4
            self._attr_brightness = brightness
        
        hs_color = kwargs.get(ATTR_HS_COLOR)
        if hs_color is not None:
            payload['5'] = int(hs_color[0])
            payload['6'] = int(hs_color[1] * 10)
            self._attr_hs_color = hs_color
        
        color_temp = kwargs.get(ATTR_COLOR_TEMP)
        if color_temp is not None:
            payload['3'] = 1000 - color_temp * 2
            self._attr_color_temp = color_temp
        
        try:
            self._tcp_client.control(payload)
            self._attr_is_on = True
            # Refresh state after a short delay to get updated values
            await self.hass.async_add_executor_job(self._refresh_state)
        except Exception as err:
            _LOGGER.error("Error turning on light: %s", err)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.debug("Turning off light with kwargs: %s", kwargs)
        
        try:
            self._tcp_client.control({'1': 0})
            self._attr_is_on = False
            await self.hass.async_add_executor_job(self._refresh_state)
        except Exception as err:
            _LOGGER.error("Error turning off light: %s", err)
