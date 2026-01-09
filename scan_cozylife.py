#!/usr/bin/env python3
"""
Simple script to scan IP range for CozyLife devices.
Usage: python scan_cozylife.py <IP_RANGE>
Example: python scan_cozylife.py 192.168.123.0/24
         python scan_cozylife.py 192.168.123.1-254
"""

import socket
import json
import time
import sys
import ipaddress


def get_sn():
    """Generate message serial number (timestamp)"""
    return str(int(round(time.time() * 1000)))


def check_cozylife_device(ip, port=5555, timeout=2):
    """
    Check if an IP address is a CozyLife device.
    Returns device info dict if found, None otherwise.
    """
    try:
        # Connect to device
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Send CMD_INFO command
        message = {
            'cmd': 0,
            'pv': 0,
            'sn': get_sn(),
            'msg': {}
        }
        payload = json.dumps(message, separators=(',', ':')) + "\r\n"
        sock.send(payload.encode('utf-8'))

        # Receive response
        response = sock.recv(1024).decode('utf-8').strip()
        sock.close()

        # Parse response
        resp_json = json.loads(response)

        # Check if it's a valid CozyLife device response
        if (resp_json.get('msg') and
            isinstance(resp_json['msg'], dict) and
            resp_json['msg'].get('did') and
            resp_json['msg'].get('pid')):
            return resp_json['msg']

    except (socket.timeout, socket.error, json.JSONDecodeError, KeyError) as e:
        pass

    return None


def parse_ip_range(ip_range):
    """
    Parse IP range string into list of IP addresses.
    Supports CIDR notation (192.168.1.0/24) or range (192.168.1.1-254)
    """
    ips = []

    # Try CIDR notation first
    if '/' in ip_range:
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            ips = [str(ip) for ip in network.hosts()]
        except ValueError:
            print(f"Error: Invalid CIDR notation: {ip_range}")
            sys.exit(1)

    # Try range notation (e.g., 192.168.1.1-254)
    elif '-' in ip_range:
        try:
            base_ip, end = ip_range.rsplit('.', 1)
            start_part, end_part = end.split('-')
            base_parts = base_ip.split('.')

            if len(base_parts) != 3:
                raise ValueError("Invalid range format")

            start = int(start_part)
            end_val = int(end_part)

            for i in range(start, end_val + 1):
                ips.append(f"{base_ip}.{i}")
        except (ValueError, IndexError):
            print(f"Error: Invalid range notation: {ip_range}")
            sys.exit(1)

    # Single IP
    else:
        try:
            ipaddress.ip_address(ip_range)
            ips = [ip_range]
        except ValueError:
            print(f"Error: Invalid IP address: {ip_range}")
            sys.exit(1)

    return ips


def main():
    if len(sys.argv) != 2:
        print("Usage: python scan_cozylife.py <IP_RANGE>")
        print("Examples:")
        print("  python scan_cozylife.py 192.168.123.0/24")
        print("  python scan_cozylife.py 192.168.123.1-254")
        print("  python scan_cozylife.py 192.168.123.151")
        sys.exit(1)

    ip_range = sys.argv[1]
    ips = parse_ip_range(ip_range)

    print(f"Scanning {len(ips)} IP addresses for CozyLife devices...")
    print()

    found_devices = []

    for ip in ips:
        print(f"Checking {ip}...", end=' ', flush=True)
        device_info = check_cozylife_device(ip)

        if device_info:
            print("✓ FOUND")
            found_devices.append((ip, device_info))
            print(f"  Serial Number: {device_info.get('did', 'N/A')}")
            print(f"  Product ID: {device_info.get('pid', 'N/A')}")
            print(f"  MAC: {device_info.get('mac', 'N/A')}")
            print(f"  IP: {device_info.get('ip', ip)}")
            print()
        else:
            print("✗")

    print()
    print(f"Scan complete. Found {len(found_devices)} CozyLife device(s)")
    print()

    if found_devices:
        print("# Copy-paste this into your configuration.yaml:")
        print("hass_cozylife_local_pull:")
        print("  lang: en")
        print("  devices:")
        for ip, info in found_devices:
            serial_number = info.get('did', 'N/A')
            print(f"    - serial_number: {serial_number}")
            print(f"      alias: Device_{serial_number[-4:]}")
            print(f"      ip: {ip}")
        print()
    else:
        print("No devices found.")


if __name__ == '__main__':
    main()
