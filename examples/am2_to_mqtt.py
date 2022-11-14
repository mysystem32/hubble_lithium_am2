"""
    Description: Home Assistant mqtt discovery and publish
    Author:     Alberto da Silva
    Date:       10 Aug 2022
    Some ideas from: https://github.com/dreadnought/python-daly-bms/blob/main/bin/daly-bms-cli

    Note: mqtt_topic is not checked for "/" or incorrect input
    Only minimal checking of arguments is done
"""

import os
import time
import logging
import json
import argparse

import minimalmodbus
import paho.mqtt.client as mqtt
import hubble_lithium_am2 as am2

# globals
instrument = None
args = None
logger = None
mqtt_client = None

def mqtt_publish(topic: str, payload: str, retain: bool = False, wait: bool = False) -> None:
    """publish payload on mqtt topic"""
    logger.debug("topic=%s, payload=%s", topic, payload)
    infot = mqtt_client.publish(topic=topic, payload=payload, qos=0, retain=retain)
    if wait:
        infot.wait_for_publish()


# https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
DEVICE_CLASS_DICT = {
    "A"  : "current",
    "V"  : "voltage",
    "W"  : "power",
    "°C" : "temperature",
    "Hz" : "frequency",
    "Ah" : "energy",
    "Wh" : "energy",
    "%"  : "battery",     # SoC
    "tm" : "timestamp"    # mdi:progress-clock
}


def get_device_class(key: str):
    """return device_class from the dict()"""
    return DEVICE_CLASS_DICT[key] if key in DEVICE_CLASS_DICT else None


def mqtt_publish_hass_discovery(base_topic: str, battery):
    """
    HASS discovery - publish AM2 register information via mqtt
    topic & payload need to be formatted according to:
        https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
        https://developers.home-assistant.io/docs/core/entity
    for HASS to "discover" the register
    """

    # static information
    addr = battery.station_address
    manufacturer = "Hubble Lithium"
    model = "AM2 48V 5.5kWh"
    sw_version = battery.get_string('Version')
    hw_version = "AM2 Lithium ion"
    device_name = f"AM2_battery_{addr}" # display name
    device_id = f"am2_battery_{addr}"   # same in mqtt_publish_state()
    identifiers = [device_id]

    # for every register create a disovery_topic & discovery_payload, then mqtt_publish
    for key, reg_data in battery:
        reg = battery.register_data[key]
        name = reg.name                 # eg SoC, T_ENV, Voltage
        state_name = reg.name
        unit_of_measure = reg.unit
        unique_id = device_id + "_" + reg.name # alphanumerics, underscore and hyphen only
        object_id = unique_id  # Best practice for entities with a unique_id is to set <object_id> to unique_id

        # <discovery_prefix>/<component>/[<node_id>/]<object_id>/config
        discovery_topic = "homeassistant/sensor/" + object_id + "/config"

        # state_topic - topic we use via mqtt_publish_state()
        state_topic = base_topic + "/" + device_id + "/" + state_name + "/state"

        # discovery payload is the register information + device(battery)
        discovery_payload = { "name": name,
                              "state_topic": state_topic,
                              "unit_of_measurement": unit_of_measure,
                              "unique_id": unique_id,
                              "object_id": object_id,
                              "device": {
                                        "identifiers": identifiers,
                                        "name": device_name,
                                        "model": model,
                                        "sw_version": sw_version,
                                        "hw_version": hw_version,
                                        "manufacturer": manufacturer
                                    }
                            }

        # add device_class to discovery payload
        device_class = get_device_class(unit_of_measure)
        if device_class:
            discovery_payload["device_class"] = device_class

        logger.info("discovery_topic=%s,\ndiscovery_payload=%s", discovery_topic, json.dumps(discovery_payload,indent=4))

        # publish discovery topic & payload with optional retained=True
        # retained=True to make mqtt retain discovery messages on restart
        if args.mqtt and args.mqtt_hass:
            mqtt_publish(topic=discovery_topic, payload=json.dumps(discovery_payload), retain=args.mqtt_hass_retain)


def mqtt_publish_state(base_topic: str, battery):
    """ loop thru registers and publish via mqtt """
    addr = battery.station_address
    device_id = f"am2_battery_{addr}"

    for key, reg_data in battery:
        reg = battery.register_data[key]
        state_name = reg.name

        state_topic = base_topic + "/" + device_id + "/" + state_name + "/state"
        payload = reg.register_scaled

        logger.info("state_topic=%s, payload=%s", state_topic, payload)

        if args.mqtt:
            mqtt_publish(state_topic, payload, False)


