"""
Chiltrix cxi MQTT Publisher for Home Assistant
Publishes heat pump data with MQTT discovery for automatic HA integration.
"""
import argparse
import json
import time
import os
import paho.mqtt.client as mqtt
from cxi import cxi
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

POLL_INTERVAL = 300  # seconds between updates

TEMP_UNITS = "F"
TEMP_UNIT_SUFFIX="°F"

# ============ MQTT DISCOVERY SETUP ============

# Set dynamically in main() from CLI args
DEVICE_ID = None
DEVICE_NAME = None
DEVICE_INFO = None
TOPIC_PREFIX = None

# Define all sensors: (entity_id, name, value_func, unit, device_class, icon)
# value_func is a lambda that takes fc and returns the value
SENSORS = [
    ("room_temp", "Room Temperature", lambda fc: f"{fc.get_roomtemp():.1f}", TEMP_UNIT_SUFFIX, "temperature", None),
    ("coil_temp", "Coil Temperature", lambda fc: fc.get_coiltemp(), TEMP_UNIT_SUFFIX, "temperature", None),
    ("opmode", "Operation Mode", lambda fc: fc.get_opmode_str(), None, None, "mdi:hvac"),
    ("fanspeed", "Fan Speed", lambda fc: fc.get_fanspeed_str(), None, None, "mdi:fan"),
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
            "state_topic": f"{TOPIC_PREFIX}/{entity_id}",
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
            "state_topic": f"{TOPIC_PREFIX}/{entity_id}",
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
        "state_topic": f"{TOPIC_PREFIX}/is_on",
        "command_topic": f"{TOPIC_PREFIX}/power/set",
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
        "state_topic": f"{TOPIC_PREFIX}/opmode",
        "command_topic": f"{TOPIC_PREFIX}/opmode/set",
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
        "state_topic": f"{TOPIC_PREFIX}/fanspeed",
        "command_topic": f"{TOPIC_PREFIX}/fanspeed/set",
        "options": cxi.fan_speed_list,
        "device": DEVICE_INFO,
        "icon": "mdi:fan",
    }
    client.publish(topic, json.dumps(payload), retain=True)
    print("Published discovery: fanspeed select")

    # Number — target temperatures
    for entity_id, name, min_val, max_val, step, unit, icon in CONTROLLABLE_ENTITIES:
        topic = f"homeassistant/number/{DEVICE_ID}_{entity_id}/config"
        payload = {
            "name": name,
            "unique_id": f"{DEVICE_ID}_{entity_id}_ctrl",
            "state_topic": f"{TOPIC_PREFIX}/{entity_id}",
            "command_topic": f"{TOPIC_PREFIX}/{entity_id}/set",
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
            client.publish(f"{TOPIC_PREFIX}/{entity_id}", str(value), retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")

    # Binary sensors
    for entity_id, _, value_func, _, _ in BINARY_SENSORS:
        try:
            value = "ON" if value_func(fc) else "OFF"
            client.publish(f"{TOPIC_PREFIX}/{entity_id}", value, retain=True)
        except Exception as e:
            print(f"Error reading {entity_id}: {e}")

    print(f"Published state update at {time.strftime('%H:%M:%S')}")


COMMAND_HANDLERS = {
    "power": lambda fc, val: fc.set_power(1 if val.upper() == "ON" else 0),
    "opmode": lambda fc, val: fc.set_opmode(cxi.op_mode.index(val)),
    "fanspeed": lambda fc, val: fc.set_fanspeed(cxi.fan_speed_list.index(val)),
    "cooling_target": lambda fc, val: fc.set_cool_target(float(val)),
    "heating_target": lambda fc, val: fc.set_heat_target(float(val)),
}

def on_connect(client, userdata, flags, rc):
    client.subscribe(f"{TOPIC_PREFIX}/+/set")
    client.subscribe("homeassistant/refresh/#")
    print(f"Connected to MQTT broker (rc={rc}), subscribed to command topics")


def on_message(client, userdata, msg):
    """Handle incoming MQTT command messages."""
    fc = userdata
    topic = msg.topic

    if topic.startswith("homeassistant/refresh"):
        refresh_event.set()
        return

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
    global DEVICE_ID, DEVICE_NAME, DEVICE_INFO, TOPIC_PREFIX

    parser = argparse.ArgumentParser(description="Chiltrix CXI MQTT publisher for Home Assistant")
    parser.add_argument("mb_address", type=int, help="Modbus address of the fan coil (e.g. 15, 19)", default=15)
    parser.add_argument("device_id", help="HA device ID (e.g. cxi_livingroom)", default="cxi")
    parser.add_argument("device_name", help="HA device name (e.g. 'Living Room Fan Coil')", default="Fan Coil")
    args = parser.parse_args()

    DEVICE_ID = args.device_id
    DEVICE_NAME = args.device_name
    TOPIC_PREFIX = f"chiltrix/cxi{args.mb_address}"
    DEVICE_INFO = {
        "identifiers": [DEVICE_ID],
        "name": DEVICE_NAME,
        "manufacturer": "Chiltrix",
        "model": "CXI"
    }

    fc = cxi(args.mb_address, "/dev/ttyUSB0", 2)
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
            refresh_event.wait(POLL_INTERVAL)
            refresh_event.clear()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()