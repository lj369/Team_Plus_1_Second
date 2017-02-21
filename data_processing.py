#---------------------------------------------------------------------------------------------
# structure of flag
# flag [0] = comparison_flag    True -> Fish tank is turbid                         False -> Still clear
# flag [1] = sent_flag          True -> Sent                                        False -> Not sent
# flag [2] = user_clean         True -> User has cleaned                            False -> Not yet
# flag [3] = user_acquire       True -> User acquire data                           False -> Not
# 
#
#----------------------------------------------------------------------------------------------


import sys,time,network,machine,json
from umqtt.simple import MQTTClient
from machine import I2C,Pin,RTC

import rgb_sensor, net_manage

#----------------------------------------------------------------------------------------------------------
# logical functions

# this function takes a list of values and eliminate the outsider, then return their average value.
def outsider_eliminator(data):
    if len(data)>2:
        data_max = max (data)
        data_min = min (data)
        data_average = (sum(data) - data_max - data_min)/(len(data)-2)
#    else if len(data)>0:
#        data_average = sum(data)/len(data)
#    else:
#        data_average = [1,0,0,0]
    return data_average

# this function normalise rgb respect to clear, it takes average rgb value and returns its normalised version
def normalisation(rgb_values):
    intensity = rgb_values[0]
    rgb_values[1] = rgb_values[1]/intensity
    rgb_values[2] = rgb_values[2]/intensity
    rgb_values[3] = rgb_values[3]/intensity
    rgb_values[0] = intensity
    return rgb_values

# this function takes rgb_normalised and calibration_value, decides if the current detected color color by exam the max error in 4 input data compare to calibrated data
# if max error exceed thershold (20%), then it sets flag[0] (comparison_flag) True. otherwise do nothing.
def comparison (flag,rgb_normalised,calibration_value):
    flag[0] = False
    error = [0,0,0,0]
    for i in range (0,4):
        error[i] = abs(rgb_normalised[i] - calibration_value[i])/calibration_value[i]
    if (max(error)>=0.20):
        flag[0] = True
    return flag

# this function send warning message to MQTT broker according to flag condition.(when Fish tank is turbid (i.e. flag[0] is True) and no message was sent(flag[1] is False),)
def message_sending (flag,client):
    if ((flag[0]==True)& (flag[1] == False)):
        net_manage.send_data(client,{'message':'Please refresh your fish tank!'})
        print ('Please refresh your fish tank!')
        flag[1] = True
    return flag


# this function sets next calibration time. (After user has cleaned the fish tank,)
# reason why choosing 9 am is because user won't normally clean fish tank in the morning, therefore there is sufficient time to wait until fish tank environment is stable.
# It makes calibration value more reliable. Also, always calibrating at 9 calibration eliminates some uncertaintly (such as ambient light intensity etc.).
# Therefore makes comparison between new and old calibration value possible and less likely causing problem.
# further development possible ---> according to current time determine next_cal_time rather than directly set it to 9
def cal_time_adjusting(flag): 
    next_cal_time=25
    if (flag[2] == True):
        next_cal_time = 9
        flag[2] == False
    return next_cal_time

# This function deals with user inputs
# It takes old WAKE_TIME and flags, when user wishes acquire real time data // has cleant fish tank // sets new detecting time, it will set corresponding flags/value.
def user_interrupt(flag,WAKE_TIME,client):
    user_msg=net_manage.check_message(client)
    while (user_msg!= 'None'):
        print (user_msg)
        if (user_msg=='acquire'):
            flag[3]=True
        if (user_msg=='clear'):
            flag[2]=True
        if (type(user_msg) is list):
                WAKE_TIME=user_msg
                print (WAKE_TIME)
                print (user_msg)
                print (type(user_msg))
        user_msg=net_manage.check_message(client)
    return flag,WAKE_TIME


# This function reads data from rgb sensor and returns a normalised average rgb value in a list [clear reading, r reading, g reading, b reading]
def data_reading(i2c,pled):
    rgb_sensor.start_reading(i2c)
    rgb_value = [0 for x in range(5)]
    clear_value =[0 for x in range(5)]
    r_value =[0 for x in range(5)]
    g_value =[0 for x in range(5)]
    b_value =[0 for x in range(5)]
    for i in range (0,5):
        time.sleep(1)
        rgb_value[i]=rgb_sensor.reading_period(i2c,pled)
        clear_value[i] = rgb_value[i][0]
        r_value[i] = rgb_value[i][1]
        g_value[i] = rgb_value[i][2]
        b_value[i] = rgb_value[i][3]
    rgb_sensor.switch_off(i2c)
    clear_average = outsider_eliminator(clear_value)
    r_average = outsider_eliminator(r_value)
    g_average = outsider_eliminator(g_value)
    b_average = outsider_eliminator(b_value)
    rgb_average = [clear_average, r_average, g_average, b_average]
    rgb_normalised = normalisation(rgb_average)
    print ('....')
    return rgb_normalised

#--------------------------------------------------------------
# system functions

# This function acquires real time rgb value, analyses data acquired and sets corresponding flags.
def data_acquire_and_analysation (flag,calibration_value,client,i2c,pled):
    rgb_normalised = data_reading(i2c,pled)
    print('measured value:')
    print(rgb_normalised)
    print('calibration value:')
    print(calibration_value)
    net_manage.send_data(client,{'measured value:':rgb_normalised,'calibration value:':calibration_value})
    flag=comparison (flag,rgb_normalised,calibration_value)
    return flag

# This function sets new calibration value for comparing, also when new calibration value shows large difference to last calibration value, it sends warining to user.
# This is because when calibration values differs quite much, it may because the user has accidentally send 'clear' message but have not clear the fish tank. Or the something unexpected happens.
# For example, something stick to fish tank glass that prevents normal reading.
def system_calibration (calibration_value,client,i2c,pled):
    rgb_sensor.set_gain (i2c,pled)
    calibration_value_new= data_reading(i2c,pled)
    error = [0,0,0,0]
    for i in range (4):
        error[i] = abs(calibration_value_new[i] - calibration_value[i]) / calibration_value[i]
    if (max(error) > 0.2):
        for i in range (4):
            error[i] = abs(calibration_value_new[i] - calibration_value[i]) / calibration_value[i]
        if (max(error) > 0.2):
            net_manage.send_data(client,{'message':'Large difference between previous calibration value and this calibration value.'})
            print ('Large difference between previous calibration value and this calibration value.')
    print(calibration_value_new)
    return calibration_value_new
    
# This function sends message to user, receives interpretation message from user and sets corresponding flags and calibration time.
def user_interaction(flag,WAKE_TIME,next_cal_time,client):
    flag=message_sending (flag,client)
    flag,WAKE_TIME=user_interrupt(flag,WAKE_TIME,client)
    next_cal_time=cal_time_adjusting(flag)
    return flag,WAKE_TIME,next_cal_time
