"""
Description: Print all hubble am2 modbus registers
Author: Alberto da Silva
Date: 10 Aug 2022
"""

import minimalmodbus
import hubble_lithium_am2 as am2

"""test code"""

# open the instrument aka device
# this is done ouside of the AM2_Pack class so you can adjust any serial settings
instrument = minimalmodbus.Instrument(port="/dev/ttyUSB1", slaveaddress=1, debug=False, close_port_after_each_call=True)
instrument.serial.baudrate = 9600
print(f"modbus serial instrument={instrument}")
    
# create an AM2_Pack object
pack = am2.AM2_Pack(instrument)

print("Reading AM2 registers...")
pack.read_pack()

result_dict = dict(pack)
print(result_dict)
