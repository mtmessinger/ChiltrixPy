from chiltrix_modbus import chiltrix_modbus

class cxi(chiltrix_modbus):
    fan_speed_list=('off','ultra-low','LOW', 'MED', 'HI', 'TOP', 'AUTO') 
    op_mode = ('auto','cooling','dehumidification','ventilate', 'heating')
    def __init__(self, mb_address:int=15, usb:str = '/dev/ttyUSB0', retries=1):
        super().__init__(mb_address, usb, retries)
        """
        create a connection to the unit
        the address for a cxi fancoil is 15 by default
        the usb location is for a modbus interface 
        to find the location, can just look at /dev before 
        and after you plug in a usb dongle and see what 
        device it is.
        """
    def set_power(self, val:int):
       """
       set the unit as on (1) or off (0)
       """
       return self.write_register(28301,val,16)
    def set_opmode(self, mode:int):
       """
       sets the operating mode
       0=auto, 1=cooling, 2=dehumidification, 3=ventilate, 4=heating
       """
       return self.write_register(28302,mode,16)
    def set_fanspeed(self, val:int):
       """
       sets the fan speed
       0=off, 1=ultra-low, 2=low, 3=medium, 4=high, 5=top, 6=auto
       """
       return self.write_register(28303,val,16)
    def set_cool_target(self, val:int):
       """
       set the cooling target temperature in configured units (F or C)
       """
       return self.write_register(28310, self.temp_local_to_c(val), 16)
    def set_heat_target(self, val:int):
       """
       set the heating target temperature in configured units (F or C)
       """
       return self.write_register(28311, self.temp_local_to_c(val), 16)
    def is_on(self):
       """
       returns True is powered on
       """   
       return self.checkvalRaw(28301, 3)==1
    def get_roomtemp(self):
      """
      gets the room temperature from the fan coil's sensor
      """
      return self.checkvalTemp(46801, 4, .1)
    def get_coiltemp(self):
      """
      gets the coil (water) temperature 
      """
      return self.checkvalTemp(46802, 4, .1)
    def get_fanspeed(self):
      """
      gets the fan speed (0=off, 1=ultra-low, 2=low, 3=medium, 4=high, 5=top)
      """
      return self.checkvalRaw(46803, 4)
    def get_fanspeed_str(self):
      """
      gets the current fan speed as a string
      """
      return self.checkvalList(46803, self.fan_speed_list, 4)
    def get_opmode(self):
      """
      gets the operating mode (0=auto, 1=cooling, 2=dehumidification, 3=ventilate, 4=heating)
      """
      return self.checkvalRaw(28302, 3)
    def get_opmode_str(self):
      """
      gets the operating mode as a string
      """
      return self.checkvalList(28302, self.op_mode, 3)