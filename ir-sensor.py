#!/usr/bin/env python

import os
import time
import pigpio
import json
import requests
import serial

def read_pixel():
	light_sensor = pigpio.read(config['pins']['reflective_sensor'])
	print(config['pins']['reflective_sensor'], 'light sensor:', str(light_sensor))

# load config
with open('config.json') as config_file:
	config = json.load(config_file)

# init GPIO to read reflective sensor
pigpio = pigpio.pi()
if not pigpio.connected:
	print('could not init pigpio')
	exit(0)
# pigpio.set_mode(config['pins']['reflective_sensor'], pigpio.INPUT)

keep_on_looping = 1
while keep_on_looping:
	read_pixel()
	time.sleep(1)

# close pigpio
pigpio.stop()
