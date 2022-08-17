#!/usr/bin/env python3

import serial
import time
import threading
import settings

from pythonosc import dispatcher
from pythonosc import osc_server

channel = [0] * 513 
dmxd = {0: channel}

class PyDMX:
    def __init__(self,COM=settings.serial,Cnumber=512,Brate=250000,Bsize=8,StopB=2,use_prev_data=False,preserve_data_name="preserved_data.txt"):
    # try:
        #start serial
        self.channel_num = Cnumber
        try:
            self.ser = serial.Serial(COM,baudrate=Brate,bytesize=Bsize,stopbits=StopB)
            self.data = [0] * (self.channel_num+1)
            self.data[0] = 0 # StartCode
            self.sleepms = 1.0
            self.breakus = 176.0
            self.MABus = 16.0

        except serial.SerialException as err:
            print("Serial error: {0}".format(err))
            return

    def set_data(self,data):
        self.data=data

    def send(self):
        # Send Break : 88us - 1s
        try:
            self.ser.break_condition = True
            # Send MAB : 8us - 1s
            self.ser.break_condition = False
            time.sleep(self.MABus/1000000.0)
            
            # Send Data
            self.ser.write(bytearray(self.data))
            
            # Sleep
            time.sleep(self.sleepms/1000.0) # between 0 - 1 sec
            time.sleep(self.breakus/1000000.0)
        except:
            print("Serial error. Check the port.")
            time.sleep(5)
            return
        
        
        

    def sendzero(self):
        self.data = [0] * (self.channel_num+1)
        self.send()        

    def __del__(self):
        print('Close serial server!')
        # close with preserving current DMX data, I guess you may not need to reset DMX signal in this option.
        if self.use_prev_data:
            self.preserve_data()
        else:
            self.sendzero()
        self.ser.close()

def thread_function(): #Write to serial loop
    dmx = PyDMX(settings.serial, Cnumber=1)
    while 1:
        dmx.set_data(dmxd.get(0))
        dmx.send()


def osc_handler(addr, *args):
    global dmxd
    try:
        universe = int(addr.split("/")[-2])
        channel_num = int(addr.split("/")[-1])
        value = int(args[0])
        channel.pop(channel_num)
        channel.insert(channel_num, value)
        dmxd[universe] = channel

        print(f"universe {universe} channel {channel_num} = {value}")
    except ValueError:
        dmxd = {0: 0}
        print("Please, use /dmx/#/# format, reset channel")
        return



def main():
    
    x = threading.Thread(target=thread_function)
    x.start()
    print("Serial write DMX loop begin")

    disp = dispatcher.Dispatcher()
    disp.map("/dmx/*", osc_handler)
    server = osc_server.ThreadingOSCUDPServer(
        (settings.host, settings.port),
        disp
    )
    print(f"Serving on {server.server_address}")
    server.serve_forever()

    del dmx

if __name__ == '__main__':
    try: 
        main()
    except Exception as e:
        print(e)
