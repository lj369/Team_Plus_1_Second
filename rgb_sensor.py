from machine import Pin,I2C
import sys
import time


#This is a function for purely reading sensor data
#return raw colour data in a list [clear,red,green,blue]
def read_colour(i2c):
    while (((i2c.readfrom_mem(0x29,0x93,1)[0])&0x01) == 0):
       time.sleep_ms(204)
    colour=i2c.readfrom_mem(0x29,0x94,8)
    colour_translate=[0 ,0,0,0]
    for i in range(4):
       colour_translate[i]=colour[(2*i+1)]+(colour[(2*i)]/256)
    s=' clear: ' + repr(colour_translate[0])+'; red: ' +repr(colour_translate[1])+'; green: '+repr(colour_translate[2])+';  blue: '+repr(colour_translate[3])+'.'
   # print(s)
    return [colour_translate[0],colour_translate[1],colour_translate[2],colour_translate[3]]

#--------------------------------------------------------------------------------
#this is sensor register introduction 
#0x81 is the integration time of the sensor
#0x83 controls the wait time before each measurement whcih is set to be 204 ms
#0x8d is enable wait long which is set to be inactive
#0x8f is the setting the gain of the sensor
#0x80 is general setting of the sensor including 0 is Power EN, 1 is RGBC ADC  EN
#3 is wait EN and 4 is interupt EN
#--------------------------------------------------------------------------------
#this is to configure the sensor and start reading from it
def start_reading(i2c):
    i2c.writeto_mem(0x29,0x81,'\x00')
    i2c.writeto_mem(0x29,0x83,'\xab')
    i2c.writeto_mem(0x29,0x8d,'\x00')
    i2c.writeto_mem(0x29,0x8f,'\x02')
    i2c.writeto_mem(0x29,0x80,'\x0b')

#Both power and ADC of sensors are turned off
def switch_off(i2c):
    i2c.writeto_mem(0x29,0x80,'\x08')   
    


    

#taking count amount of measurements with time_int seperation each of them
#pled is the control of sensor led and active high. It is switched off each time after reading
#to save power
def avg_data(i2c,time_int,count,pled):
    pled.value(1)
    time.sleep_ms(50)
    avg=[0 for x in range(4)]
    for x in range(count):
        tmpp = read_colour(i2c)
        time.sleep(time_int)
        for y in range(4):
            avg[y]+=tmpp[y]/count
    pled.value(0)
    return avg
            
    
#set gain is to change the gain of adc to maximise the swing of sensor data without saturating
#the output data to 255 but keep the highest data above 64 
def set_gain (i2c,pled):
    start_reading(i2c)
    pled.value(1)
    time.sleep_ms(50)
    current_gain=i2c.readfrom_mem(0x29,0x8f,1)[0]
    current_value=read_colour(i2c)
    while (current_gain<3) & (max(current_value)<64):
        i2c.writeto_mem(0x29,0x8f,repr(current_gain+1))
        current_gain+=1
        time.sleep(5)
        current_value=read_colour(i2c)
    while (current_gain>0) & (max(current_value)>=255):
        i2c.writeto_mem(0x29,0x8f,repr(current_gain-1))
        current_gain+=(-1)
        time.sleep(5)
        current_value=read_colour(i2c)
    pled.value(0)
    switch_off(i2c)

#top level functing to set the normal reading period with 10s in between each reading and
#take 5 readings each time
def reading_period(i2c,pled):
    return avg_data(i2c,0.1,5,pled)

#maintainance purpose
#enable for maintainance people to view gain store in specific register
def view_gain(i2c):
    gainlst={0:1,1:4,2:16,3:60}
    gain_index=gainlst[i2c.readfrom_mem(0x29,0x8f,1)[0]]
    print (repr(gain_index))
    return gain_index


    
