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
```
hass_cozylife_local_pull:
   lang: en
   ip:
     - "192.168.1.99"
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
