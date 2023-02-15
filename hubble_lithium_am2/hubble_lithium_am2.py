"""
    Description: Read Hubble AM2 Lithium battery BMS registers via RS485/modbus
    Author:      Alberto da Silva
    Date:        10 Aug 2022
    Version:     0.9.0 - initial public release
                 0.9.1 - fix bug in min/max voltage calculation, cleanup code
                 0.9.2 - fix bug in string registers
                        rename pack to battery
                        rename registers to better group
                        Track read errors in read_registers
    License:     MIT
    Copyright:   2022 (c) Alberto da Silva
    DISCLAIMER:  Use at your own risk!
    Terminology:
        pack = Hubble Lithium AM-2 battery (single)
        bank = pack of batteries
    Tested on:   RPI3b with Raspbian 10 (buster), Python 3.7.3
    Device:      USB/RS485
    Library:     minimalmodbus
                 minimalmodbus.Instrument aka device
    AM-2 Registers: 0..180 - many unknown.
    Not sure what BMS is inside an AM-2.
    Google failed to locate any techical information information
    The modbus register ID/value were reverse engineered / comparing to pbmstools
    See test/ folder for displaying all registers

    Terminology:
        names are mostly derived from minimalmodbus
	station_address = Modbus address of the device 1 to 247, 0 = broadcast
                        = instrument.address / Pack_address
	register_address = 0 to 180

    Possible enahancement: use constants/enum for registers
"""

import time
import logging
from ctypes import c_int16
from dataclasses import dataclass

# Globals
logger = logging.getLogger(__name__)

AM2_READ_DELAY = 0.3              # delay beween read retries in seconds
AM2_READ_RETRY = 5                # number of read retries
AM2_NUMBER_OF_REGISTERS = 181     # The AM2 has 180 registers numberd 0..180

AM2_REGISTER_VCELL_START = 15     # Register address of first cell
AM2_REGISTER_VCELL_END = 27       # Register address of end cell
AM2_VCELL_COUNT = AM2_REGISTER_VCELL_END - AM2_REGISTER_VCELL_START


"""There are 180 registers in the Hubble AM2.
dict() of registers that have been 'discovered'
    'name': alphanumerics, underscore and hyphen only for HASS
    'name' is similar to names from PBMS tools
"""
AM2_REGISTERS_DICT = { # dict
    # address: register
        0: {'name':'Current',        'unit':'A',  'factor':'f100s', 'count':1},
        1: {'name':'Voltage',        'unit':'V',  'factor':'f100',  'count':1},
        2: {'name':'SoC',            'unit':'%',  'factor':'uint',  'count':1},
        3: {'name':'SoH',            'unit':'%',  'factor':'uint',  'count':1},
        4: {'name':'Capacity_Remain','unit':'Ah', 'factor':'f100',  'count':1},
        5: {'name':'Capacity_Full',  'unit':'Ah', 'factor':'f100',  'count':1},
        7: {'name':'Cycles',         'unit':'int','factor':'uint',  'count':1},
       15: {'name':'Vcell_01',       'unit':'V',  'factor':'f1000', 'count':1},
       16: {'name':'Vcell_02',       'unit':'V',  'factor':'f1000', 'count':1},
       17: {'name':'Vcell_03',       'unit':'V',  'factor':'f1000', 'count':1},
       18: {'name':'Vcell_04',       'unit':'V',  'factor':'f1000', 'count':1},
       19: {'name':'Vcell_05',       'unit':'V',  'factor':'f1000', 'count':1},
       20: {'name':'Vcell_06',       'unit':'V',  'factor':'f1000', 'count':1},
       21: {'name':'Vcell_07',       'unit':'V',  'factor':'f1000', 'count':1},
       22: {'name':'Vcell_08',       'unit':'V',  'factor':'f1000', 'count':1},
       23: {'name':'Vcell_09',       'unit':'V',  'factor':'f1000', 'count':1},
       24: {'name':'Vcell_10',       'unit':'V',  'factor':'f1000', 'count':1},
       25: {'name':'Vcell_11',       'unit':'V',  'factor':'f1000', 'count':1},
       26: {'name':'Vcell_12',       'unit':'V',  'factor':'f1000', 'count':1},
       27: {'name':'Vcell_13',       'unit':'V',  'factor':'f1000', 'count':1},
       31: {'name':'Tcell_1',        'unit':'°C', 'factor':'f10',   'count':1}, # Avg temp
       32: {'name':'Tcell_2',        'unit':'°C', 'factor':'f10',   'count':1}, # Avg temp
       33: {'name':'Tcell_3',        'unit':'°C', 'factor':'f10',   'count':1}, # Avg temp
       34: {'name':'Tcell_4',        'unit':'°C', 'factor':'f10',   'count':1}, # Avg temp
       35: {'name':'T_MOSFET',       'unit':'°C', 'factor':'f10',   'count':1},
       36: {'name':'T_ENV',          'unit':'°C', 'factor':'f10',   'count':1},

    # String registers - these are only read once
      150: {'name':'Version',        'unit':'str','factor':'char2', 'count':10},
      160: {'name':'S_N_BMS',        'unit':'str','factor':'char2', 'count':10},
      170: {'name':'S_N_Pack',       'unit':'str','factor':'char2', 'count':10},

    # computed registers - not really neccessary
     1000: {'name':'Vcell_max_id',   'unit':'int','factor':'comp',  'count':1},
     1001: {'name':'Vcell_max',      'unit':'V',  'factor':'comp',  'count':1},
     1002: {'name':'Vcell_min_id',   'unit':'int','factor':'comp',  'count':1},
     1003: {'name':'Vcell_min',      'unit':'V',  'factor':'comp',  'count':1},
     1004: {'name':'Vcell_diff',     'unit':'V',  'factor':'comp',  'count':1},
     1005: {'name':'Vcell_avg',      'unit':'V',  'factor':'comp',  'count':1},
     1006: {'name':'Power',          'unit':'W',  'factor':'comp',  'count':1},
     1010: {'name':'Address',        'unit':'int','factor':'comp',  'count':1},
     1011: {'name':'Time',           'unit':'tm', 'factor':'comp',  'count':1}
}


