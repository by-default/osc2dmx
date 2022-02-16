#!/usr/bin/env python3
import serial
import time
import numpy as np
import paho.mqtt.client as mqtt
import threading
import settings

channel = [0] * 513 
dmxd = {0: channel}

class PyDMX:
    def __init__(self,COM=settings.serial,Cnumber=512,Brate=250000,Bsize=8,StopB=2,use_prev_data=False,preserve_data_name="preserved_data.txt"):
    # try:
        #start serial
        self.channel_num = Cnumber
        try:
            self.ser = serial.Serial(COM,baudrate=Brate,bytesize=Bsize,stopbits=StopB)
            self.data = np.zeros([self.channel_num+1],dtype='uint8')
            self.data[0] = 0 # StartCode
            self.sleepms = 50.0
            self.breakus = 176.0
            self.MABus = 16.0
            # save filename
            self.preserve_data_name = preserve_data_name
            self.use_prev_data = use_prev_data
            # load preserved DMX data
            if use_prev_data:
                try:
                    self.load_data()
                except:
                    print("Something is wrong. please check data format!")
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
        self.data = np.zeros([self.channel_num+1],dtype='uint8')
        self.send()

    def load_data(self):
        self.data = np.loadtxt(self.preserve_data_name,dtype='int')        

    def preserve_data(self):
        np.savetxt(self.preserve_data_name,self.data)        

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

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    client.username_pw_set(settings.mqtt_login, settings.mqtt_pass)
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bus/dmx/#")
    

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global dmxd
    try:
        universe = int(msg.topic.split("/")[-2])
        channel_num = int(msg.topic.split("/")[-1])
        channel.pop(channel_num)
        channel.insert(channel_num, int(msg.payload))
        dmxd[universe] = channel
    except ValueError:
        dmxd = {0: 0}
        print("Please, use bus/dmx/#/# format, reset channel")
        return
    
    print(msg.topic+" "+str(msg.payload))

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    if settings.ca_certs:
        client.tls_set(ca_certs=settings.ca_certs)

    client.connect(settings.mqtt_ip, settings.mqtt_port, 60)
    x = threading.Thread(target=thread_function)
    x.start()
    print("Serial write DMX loop begin")
    client.loop_forever()
    del dmx
if __name__ == '__main__':
    while 1:
        try: 
            main()
        except:
            print("Please, debug the program. Check mqtt and serial ports. Comment this TRY.")
            time.sleep(1)