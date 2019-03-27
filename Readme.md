# Purpose 

This project is to simulate an instrument that implements SCPI or other commands, 
such as most instruments from Keysight, Agilent or Rohde & Schwarz.

Currently, only communication over the Socket protocol is supported.

These instruments normally attached using GPIB or LAN. LAN instruments usually use socket, 
but GPIB doesn't.


## Program start
> python3 socketMain.py NCD

if the instrument to simulate is an NCD.

## Connecting
On Linux and windows, connect with 
> telnet localhost 2049

and on Mac connect with
> nc localhost 2049

if the server is running on localhost, and the port for the simulated instrument is 2049. The port is reported when the program starts.