# look up table
AM2_STRING_DICT = {
    'Version'  : 150,
    'S_N_BMS'  : 160,
    'S_N_Pack' : 170
}


def get_name(key: int):
    """return name from the dict()"""
    return AM2_REGISTERS_DICT[key]['name'] if key in AM2_REGISTERS_DICT else "unknown_reg_" + str(key)


def get_unit(key: int):
    """return unit from the dict()"""
    return AM2_REGISTERS_DICT[key]['unit'] if key in AM2_REGISTERS_DICT else "?"


def get_factor(key: int):
    """return factor from the dict()"""
    return AM2_REGISTERS_DICT[key]['factor'] if key in AM2_REGISTERS_DICT else 'null'


def get_count(key: int):
    """return count from the dict()"""
    return AM2_REGISTERS_DICT[key]['count'] if key in AM2_REGISTERS_DICT else 1


def scale_raw_register(factor: str, register_raw: int, register_scaled):
    """return register_scaled = factor(register_raw)"""
    if register_raw is None:
        return register_scaled
    if factor in ('uint', 'null'):
        return int(register_raw) # unsigned int
    if factor == 'f10':
        return round(float(register_raw)/10.0, 1) # divide / 10
    if factor == "f100":
        return round(float(register_raw)/100.0, 2) # divide / 100
    if factor == "f1000":
        return round(float(register_raw)/1000.0, 3) # divide / 1000
    if factor == 'f100s':
        return round(float(c_int16(register_raw).value)/100.0, 2) # signed c_int16 / 100.0
    if factor == 'int':
        return c_int16(register_raw).value # signed c_int16
    if factor == 'char2': # two chars
        result_str=""
        for byte in register_raw.to_bytes(2,'big'):
            if byte < 32 or byte > 126: # non-printable ascii
                result_str = result_str + '?'
            else:
                result_str = result_str + chr(byte)
        return result_str

    return round(register_raw, 3)


# track reads and errors.
# If you experience high number of errors, you may need 120Ω termination resistor on the cable
AM2_READ_COUNT = 0
AM2_READ_ERRORS = 0

def get_read_count():
    return AM2_READ_COUNT

def get_read_errors():
    return AM2_READ_ERRORS

def read_registers(instrument, register_address: int, number_of_registers: int = 1) -> list:
    """ read count registers = returns a List """
    global AM2_READ_COUNT, AM2_READ_ERRORS
    for _ in range(AM2_READ_RETRY):
        AM2_READ_COUNT += 1
        try:
            raw_result = instrument.read_registers(registeraddress=register_address, number_of_registers=number_of_registers) # LIST
            return raw_result
        except Exception as ex:
            exception_save = ex
            AM2_READ_ERRORS += 1
            time.sleep(AM2_READ_DELAY)

    logger.warning("Exception: register_address=%d, number_of_registers=%d, exception=%s, roundtrip_time=%0.3f, read_retry=%d, read_count=%d, read_errors=%d",
                    register_address, number_of_registers, exception_save, instrument.roundtrip_time, AM2_READ_RETRY, AM2_READ_COUNT, AM2_READ_ERRORS)

    return [None] * number_of_registers


