#!/usr/bin/env python

# MASTER CONTROL SCRIPT v0.2.0

import os
import time
import pigpio
import json
import requests
import serial
from random import randint

def change_pixel(x, y, state):
	print(f'setting {x}, {y} to {state}')

	pigpio.set_mode(config['pins']['actuator_power'], pigpio.OUTPUT)
	pigpio.set_mode(config['pins']['actuator_sensor'], pigpio.INPUT)

	pigpio.write(config['pins']['actuator_power'], pigpio.HIGH)

	turning = 1
	while turning > 0:
		turning += 1
		light_sensor = pigpio.read(config['pins']['actuator_sensor'])
		print('light sensor:', str(light_sensor))
		time.sleep(0.2)
		if turning > 10:
			turning = 0

	pigpio.write(config['pins']['actuator_power'], pigpio.LOW)

	print('✅ done turning')

	return state

def send_gcode_from_file(grbl, filename):
	# note this probably wouldn't be a great idea for long gcode files. But this application should be VERY short gcode files
	print('opening '+filename)
	gcode_file = open(filename, 'r')
	gcode = gcode_file.read()
	gcode_file.close()

	send_gcode(grbl, gcode)

def send_gcode(grbl, gcode):
	for line in gcode.splitlines():
		line = line.strip()
		if len(line) > 1:
			print('Sending ' + line)
			grbl.write(line + '\n')
			grbl_response = grbl.readline()
			print(' : ' + grbl_response.strip())

			# check status
			grbl.write('?')
			grbl_status = grbl.readline()
			while grbl_status.find('Idle') == -1:
				grbl.write('?')
				grbl_status = grbl.readline()
				time.sleep(1/500)

def still_connected(grbl):
	grbl.write('$I')
	grbl_response = grbl.readline()

	if len(grbl_response) > 0:
		return 1
	else:
		return 0

def home():
	send_gcode('$H')

def goto_pixel(x, y):
	x_real = x * config['pixel_width']
	y_real = y * config['pixel_height']

	# generate gcode to go to this pixel
	gcode = 'G0 X' + str(x_real) + ' Y' + str(y_real)
	print('↘️ beginning move')

	# send gcode to grbl
	send_gcode(grbl, gcode)
	print('done with move')

def get_next_pixel():
	url = f"/api/{config['kilopixel_id']}/next"

	conn = http.client.HTTPConnection(config['api_host'])

	try:
		conn.request("GET", url)
		response = conn.getresponse()

		response_data = response.read().decode()
		if response.status == 200:
			print("Next pixel:", json.loads(response_data))

			return json.loads(response_data)
		else:
			print("An error occurred when getting the next pixel: HTTP", response.status)
	except Exception as e:
		print("An error occurred when getting the next pixel:", e)
	finally:
		conn.close()

def save_pixel_state(x, y, state):
	url = f"/api/{config['kilopixel_id']}/pixel"
	headers = {
		"Authorization": f"Bearer {config['api_key']}",
		"Content-Type": "application/x-www-form-urlencoded",
	}
	form_data = urllib.parse.urlencode({
		"x": x,
		"y": y,
		"state": state,
	})

	conn = http.client.HTTPConnection(config['api_host'])

	try:
		conn.request("PUT", url, body=form_data, headers=headers)
		response = conn.getresponse()

		if response.status == 200:
			print("✅ pixel status saved")
		else:
			print("An error occurred when saving the pixel state: HTTP", response.status)
	except Exception as e:
		print("An error occurred when saving the pixel state:", e)
	finally:
		conn.close()

####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

# init pins if I want to use GPIO in this script
pigpio = pigpio.pi()
if not pigpio.connected:
  print('could not init pigpio')
  exit(0)

# init grbl
print('init grbl')
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write("\r\n\r\n")
print('...')
time.sleep(1)
grbl.flushInput()
print('...')

# what's the version of grbl?
send_gcode(grbl, '$I')

# run config grbl
# not sure if this needs to be run every time but it can't hurt
print('beginning setup gcode')
send_gcode_from_file(grbl, 'gcode/setup.gcode')
print('finished setup')

# home grbl which also unlocks it
# this doesn't really work without proper limit switches
home()

keep_on_looping = 1
while keep_on_looping == 1:
	pixel = get_next_pixel()

	print('next pixel:', str(pixel))

	if pixel is None:
		# park the machine
		home()
	else:
		print('next pixel: ' + str(pixel))
		x = pixel[0]
		y = pixel[1]

		goto_pixel(x, y)

		state = change_pixel(pixel[2])
		save_pixel_state(x, y, state)

	# check if still connected
	if still_connected(grbl) == 0:
		print('lost connection')
		exit(0)

# close grbl
grbl.close()

# close pigpio
pigpio.stop()
