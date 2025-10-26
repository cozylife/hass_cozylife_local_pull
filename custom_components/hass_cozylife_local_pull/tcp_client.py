# -*- coding: utf-8 -*-
"""TCP client for CozyLife Local Pull integration."""
from __future__ import annotations

import asyncio
import json
import socket
from typing import Any, Dict, Optional, Union

import logging

from .utils import get_pid_list, get_sn

_LOGGER = logging.getLogger(__name__)

CMD_INFO = 0
CMD_QUERY = 2
CMD_SET = 3
CMD_LIST = [CMD_INFO, CMD_QUERY, CMD_SET]


class CozyLifeDevice:
    """
    Represents a CozyLife device with async support.

    Protocol examples:
    send:{"cmd":0,"pv":0,"sn":"1636463553873","msg":{}}
    receiver:{"cmd":0,"pv":0,"sn":"1636463553873","msg":{"did":"629168597cb94c4c1d8f","dtp":"02","pid":"e2s64v",
    "mac":"7cb94c4c1d8f","ip":"192.168.123.57","rssi":-33,"sv":"1.0.0","hv":"0.0.1"},"res":0}
    """

    def __init__(self, ip: str) -> None:
        """Initialize the device."""
        self._ip = ip
        self._port = 5555
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._is_available = False

        # Device info
        self._device_id: str = ""
        self._pid: str = ""
        self._device_type_code: str = ""
        self._icon: str = ""
        self._device_model_name: str = ""
        self._dpid: list = []
        self._sn: str = ""
        self._software_version: str = "Unknown"
    @property
    def is_available(self) -> bool:
        """Return whether the device is available."""
        return self._is_available

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._device_id

    @property
    def device_type_code(self) -> str:
        """Return the device type code."""
        return self._device_type_code

    @property
    def device_model_name(self) -> str:
        """Return the device model name."""
        return self._device_model_name

    @property
    def icon(self) -> str:
        """Return the device icon."""
        return self._icon

    @property
    def dpid(self) -> list:
        """Return the device DPID list."""
        return self._dpid

    @property
    def pid(self) -> str:
        """Return the device PID."""
        return self._pid

    @property
    def software_version(self) -> str:
        """Return the software version."""
        return self._software_version

    async def async_connect(self) -> bool:
        """Connect to the device asynchronously."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._ip, self._port),
                timeout=10.0,
            )
            await self._async_device_info()
            self._is_available = True
            _LOGGER.info(f"Connected to device at {self._ip}")
            return True
        except asyncio.TimeoutError:
            _LOGGER.warning(f"Timeout connecting to {self._ip}")
            self._is_available = False
            return False
        except Exception as e:
            _LOGGER.error(f"Failed to connect to {self._ip}: {e}")
            self._is_available = False
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                _LOGGER.error(f"Error closing connection: {e}")
        self._reader = None
        self._writer = None
        self._is_available = False

    async def _async_device_info(self) -> None:
        """Get device information asynchronously."""
        try:
            response = await self._async_send_receive(CMD_INFO, {})
            if not response or not response.get("msg"):
                _LOGGER.warning("Invalid device info response")
                return

            msg = response["msg"]
            self._device_id = msg.get("did", "")
            self._pid = msg.get("pid", "")
            self._software_version = msg.get("sv", "Unknown")

            if not self._device_id or not self._pid:
                _LOGGER.warning("Missing device ID or PID")
                return

            # Get product information
            pid_list = await asyncio.get_event_loop().run_in_executor(
                None, get_pid_list
            )

            for item in pid_list:
                if item.get("m"):
                    for model in item["m"]:
                        if model.get("pid") == self._pid:
                            self._icon = model.get("i", "")
                            self._device_model_name = model.get("n", "")
                            self._dpid = model.get("dpid", [])
                            self._device_type_code = item.get("c", "")
                            _LOGGER.info(
                                f"Device info - ID: {self._device_id}, "
                                f"Model: {self._device_model_name}, "
                                f"Type: {self._device_type_code}"
                            )
                            return

            _LOGGER.warning(
                f"Could not find product info for PID: {self._pid}"
            )
        except Exception as e:
            _LOGGER.error(f"Error getting device info: {e}")
    def _get_package(self, cmd: int, payload: Dict[str, Any]) -> bytes:
        """Package a message for the device."""
        self._sn = get_sn()
        if cmd == CMD_SET:
            message = {
                "pv": 0,
                "cmd": cmd,
                "sn": self._sn,
                "msg": {
                    "attr": [int(item) for item in payload.keys()],
                    "data": payload,
                },
            }
        elif cmd == CMD_QUERY:
            message = {
                "pv": 0,
                "cmd": cmd,
                "sn": self._sn,
                "msg": {"attr": [0]},
            }
        elif cmd == CMD_INFO:
            message = {
                "pv": 0,
                "cmd": cmd,
                "sn": self._sn,
                "msg": {},
            }
        else:
            raise ValueError(f"Invalid CMD: {cmd}")

        payload_str = json.dumps(message, separators=(",", ":"))
        _LOGGER.debug(f"Sending: {payload_str}")
        return bytes(payload_str + "\r\n", encoding="utf-8")

    async def _async_send_receive(
        self, cmd: int, payload: Dict[str, Any], retries: int = 3
    ) -> Dict[str, Any]:
        """Send a command and receive the response asynchronously."""
        if not self._writer or not self._reader:
            _LOGGER.warning("Not connected to device")
            return {}

        async with self._lock:
            try:
                package = self._get_package(cmd, payload)
                self._writer.write(package)
                await self._writer.drain()

                # Read response
                for attempt in range(retries):
                    try:
                        response_data = await asyncio.wait_for(
                            self._reader.readuntil(b"\r\n"), timeout=5.0
                        )
                        response = json.loads(response_data.decode("utf-8").strip())

                        # Verify SN matches
                        if response.get("sn") == self._sn:
                            return response
                    except asyncio.TimeoutError:
                        if attempt < retries - 1:
                            _LOGGER.debug(f"Timeout on attempt {attempt + 1}, retrying...")
                            continue
                        break

                _LOGGER.warning("No valid response received")
                return {}

            except Exception as e:
                _LOGGER.error(f"Error in send_receive: {e}")
                await self.async_disconnect()
                return {}

    async def async_send_only(self, cmd: int, payload: Dict[str, Any]) -> None:
        """Send a command without waiting for response."""
        if not self._writer:
            _LOGGER.warning("Not connected to device")
            return

        try:
            package = self._get_package(cmd, payload)
            self._writer.write(package)
            await self._writer.drain()
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            await self.async_disconnect()

    async def async_query(self) -> Dict[str, Any]:
        """Query the device state."""
        response = await self._async_send_receive(CMD_QUERY, {})
        if response and response.get("msg") and response["msg"].get("data"):
            return response["msg"]["data"]
        return {}

    async def async_control(self, payload: Dict[str, Any]) -> bool:
        """Control the device."""
        try:
            await self.async_send_only(CMD_SET, payload)
            return True
        except Exception as e:
            _LOGGER.error(f"Error controlling device: {e}")
            return False

    # Backward compatibility wrappers for sync code
    def query(self) -> dict:
        """Synchronous query for backward compatibility."""
        _LOGGER.warning(
            "Using sync query() is deprecated, use async_query() instead"
        )
        # This won't work properly in async context, but provides fallback
        return {}

    def control(self, payload: dict) -> bool:
        """Synchronous control for backward compatibility."""
        _LOGGER.warning(
            "Using sync control() is deprecated, use async_control() instead"
        )
        return False


# Backward compatibility alias
tcp_client = CozyLifeDevice