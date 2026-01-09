# CozyLife & Home Assistant

CozyLife Assistant integration is developed for controlling CozyLife devices using local net, officially
maintained by the CozyLife Team.


## Supported Device Types

- RGBCW Light
- CW Light
- Switch & Plug


## Install

* A home assistant environment that can access the external network
* clone the repo to the custom_components directory
* configuration.yaml

### Configuration

#### Step 1: Scan Your Network

Use the provided scanning script to find all CozyLife devices on your network:

```bash
python3 scan_cozylife.py 192.168.123.0/24 192.168.123.0/24
```

Or scan a specific range:
```bash
python3 scan_cozylife.py 192.168.123.130-170 192.168.123.130-170
```

The script will output a ready-to-use configuration block that you can copy-paste into your `configuration.yaml`.

#### Step 2: Add Configuration to Home Assistant

Copy the generated configuration into your `configuration.yaml`:

```yaml
hass_cozylife_local_pull:
  lang: en
  devices:
    - serial_number: 767941640050c2edda8b
      alias: Living Room Light
      ip: 192.168.123.151
    - serial_number: 629168597cb94c4c1d8f
      alias: Bedroom Switch
      ip: 192.168.123.158
    - serial_number: 767953670050c2856f66
      alias: Kitchen Light
      ip: 192.168.123.159
```

**Configuration Fields:**
- `lang` (optional): Language for device names. Default: `en`
- `devices` (required): List of device configurations
  - `serial_number` (required): The unique device serial number
  - `alias` (required): Friendly name for the device in Home Assistant
  - `ip` (required): IP address of the device

**Note:** IP addresses must be hard-coded in the configuration. If a device's IP changes (e.g., due to DHCP), you'll need to rescan the network and update the configuration.

#### Legacy Configuration (UDP Discovery + Explicit IPs)

For backward compatibility, you can still use the old format:

```yaml
hass_cozylife_local_pull:
   lang: en
   ip:
     - "192.168.1.99"
     - "192.168.1.100"
```


### Feedback
* Please submit an issue
* Send an email with the subject of hass support to info@cozylife.app

### Troubleshoot
* Check whether the internal network isolation of the router is enabled
* Check if the plugin is in the right place
* Restart HASS multiple times
* View the output log of the plugin
* It is currently the first version of the plugin, there may be problems that cannot be found


### TODO
- Sending broadcasts regularly has reached the ability to discover devices at any time
- Support sensor device

### PROGRESS
- None
