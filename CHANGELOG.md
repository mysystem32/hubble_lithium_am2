# Changelog

All notable changes to hubble_lithium_am2 are documented in this file.

## 0.9.0 (`main`)

Initial public release

## 0.9.1 (`main`)

Bug fix in min/max caculation
Rename some variables to make more readable
Add some AM2_REGISTER constants to make more readable

## 0.9.2 (`main`)

Rename:  
- pack to battery
- MOS_T to T_MOSFET
- ENV_T to T_ENV
- BMS_S_N to S_N_BMS
- PACK_S_N to S_N_Pack
- MOS_T to T_MOSFET
- ENV_T to T_ENV
- etc

Using the same prefix allows better sorting/grouping in Home Assistant

Make reading strings from AM2 more robust  
Track read errors on RS485/modbus via global am2_read_count and am2_read_errors

New example [am2_to_mqtt.py](/examples/am2_to_mqtt.py)  
Example utility to read AM2 and send register data to mqtt.  
Supports Home Assistant MQTT discovery