import sys,time,network,machine,json
from umqtt.simple import MQTTClient
from machine import I2C,Pin,RTC

import rgb_sensor, net_manage,data_processing

def initialisation():
    flag=[False for x in range(5)]
    WAKE_TIME = [11,17]
    SERVER='192.168.0.10'
    WIFI_NAME ='EEERover'
    WIFI_PASSWORD='exhibition'
    MQTT_TOPIC='esys/team_plus_one_second'
    TIME_TOPIC='esys/time'

    pled = Pin(0, Pin.OUT)
    pled.value(0)

    #!global pwarn
    #!pwarn=Pin(13,Pin.OUT)
    #!pwarn.value(0)
    #!print('variables defined \n')

    #!   global puser
    #!   puser=Pin(2,Pin.IN,Pin.PULL_UP)

    i2c=I2C(scl=Pin(5),sda=Pin(4),freq=100000)
    print('i2c defined \n')

    pctrl=Pin(14, Pin.IN)

    sta_if = network.WLAN(network.STA_IF)
    net_manage.wifi_connect(sta_if,WIFI_NAME,WIFI_PASSWORD)

    ap_if=network.WLAN(network.AP_IF)
    net_manage.internal_wifi_disconnect(ap_if)
    print('WiFi set up completed \n')

    rtc = machine.RTC()

    client = MQTTClient(machine.unique_id() ,SERVER)
    net_manage.mqtt_connect(client)

    print('rtc set up completed \n')

    #######net_manage.setting_datetime(rtc,client)
    #running_time=list(rtc.datetime())

    print('mqtt time retrieved \n')

    #no rtc
    #running_time=[2017,2,16,4,7,55,44,0]

    net_manage.mqtt_connect(client)
    net_manage.subscribe_message(client)
    calibration_value = [1,0,0,0]
    rgb_sensor.set_gain (i2c,pled)
    print ('calibration initialisation start')
    calibration_value=data_processing.data_reading(i2c,pled)
    print ('calibration initialisation finished')
    calibration_value=data_processing.system_calibration(calibration_value,client,i2c,pled)
    print(calibration_value)

    print('data calibrated \n clear to run \n')

    #print ('system time is '+repr(running_time)+' \n')
 
    next_cal_time=25

    last_hour=25
    
    return flag,WAKE_TIME,MQTT_TOPIC,pled,i2c,client,calibration_value,next_cal_time,last_hour
