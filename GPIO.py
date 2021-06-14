#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import wiringpi as GPIO

outPin = 10
timeOut = 10 # Sec

GPIO.wiringPiSetup()
GPIO.pinMode(outPin, 1) # Output mode

GPIO.digitalWrite(outPin, 1) # Power on
time.sleep(timeOut)
GPIO.digitalWrite(outPin, 0) # Power off
exit(0)
