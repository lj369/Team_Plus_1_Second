#---------------------------------------------------------------------------------------------
# structure of flag
# flag [0] = comparison_flag    True -> Remind needed                               False -> Remind not needed
# flag [1] = sent_flag          True -> Sent                                        False -> Not sent
# flag [2] = user_clean         True -> User has cleaned                            False -> Not yet
# flag [3] = user_acquire       True -> User acquire data                           False -> Not
# 
#
#----------------------------------------------------------------------------------------------

# This is the main function for our embedded system design, our design is a device that can be placed on the outer glass surface of consumers' fish tank to warn user when their fish tank is turbid.
# The basic principle is compare the real time colour reading with calibrated colour reading, and send corresponding message to user.
# We have also develop several extra features:
# I. User could define the reading time by UI program.
# II. User could actively acquire real time data by UI program.
# III. When there are large difference between calibration values, warning message will be sent.

import sys,time,network,machine,json
from umqtt.simple import MQTTClient
from machine import I2C,Pin,RTC
#library import above

import rgb_sensor, net_manage,initialisation,data_processing

flag,WAKE_TIME,MQTT_TOPIC,pled,i2c,client,calibration_value,next_cal_time,last_hour=initialisation.initialisation()

#net_manage.send_date(client,{'system time':current_time[4:6]},MQTT_TOPIC)
#current_time = [2017,2,16,4,7,55,44,0]

# We are facing trading off between two different features(low power consuming and fast user input response).
# In order to achieve low power consuming, we need to force our device to sleep when certain time(Read and calibration time) (approximately) arrives.
# However, in order to achieve fast user input response, we should keep polling and checking if there is any user inputs and respond to that (especially for acquire data feature).

while 1:
    time.sleep(1)
    #-------------------------------------------------------------------------------------------
    ## Alternative way to set time, we use this for testing because retrive time from broker is too time consuming
    #
    #current_time[4] = current_time[4]+1
    #print(current_time)
    #if current_time[4] >23:
    #    current_time[4]=0
    #    current_time[2]=current_time[2]+1
    #--------------------------------------------------------------------------------------------
    current_time=list(rtc.datetime())
    print ('system time is '+repr(current_time)+' \n')    

#!   if flag[1]==True:
#!       pwarn.value(1)
    if flag[3]==True:
        rgb_sensor.start_reading(i2c)
        acquired_value=data_processing.data_reading(i2c,pled)
        net_manage.send_data(client,{'message':('Current fish tank reading is: '+repr(acquired_value))})
        print (acquired_value)
        rgb_sensor.switch_off(i2c)
        flag[3]=False
    if ((last_hour != current_time[4])&(current_time[4] in WAKE_TIME)): 
        print ('check if the fish tank is clean') 
        rgb_sensor.start_reading(i2c)
        flag=data_processing.data_acquire_and_analysation(flag,calibration_value,client,i2c,pled)
        rgb_sensor.switch_off(i2c)
    if (current_time[4] == next_cal_time):
        rgb_sensor.start_reading(i2c)
        calibration_value=data_processing.system_calibration(calibration_value,client,i2c,pled)
        rgb_sensor.switch_off(i2c)
        print ('calibration after user has cleant fish tank')
#!        pwarn.value(0)
        flag[0]=False
        flag[1]=False
        flag[2]=False
    flag,WAKE_TIME,next_cal_time= data_processing.user_interaction(flag,WAKE_TIME,next_cal_time,client)
    last_hour=current_time[4]
    print (flag)
   # if (current_time[2] == 17)&(current_time[4] == 18):
   #     net_manage.send_user_data(client,[10,11,15,18])
   #     print ('new wait time sent')
