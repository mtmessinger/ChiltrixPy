"""
Scan CXI Modbus registers looking for values that look like temperatures.
Tries both function code 3 (holding) and 4 (input) across known register ranges.
Reports raw value, signed value, and value*0.1 (since some temps use that factor).
"""
import minimalmodbus
import sys
from chiltrix_modbus import unsigned_to_signed

MB_ADDRESS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
USB = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB0"

bus = minimalmodbus.Instrument(USB, MB_ADDRESS, minimalmodbus.MODE_RTU)
bus.serial.baudrate = 9600
bus.clear_buffers_before_each_transaction = True
bus.close_port_after_each_call = True

# CXI registers seem to be in 28xxx (holding) and 46xxx (input) ranges
RANGES = [
    (28300, 28400, 3),
    (46800, 46900, 4),
]

def looks_like_temp_c(val):
    """Could this be a Celsius temperature? Roughly -20 to 80C."""
    return -20 <= val <= 80

for start, end, fc in RANGES:
    print(f"\n=== Scanning registers {start}-{end} (func code {fc}) ===")
    for reg in range(start, end):
        try:
            raw = bus.read_registers(reg, 1, fc)[0]
            signed = unsigned_to_signed(raw)
            scaled = signed * 0.1
            # Check if raw, signed, or scaled look like a temperature
            if looks_like_temp_c(signed) or looks_like_temp_c(scaled):
                f_raw = (signed * 9/5) + 32
                f_scaled = (scaled * 9/5) + 32
                print(f"  reg {reg}: raw={raw} signed={signed} (~{f_raw:.1f}°F)  x0.1={scaled:.1f} (~{f_scaled:.1f}°F)")
        except Exception:
            pass
