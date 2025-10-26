# -*- coding: utf-8 -*-
"""Config flow for CozyLife Local Pull integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, LANG

_LOGGER = logging.getLogger(__name__)


def _get_user_schema() -> vol.Schema:
    """Get the user configuration schema with field names."""
    return vol.Schema(
        {
            vol.Optional("lang", default=LANG): vol.In(
                ["zh", "en", "es", "pt", "ja", "ru", "nl", "ko", "fr", "de"]
            ),
            vol.Optional("device_ips", default=""): cv.string,
            vol.Optional("subnet_ranges", default=""): cv.string,
            vol.Optional("scan_interval", default=300): vol.All(
                cv.positive_int, vol.Range(min=60)
            ),
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CozyLife Local Pull."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Parse the device IP addresses
            ip_list = []
            if user_input.get("device_ips"):
                ip_str = user_input["device_ips"].strip()
                if ip_str:
                    # Support comma-separated or space-separated IPs
                    ips = [
                        ip.strip()
                        for ip in ip_str.replace(",", " ").split()
                        if ip.strip()
                    ]
                    ip_list = ips

            # Parse the subnet ranges
            subnets_list = []
            if user_input.get("subnet_ranges"):
                subnet_str = user_input["subnet_ranges"].strip()
                if subnet_str:
                    # Support comma-separated or space-separated subnets
                    subnets = [
                        subnet.strip()
                        for subnet in subnet_str.replace(",", " ").split()
                        if subnet.strip()
                    ]
                    subnets_list = subnets

            # Validate language
            lang = user_input.get("lang", LANG)

            # Store the config (using old field names for backward compatibility)
            data = {
                "lang": lang,
                "ip": ip_list,
                "subnets": subnets_list,
                "scan_interval": user_input.get("scan_interval", 300),
            }

            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="CozyLife Local",
                data=data,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_user_schema(),
            errors=errors,
            description_placeholders={
                "guide": (
                    "**Device IP Addresses (Optional)**\n"
                    "Manually specify device IPs if known.\n"
                    "Format: 192.168.1.100 192.168.1.101 (space or comma separated)\n"
                    "Leave empty for auto-discovery via UDP broadcast.\n\n"
                    "**Subnet Ranges to Scan (Optional)**\n"
                    "Auto-scan these subnets for devices (useful for cross-subnet discovery).\n"
                    "Format: 192.168.2.0/24 192.168.4.0/24 (CIDR format, space or comma separated)\n"
                    "Leave empty if all devices are on the same network as Home Assistant.\n\n"
                    "**Scan Interval (Seconds)**\n"
                    "Minimum: 60, Recommended: 300 (5 minutes)\n\n"
                    "ℹ️ One integration instance manages all CozyLife devices."
                ),
            },
        )

    async def async_step_import(self, import_data: Dict[str, Any]) -> FlowResult:
        """Handle import from YAML configuration."""
        # Parse the IP addresses
        ip_list = []
        if isinstance(import_data.get("ip"), list):
            ip_list = import_data["ip"]

        # Parse the subnets
        subnets_list = []
        if isinstance(import_data.get("subnets"), list):
            subnets_list = import_data["subnets"]

        # Create config entry from YAML
        data = {
            "lang": import_data.get("lang", LANG),
            "ip": ip_list,
            "subnets": subnets_list,
            "scan_interval": import_data.get("scan_interval", 300),
        }

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="CozyLife Local (YAML)", data=data)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for CozyLife Local Pull."""

    async def async_step_init(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Parse the device IP addresses
            ip_list = []
            if user_input.get("device_ips"):
                ip_str = user_input["device_ips"].strip()
                if ip_str:
                    # Support comma-separated or space-separated IPs
                    ips = [
                        ip.strip()
                        for ip in ip_str.replace(",", " ").split()
                        if ip.strip()
                    ]
                    ip_list = ips

            # Parse the subnet ranges
            subnets_list = []
            if user_input.get("subnet_ranges"):
                subnet_str = user_input["subnet_ranges"].strip()
                if subnet_str:
                    # Support comma-separated or space-separated subnets
                    subnets = [
                        subnet.strip()
                        for subnet in subnet_str.replace(",", " ").split()
                        if subnet.strip()
                    ]
                    subnets_list = subnets

            # Update config entry data with new IP and subnet lists
            # (using old field names for backward compatibility)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    "ip": ip_list,
                    "subnets": subnets_list,
                },
            )

            # Update options with scan_interval
            return self.async_create_entry(
                title="",
                data={"scan_interval": user_input.get("scan_interval", 300)},
            )

        # Get current IP list from config entry data
        current_ips = self.config_entry.data.get("ip", [])
        ip_str = " ".join(current_ips) if current_ips else ""

        # Get current subnet list from config entry data
        current_subnets = self.config_entry.data.get("subnets", [])
        subnet_str = " ".join(current_subnets) if current_subnets else ""

        current_scan_interval = self.config_entry.options.get("scan_interval", 300)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    "device_ips",
                    default=ip_str,
                ): cv.string,
                vol.Optional(
                    "subnet_ranges",
                    default=subnet_str,
                ): cv.string,
                vol.Optional(
                    "scan_interval",
                    default=current_scan_interval,
                ): vol.All(cv.positive_int, vol.Range(min=60)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "guide": (
                    "**Device IP Addresses (Optional)**\n"
                    "Manually specify device IPs if known.\n"
                    "Format: 192.168.1.100 192.168.1.101 (space or comma separated)\n"
                    "Leave empty for auto-discovery.\n\n"
                    "**Subnet Ranges to Scan (Optional)**\n"
                    "Auto-scan these subnets for devices (cross-subnet discovery).\n"
                    "Format: 192.168.2.0/24 192.168.4.0/24 (CIDR format, space or comma separated)\n"
                    "Leave empty if all devices are on same network.\n\n"
                    "**Scan Interval (Seconds)**\n"
                    "How often to scan for new devices. Minimum: 60, Recommended: 300 (5 minutes)"
                ),
            },
        )