def setup_args() -> None:
    """ parse arguments """
    global args
    parser = argparse.ArgumentParser(description="AM2 to HASS via MQTT example app")

    parser.add_argument("--device", help="RS485 device, e.g. /dev/ttyUSB1", type=str, required=True)
    parser.add_argument("--max-address", help="Max modbus station address to read, default=1", type=int, default=1)
    parser.add_argument("--mqtt", help="MQTT enable message publish", action="store_true")
    parser.add_argument("--mqtt-user", help="MQTT username", type=str) # WARNING: passing passwords on cmd line is not secure
    parser.add_argument("--mqtt-password", help="MQTT password", type=str)
    parser.add_argument("--mqtt-broker", help="MQTT broker (server), default localhost", type=str, default="localhost")
    parser.add_argument("--mqtt-port", help="MQTT port, default 1883", type=int, default=1883)
    parser.add_argument("--mqtt-topic", help="MQTT topic, default 'hubble_am2'", type=str, default="hubble_am2")
    parser.add_argument("--mqtt-hass", help="MQTT enable Home Assistant discovery", action="store_true")
    parser.add_argument("--mqtt-hass-retain", help="MQTT enable retain HASS discovery mesages", action="store_true")
    parser.add_argument("--debug", help="Enable debug output", action="store_true")
    parser.add_argument("--sleep", help="Seconds bettwen sampling loop, default=60", type=int, default=60)

    args = parser.parse_args()

    #arg.mqtt_topic should only be alpha,numeric,-,_ and no /
    #mqtt_topic = ''.join([c for c in args.mqtt_topic if c.isalnum() or c in ['-','_']])
    #args.mqtt_topic = mqtt_topic


def setup_logger() -> None:
    """ setup logging """
    global logger

    level = logging.DEBUG if args.debug else logging.INFO
    logger = logging.getLogger(__name__)
    logging.basicConfig(format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)s %(funcName)s()] %(message)s", level=level)


def setup_instrument() -> None:
    """ setup rs485 device """
    global instrument
    # open the instrument aka device
    # this is done ouside of the AM2battery class so you can adjust any serial settings
    logger.info("minimalmodbus: Connecting to %s",args.device)
    instrument = minimalmodbus.Instrument(port=args.device, slaveaddress=1, debug=False, close_port_after_each_call=True)
    instrument.serial.baudrate = 9600
    logger.info("minimalmodbus: instrument=%s",instrument)


def setup_mqtt_client() -> None:
    """ connect to mqtt """
    global mqtt_client
    client_name = os.path.basename(__file__)
    logger.info("setup_mqtt_client: connecting=%s",args.mqtt_broker)
    mqtt_client = mqtt.Client(client_name)
    #mqtt_client.enable_logger(logger)
    mqtt_client.username_pw_set(args.mqtt_user, args.mqtt_password)
    mqtt_client.connect(args.mqtt_broker, port=args.mqtt_port)


def main() -> None:
    """ setup and loop """
    setup_args()
    setup_logger()
    setup_instrument()
    if args.mqtt:
        setup_mqtt_client()

    bank={}
    bank_range = range(1, args.max_address + 1)
    for addr in bank_range:
        logger.info("Connecting to battery.addr=%d",addr)
        bank[addr] = am2.AM2battery(instrument, station_address=addr)
#        bank[addr].read_battery()
#        if args.mqtt and args.mqtt_hass:
#            logger.info("publishing hass discovery battery.addr=%d",addr)
#            mqtt_publish_hass_discovery(args.mqtt_topic, bank[addr])

    loop_count = 0
    start_time = time.time()
    while True:
        for addr in bank_range:
            logger.info("reading battery.addr=%d",addr)
            battery = bank[addr]
            battery.read_battery()

            # publish discovery every 15 minutes
            if loop_count % 15 == 0:
                logger.info("publishing hass discovery battery.addr=%d",addr)
                mqtt_publish_hass_discovery(args.mqtt_topic, bank[addr])

            logger.info("publishing battery.addr=%d",addr)
            mqtt_publish_state(args.mqtt_topic, bank[addr])

        loop_count += 1
        logger.info("============= sleep %d, loop_count=%d, ===========", args.sleep, loop_count)
        time.sleep(args.sleep - (time.time() - start_time) % args.sleep)


if __name__ == "__main__":
    main()
