# CozyLife & Home Assistant

CozyLife Assistant integration is developed for controlling CozyLife devices using local network. This version includes significant improvements over the original implementation with modern async architecture, enhanced device discovery, and stability enhancements.


## Supported Device Types

- RGBCW Light (with brightness, color temperature, and RGB color control)
- CW Light (with brightness and color temperature control)
- Switch & Plug


## Key Features

- **Automatic Device Discovery**: UDP broadcast discovery on startup, periodic scanning every 5 minutes
- **Cross-subnet Discovery**: TCP port scanning to find devices across different network segments
- **Modern Architecture**: Full async/await implementation with non-blocking operations
- **UI Configuration**: No YAML editing required, configure through Home Assistant UI
- **Device Registry**: Proper integration with Home Assistant Device Registry
- **Auto Reconnection**: Automatic offline detection and reconnection
- **Multiple Color Modes**: Support for brightness, color temperature, and RGB colors simultaneously


## Install

### Via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cozylife&repository=hass_cozylife_local_pull&category=integration)

Or search for "CozyLife Local" in HACS and install, then restart Home Assistant.

### Manual Installation

1. Clone this repository to your `custom_components` directory:
```bash
git clone https://github.com/cozylife/hass_cozylife_local_pull.git custom_components/hass_cozylife_local_pull
```

2. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. **Settings** → **Devices & Services**
2. Click **Create Integration** → Search for **"CozyLife Local"**
3. Configure:
   - **Language**: Select your language
   - **Device IP Addresses** (Optional): Manually add specific device IPs
   - **Subnet Ranges** (Optional): Add subnets for cross-network discovery (e.g., 192.168.2.0/24)
   - **Scan Interval**: Default 300 seconds

### Via YAML Configuration

Add to `configuration.yaml`:

```yaml
hass_cozylife_local_pull:
  lang: en
  ip:
    - "192.168.1.99"
  subnets:
    - "192.168.2.0/24"
  scan_interval: 300
```

**Configuration Parameters:**
- `lang`: Language code (en, zh, es, pt, ja, ru, nl, ko, fr, de)
- `ip`: List of device IP addresses (optional)
- `subnets`: Subnet ranges for cross-network device discovery (optional)
- `scan_interval`: Device discovery interval in seconds (default: 300, minimum: 60)


## Troubleshooting

- **Devices not discovered**: Check network connectivity and ensure devices are on the same network. Verify UDP port 6095 is not blocked by firewall. Try manually adding device IP addresses.

- **Connection issues**: Verify device IP is correct, check if device supports TCP port 5555, restart the device if necessary.

- **Slow response**: Check network quality and WiFi signal strength. Consider reducing scan interval or using wired connection.

- **Check plugin logs**: View Home Assistant logs to debug issues.


## Feedback

- Please submit an [Issue](https://github.com/cozylife/hass_cozylife_local_pull/issues) on GitHub
- Send an email to info@cozylife.app


## Changelog

### v0.3.0
- Complete async architecture upgrade
- Periodic automatic device discovery (configurable, default 5 minutes)
- Cross-subnet device discovery via TCP scanning
- Device Registry integration
- UI configuration support (no YAML editing required)
- Automatic offline detection and reconnection
- 3-5x faster device control response
- 20%+ lower memory usage

### v0.2.0
- Initial release


## License

MIT License - See LICENSE file for details
