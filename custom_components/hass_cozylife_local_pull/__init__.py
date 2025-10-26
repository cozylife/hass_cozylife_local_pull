"""CozyLife Local Pull integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, LANG
from .device_manager import DeviceManager
from .tcp_client import CozyLifeDevice
from .udp_discover import get_ip, scan_subnet_async
from .utils import get_pid_list

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.LIGHT, Platform.SWITCH]
SCAN_INTERVAL_CONFIG_KEY = "scan_interval"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the CozyLife Local Pull integration using YAML config."""
    if DOMAIN not in config:
        return True

    hass.data[DOMAIN] = {}

    # Create config entry from YAML for backward compatibility
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CozyLife Local Pull from a config entry."""
    _LOGGER.info(f"Setting up {DOMAIN} with entry {entry.title}")

    # Initialize domain data if not already done by async_setup (YAML config)
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Initialize device manager
    device_manager = DeviceManager(hass, entry.entry_id)
    await device_manager.async_setup()

    # Get configuration
    lang = entry.data.get("lang", LANG)
    ip_list_config = entry.data.get("ip", [])
    subnets_config = entry.data.get("subnets", [])
    scan_interval = entry.options.get(SCAN_INTERVAL_CONFIG_KEY, 300)

    # Initialize PID list
    try:
        await hass.async_add_executor_job(get_pid_list, lang)
    except Exception as e:
        _LOGGER.error(f"Failed to load PID list: {e}")

    # Discover devices via UDP broadcast
    discovered_ips = await hass.async_add_executor_job(get_ip)
    _LOGGER.info(f"UDP discovery found {len(discovered_ips)} device(s): {discovered_ips}")

    # Scan user-configured subnets (for cross-subnet discovery)
    subnet_ips = []
    if subnets_config:
        _LOGGER.info(f"Scanning {len(subnets_config)} subnet(s) for cross-subnet devices: {subnets_config}")
        for subnet in subnets_config:
            try:
                ips = await scan_subnet_async(subnet, timeout=1.0)
                subnet_ips.extend(ips)
            except Exception as e:
                _LOGGER.error(f"Error scanning subnet {subnet}: {e}")

    # Combine discovered IPs from all sources
    all_ips = list(set(discovered_ips + ip_list_config + subnet_ips))

    if not all_ips:
        _LOGGER.warning("No devices discovered or configured")
        hass.data[DOMAIN][entry.entry_id] = {
            "device_manager": device_manager,
            "tcp_clients": [],
            "scan_task": None,
        }
        return True

    _LOGGER.info(f"Found {len(all_ips)} devices: {all_ips}")

    # Connect to all devices
    tcp_clients = []
    for ip in all_ips:
        device = CozyLifeDevice(ip)
        try:
            if await device.async_connect():
                tcp_clients.append(device)
                device_manager.add_device(device)
                device_manager.register_device(device)
                _LOGGER.info(f"Successfully connected to device at {ip}")
            else:
                _LOGGER.warning(f"Failed to connect to device at {ip}")
        except Exception as e:
            _LOGGER.error(f"Error connecting to {ip}: {e}")

    if not tcp_clients:
        _LOGGER.warning("No devices connected initially - will discover via periodic scan")

    # Store data
    hass.data[DOMAIN][entry.entry_id] = {
        "device_manager": device_manager,
        "tcp_clients": tcp_clients,
        "scan_interval": scan_interval,
        "last_scan_ips": set(all_ips),
    }

    # Setup platforms - even if no devices connected yet
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start periodic discovery and reconnection
    scan_task = asyncio.create_task(
        _async_periodic_discovery(hass, entry, device_manager, scan_interval)
    )
    hass.data[DOMAIN][entry.entry_id]["scan_task"] = scan_task

    # Setup reload listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"Unloading {DOMAIN} entry {entry.title}")

    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return True

    data = hass.data[DOMAIN][entry.entry_id]

    # Cancel scan task
    scan_task = data.get("scan_task")
    if scan_task:
        scan_task.cancel()
        try:
            await scan_task
        except asyncio.CancelledError:
            pass

    # Disconnect all devices
    device_manager: DeviceManager = data.get("device_manager")
    if device_manager:
        for device in device_manager.get_all_devices():
            await device.async_disconnect()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_periodic_discovery(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_manager: DeviceManager,
    scan_interval: int,
) -> None:
    """Periodically discover new devices."""
    while True:
        try:
            await asyncio.sleep(scan_interval)

            _LOGGER.debug(f"Running periodic device discovery (interval: {scan_interval}s)")

            # Perform UDP discovery
            ip_list_config = entry.data.get("ip", [])
            subnets_config = entry.data.get("subnets", [])

            discovered_ips = await hass.async_add_executor_job(get_ip)

            # Scan user-configured subnets (for cross-subnet discovery)
            subnet_ips = []
            if subnets_config:
                for subnet in subnets_config:
                    try:
                        ips = await scan_subnet_async(subnet, timeout=1.0)
                        subnet_ips.extend(ips)
                    except Exception as e:
                        _LOGGER.debug(f"Error scanning subnet {subnet} in periodic discovery: {e}")

            all_ips = set(discovered_ips + ip_list_config + subnet_ips)

            data = hass.data[DOMAIN][entry.entry_id]
            last_scan_ips = data.get("last_scan_ips", set())

            # Check for new devices
            new_ips = all_ips - last_scan_ips
            if new_ips:
                _LOGGER.info(f"Found new devices: {new_ips}")

                for ip in new_ips:
                    try:
                        device = CozyLifeDevice(ip)
                        if await device.async_connect():
                            device_manager.add_device(device)
                            device_manager.register_device(device)
                            data["tcp_clients"].append(device)
                            _LOGGER.info(f"Successfully connected to new device at {ip}")

                            # Reload platforms to add new entities
                            await hass.config_entries.async_reload(entry.entry_id)
                        else:
                            _LOGGER.warning(f"Failed to connect to new device at {ip}")
                    except Exception as e:
                        _LOGGER.error(f"Error connecting to new device {ip}: {e}")

            # Check for devices that disappeared
            disappeared_ips = last_scan_ips - all_ips
            if disappeared_ips:
                _LOGGER.info(f"Devices no longer available: {disappeared_ips}")
                for device in device_manager.get_all_devices():
                    if device._ip in disappeared_ips:
                        await device.async_disconnect()
                        device_manager.remove_device(device.device_id)

            # Update last scan IPs
            data["last_scan_ips"] = all_ips

            # Check device availability
            for device in device_manager.get_all_devices():
                if not device.is_available:
                    try:
                        _LOGGER.debug(f"Attempting to reconnect to {device._ip}")
                        await device.async_connect()
                    except Exception as e:
                        _LOGGER.debug(f"Reconnection attempt failed: {e}")

        except asyncio.CancelledError:
            _LOGGER.debug("Periodic discovery task cancelled")
            break
        except Exception as e:
            _LOGGER.error(f"Error in periodic discovery: {e}")
