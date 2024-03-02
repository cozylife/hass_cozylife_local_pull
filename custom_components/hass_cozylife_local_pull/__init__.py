"""Example Load Platform integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
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
    TODO:timer discover
    config:{'lang': 'zh', 'ip': ['192.168.5.201', '192.168.5.202', '192.168.5.1']}
}
    """
    ip = get_ip()
    ip_from_config = config[DOMAIN].get('ip') if config[DOMAIN].get('ip') is not None else []    
    ip += ip_from_config
    ip_list = []
    [ip_list.append(i) for i in ip if i not in ip_list]

    if 0 == len(ip_list):
        _LOGGER.info('discover nothing')
        return True

    _LOGGER.info('try conncet ip_list:', ip_list)
    lang_from_config = (config[DOMAIN].get('lang') if config[DOMAIN].get('lang') is not None else LANG)
    get_pid_list(lang_from_config)

    hass.data[DOMAIN] = {
        'temperature': 24,
        'ip': ip_list,
        'tcp_client': [tcp_client(item) for item in ip_list],
    }

    #wait for get device info from tcp conncetion
    #but it is bad
    time.sleep(3)
    # _LOGGER.info('setup', hass, config)
    # hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('light', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)
    
    return True
