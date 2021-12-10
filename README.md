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
```


### Feedback
* Please submit an issue
* Send an email with the subject of hass support to info@cozylife.app


### TODO
- Compatible with python3.9
- Sending broadcasts regularly has reached the ability to discover devices at any time
- TCP reconnect