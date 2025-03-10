# ChiltrixPy
Library for connecting over modbus to the Chiltrix CX34 heat pump and Chiltrix CXI fan coil.

I used a waveshare usb to RS485 dongle to connect to the modbus interface of each of the devices.
For the cx34, I was able to connect right to the controller in my basement.  I did this from a Raspberry Pi and had no real problems.  The main program here will just interrogate the heatpump on interval and output elements suitable for a CSV file.  I found examining my heat pump operation over the course of several days let me optimize my house operations.  I found that I needed to try multiple times to get consistent readings and I believe this is because I'm sharing the modbus connection with the cx34 controller.  
For the CXI fancoils, the modbus connection is wide open and I didn't have this problem.  I connected 2 fan coils to 1 controller and as long I only talked to one at a time, everything works ok. 

USB to RS485: https://www.amazon.com/dp/B081MB6PN2?ref=ppx_yo2ov_dt_b_fed_asin_title

