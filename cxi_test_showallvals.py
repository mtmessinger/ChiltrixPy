from cxi import cxi
import sys
MB_ADDRESS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
USB = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB0"
fc = cxi(MB_ADDRESS, USB)
fc.temperature_units='F'

print(f"fan coil is on: {fc.is_on()}")
print(f"coil temperature: {fc.get_coiltemp()}{fc.temperature_units}")
print(f"cool target: {fc.get_cool_target()}{fc.temperature_units}")
print(f"heat target: {fc.get_heat_target()}{fc.temperature_units}")
print(f"fan speed: {fc.get_fanspeed_str()}")
print(f"op mode: {fc.get_opmode_str()}")
print(f"room temperature: {fc.get_roomtemp()}{fc.temperature_units}")
