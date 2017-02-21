#------------------------------------------------------------------------------------------------
#This part of the code is for creating a user interface to the device asumming they have
#connected to the same broker
#it is able to ask the user to send three commands
#programme is aimed for user to enter ctrl+c to start entering commands and sleep
#unless data is sent
#"acquire":acquire real time data
#"clear":this is the command send after the user has cleaned the fish tank or need carlibration
#"check time update":this is for user to set check time every day which is by default 11 and 17
#------------------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt
import time
import json

#topic to communicate between user and device, host has to be changed by code
MQTT_DEVICE_IN_TOPIC='esys/plus_one_second/device_out'
MQTT_USER_OUT_TOPIC='esys/plus_one_second/user_in'
HOST='192.168.0.10'

#MQTT connection interrupt, allow reconnection to automatically subscribe to device_in topic
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_DEVICE_IN_TOPIC)

#message interrupt and call back function, only works when it is in a mqtt loop
def on_message(client, userdata, msg):
    msg_in=json.loads(msg.payload)['message']
    
    #when a dict is in 'message', then it is reporting data, thus have explanation of msg_in
    if type(msg_in) is dict:
        print 'the list is in [clear value, red value, green value, blue value]'
    print msg_in

#mqtt set up and mapping callback function
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

#connecting to HOST and start the loop allowing interrupt in the middle of while loop
client.connect(HOST)
client.loop_start()

print('Please press ctrl+c for enter\n')

#while loop forever
while(1):
    try:
        #allow keyboard interrupt to have delay which cannot be done by "pass"
        #when using pass, keyboard interrupt cause error instead of going into except loop
        time.sleep(3)
    
    except KeyboardInterrupt:
        print('commands available are "acquire", "clear", and "check time update"\n')
        print('please enter command one at a time without quotation marks')

        #user command in
        data_in=raw_input('Please type in your command: ')
        tmpp=data_in

        #if command is "acquire" or "clear", send it straight away
        if (tmpp=='acquire')|(tmpp=='clear'):
            client.publish(MQTT_USER_OUT_TOPIC,json.dumps({'message':tmpp}))
            
        #if command is "check time update", create a list and send the list
        elif (tmpp == 'check time update'):
            print 'check time update, please type time you wish to \n'
            print 'check your fish tank one by one then end with "end"'
            print 'please enter time in 24-hour format and as an int'
            data=[]
            data_in=raw_input()
            while (data_in != 'end'):
                if (data_in.isdigit()&(int(data_in) in range(1,25))):
                    data.append(int(data_in))
                else:
                    print 'wrong input'
                data_in=raw_input()
            print 'time enter are:'
            print data
            client.publish(MQTT_USER_OUT_TOPIC,json.dumps({'message':data}))
        else:
            print'command not available'
        #indicate end of 'except loop
        print 'waiting for next commmand'
        
#the following is part that is not going to arrive but to show maintainer how to stop the mqtt loop
client.loop_stop()
