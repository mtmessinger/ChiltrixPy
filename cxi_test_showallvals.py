from cxi import cxi
fc = cxi(15,"/dev/ttyUSB0", 1)
fc.temperature_units='F'

print(f"fan coil is on: {fc.is_on()}")
print(f"room temperature: {fc.get_roomtemp()}{fc.temperature_units}")
print(f"coil temperature: {fc.get_coiltemp()}{fc.temperature_units}")
print(f"fan speed: {fc.get_fanspeed_str()}")
print(f"op mode: {fc.get_opmode_str()}")
print(f"cooling target temperature: {fc.get_cool_target()}{fc.temperature_units}")
print(f"heating target temperature: {fc.get_heat_target()}{fc.temperature_units}")
