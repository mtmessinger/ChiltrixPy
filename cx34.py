from chiltrix_modbus import chiltrix_modbus

class cx34(chiltrix_modbus):
    on_off = ('off','on')
    no_yes = ('no','yes')
    v18 = ('off','low','med','high','super-high')
    disable_enable = ('disable', 'enable')
    operating_mode = ('au', 'cool', 'heat', 'dhw','au+dhw','cool+dhw','heat+dhw')
    running_mode = ('off','cool','heat','dhw')
    def __init__(self, mb_address:int=1, usb:str = '/dev/ttyUSB0', retries=5):
        super().__init__(mb_address, usb, retries)
        """
        create a connection to the unit
        the address for a cx34 is 1 by default
        the usb location is for a modbus interface 
        to find the location, can just look at /dev before 
        and after you plug in a usb dongle and see what 
        device it is.
        reties at 5 was necessary for me since the 
        I was sharing the modbus wire with the heat pump
        monitor and the communications would sometimes overlap
        """
    def set_power(self, val:int):
       """
       set the unit as on (1) or off (0)
       """
       return self.write_register(140,val,16)
    def set_opmode(self, mode:int):
       """
       sets the operating mode
       0=au, 1=cool, 2=heat, 3=dhw, 4=au+dhw
       5=cool+dhw, 6=heat+dhw
       """
       return self.write_register(141,mode,16)
    def set_dhw_target(self, val):
       """
       sets the dhw target temperature 
       """
       return self.write_register(144,self.temp_local_to_c(val),16)
    def set_heat_target(self, val):
       """
       sets the heating target temperature 
       """
       return self.write_register(143, self.temp_local_to_c(val), 16)
    def set_cool_target(self, val):
       """
       sets the cooling target temperature 
       """
       return self.write_register(142,self.temp_local_to_c(val),16)
    def is_on(self):
      """
      returns True if on
      """
      return self.checkvalRaw(140, 3)==1
    def get_opmode(self):
      """
      gets the setting for operating mode
      """
      return self.checkvalRaw(141, 3)
    def get_opmode_str(self):
      """
      gets the setting for operating mode as a string
      """
      return self.checkvalList(141, self.operating_mode, 3)
    def get_cooling_target(self):
      """
      gets the cooling target temperature
      """
      return self.checkvalTemp(142, 3)
    def get_heating_target(self):
      """
      gets the heating target temperature
      """
      return self.checkvalTemp(143, 3)
    def get_dhw_target(self):
      """
      gets the dwh target temperature
      """
      return self.checkvalTemp(144, 3)
    def get_ambient_temp(self):
      """
      gets the ambient air temperature for the unit
      """
      return self.checkvalTemp(202, 3, 0.1)
    def get_inlet_temp(self):
      """
      gets the inlet water (glycol) temperature for the unit
      """
      return self.checkvalTemp(260, 3, 0.1)
    def get_outlet_temp(self):
      """
      gets the outlet water (glycol) temperature for the unit
      """
      return self.checkvalTemp(203, 3, 0.1)
    def get_dhw_temp(self):
      """
      gets the domestic hot water temperature
      """
      return self.checkvalTemp(204, 3, 0.1)
    def is_defrost(self):
      """
      is the unit in defrost mode
      """
      return self.checkvalRaw(216, 3)==1
    def get_compressor_frequency(self):
      """
      gets the running frequency of the compressor 0-80 hertz
      """
      return self.checkvalRaw(219, 3)
    def is_dhw_elec(self):
      """
      is E1 on (DHW electric element)
      """
      return self.checkvalRaw(227, 3)==1
    def is_aux_elec(self):
      """
      is E2 on (V18 aux electric element)
      """
      return self.checkvalRaw(228, 3)>0
    def get_running_mode(self):
      """
      gets the running mode
      0=off, 1=cool, 2=heat, 3=dhw
      """
      return self.checkvalRaw(255, 3)
    def get_running_mode_str(self):
      """
      gets the running mode
      """
      return self.checkvalList(255, self.running_mode, 3)
    def get_water_flow(self):
      """
      gets the water flow rate (0-100) in L/m)
      """
      return self.checkvalRaw(247, 3, 0.1)
    def get_water_pump_speed(self):
      """
      gets the water pump speed in % from 0-100
      """
      return self.checkvalRaw(251, 3, 10)
    def get_input_current(self):
      """
      gets the input current 0-50A
      """
      return self.checkvalRaw(256, 3)
    def get_input_voltage(self):
      """
      gets the input current 0-550V
      """
      return self.checkvalRaw(273, 3)