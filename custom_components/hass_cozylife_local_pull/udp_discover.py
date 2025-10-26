import socket
import time
import ipaddress
import asyncio
from .utils import get_sn
import logging


_LOGGER = logging.getLogger(__name__)

"""
discover device
"""


async def scan_subnet_async(subnet: str, timeout: float = 1.0) -> list:
    """
    Scan a subnet for CozyLife devices by attempting TCP connection.

    Args:
        subnet: CIDR notation subnet (e.g., '192.168.2.0/24')
        timeout: Connection timeout in seconds

    Returns:
        List of IP addresses where CozyLife devices were found
    """
    found_ips = []

    try:
        # Parse the subnet
        network = ipaddress.ip_network(subnet, strict=False)
        _LOGGER.info(f"Scanning subnet {subnet} ({network.num_addresses} hosts)")

        # Create tasks for all IPs in the subnet
        tasks = []
        for ip in network.hosts():  # Skip network and broadcast addresses
            tasks.append(_check_device_at_ip(str(ip), timeout))

        # Run all checks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for ip, found in zip([str(ip) for ip in network.hosts()], results):
            if found is True:
                found_ips.append(ip)
                _LOGGER.info(f"Found CozyLife device at {ip}")

    except ValueError as e:
        _LOGGER.error(f"Invalid subnet format '{subnet}': {e}")
    except Exception as e:
        _LOGGER.error(f"Error scanning subnet {subnet}: {e}")

    return found_ips


async def _check_device_at_ip(ip: str, timeout: float = 1.0) -> bool:
    """
    Check if there's a CozyLife device at the given IP by attempting TCP connection.

    Args:
        ip: IP address to check
        timeout: Connection timeout in seconds

    Returns:
        True if device found, False otherwise
    """
    try:
        # Try to connect to TCP port 5555 (CozyLife device port)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, 5555),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False
    except Exception:
        return False


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

    # max tries before first data received
    max = 5
    i = 0
    while i < max:
        i += 1
        try:
            data, addr = server.recvfrom(1024, socket.MSG_PEEK)
        except Exception as err:
            _LOGGER.info(f'{i}/{max} try, udp timeout')
            continue
        _LOGGER.info(f'first udp.receiver:{addr[0]}')
        break
    else:
        _LOGGER.warning('cannot find any device')
        return []
    
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
