# -*- coding: utf-8 -*-
import json
import time
import requests
import logging

_LOGGER = logging.getLogger(__name__)


def get_sn() -> str:
    """
    message sn
    :return: str
    """
    return str(int(round(time.time() * 1000)))


# cache get_pid_list result for many calls
_CACHE_PID = []


def get_pid_list(lang='en') -> list:
    """
    http://doc.doit/project-12/doc-95/
    :param lang:
    :return:
    """
    global _CACHE_PID
    if len(_CACHE_PID) != 0:
        return _CACHE_PID
    
    domain = 'api-us.doiting.com'
    protocol = 'http'
    url_prefix = protocol + '://' + domain
    res = requests.get(url_prefix + '/api/device_product/model', {
        'lang': lang
    }, timeout=3)
    
    if 200 != res.status_code:
        _LOGGER.info('get_pid_list.result is none')
        return []
    try:
        pid_list = json.loads(res.content, encoding='utf-8')
    except:
        _LOGGER.info('get_pid_list.result is not json')
        return []
    
    if pid_list.get('ret') is None:
        return []
    
    if '1' != pid_list['ret']:
        return []
    
    if pid_list.get('info') is None or type(pid_list.get('info')) is not dict:
        return []
    
    if pid_list['info'].get('list') is None or type(pid_list['info']['list']) is not list:
        return []
    
    _CACHE_PID = pid_list['info']['list']
    return _CACHE_PID
