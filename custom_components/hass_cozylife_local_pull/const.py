DOMAIN = "hass_cozylife_local_pull"

# http://doc.doit/project-5/doc-8/
SWITCH_TYPE_CODE = '00'
LIGHT_TYPE_CODE = '01'
SUPPORT_DEVICE_CATEGORY = [SWITCH_TYPE_CODE, LIGHT_TYPE_CODE]

# http://doc.doit/project-5/doc-8/
SWITCH = '1'
WORK_MODE = '2'
TEMP = '3'
BRIGHT = '4'
HUE = '5'
SAT = '6'

LIGHT_DPID = [SWITCH, WORK_MODE, TEMP, BRIGHT, HUE, SAT]
SWITCH_DPID = [SWITCH, ]
