"""
Publishes MQTT discovery for a Chiltrix refresh button in Home Assistant.
Run once (or on broker restart) to register the button.
"""
import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASSWORD"]

client = mqtt.Client()
if MQTT_USER and MQTT_PASS:
    client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_BROKER, MQTT_PORT)

payload = {
    "name": "Refresh All Chiltrix",
    "unique_id": "chiltrix_refresh",
    "command_topic": "homeassistant/refresh/chiltrix",
    "icon": "mdi:refresh",
}

client.publish("homeassistant/button/chiltrix_refresh/config", json.dumps(payload), retain=True)
print("Published refresh button discovery")

client.disconnect()
