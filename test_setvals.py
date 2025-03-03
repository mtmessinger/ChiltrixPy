from cx34 import cx34
hp = cx34(1,"/dev/ttyUSB0", 5)
hp.temperature_units='F'

#turn off
#print(f"powering heat pump: {hp.set_power(1)}")
print(f"heat pump on: {hp.is_on()}")
#print(f"setting mode {hp.set_opmode(2)}")
print(f"opmode:{hp.get_opmode_str()}")
#print(f"setting cooling temp {hp.set_cool_target(45)}")
print(f"cooling target: {hp.get_cooling_target()}{hp.temperature_units}")
#print(f"setting heating temp {hp.set_heat_target(103)}")
print(f"heating target: {hp.get_heating_target()}{hp.temperature_units}")
#print(f"setting dhw temp {hp.set_dhw_target(122)}")
print(f"dhw target: {hp.get_dhw_target()}{hp.temperature_units}")