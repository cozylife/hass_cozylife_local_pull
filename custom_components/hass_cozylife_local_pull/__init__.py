"""Example Load Platform integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
import logging
import time
from .const import (
    DOMAIN,
    LANG
)
from .utils import get_pid_list
from .udp_discover import get_ip
from .tcp_client import tcp_client

_LOGGER = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:

    """
    Setup CozyLife integration.
    Supports config formats:
    1. Legacy: {'lang': 'zh', 'ip': ['192.168.5.201', '192.168.5.202']}
    2. New with list: {'lang': 'en', 'devices': [{'serial_number': '...', 'alias': '...', 'ip': '...'}]}
    """
    config_data = config.get(DOMAIN, {})
    lang_from_config = config_data.get('lang') if config_data.get('lang') is not None else LANG
    get_pid_list(lang_from_config)

    # Parse devices from config
    device_configs = config_data.get('devices', {})
    device_aliases = {}  # Maps device_id to alias
    device_ips = {}  # Maps device_id to IP

    if isinstance(device_configs, list):
        # List format: [{'serial_number': '...', 'alias': '...', 'ip': '...'}, ...]
        for item in device_configs:
            if isinstance(item, dict):
                # Check for new format: {'serial_number': '...', 'alias': '...', 'ip': '...'}
                if 'serial_number' in item:
                    device_id = item['serial_number']
                    device_aliases[device_id] = item.get('alias', '')
                    if 'ip' in item:
                        device_ips[device_id] = item['ip']
                    else:
                        _LOGGER.warning(f'Device {device_id} missing IP address in config')
                # Backward compat: support 'device_id' key
                elif 'device_id' in item:
                    device_id = item['device_id']
                    device_aliases[device_id] = item.get('alias', '')
                    if 'ip' in item:
                        device_ips[device_id] = item['ip']
                    else:
                        _LOGGER.warning(f'Device {device_id} missing IP address in config')
    elif isinstance(device_configs, dict):
        # Dict format: {'SERIAL_NUMBER': 'ALIAS'} (backward compat, but requires IP in legacy 'ip' list)
        device_aliases = device_configs.copy()

    # Determine IP addresses to use
    ip_list = []

    # Use IPs from device configs (new format)
    if device_ips:
        ip_list = list(device_ips.values())
        _LOGGER.info(f'Using IPs from device config: {ip_list}')
    else:
        # Legacy config: use UDP discovery + explicit IPs
        _LOGGER.info('Using legacy UDP discovery + explicit IPs')
        ip = get_ip()
        ip_from_config = config_data.get('ip') if config_data.get('ip') is not None else []
        ip += ip_from_config
        [ip_list.append(i) for i in ip if i not in ip_list]

    if 0 == len(ip_list):
        _LOGGER.info('discover nothing')
        return True

    _LOGGER.info(f'try connect ip_list: {ip_list}')

    # Create tcp_client instances with aliases
    # Create a reverse map: IP -> device_id for easier lookup
    ip_to_device_id = {}
    if device_ips:
        for device_id, ip in device_ips.items():
            ip_to_device_id[ip] = device_id

    tcp_clients = []
    for ip in ip_list:
        # Find alias for this IP
        alias = None
        if ip in ip_to_device_id:
            device_id = ip_to_device_id[ip]
            alias = device_aliases.get(device_id)
        tcp_clients.append(tcp_client(ip, alias=alias))

    hass.data[DOMAIN] = {
        'temperature': 24,
        'ip': ip_list,
        'tcp_client': tcp_clients,
    }

    #wait for get device info from tcp conncetion
    #but it is bad
    time.sleep(3)
    # _LOGGER.info('setup', hass, config)
    # hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.loop.call_soon_threadsafe(hass.async_create_task, async_load_platform(hass, 'light', DOMAIN, {}, config))
    hass.loop.call_soon_threadsafe(hass.async_create_task, async_load_platform(hass, 'switch', DOMAIN, {}, config))
    return True
