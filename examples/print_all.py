"""
    Description: Print all hubble am2 modbus registers
    Author:     Alberto da Silva
    Date:       10 Aug 2022
"""

import sys
import logging
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
    # this is done ouside of the AM2battery class so you can adjust any serial settings
    instrument = minimalmodbus.Instrument(port=port, slaveaddress=1, debug=False, close_port_after_each_call=True)
    instrument.serial.baudrate = 9600
    print(f"modbus serial instrument={instrument}")

    # create an AM2battery object
    battery = am2.AM2battery(instrument, know_registers_only=False)

    print("Reading AM2 registers...")
    battery.read_battery()

    print("version information")
    version=battery.get_string('Version')
    sn_bms=battery.get_string('S_N_BMS')
    sn_pack=battery.get_string('S_N_Pack')

    print(f"AM2battery: battery_address={instrument.address}, all_registers=True")
    print(f"Version={version}")
    print(f"S_N_BMS={sn_bms}")
    print(f"S_N_Pack={sn_pack}")
    print(f"AM2_READ_RETRY={am2.AM2_READ_RETRY}, AM2_READ_DELAY={am2.AM2_READ_DELAY:0.2f}")
    print("")

    # this is useful to decide a register type
    print(" id name                          scaled unit factor    HEX   uint    int   f/10  f/100 f/1000  fs/100 char2")
    for key in range(am2.AM2_NUMBER_OF_REGISTERS):
        reg=battery.register_data[key]
        print(f"{reg.register_address:3} {reg.name:15} {reg.register_scaled:20} {reg.unit:4} "
              f"{am2.get_factor(reg.register_address):6} "
              f"0x{reg.register_raw:04x} "
              f"{am2.scale_raw_register('uint',reg.register_raw, reg.register_scaled):6d} "
              f"{am2.scale_raw_register('int',reg.register_raw, reg.register_scaled):6} "
              f"{am2.scale_raw_register('f10',reg.register_raw, reg.register_scaled):6.1f} "
              f"{am2.scale_raw_register('f100',reg.register_raw, reg.register_scaled):6.2f} "
              f"{am2.scale_raw_register('f1000',reg.register_raw, reg.register_scaled):6.3f} "
              f"{am2.scale_raw_register('f100s',reg.register_raw, reg.register_scaled):7.2f} "
              f"'{am2.scale_raw_register('char2',reg.register_raw, reg.register_scaled):2}'")

if __name__ == "__main__":
    main()
