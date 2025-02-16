# CX34Py
Library for connecting over modbus to the Chiltrix CX34

I used a waveshare usb to RS485 dongle to connect to the heat pump.  On mine, I was able to connect right to the controller in my basement.  I did this from a Raspberry Pi and had no real problems.  The main program here will just interrogate the heatpump on interval and output elements suitable for a CSV file.  I found examining my heat pump operation over the course of several days let me optimize my house operations.

USB to RS485: https://www.amazon.com/dp/B081MB6PN2?ref=ppx_yo2ov_dt_b_fed_asin_title

