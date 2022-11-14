"""
    Description: Print all hubble am2 modbus registers
    Author:     Alberto da Silva
    Date:       10 Aug 2022
"""

import sys
import logging
import json
import minimalmodbus
import hubble_lithium_am2 as am2

def main() -> None:
    """test code"""

    # if argv[1] supplied, then use that as the port
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "/dev/ttyUSB1"

    logging.basicConfig(level=logging.DEBUG)

    # open the instrument aka device
    # this is done ouside of the AM2_battery class so you can adjust any serial settings
    instrument = minimalmodbus.Instrument(port=port, slaveaddress=1, debug=False, close_port_after_each_call=True)
    instrument.serial.baudrate = 9600
    print(f"modbus serial instrument={instrument}")
    
    # create an AM2battery object
    battery = am2.AM2battery(instrument)

    print("Reading AM2 registers...")
    battery.read_battery()

    sep = ""
    print("{")
    for key, reg in battery:
        print(sep, key, ":", reg, end="")
        sep = ",\n"
    print("\n}")

if __name__ == "__main__":
    main()
