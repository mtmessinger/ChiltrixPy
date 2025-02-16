import minimalmodbus

class cx34:
    def _init(self, mb_address:int=1, usb:str = '/dev/ttyUSB0', retries=5):
        self.bus =  minimalmodbus.Instrument(usb,mb_address, minimalmodbus.MODE_RTU)
        self.bus.serial.baudrate = 9600				# BaudRate
        self.bus.clear_buffers_before_each_transaction = True
        self.bus.close_port_after_each_call = True
        self.retries = retries
        #I found that a lot of communication was garbled.  I believe this is because
        # the heat pump controller is often trying to use the link at the same time
        # to update its monitor

    def read_register(self, register, func_code):
        for x in range(1,self.retries):
            try:
                return self.bus.read_registers(register,1,func_code)[0]
            except:
                pass
        return "error"

    def checkvalList(self,register, vals, func_code=3):
        data = self.read_register(register, func_code)
        if data=="error":
            return data
        else:
            return vals[data]
        
    def checkvalTemp(self, register, factor=1, func_code=3):
        data =self.read_register(register, func_code) 
        data = unsigned_to_signed(data)
        tempF = ((data*factor)*9/5)+32
        return tempF
    
    def checkvalRaw(self, register, factor=1, func_code=3):
        data =self.read_register(register, func_code)
        return data*factor

def unsigned_to_signed(unsigned_int, num_bits=16):
    max_unsigned = (1 << num_bits) - 1
    if unsigned_int > max_unsigned:
        raise ValueError("Unsigned integer is too large for the specified number of bits")
    if unsigned_int & (1 << (num_bits - 1)): # Check if the most significant bit is set
        return unsigned_int - (1 << num_bits)
    else:
        return unsigned_int