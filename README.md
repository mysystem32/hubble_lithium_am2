# Hubble Lithium AM2 BMS modbus RS485 reader

Python 3 module that provides read access to Hubble Lithium AM2 battery BMS via RS485/modbus.

See [Hubble Lithium](https://www.hubblelithium.co.za/) website for more information on Hubble Lithium AM2 batteries.

Uses [minimalmodbus](https://github.com/pyhys/minimalmodbus/) for communications

> DISCLAIMER: Use at your own risk! Access is read only so no issues are expected.

## 📜 AM2 Python Library installation

Clone the repo and pip3 install
```bash
# Install into .local
$ git clone https://github.com/mysystem32/hubble_lithium_am2.git
$ cd hubble_lithium_am2
$ pip3 install .
```

## ⚙️ AM2 BMS Registers

Not sure what BMS is inside an AM-2.  
Google search failed to locate any techical information.  
The modbus register ID/value were reverse engineered / comparing to pbmstools.  
Execute examples/print_all.py to displaying all registers.

hubble_lithium_am2.py module is able to read:

- Pack Current (A)
- Pack Voltage (V)
- State of Charge (SoC %)
- State of Health (SoH %)
- Full Capacity (Ah)
- Remain Capacity (Ah)
- Cycles (int)
- Cell Voltages 1..13 (V)
- Cell Area Temperature 1..4 (°C)
- MOS Temperature (°C)
- ENV Temperature (°C)
- Firmware Version
- BMS S/N
- Pack S/N

### AM-2 Registers: 0..180 - many unknown:

PBMS Tools is able to read and display the Hubble Lithium AM2 BMS.  

![PBMS Tools](/images/PBMS-Tools-Battery-Status.png)

The register id / name correlation was done by reading all the registers and comparing to PBMS tools screen.  
There are 180 registers, of which about half have been decoded.

```python
# dict() of registers that have been 'discovered'
AM2_REGISTERS_DICT = { # dict
    #  id 
        0: {'name':'Current',        'unit':'A',  'factor':'f100s', 'count':1},
        1: {'name':'Voltage',        'unit':'V',  'factor':'f100',  'count':1},
        2: {'name':'SoC',            'unit':'%',  'factor':'uint',  'count':1},
        3: {'name':'SoH',            'unit':'%',  'factor':'uint',  'count':1},
        4: {'name':'RemainCapacity', 'unit':'Ah', 'factor':'f100',  'count':1},
        5: {'name':'FullCapacity',   'unit':'Ah', 'factor':'f100',  'count':1},
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
       31: {'name':'TCell_1',        'unit':'C',  'factor':'f10',   'count':1},
       32: {'name':'TCell_2',        'unit':'C',  'factor':'f10',   'count':1},
       33: {'name':'TCell_3',        'unit':'C',  'factor':'f10',   'count':1},
       34: {'name':'TCell_4',        'unit':'C',  'factor':'f10',   'count':1},
       35: {'name':'MOS_T',          'unit':'C',  'factor':'f10',   'count':1}, # mosfet
       36: {'name':'ENV_T',          'unit':'C',  'factor':'f10',   'count':1},

    # String registers - these are only read once
      150: {'name':'Version',        'unit':'str','factor':'char2', 'count':10},
      160: {'name':'BMS_S_N',        'unit':'str','factor':'char2', 'count':10},
      170: {'name':'Pack_S_N',       'unit':'str','factor':'char2', 'count':10},
    
    # computed registers - not physical - not really neccessary
     1000: {'name':'MaxVolt_cell',   'unit':'int','factor':'comp',  'count':1},
     1001: {'name':'MaxVolt',        'unit':'V',  'factor':'comp',  'count':1},
     1002: {'name':'MinVolt_cell',   'unit':'int','factor':'comp',  'count':1},
     1003: {'name':'MinVolt',        'unit':'V',  'factor':'comp',  'count':1},
     1004: {'name':'VoltDiff',       'unit':'V',  'factor':'comp',  'count':1},
     1005: {'name':'AvgVolt',        'unit':'V',  'factor':'comp',  'count':1},
     1006: {'name':'Power',          'unit':'W',  'factor':'comp',  'count':1}
}
```

## 🔌 USB-to-RS485 adaptor

The Hubble Lithium AM2 battery has a number of ports.  Use the RS485/modbus port.

![Hubble Lithium AM2 RS458 port](/images/hubble-lithium-am2.jpg)

To communicate you will need a USB RS485 Serial Adapter Modbus Communication Cable similar to this:

![USB RS485 RJ45 Serial Modbus Communication Cable](/images/usb_rs485_rj45_cable.png)

Tested with <https://solar-assistant.io/shop/products/sunsynk_rs485> cable.

Connect the RJ45 end to the RS485 port on the AM2.

## 🔋 Multiple batteries

You can connect multiple batteries using cable using a splitter.

![2 port cable splitter](/images/splitter-2-port.png)  
![4 port cable splitter](/images/splitter-4-port.png) 
![make your own 8 port cable splitter](/images/splitter-make-your-own-8-port.png) 
![make your own 4 port cable splitter](/images/splitter-make-your-own-4-port.png) 

## Reading AM2 registers

Some sample code to read registers from an AM2:

```python
import minimalmodbus
import hubble_lithium_am2 as am2

"""test code"""

# open the instrument aka device
# this is done ouside of the AM2_Pack class so you can adjust any serial settings
instrument = minimalmodbus.Instrument(port="/dev/ttyUSB1", slaveaddress=1,
                               debug=False, close_port_after_each_call=True)
instrument.serial.baudrate = 9600
print(f"modbus serial instrument={instrument}")

# create an AM2_Pack object
pack = am2.AM2_Pack(instrument)

print("Reading AM2 registers...")
pack.read_pack()

result_dict = dict(pack)
print(result_dict)
```


## Typical usage

Record cell voltages, cycles over time, etc


see [Grafana.md](/Grafana.md) for charts produced from BMS data


## 🙇‍♂️ Credits

Thanks to:
- Developers of minimalmodbus
- kellaza <https://github.com/kellerza/sunsynk> for insparation
- Powerforum <https://powerforum.co.za/> for advice
- Solar-Assistant <https://solar-assistant.io/> for a great product

## ⚖️ License

This project is under the MIT License. See the [LICENSE](LICENSE) file for the full license text.
