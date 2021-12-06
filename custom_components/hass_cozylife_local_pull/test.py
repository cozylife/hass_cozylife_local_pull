# -*- coding: utf-8 -*-
import socket
import time
from utils import get_sn
import logging


_LOGGER = logging.getLogger(__name__)

def get_ip() -> list:
    """
    get device ip
    :return: list
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # server.bind(('192.168.123.1', 0))
    # Enable broadcasting mode
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.1)
    socket.setdefaulttimeout(0.1)
    message = '{"cmd":0,"pv":0,"sn":"' + get_sn() + '","msg":{}}'
    
    i = 0
    while i < 3:
        # server.sendto(bytes(message, encoding='utf-8'), ('<broadcast>', 6095))
        server.sendto(bytes(message, encoding='utf-8'), ('255.255.255.255', 6095))
        time.sleep(0.03)
        i += 1
    
    i = 255
    ip = []
    while i > 0:
        try:
            data, addr = server.recvfrom(1024)
        except:
            _LOGGER.info('udp timeout')
            break
        _LOGGER.info(f'udp.receiver:{addr[0]}')
        if addr[0] not in ip: ip.append(addr[0])
        i -= 1
    
    return ip

ip_list = get_ip()
print(ip_list)
