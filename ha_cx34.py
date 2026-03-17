#!/usr/bin/env python3
"""
Chiltrix CX34 MQTT Publisher for Home Assistant
Publishes heat pump data with MQTT discovery for automatic HA integration.
"""

import json
import time
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from cx34 import cx34

load_dotenv()
# ============ CONFIGURATION ============
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASSWORD"]

POLL_INTERVAL = 120        # seconds between updates

DEVICE_ID = "chiltrix_cx34"
DEVICE_NAME = "Chiltrix CX34"

# ============ MQTT DISCOVERY SETUP ============

# Device info shared by all entities
DEVICE_INFO = {
    "identifiers": [DEVICE_ID],
    "name": DEVICE_NAME,
    "manufacturer": "Chiltrix",
    "model": "CX34"
}

# Define all sensors: (entity_id, name, value_func, unit, device_class, icon)
# value_func is a lambda that takes hp and returns the value
SENSORS = [
    ("ambient_temp", "Ambient Temperature", lambda hp: f"{hp.get_ambient_temp():.1f}", "°F", "temperature", None),
    ("inlet_temp", "Inlet Temperature", lambda hp: hp.get_inlet_temp(), "°F", "temperature", None),
    ("outlet_temp", "Outlet Temperature", lambda hp: hp.get_outlet_temp(), "°F", "temperature", None),
    ("dhw_temp", "DHW Temperature", lambda hp: hp.get_dhw_temp(), "°F", "temperature", None),
    ("cooling_target", "Cooling Target", lambda hp: hp.get_cooling_target(), "°F", "temperature", None),
    ("heating_target", "Heating Target", lambda hp: hp.get_heating_target(), "°F", "temperature", None),
    ("dhw_target", "DHW Target", lambda hp: hp.get_dhw_target(), "°F", "temperature", None),
    ("compressor_freq", "Compressor Frequency", lambda hp: hp.get_compressor_frequency(), "Hz", "frequency", None),
    ("water_flow", "Water Flow", lambda hp: hp.get_water_flow(), "L/min", None, "mdi:water"),
    ("water_pump_speed", "Water Pump Speed", lambda hp: hp.get_water_pump_speed(), "%", None, "mdi:pump"),
    ("input_current", "Input Current", lambda hp: hp.get_input_current(), "A", "current", None),
    ("input_voltage", "Input Voltage", lambda hp: hp.get_input_voltage(), "V", "voltage", None),
    ("opmode", "Operation Mode", lambda hp: hp.get_opmode_str(), None, None, "mdi:hvac"),
    ("running_mode", "Running Mode", lambda hp: hp.get_running_mode_str(), None, None, "mdi:state-machine"),
]

BINARY_SENSORS = [
    ("is_on", "Heat Pump On", lambda hp: hp.is_on(), None, "mdi:power"),
    ("defrost", "Defrosting", lambda hp: hp.is_defrost(), "cold", None),
    ("dhw_elec", "DHW Electric (E1)", lambda hp: hp.is_dhw_elec(), None, "mdi:water-boiler"),
    ("aux_elec", "Aux Electric (E2)", lambda hp: hp.is_aux_elec(), None, "mdi:heating-coil"),
]


def publish_discovery(client):
    """Publish MQTT discovery messages for all entities."""
    
    # Sensors
    for entity_id, name, _, unit, device_class, icon in SENSORS:
        topic = f"homeassistant/sensor/{DEVICE_ID}_{entity_id}/config"
        payload = {
            "name": name,
            "unique_id": f"{DEVICE_ID}_{entity_id}",
            "state_topic": f"chiltrix/cx34/{entity_id}",
            "device": DEVICE_INFO,
        }
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        if icon:
            payload["icon"] = icon
            
        client.publish(topic, json.dumps(payload), retain=True)
        print(f"Published discovery: {entity_id}")
    
    # Binary sensors
    for entity_id, name, _, device_class, icon in BINARY_SENSORS:
        topic = f"homeassistant/binary_sensor/{DEVICE_ID}_{entity_id}/config"
        payload = {
            "name": name,
            "unique_id": f"{DEVICE_ID}_{entity_id}",
            "state_topic": f"chiltrix/cx34/{entity_id}",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device": DEVICE_INFO,
        }
        if device_class:
            payload["device_class"] = device_class
        if icon:
            payload["icon"] = icon
            
        client.publish(topic, json.dumps(payload), retain=True)
        print(f"Published discovery: {entity_id}")


def publish_state(client, hp:cx34):
    """Publish current state for all entities."""
    
    # Sensors
    for entity_id, _, value_func, _, _, _ in SENSORS:
        try:
            value = value_func(hp)
            client.publish(f"chiltrix/cx34/{entity_id}", str(value), retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")
    
    # Binary sensors
    for entity_id, _, value_func, _, _ in BINARY_SENSORS:
        try:
            value = "ON" if value_func(hp) else "OFF"
            client.publish(f"chiltrix/cx34/{entity_id}", value, retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")
    
    print(f"Published state update at {time.strftime('%H:%M:%S')}")


def main():    
    # Initialize heat pump connection
    # Adjust port as needed
    hp = cx34(1,"/dev/ttyUSB0", 5)  
    hp.temperature_units='F'    
    
    # Initialize MQTT client
    client = mqtt.Client()
    
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    
    # Publish discovery on startup
    publish_discovery(client)
    
    # Main loop
    try:
        while True:
            publish_state(client, hp)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()