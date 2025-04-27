# ChiltrixPy
Library for connecting over modbus to the Chiltrix CX34 heat pump and Chiltrix CXI fan coil.

I used a waveshare usb to RS485 dongle to connect to the modbus interface of each of the devices.
For the cx34, I was able to connect right to the controller in my basement.  I did this from a Raspberry Pi and had no real problems.  The main program here will just interrogate the heatpump on interval and output elements suitable for a CSV file.  I found examining my heat pump operation over the course of several days let me optimize my house operations.  

For the CXI fancoils, the modbus connection is wide open and I didn't have this problem.  I connected 2 fan coils to 1 controller and as long I only talked to one at a time, everything works ok. 

USB to RS485: https://www.amazon.com/dp/B081MB6PN2
<img width="200" alt="image" src="https://github.com/user-attachments/assets/fef9be54-c8bb-455f-b99a-eb83f6729a13" />

#Wrinkles/Issues
- I found that I needed to try multiple times to get consistent readings and I believe this is because I'm sharing the modbus connection with the cx34 controller.
- I was confounded for a while when getting some temperature values, but eventually figured out that I needed treat them as signed longs.  That fixed it and allowed me to get negative values.
- There's various documentation from Chiltrix and other folks on what modbus addresses map to which values.  Certain values did not match the documentation, so your mileage may vary.  For example, the e2 setting is supposed to be a 0 or 1, but in fact seems to be 0-9 indicating some sort of 0 - 90% or something.


