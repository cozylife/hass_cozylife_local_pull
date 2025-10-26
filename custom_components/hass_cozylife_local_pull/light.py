"""Light platform for CozyLife Local Pull integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    DEFAULT_MAX_KELVIN,
    DEFAULT_MIN_KELVIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import color as colorutil

from .const import DOMAIN, LIGHT_TYPE_CODE
from .tcp_client import CozyLifeDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light platform from a config entry."""
    _LOGGER.info("Setting up light platform")

    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("Integration not initialized")
        return

    data = hass.data[DOMAIN][config_entry.entry_id]
    device_manager = data.get("device_manager")

    if not device_manager:
        return

    # Get all light devices
    light_devices = device_manager.get_devices_by_type(LIGHT_TYPE_CODE)

    lights = [CozyLifeLight(device) for device in light_devices]

    async_add_entities(lights)
    _LOGGER.info(f"Added {len(lights)} light entities")


class CozyLifeLight(LightEntity):
    """Representation of a CozyLife light."""

    _attr_has_entity_name = True

    def __init__(self, device: CozyLifeDevice) -> None:
        """Initialize the light."""
        self._device = device
        self._attr_unique_id = device.device_id
        self._attr_name = f"{device.device_model_name}"

        # Set device info to associate this entity with the device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            manufacturer="CozyLife",
            model=device.device_model_name,
            name=device.device_model_name,
        )

        # Calculate color temperature limits (Mireds)
        # Cold: 6500K, Warm: 2700K
        self._min_mireds = colorutil.color_temperature_kelvin_to_mired(6500)
        self._max_mireds = colorutil.color_temperature_kelvin_to_mired(2700)
        self._miredsratio = (self._max_mireds - self._min_mireds) / 1000
        self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
        self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

        # Initialize supported color modes - start with basic modes
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS, ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.BRIGHTNESS

        # Add color modes based on device capabilities
        # Important: Use .add() to support multiple modes, not replace
        if 3 in device.dpid:
            # Device supports color temperature
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)

        if 5 in device.dpid or 6 in device.dpid:
            # Device supports HS color
            self._attr_color_mode = ColorMode.HS
            self._attr_supported_color_modes.add(ColorMode.HS)

        _LOGGER.debug(
            f"Device {device.device_id}: dpid={device.dpid}, "
            f"color_mode={self._attr_color_mode}, "
            f"supported_color_modes={self._attr_supported_color_modes}"
        )

        # Initialize state with sensible defaults (not None)
        # This ensures the entity has valid state even before first update
        self._attr_is_on = False
        self._attr_brightness = 128  # Mid-range brightness
        self._attr_color_temp_kelvin = 4000  # Warm-neutral color temp
        self._attr_hs_color = (0, 0)  # Black/off state for HS

        _LOGGER.debug(
            f"Initialized light {self._attr_unique_id} with color mode: {self._attr_color_mode}, supported: {self._attr_supported_color_modes}"
        )

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        # Entity is available if device is available
        return self._device.is_available

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        await super().async_added_to_hass()
        # Fetch initial state from device
        await self.async_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # dpid 2 = 0: normal color/brightness mode, 1: special effects mode
        # For normal control, always use dpid 2 = 0
        payload = {"1": 255, "2": 0}

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        colortemp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        # Handle HS color (dpid 5, 6)
        if hs_color is not None:
            r, g, b = colorutil.color_hs_to_RGB(*hs_color)
            converted_hs = colorutil.color_RGB_to_hs(r, g, b)
            payload["5"] = round(converted_hs[0])
            payload["6"] = round(converted_hs[1] * 10)
            self._attr_hs_color = hs_color
            self._attr_color_mode = ColorMode.HS
            _LOGGER.debug(f"HS color: HA H={hs_color[0]}, S={hs_color[1]}, payload 5={payload['5']}, 6={payload['6']}")

        # Handle color temperature (dpid 3)
        if colortemp_kelvin is not None:
            mireds = colorutil.color_temperature_kelvin_to_mired(colortemp_kelvin)
            payload["3"] = round(1000 - (mireds - self._min_mireds) / self._miredsratio)
            self._attr_color_temp_kelvin = colortemp_kelvin
            self._attr_color_mode = ColorMode.COLOR_TEMP
            _LOGGER.debug(f"Color temp: Kelvin={colortemp_kelvin}, payload={payload['3']}")

        # Handle brightness (dpid 4) - applies to all modes
        if brightness is not None:
            payload["4"] = round(brightness / 255 * 1000)
            self._attr_brightness = brightness
            _LOGGER.debug(f"Brightness: HA={brightness}, payload={payload['4']}")

        _LOGGER.info(f"Sending payload: {payload}")
        await self._device.async_control(payload)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._device.async_control({"1": 0})
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the light state from device."""
        state = await self._device.async_query()
        if not state:
            _LOGGER.debug(f"Failed to query device {self._attr_unique_id}, device may be initializing")
            return

        _LOGGER.debug(f"Device state: {state}")

        # Update on/off state (dpid 1)
        if "1" in state:
            self._attr_is_on = state["1"] > 0

        # Check dpid 2 (mode): 0 = normal mode, 1 = special effects mode
        # Only update color/brightness values when in normal mode (dpid 2 == 0)
        device_mode = state.get("2", 0)

        # Update brightness (dpid 4): device 0-1000 → HA 0-255
        # Brightness is available in normal mode
        if "4" in state:
            brightness_value = int(state["4"])
            # Validate brightness value
            if 0 <= brightness_value <= 1000:
                self._attr_brightness = int(brightness_value / 1000 * 255)
                _LOGGER.debug(f"Brightness: dpid 4={brightness_value} → {self._attr_brightness}")

        # Only update color values when device is in normal mode (dpid 2 == 0)
        if device_mode == 0:
            # Update color temperature (dpid 3) if present
            if "3" in state:
                device_value = int(state["3"])
                # Validate color temp value (skip if > 60000, indicating invalid data)
                if 0 <= device_value < 60000:
                    mireds = self._max_mireds - (device_value * self._miredsratio)
                    if mireds > 0:
                        self._attr_color_temp_kelvin = int(1000000 / mireds)
                        self._attr_color_mode = ColorMode.COLOR_TEMP
                        _LOGGER.debug(f"Color temp: dpid 3={device_value} → {self._attr_color_temp_kelvin}K")

            # Update HS color (dpid 5, 6) if present
            if "5" in state and "6" in state:
                h_device = int(state["5"])
                s_device = int(state["6"] / 10)
                # Validate HS values (skip if > 60000, indicating invalid data)
                if h_device < 60000 and s_device < 60000:
                    # Convert through RGB for proper color space handling
                    r, g, b = colorutil.color_hs_to_RGB(h_device, s_device)
                    h_ha, s_ha = colorutil.color_RGB_to_hs(r, g, b)
                    self._attr_hs_color = (h_ha, s_ha)
                    self._attr_color_mode = ColorMode.HS
                    _LOGGER.debug(f"HS color: dpid 5={state['5']}, dpid 6={state['6']} → H={h_ha}, S={s_ha}")
