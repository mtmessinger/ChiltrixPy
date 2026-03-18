"""
Chiltrix cxi MQTT Publisher for Home Assistant
Publishes heat pump data with MQTT discovery for automatic HA integration.
"""
import json
import time
import os
import paho.mqtt.client as mqtt
from cxi import cxi
import threading
#lock for modbus access in main thread and in on message
modbus_lock = threading.Lock()

# ============ CONFIGURATION ============
from dotenv import load_dotenv
load_dotenv()
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASSWORD"]

POLL_INTERVAL = 120        # seconds between updates
DEVICE_ID = "chiltrix_cxi"
DEVICE_NAME = "Chiltrix CXI"

TEMP_UNITS = "F"
TEMP_UNIT_SUFFIX="°F"

# ============ MQTT DISCOVERY SETUP ============

# Device info shared by all entities
DEVICE_INFO = {
    "identifiers": [DEVICE_ID],
    "name": DEVICE_NAME,
    "manufacturer": "Chiltrix",
    "model": "cxi"
}

# Define all sensors: (entity_id, name, value_func, unit, device_class, icon)
# value_func is a lambda that takes fc and returns the value
SENSORS = [
    ("room_temp", "Room Temperature", lambda fc: f"{fc.get_roomtemp():.1f}", TEMP_UNIT_SUFFIX, "temperature", None),
    ("coil_temp", "Coil Temperature", lambda fc: fc.get_coiltemp(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("opmode", "Operation Mode", lambda fc: fc.get_opmode_str(), None, None, "mdi:hvac"),
    ("fan_speed", "Fan Speed", lambda fc: fc.get_fanspeed_str(), None, None, None)
    ("running_mode", "Running Mode", lambda fc: fc.get_running_mode_str(), None, None, "mdi:state-machine"),
]

BINARY_SENSORS = [
    ("is_on", "Fan Coil On", lambda fc: fc.is_on(), None, "mdi:power")
]

# Controllable entities
# (entity_id, name, min, max, step, unit, icon)
CONTROLLABLE_ENTITIES = [
    ("cooling_target", "Cooling Target", 40, 80, 1, TEMP_UNIT_SUFFIX, None),
    ("heating_target", "Heating Target", 60, 140, 1, TEMP_UNIT_SUFFIX, None)
]

def publish_discovery(client):
    """Publish MQTT discovery messages for all entities."""
    
    # Sensors
    for entity_id, name, _, unit, device_class, icon in SENSORS:
        topic = f"homeassistant/sensor/{DEVICE_ID}_{entity_id}/config"
        payload = {
            "name": name,
            "unique_id": f"{DEVICE_ID}_{entity_id}",
            "state_topic": f"chiltrix/cxi/{entity_id}",
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
            "state_topic": f"chiltrix/cxi/{entity_id}",
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
        "state_topic": "chiltrix/cxi/is_on",
        "command_topic": "chiltrix/cxi/power/set",
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
        "state_topic": "chiltrix/cxi/opmode",
        "command_topic": "chiltrix/cxi/opmode/set",
        "options": cxi.op_mode,
        "device": DEVICE_INFO,
        "icon": "mdi:hvac",
    }
    client.publish(topic, json.dumps(payload), retain=True)
    print("Published discovery: opmode select")

    # Select — fan speed
    topic = f"homeassistant/select/{DEVICE_ID}_fanspeed/config"
    payload = {
        "name": "Fan Speed",
        "unique_id": f"{DEVICE_ID}_fanspeed",
        "state_topic": "chiltrix/cxi/fanspeed",
        "command_topic": "chiltrix/cxi/fanspeed/set",
        "options": cxi.fan_speed_list,
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
            "state_topic": f"chiltrix/cxi/{entity_id}",
            "command_topic": f"chiltrix/cxi/{entity_id}/set",
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


def publish_state(client, fc:cxi):
    """Publish current state for all entities. Caller must hold modbus_lock."""

    # Sensors
    for entity_id, _, value_func, _, _, _ in SENSORS:
        try:
            value = value_func(fc)
            client.publish(f"chiltrix/cxi/{entity_id}", str(value), retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")

    # Binary sensors
    for entity_id, _, value_func, _, _ in BINARY_SENSORS:
        try:
            value = "ON" if value_func(fc) else "OFF"
            client.publish(f"chiltrix/cxi/{entity_id}", value, retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")

    print(f"Published state update at {time.strftime('%H:%M:%S')}")


COMMAND_HANDLERS = {
    "power": lambda fc, val: fc.set_power(1 if val.upper() == "ON" else 0),
    "opmode": lambda fc, val: fc.set_opmode(cxi.operating_mode.index(val)),
    "fan_speed": lambda fc, val: fc.set_fanspeed(cxi.fan_speed.index(val)),
    "cooling_target": lambda fc, val: fc.set_cool_target(float(val)),
    "heating_target": lambda fc, val: fc.set_heat_target(float(val)),
}

def on_connect(client, userdata, flags, rc):
    """Subscribe on every (re)connect so subscriptions survive reconnects."""
    client.subscribe("chiltrix/cxi/+/set")
    print(f"Connected to MQTT broker (rc={rc}), subscribed to command topics")


def on_message(client, userdata, msg):
    """Handle incoming MQTT command messages."""
    fc = userdata
    topic = msg.topic
    payload = msg.payload.decode()

    # Extract entity from topic: chiltrix/cxi/{entity}/set
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
            handler(fc, payload)
            publish_state(client, fc)
        print(f"Handled command: {entity} = {payload}")
    except Exception as e:
        print(f"Error handling command {entity}={payload}: {e}")


def main():
    # Initialize heat pump connection
    fc = cxi(15, "/dev/ttyUSB0", 1)
    fc.temperature_units = TEMP_UNITS

    # Initialize MQTT client
    client = mqtt.Client(userdata=fc)
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
                publish_state(client, fc)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()