@dataclass(init=False)
class Register:
    """Class represenation of a AM2 BMS modbus Register/sensor"""
    name: str # name of the register / sensor
    unit: str # unit - eg Volts, Amps, Watts
    register_scaled: int = 0 # register value after processing/scaling

    def __init__(self, register_address: int):
        """constructor"""
        self.register_address = register_address
        self.name = get_name(register_address)
        self.unit = get_unit(register_address)
        self.register_raw: int = None  # register value from BMS
        self.register_scaled = "??" if self.unit == "str" else 0

    def read_1_register(self, instrument) -> None:
        """read a Register from the instrument"""
        factor = get_factor(self.register_address)

        # don't re-read 'char2' (Version/BMS S_N/Pack S_N) as these are static
        if factor == 'char2' and self.register_raw is not None:
            return

        # skip 'computed' registers
        if factor == 'comp':
            return

        count = get_count(self.register_address)
        result_list = read_registers(instrument, register_address=self.register_address, number_of_registers=count)
        self.register_raw = result_list[0]
        if count == 1:
            # single register - int / uint / float
            self.register_scaled = scale_raw_register(factor, result_list[0], self.register_scaled)
        else:
            # string of concat count registers
            result_str = ""
            for _r in range(count):
                result_str += scale_raw_register(factor, result_list[_r], self.register_scaled[_r*2:2])
            self.register_scaled = result_str.rstrip()


@dataclass(init=False)
class AM2battery:
    """AM2 class for reading Hubble AM2 battery"""
    def __init__(self, instrument, station_address: int = None, know_registers_only: bool=True) -> None:
        """constructor"""
        self.instrument = instrument # minimalmodbus.Instrument aka device
        instrument.address = instrument.address if station_address is None else station_address
        self.station_address = instrument.address
        self.register_data = {} # dict()
        self.itr = None
        self.time=time.strftime('%FT%T%z')

        # create dict of know registers
        for reg in AM2_REGISTERS_DICT:
            self.register_data[reg]=Register(reg)

        if know_registers_only is False:
            # add unknown registers 0..180 to dict
            for reg in range(AM2_NUMBER_OF_REGISTERS):
                self.register_data[reg]=Register(reg)


    def __iter__(self):
        """ implement iterator over register_data """
        self.itr = iter(self.register_data)
        return self

    def __next__(self):
        """ implement iterator over register_data """
        key = next(self.itr)
        reg = self.register_data[key]
        # return key, value - value is a dict()
        return reg.register_address, { 'name': reg.name,
                                       'register_scaled': reg.register_scaled,
                                       'unit': reg.unit }

    def calc_computed(self):
        """calc min min avg diff - cell voltages 15..27"""
        tot_val = max_val = min_val = self.register_data[AM2_REGISTER_VCELL_START].register_scaled
        max_id = min_id = 1
        for cell in range(1, AM2_VCELL_COUNT):
            cell_id = cell + 1
            reg = AM2_REGISTER_VCELL_START + cell
            val = self.register_data[reg].register_scaled
            min_id = cell_id if val < min_val else min_id
            max_id = cell_id if val > max_val else max_id
            max_val = max(val,max_val)
            min_val = min(val,min_val)
            tot_val += val

        # store the min min avg diff and power
        self.register_data[1000].register_scaled=max_id
        self.register_data[1001].register_scaled=max_val
        self.register_data[1002].register_scaled=min_id
        self.register_data[1003].register_scaled=min_val
        self.register_data[1004].register_scaled=round(max_val-min_val, 3) # VoltDiff
        self.register_data[1005].register_scaled=round(tot_val/AM2_VCELL_COUNT, 3)  # AvgVolt
        self.register_data[1006].register_scaled=round(self.register_data[0].register_scaled *
                                                       self.register_data[1].register_scaled, 1)  # Power = Watts = A * V

        self.register_data[1010].register_scaled=self.station_address
        self.register_data[1011].register_scaled=time.strftime('%FT%T%z')

    def read_battery(self) -> None:
        """read all register_data of a battery"""
        self.instrument.address = self.station_address
        self.time=time.strftime('%FT%T%z')
        for reg in self.register_data.values():
            reg.read_1_register(self.instrument)

        self.calc_computed()

    def get_string(self, key: str) -> str:
        """extract 'Version', 'S_N_BMS', 'S_N_Pack' from register_data"""
        return self.register_data[AM2_STRING_DICT[key]].register_scaled
