"""
Chiltrix CX34 MQTT Publisher for Home Assistant
Publishes heat pump data with MQTT discovery for automatic HA integration.
"""
import json
import time
import os
import paho.mqtt.client as mqtt
from cx34 import cx34
import threading
#lock for modbus access in main thread and in on message
modbus_lock = threading.Lock()
refresh_event = threading.Event()

# ============ CONFIGURATION ============
from dotenv import load_dotenv
load_dotenv()
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASSWORD"]

POLL_INTERVAL = 300    # seconds between updates
DEVICE_ID = "chiltrix_cx34"
DEVICE_NAME = "Chiltrix CX34"

TEMP_UNITS = "F"
TEMP_UNIT_SUFFIX="°F"

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
    ("ambient_temp", "Ambient Temperature", lambda hp: f"{hp.get_ambient_temp():.1f}", TEMP_UNIT_SUFFIX, "temperature", None),
    ("inlet_temp", "Inlet Temperature", lambda hp: hp.get_inlet_temp(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("outlet_temp", "Outlet Temperature", lambda hp: hp.get_outlet_temp(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("dhw_temp", "DHW Temperature", lambda hp: hp.get_dhw_temp(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("cooling_target", "Cooling Target", lambda hp: hp.get_cooling_target(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("heating_target", "Heating Target", lambda hp: hp.get_heating_target(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("dhw_target", "DHW Target", lambda hp: hp.get_dhw_target(), TEMP_UNIT_SUFFIX, "temperature", None),
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

# Controllable entities
# (entity_id, name, min, max, step, unit, icon)
CONTROLLABLE_ENTITIES = [
    ("cooling_target", "Cooling Target", 40, 80, 1, TEMP_UNIT_SUFFIX, None),
    ("heating_target", "Heating Target", 60, 140, 1, TEMP_UNIT_SUFFIX, None),
    ("dhw_target", "DHW Target", 100, 150, 1, TEMP_UNIT_SUFFIX, None),
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

    # Switch — power on/off
    topic = f"homeassistant/switch/{DEVICE_ID}_power/config"
    payload = {
        "name": "Power",
        "unique_id": f"{DEVICE_ID}_power",
        "state_topic": "chiltrix/cx34/is_on",
        "command_topic": "chiltrix/cx34/power/set",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": DEVICE_INFO,
        "icon": "mdi:power",
    }
    client.publish(topic, json.dumps(payload), retain=True)
    print("Published discovery: power switch")

    # Select — operating mode
    topic = f"homeassistant/select/{DEVICE_ID}_opmode/config"
    payload = {
        "name": "Operation Mode",
        "unique_id": f"{DEVICE_ID}_opmode",
        "state_topic": "chiltrix/cx34/opmode",
        "command_topic": "chiltrix/cx34/opmode/set",
        "options": cx34.operating_mode,
        "device": DEVICE_INFO,
        "icon": "mdi:hvac",
    }
    client.publish(topic, json.dumps(payload), retain=True)
    print("Published discovery: opmode select")

    # Number — target temperatures
    for entity_id, name, min_val, max_val, step, unit, icon in CONTROLLABLE_ENTITIES:
        topic = f"homeassistant/number/{DEVICE_ID}_{entity_id}/config"
        payload = {
            "name": name,
            "unique_id": f"{DEVICE_ID}_{entity_id}_ctrl",
            "state_topic": f"chiltrix/cx34/{entity_id}",
            "command_topic": f"chiltrix/cx34/{entity_id}/set",
            "min": min_val,
            "max": max_val,
            "step": step,
            "unit_of_measurement": unit,
            "device": DEVICE_INFO,
        }
        if icon:
            payload["icon"] = icon
        client.publish(topic, json.dumps(payload), retain=True)
        print(f"Published discovery: {entity_id} number")


def publish_state(client, hp:cx34):
    """Publish current state for all entities. Caller must hold modbus_lock."""

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


COMMAND_HANDLERS = {
    "power": lambda hp, val: hp.set_power(1 if val.upper() == "ON" else 0),
    "opmode": lambda hp, val: hp.set_opmode(cx34.operating_mode.index(val)),
    "cooling_target": lambda hp, val: hp.set_cool_target(float(val)),
    "heating_target": lambda hp, val: hp.set_heat_target(float(val)),
    "dhw_target": lambda hp, val: hp.set_dhw_target(float(val)),
}


def on_connect(client, userdata, flags, rc):
    """Subscribe on every (re)connect so subscriptions survive reconnects."""
    client.subscribe("chiltrix/cx34/+/set")
    client.subscribe("homeassistant/refresh/#")
    print(f"Connected to MQTT broker (rc={rc}), subscribed to command topics")


def on_message(client, userdata, msg):
    """Handle incoming MQTT command messages."""
    hp = userdata
    topic = msg.topic

    if topic.startswith("homeassistant/refresh"):
        refresh_event.set()
        return

    payload = msg.payload.decode()

    # Extract entity from topic: chiltrix/cx34/{entity}/set
    parts = topic.split("/")
    if len(parts) != 4 or parts[3] != "set":
        return
    entity = parts[2]

    handler = COMMAND_HANDLERS.get(entity)
    if not handler:
        print(f"Unknown command entity: {entity}")
        return

    try:
        with modbus_lock:
            handler(hp, payload)
            publish_state(client, hp)
        print(f"Handled command: {entity} = {payload}")
    except Exception as e:
        print(f"Error handling command {entity}={payload}: {e}")


def main():
    # Initialize heat pump connection
    hp = cx34(1, "/dev/ttyUSB0", 5)
    hp.temperature_units = TEMP_UNITS

    # Initialize MQTT client
    client = mqtt.Client(userdata=hp)
    client.on_connect = on_connect
    client.on_message = on_message

    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    # Publish discovery on startup
    publish_discovery(client)

    # Main loop
    try:
        while True:
            with modbus_lock:
                publish_state(client, hp)
            refresh_event.wait(POLL_INTERVAL)
            refresh_event.clear()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()