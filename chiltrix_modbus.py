import minimalmodbus
import time

class chiltrix_modbus:
    def __init__(self, mb_address:int=1, usb:str = '/dev/ttyUSB0', retries=5):
        self.mb_address = mb_address
        self.bus =  minimalmodbus.Instrument(usb, mb_address, minimalmodbus.MODE_RTU)
        self.bus.serial.baudrate = 9600
        self.bus.clear_buffers_before_each_transaction = True
        self.bus.close_port_after_each_call = True
        self.retries = retries
        self.temperature_units='c'
        time.sleep(1)

    def get_mbAddress(self):
        return self.mb_address

    def is_fahrenheit(self):
        """
        just returns if the interface is set to be fahrenheit rather than the default of Celsius.
        """
        return str.startswith(str.lower(self.temperature_units), 'f')
    
    def temp_local_to_c(self, temp_ext_units):
        """
        used internally so that the temperature to be written is converted to C
        if the internal units are fahrenheit.  I could add kelvin if I felt like it.
        """
        if not self.is_fahrenheit():
            return int(temp_ext_units)
        return int((temp_ext_units-32)*5/9)
    
    def read_register(self, register, func_code):
        for x in range(0,self.retries):
            try:
                return self.bus.read_registers(register,1,func_code)[0]
            except:
                pass
        raise IOError(f"Failed to read register {register} after {self.retries} retries")
    
    def write_register(self, register, value, func_code_write=16, func_code_read=3):
        for x in range(0,self.retries):
            try:
                self.bus.write_register(register, value, 0, func_code_write)
                new_val = self.read_register(register,func_code_read)
                if new_val==value:
                    return True
            except:
                pass
        raise IOError(f"Failed to write register {register} after {self.retries} retries")

    def checkvalList(self,register, vals, func_code=3):
        data = self.read_register(register, func_code)
        return vals[data]
        
    def checkvalTemp(self, register, func_code=3, factor=1):
        data =self.read_register(register, func_code) 
        data = unsigned_to_signed(data)
        #some of the temperatures are multiplied by 10 (and require .1 for a factor)
        temp = data*factor
        if self.is_fahrenheit():
            temp = ((temp)*9/5)+32
        return temp
    
    def checkvalRaw(self, register, func_code=3, factor=1):
        data =self.read_register(register, func_code)
        return data*factor
    
    def setval(self, register, value, func_code=16):
        self.write_register(register,value,16)

def unsigned_to_signed(unsigned_int, num_bits=16):
    max_unsigned = (1 << num_bits) - 1
    if unsigned_int > max_unsigned:
        raise ValueError("Unsigned integer is too large for the specified number of bits")
    if unsigned_int & (1 << (num_bits - 1)): # Check if the most significant bit is set
        return unsigned_int - (1 << num_bits)
    else:
        return unsigned_int   