#-----------------------------------------------------------------
#This part of the code is focus on WiFi communication with the server
#The following are declaration of all related parameter and libraies
#-------------------------------------------------------
import sys, machine,network,time,json
from umqtt.simple import MQTTClient
from machine import RTC
TIME_TOPIC='esys/time'
MQTT_OUT_TOPIC='esys/plus_one_second/device_out'
MQTT_USER_IN_TOPIC='esys/plus_one_second/user_in'

#this function is to set up basic wifi connection with the modem
#This function only uses the wifi set up for this course
def wifi_connect(sta_if,WIFI_NAME,WIFI_PASSWORD):
    sta_if.connect(WIFI_NAME, WIFI_PASSWORD)
    time.sleep_ms(500)
    wificonnected=sta_if.isconnected()
    while wificonnected==False:
        sta_if.connect(WIFI_NAME, WIFI_PASSWORD)
        time.sleep_ms(500)
        wificonnected=sta_if.isconnected()

#This is to disconnect the Wifi internally       
def internal_wifi_disconnect(ap_if):
    ap_if.active(False)

#this is to connect to the MQTT server in EERover
def mqtt_connect(client):
    global MQTT_OUT_TOPIC
    client.connect()
    send_data(client,{'message':'connected'})
#Function for sending message in json format
def send_data(client,message):
    global MQTT_OUT_TOPIC
    payload = json.dumps(message)
    client.publish(MQTT_OUT_TOPIC,bytes(payload,'utf-8'))

#def send_user_data(client,message):
#    global MQTT_USER_IN_TOPIC
#    if (type(message) is list):
#        message={'message':message}
#    else:
#        message={'message':str(message)}
#    payload = json.dumps(message)
#    client.publish(MQTT_USER_IN_TOPIC,bytes(payload,'utf-8'))

#This is a call back function specific for retrieving real time clock    
def sub_time(topic,msg):
    global timenow
    timenow = json.loads(msg)['date']
    
#call back function for receiving user message
def sub_user_msg(topic,msg):
    global user_msg
    tmpp = json.loads(msg)
    if 'message' in tmpp:
        user_msg = tmpp['message']
        
#Function for setting up rtc
def setting_rtc(rtc):
    Yr=int(timenow[0:4])
    Mnh=int(timenow[5:7])
    Dy=int(timenow[8:10])
    Hr=int(timenow[11:13])
    Min=int(timenow[14:16])
    Snd=int(timenow[17:19])
    rtc.datetime((Yr, Mnh, Dy, 1, Hr, Min, Snd, 0))
    print(rtc.datetime())

#This is the higheset level function for rtc set up including calling MQTT
#and calling set up function
def setting_datetime(rtc,client):
    global TIME_TOPIC
    client.set_callback(sub_time)
    client.subscribe(TIME_TOPIC)
    client.wait_msg()
    setting_rtc(rtc)
    client.disconnect()

#This is to set up client and subscribe to MQTT function
def subscribe_message(client):
    global MQTT_USER_IN_TOPIC
    client.set_callback(sub_user_msg)
    client.subscribe(MQTT_USER_IN_TOPIC)
    
#This is function to retrieve user function
#'default' null for user_msg allow upper level function to reliease no message is received
def check_message(client):
    global user_msg
    user_msg='None'
    client.check_msg()
    return user_msg
    
    
