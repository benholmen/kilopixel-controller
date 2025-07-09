#!/usr/bin/env python

# Before running this script start pigpiod:
# sudo pigpiod

import os
import time
import pigpio
import json
import requests
import serial
import http.client
import urllib

def read_pixel():
	return 'X' if pigpio.read(config['pins']['reflective_sensor']) else 'O'

def send_gcode_from_file(grbl, filename):
	# note this probably wouldn't be a great idea for long gcode files. But this application should be VERY short gcode files
	gcode_file = open(filename, 'r')
	gcode = gcode_file.read()
	gcode_file.close()

	send_gcode(grbl, gcode)

def send_gcode(grbl, gcode):
    for line in gcode.splitlines():
        line = line.strip()
        if len(line) > 1:
            print('Sending ', line)
            grbl.write(f"{line}\n".encode())
            grbl_response = grbl.readline()
            print(": ", grbl_response.strip())

            # check status
            grbl.write(b"?")
            grbl_status = grbl.readline()
            while grbl_status.find("Idle".encode()) == -1:
                print('> ', grbl_status, "               \r",)
                grbl.write(b"?")
                grbl_status = grbl.readline()
                time.sleep(0.1)

def still_connected(grbl):
	grbl.write(b"?")
	grbl_response = grbl.readline()

	if len(grbl_response) > 0:
		return 1
	else:
		return 0

def home():
	send_gcode('$H')

def goto_pixel(x, y):
	x_real = (x - 1) * config['pixel_width'] + config['x_offset']
	y_real = (y - 1) * config['pixel_height'] + config['y_offset']

	# move to pixel
	send_gcode(grbl, 'G0 X' + str(x_real) + ' Y' + str(y_real))

def poke_pixel(x, y):
	x_real = (x - 1) * config['pixel_width'] + config['x_offset']
	y_real = (y - 1) * config['pixel_height'] + config['y_offset']

	# poke pixel (but don't, temporarily)
	send_gcode(grbl, 'G0 Z4 X' + str(x_real + config['poke_offset']['x']) + ' Y' + str(y_real + config['poke_offset']['y']))
	# move right to clear pixel before retracting
	send_gcode(grbl, 'G0 X' + str(x_real + config['retract_offset']['x']) + ' Y' + str(y_real + config['retract_offset']['y']))
	# retract
	send_gcode(grbl, 'G0 Z0')

def get_next_pixel():
	url = "/api/" + str(config['kilopixel_id']) + "/next"

	conn = http.client.HTTPSConnection(config['api_host'])

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
	url = "/api/" + str(config['kilopixel_id']) + "/pixel"

	headers = {
		"Authorization": "Bearer " + config['api_key'],
		"Content-Type": "application/x-www-form-urlencoded",
	}
	form_data = urllib.parse.urlencode({
		"x": x,
		"y": y,
		"state": state,
	})

	conn = http.client.HTTPSConnection(config['api_host'])

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

# init grbl
print('initializing GRBL...')
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write(b"\r\n\r\n")
time.sleep(1)
grbl.flushInput()

# run config gcode
print('running setup gcode')
send_gcode_from_file(grbl, 'gcode/setup.gcode')

# loop forever
keep_on_looping = 1
while keep_on_looping == 1:
	pixel = get_next_pixel()

	if pixel is None:
		# park the machine
		home()
	else:
		print('next pixel: ' + str(pixel))
		print(pixel['x'], pixel['y'], pixel['poke'], pixel['state'])
        
		pixel['x'] = 32
		pixel['y'] = 2
		pixel['poke'] = False

		goto_pixel(pixel['x'], pixel['y'])

		if pixel['poke']:
			print('poking')
			poke_pixel(pixel['x'], pixel['y'])

		save_pixel_state(pixel['x'], pixel['y'], read_pixel())

	if not still_connected(grbl):
		print('lost connection')
		keep_on_looping = 0

# close grbl
grbl.close()

# close pigpio
pigpio.stop()
