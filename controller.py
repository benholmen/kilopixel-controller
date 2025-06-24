#!/usr/bin/env python

import os
import time
import pigpio
import json
import requests
import serial

def read_pixel():
	light_sensor = pigpio.read(config['pins']['light_sensor'])
	print('light sensor:', str(light_sensor))

	return light_sensor > config['light_sensor_threshold']

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
	grbl.write('?')
	grbl_response = grbl.readline()

	if len(grbl_response) > 0:
		return 1
	else:
		return 0

def home():
	send_gcode('$H')

def goto_pixel(x, y):
	x_real = x * config['pixel_width'] + config['x_offset']
	y_real = y * config['pixel_height'] + config['y_offset']

	# send gcode to grbl
	send_gcode(grbl, 'G0 X' + str(x_real) + ' Y' + str(y_real))
	
	print('done with move')

def poke_pixel(x, y):
	x_real = x * config['pixel_width'] + config['x_offset'] + config['poke_slide']
	send_gcode(grbl, 'G1 Z4')
	send_gcode(grbl, 'G1 Z8 X' + str(x_real))
	send_gcode(grbl, 'G1 Z0')

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
			print("pixel status saved")
		else:
			print("An error occurred when saving the pixel state: HTTP", response.status)
	except Exception as e:
		print("An error occurred when saving the pixel state:", e)
	finally:
		conn.close()

# load config
with open('config.json') as config_file:
	config = json.load(config_file)

# init GPIO to read reflective sensor
pigpio = pigpio.pi()
if not pigpio.connected:
	print('could not init pigpio')
	exit(0)
pigpio.set_mode(config['pins']['reflective_sensor'], pigpio.INPUT)

# init grbl
print('initializing GRBL...')
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write("\r\n\r\n")
time.sleep(1)
grbl.flushInput()

# run config gcode
print('running setup gcode')
send_gcode_from_file(grbl, 'gcode/setup.gcode')

# home grbl which also unlocks it
home()

keep_on_looping = 1
while keep_on_looping == 1:
	pixel = get_next_pixel()

	if pixel is None:
		# park the machine
		home()
	else:
		print('next pixel: ' + str(pixel))
		x, y, state = pixel

		goto_pixel(x, y)
		poke_pixel(x, y)
		save_pixel_state(x, y, read_pixel())

	if ! still_connected(grbl):
		print('lost connection')
		keep_on_looping = 0

# close grbl
grbl.close()

# close pigpio
pigpio.stop()
