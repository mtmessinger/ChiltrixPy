# ChiltrixPy
Library for connecting over modbus to the Chiltrix CX34 heat pump and Chiltrix CXI fan coil.

I used a waveshare usb to RS485 dongle to connect to the modbus interface of each of the devices.
For the cx34, I was able to connect right to the controller in my basement.  I did this from a Raspberry Pi and had no real problems.  The main program here will just interrogate the heatpump on interval and output elements suitable for a CSV file.  I found examining my heat pump operation over the course of several days let me optimize my house operations.  

For the CXI fancoils, the modbus connection is wide open and I didn't have this problem.  I connected 2 fan coils to 1 controller and as long I only talked to one at a time, everything works ok. 

USB to RS485: https://www.amazon.com/dp/B081MB6PN2
<img width="200" alt="image" src="https://github.com/user-attachments/assets/fef9be54-c8bb-455f-b99a-eb83f6729a13" />

I used the excellent minimalmodbus library (https://github.com/pyhys/minimalmodbus) to implement this.  Thank you!

# Wrinkles/Issues
- I found that I needed to try multiple times to get consistent readings and I believe this is because I'm sharing the modbus connection with the cx34 controller.
- I was confounded for a while when getting some temperature values, but eventually figured out that I needed treat them as signed longs.  That fixed it and allowed me to get negative values.
- There's various documentation from Chiltrix and other folks on what modbus addresses map to which values.  Certain values did not match the documentation, so your mileage may vary.  For example, the e2 setting is supposed to be a 0 or 1, but in fact seems to be 0-9 indicating some sort of 0 - 90% or something.

# Home Assistant Integration

These scripts publish Chiltrix data to Home Assistant via MQTT Discovery. HA auto-discovers all entities — no manual HA configuration needed.

## Prerequisites
- MQTT broker (e.g. Mosquitto) accessible from your Pi
- `paho-mqtt` and `python-dotenv` packages: `pip install paho-mqtt python-dotenv`
- A `.env` file in the project directory:
```
MQTT_BROKER=your_broker_address
MQTT_PORT=1883
MQTT_USER=your_user
MQTT_PASSWORD=your_password
```

## Running

**CX34 Heat Pump** — publishes sensors and controls for power, operating mode, and target temperatures:
```bash
python ha_cx34.py
```

**CXI Fan Coil** — takes the Modbus address, a device ID, and a display name as arguments, so you can run one instance per fan coil:
```bash
python ha_cxi.py 15 cxi_livingroom "Living Room Fan Coil"
python ha_cxi.py 19 cxi_kitchen "Kitchen Fan Coil"
```

**Refresh Button** — run once to register a "Refresh All Chiltrix" button in HA that triggers an immediate state update from all scripts:
```bash
python ha_refresh_button.py
```

## Running on Startup
I use crontab on my Raspberry Pi with staggered delays to avoid Modbus contention at boot:
```
@reboot sleep 60 && cd /path/to/ChiltrixPy && python ha_cx34.py >> ../logs/ha_cx34.txt
@reboot sleep 60 && cd /path/to/ChiltrixPy && python ha_cxi.py 15 cxi_livingroom "Living Room Fan Coil" >> ../logs/ha_cxi15.txt
@reboot sleep 70 && cd /path/to/ChiltrixPy && python ha_cxi.py 19 cxi_kitchen "Kitchen Fan Coil" >> ../logs/ha_cxi19.txt
```

# Getting Started
I'd start by running the test_showallvals code for whatever you're trying to talk to (after hooking up all the hardware, of course).  The code just connects to a unit and sets the temperature units to Fahrenheit.  You're welcome to use Celsius.  

# Feedback
I've only been working with Python for a few years.  I'd love to get feeback on the project and suggestions for how I might improve it / my code / what-have-you.
