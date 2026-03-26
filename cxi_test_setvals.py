from cxi import cxi
import sys
MB_ADDRESS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
USB = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB0"
fc = cxi(MB_ADDRESS, USB)
fc.temperature_units='F'

#print(f"powering off fan coil: {fc.set_power(1)}")
#print(f"fan coil is on: {fc.is_on()}")
#print(f"setting speed {fc.set_fanspeed(2)}")
#print(f"fan speed: {fc.get_fanspeed_str()}")
#print(f"setting mode {fc.set_opmode(4)}")
#print(f"op mode: {fc.get_opmode_str()}")

print(f"set heat target: {fc.set_heat_target(84)}")
print(f"heat target is: {fc.get_heat_target()}")
