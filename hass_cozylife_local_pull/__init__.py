"""Example Load Platform integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import logging
from .const import (
    DOMAIN
)
from .udp_discover import get_ip
from .tcp_client import tcp_client

_LOGGER = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    ip = get_ip()
    hass.data[DOMAIN] = {
        'temperature': 24,
        'ip': ip,
        'tcp_client': [tcp_client(item) for item in ip],
    }
    _LOGGER.info('setup')
    # _LOGGER.info('setup', hass, config)
    # hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('light', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)
    
    return True
