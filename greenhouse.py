#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) 2017 @Felix Stern
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import RPi.GPIO as GPIO
import Adafruit_DHT
from MCP3008 import MCP3008
import SDL_DS1307
import time

##################################################################
##################### CUSTOMIZEABLE SETTINGS #####################
##################################################################
SETTINGS = {
    "LIGHT_GPIO":       17,                     # GPIO Number (BCM) for the Relay
    "LIGHT_FROM":       10,                     # from which time the light can be turned on (hour)
    "LIGHT_UNTIL":      20,                     # until which time (hour)
    "LIGHT_CHANNEL":    0,                      # of MCP3008
    "LIGHT_THRESHOLD":  500,                    # if the analog Threshold is below any of those, the light will turn on
    "DHT_GPIO":         27,                     # GPIO Number (BCM) of the DHT Sensor
    "DHT_SENSOR":       Adafruit_DHT.DHT22,     # DHT11 or DHT22
    "TEMP_THRESHOLD":   23.0,                   # in Celcius. Above this value, the window will be opened by the servo
    "SERVO_GPIO":       22,                     # GPIO Number (BCM), which opens the window
    "SERVO_OPEN_ANGLE": 90.0,                   # degree, how much the servo will open the window
    "PLANTS": [
        {
            "NAME":                 "Tomaten",
            "MOISTURE_CHANNELS":    [1, 2],     # of MCP3008
            "MOISTURE_THRESHOLD":   450,        # if the average analog value of all sensors is above of this threshold, the Pump will turn on
            "WATER_PUMP_GPIO":      23,         # GPIO Number (BCM) for the Relais
            "WATERING_TIME":        10,         # Seconds, how long the pump should be turned on
        },
        {
            "NAME":                 "Salat",
            "MOISTURE_CHANNELS":    [3, 4],
            "MOISTURE_THRESHOLD":   450,
            "WATER_PUMP_GPIO":      24,
            "WATERING_TIME":        12,
        },
    ]
}
##################################################################
################# END OF CUSTOMIZEABLE SETTINGS ##################
##################################################################


def readTime():
    try:
        ds1307 = SDL_DS1307.SDL_DS1307(1, 0x68)
        return ds1307.read_datetime()
    except:
        # alternative: return the system-time:
        return datetime.datetime.utcnow()
    
def checkLight():
    timestamp = readTime()
    GPIO.setup(SETTINGS["LIGHT_GPIO"], GPIO.OUT, initial=GPIO.HIGH)
    
    if SETTINGS["LIGHT_FROM"] <= timestamp.hour <= SETTINGS["LIGHT_UNTIL"]:
        # check light sensors
        adc = MCP3008()
        # read 10 times to avoid measuring errors
        value = 0
        for i in range(10):
            value += adc.read( channel = SETTINGS["LIGHT_CHANNEL"] )
        value /= 10.0
        
        if value <= SETTINGS["LIGHT_THRESHOLD"]:
            # turn light on
            GPIO.output(SETTINGS["LIGHT_GPIO"], GPIO.LOW) # Relay LOW = ON
        else:
            # turn light off
            GPIO.output(SETTINGS["LIGHT_GPIO"], GPIO.HIGH)
    else:
        # turn light off
        GPIO.output(SETTINGS["LIGHT_GPIO"], GPIO.HIGH)
        
    
def wateringPlants():
    # read moisture
    adc = MCP3008()
    for plantObject in SETTINGS["PLANTS"]:
        value = 0
        for ch in plantObject["MOISTURE_CHANNELS"]:
            # read 10 times to avoid measuring errors
            v = 0
            for i in range(10):
                v += adc.read( channel = ch )
            v /= 10.0
            value += v
        
        value /= float(len(plantObject["MOISTURE_CHANNELS"]))
        
        if value > plantObject["MOISTURE_THRESHOLD"]:
            # turn pump on for some seconds
            GPIO.setup(plantObject["WATER_PUMP_GPIO"], GPIO.OUT, initial=GPIO.LOW)
            time.sleep(plantObject["WATERING_TIME"])
            GPIO.output(plantObject["WATER_PUMP_GPIO"], GPIO.HIGH)

def checkWindow():
    # read remperature
    humidity, temperature = Adafruit_DHT.read_retry(SETTINGS["DHT_SENSOR"], SETTINGS["DHT_GPIO"])
    
    GPIO.setup(SETTINGS["SERVO_GPIO"], GPIO.OUT)
    pwm = GPIO.PWM(SETTINGS["SERVO_GPIO"], 50)
    
    if temperature > SETTINGS["TEMP_THRESHOLD"]:
        # open window
        angle = float(SETTINGS["SERVO_OPEN_ANGLE"]) / 20.0 + 2.5
        pwm.start(angle)
    else:
        # close window
        pwm.start(2.5)
    # save current
    time.sleep(2)
    pwm.ChangeDutyCycle(0)


if __name__ == '__main__':
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # execute functions
        checkLight()
        wateringPlants()
        checkWindow()
    except:
        GPIO.cleanup()
