"""
    Description: Print all hubble am2 modbus registers
    Author:     Alberto da Silva
    Date:       10 Aug 2022
"""

import sys
import logging
import json
import argparse

import minimalmodbus
import hubble_lithium_am2 as am2

# https://github.com/dreadnought/python-daly-bms/blob/main/bin/daly-bms-cli

def setup() -> None:
    """setup code"""

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--device",
                    help="RS485 device, e.g. /dev/ttyUSB1",
                    type=str, required=True)

    parser.add_argument("--mqtt", help="Write output to MQTT", action="store_true")

    parser.add_argument("--mqtt-hass", help="MQTT Home Assistant Mode", action="store_true")

    parser.add_argument("--mqtt-topic",
                    help="MQTT topic to write to. default hubble_am2",
                    type=str,
                    default="hubble_am2")

    parser.add_argument("--mqtt-broker",
                    help="MQTT broker (server). default localhost",
                    type=str,
                    default="localhost")

    parser.add_argument("--mqtt-port",
                    help="MQTT port. default 1883",
                    type=int,
                    default=1883)

    parser.add_argument("--mqtt-user",
                    help="Username to authenticate MQTT with",
                    type=str)

    parser.add_argument("--mqtt-password",
                    help="Password to authenticate MQTT with",
                    type=str)

    args = parser.parse_args()

   
    logging.basicConfig(level=logging.DEBUG)

    # open the instrument aka device
    # this is done ouside of the AM2_Pack class so you can adjust any serial settings
    instrument = minimalmodbus.Instrument(port=args.device, slaveaddress=1, debug=False, close_port_after_each_call=True)
    instrument.serial.baudrate = 9600
    print(f"modbus serial instrument={instrument}")
    

def main() -> None:

    # if argv[1] supplied, then use that as the port
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "/dev/ttyUSB1"

    
    # create an AM2_Pack object
    pack = am2.AM2_Pack(instrument)

    print("Reading AM2 registers...")
    pack.read_pack()

    result_dict = dict(pack)
    result_json = json.dumps(result_dict, indent=4) # add default=vars for "private" class variables

    print(result_json)

if __name__ == "__main__":
    main()
# https://github.com/dreadnought/python-daly-bms

# daly-bms-cli --help
usage: daly-bms-cli [-h] -d DEVICE -a ADDRESS [--sleep SLEEP] [--mqtt] [--mqtt-hass] [--mqtt-topic MQTT_TOPIC] [--mqtt-broker MQTT_BROKER] [--mqtt-port MQTT_PORT] [--mqtt-user MQTT_USER] [--mqtt-password MQTT_PASSWORD]

if SLEEP < 10 SLEEP=10
if SLEEP > 120 SLEEP = 120
