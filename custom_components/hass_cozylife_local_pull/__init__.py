"""CozyLife Local Pull integration."""
from __future__ import annotations

import logging
import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, LANG
from .utils import get_pid_list
from .udp_discover import get_ip
from .tcp_client import tcp_client

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the CozyLife Local Pull integration from YAML."""
    # This is for YAML configuration (legacy support)
    # Modern integrations should use config flow, but we'll keep this for compatibility
    if DOMAIN not in config:
        return True
    
    hass.data.setdefault(DOMAIN, {})
    
    # Get IPs from discovery and config
    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, get_ip)
    ip_from_config = config[DOMAIN].get('ip', [])
    ip += ip_from_config
    ip_list = list(dict.fromkeys(ip))  # Remove duplicates while preserving order

    if not ip_list:
        _LOGGER.info('No devices discovered')
        return True

    _LOGGER.info('Trying to connect to IPs: %s', ip_list)
    lang_from_config = config[DOMAIN].get('lang', LANG)
    get_pid_list(lang_from_config)

    # Store data for platforms
    hass.data[DOMAIN].update({
        'temperature': 24,
        'ip': ip_list,
        'tcp_client': [tcp_client(item) for item in ip_list],
    })

    # Wait for device info from TCP connections
    await asyncio.sleep(3)

    # Load platforms
    await hass.helpers.discovery.async_load_platform(Platform.LIGHT, DOMAIN, {}, config)
    await hass.helpers.discovery.async_load_platform(Platform.SWITCH, DOMAIN, {}, config)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CozyLife Local Pull from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Get IPs from discovery and config entry
    loop = asyncio.get_event_loop()
    ip = await loop.run_in_executor(None, get_ip)
    ip_from_config = entry.data.get('ip', [])
    ip += ip_from_config
    ip_list = list(dict.fromkeys(ip))  # Remove duplicates while preserving order

    if not ip_list:
        _LOGGER.info('No devices discovered')
        return True

    _LOGGER.info('Trying to connect to IPs: %s', ip_list)
    lang_from_config = entry.data.get('lang', LANG)
    get_pid_list(lang_from_config)

    # Store data for platforms
    hass.data[DOMAIN][entry.entry_id] = {
        'temperature': 24,
        'ip': ip_list,
        'tcp_client': [tcp_client(item) for item in ip_list],
    }

    # Wait for device info from TCP connections
    await asyncio.sleep(3)

    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok
