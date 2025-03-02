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
       sets the dhw target temperature (celsius)
       """
       return self.write_register(144,5,16)
    def set_heat_target(self, val):
       """
       sets the heating target temperature (celsius)
       """
       return self.write_register(143,5,16)
    def set_cool_target(self, val):
       """
       sets the cooling target temperature (celsius)
       """
       return self.write_register(142,5,16)
    def get_power(self):
      """
      returns 0 for off, 1 for on
      """
      return self.checkvalRaw(140, 1, 3)
    def get_opmode(self):
      """
      gets the setting for operating mode
      """
      return self.checkvalRaw(141, 1, 3)
   
    
