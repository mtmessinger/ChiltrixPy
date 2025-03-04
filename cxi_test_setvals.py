from cxi import cxi
fc = cxi(15,"/dev/ttyUSB0", 1)
fc.temperature_units='F'

#print(f"powering off fan coil: {fc.set_power(1)}")
print(f"fan coil is on: {fc.is_on()}")
#print(f"setting speed {fc.set_fanspeed(2)}")
print(f"fan speed: {fc.get_fanspeed_str()}")
#print(f"setting mode {fc.set_opmode(4)}")
print(f"op mode: {fc.get_opmode_str()}")