"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.light import LightEntity
# from homeassistant.components.light import *
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
    SUPPORT_EFFECT,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from typing import Any, Final, Literal, TypedDict, final
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
import logging
from homeassistant.components import zeroconf

_LOGGER = logging.getLogger(__name__)
_LOGGER.info(__name__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    _LOGGER.info(
        f'setup_platform.hass={hass},config={config},add_entities={add_entities},discovery_info={discovery_info}')
    # zc = await zeroconf.async_get_instance(hass)
    # _LOGGER.info(f'zc={zc}')
    _LOGGER.info(f'hass.data={hass.data[DOMAIN]}')
    _LOGGER.info(f'discovery_info={discovery_info}')

    if discovery_info is None:
        return

    lights = []
    for item in hass.data[DOMAIN]['tcp_client']:
        if LIGHT_TYPE_CODE == item.device_type_code:
            lights.append(CozyLifeLight(item))

    add_entities(lights)


class CozyLifeLight(LightEntity):
    # _attr_brightness: int | None = None
    # _attr_color_mode: str | None = None
    # _attr_color_temp: int | None = None
    # _attr_hs_color = None
    _tcp_client = None

    _attr_supported_color_modes = {COLOR_MODE_BRIGHTNESS, COLOR_MODE_ONOFF}
    _attr_color_mode = COLOR_MODE_BRIGHTNESS

    # _unique_id = str
    # _attr_is_on = True
    # _name = str
    # _attr_brightness = int
    # _attr_color_temp = int
    # _attr_hs_color = (float, float)

    def __init__(self, tcp_client: tcp_client) -> None:
        """Initialize the sensor."""
        _LOGGER.info('__init__')
        self._tcp_client = tcp_client
        self._unique_id = tcp_client.device_id
        # Use alias if available, otherwise use device model name + last 4 chars of device ID
        if tcp_client.alias:
            self._name = tcp_client.alias
        else:
            self._name = tcp_client.device_model_name + ' ' + tcp_client.device_id[-4:]

        _LOGGER.info(f'before:{self._unique_id}._attr_color_mode={self._attr_color_mode}._attr_supported_color_modes='
                     f'{self._attr_supported_color_modes}.dpid={tcp_client.dpid}')
        # h s
        if 3 in tcp_client.dpid:
            self._attr_color_mode = COLOR_MODE_COLOR_TEMP
            self._attr_supported_color_modes.add(COLOR_MODE_COLOR_TEMP)

        if 5 in tcp_client.dpid or 6 in tcp_client.dpid:
            self._attr_color_mode = COLOR_MODE_HS
            self._attr_supported_color_modes.add(COLOR_MODE_HS)

        _LOGGER.info(f'after:{self._unique_id}._attr_color_mode={self._attr_color_mode}._attr_supported_color_modes='
                     f'{self._attr_supported_color_modes}.dpid={tcp_client.dpid}')

        self._refresh_state()

    def _refresh_state(self):
        """
        query device & set attr
        :return:
        """
        self._state = self._tcp_client.query()
        _LOGGER.info(f'_state={self._state}')
        self._attr_is_on = 0 < self._state['1']

        if '4' in self._state:
            self._attr_brightness = int(self._state['4'] / 4)

        if '5' in self._state:
            self._attr_hs_color = (int(self._state['5']), int(self._state['6'] / 10))

        if '3' in self._state:
            self._attr_color_temp = 500 - int(self._state['3'] / 2)

    @property
    def name(self) -> str:
        return self._name

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
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self._attr_color_temp

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._unique_id

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._attr_is_on = True
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        # 153 ~ 500
        colortemp = kwargs.get(ATTR_COLOR_TEMP)
        # tuple
        hs_color = kwargs.get(ATTR_HS_COLOR)
        rgb = kwargs.get(ATTR_RGB_COLOR)
        flash = kwargs.get(ATTR_FLASH)
        effect = kwargs.get(ATTR_EFFECT)
        _LOGGER.info(f'turn_on.kwargs={kwargs}')

        payload = {'1': 255, '2': 0}
        if brightness is not None:
            payload['4'] = brightness * 4
            self._attr_brightness = brightness

        if hs_color is not None:
            payload['5'] = int(hs_color[0])
            payload['6'] = int(hs_color[1] * 10)
            self._attr_hs_color = hs_color

        if colortemp is not None:
            payload['3'] = 1000 - colortemp * 2

        self._tcp_client.control(payload)
        self._refresh_state()
        return None
        raise NotImplementedError()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._attr_is_on = False
        _LOGGER.info(f'turn_off.kwargs={kwargs}')
        self._tcp_client.control({'1': 0})
        self._refresh_state()

        return None

        raise NotImplementedError()

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue and saturation color value [float, float]."""
        _LOGGER.info('hs_color')
        self._refresh_state()
        return self._attr_hs_color

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        _LOGGER.info('brightness')
        self._refresh_state()
        return self._attr_brightness

    @property
    def color_mode(self) -> str | None:
        """Return the color mode of the light."""
        _LOGGER.info('color_mode')
        return self._attr_color_mode

    # def set_brightness(self, b):
    #     _LOGGER.info('set_brightness')
    #
    #     self._attr_brightness = b
    #
    # def set_hs(self, hs_color, duration) -> None:
    #     """Set bulb's color."""
    #     _LOGGER.info('set_hs')
    #     self._attr_hs_color = (hs_color[0], hs_color[1])
