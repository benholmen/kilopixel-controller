#!/usr/bin/python

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
            print(line)
            grbl.write(f"{line}\n".encode())
            grbl_response = grbl.readline()
            print("    ", grbl_response.decode('utf-8').strip())

            # check status
            grbl.write(b"?")
            grbl_status = grbl.readline()
            while grbl_status.find("Idle".encode()) == -1:
                print('    ', grbl_status.decode('utf-8').strip())
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

def poke_pixel(x, y):
	x_real = x * config['pixel_width'] + config['x_offset']
	y_real = y * config['pixel_height'] + config['y_offset']

	# move to pixel
	send_gcode(grbl, 'G0 X' + str(x_real) + ' Y' + str(y_real))

	# poke pixel
	send_gcode(grbl, 'G0 Z5 X' + str(x_real + config['poke_offset']['x']) + ' Y' + str(y_real + config['poke_offset']['y']))

	# move right to clear pixel and retract
	send_gcode(grbl, 'G0 Z0 X' + str(x_real + config['retract_offset']['x']) + ' Y' + str(y_real + config['retract_offset']['y']))

	# back off
	send_gcode(grbl, 'G0 Z0.2')

def read_pixel(x, y):
	x_real = x * config['pixel_width'] + config['x_offset']
	y_real = y * config['pixel_height'] + config['y_offset']

	# move to reading position
	send_gcode(grbl, 'G1 X' + str(x_real + config['read_offset']['x']) + ' Y' + str(y_real + config['read_offset']['y']) + 'F5000')

	return 'O' if pigpio.read(config['pins']['reflective_sensor']) else 'X'

def get_next_pixel():
	url = "/api/" + str(config['kilopixel_id']) + "/next"

	try:
		start_time = time.time()
		conn.request("GET", url)
		response = conn.getresponse()

		response_data = response.read().decode()
		if response.status == 200:
			print("Next pixel:", json.loads(response_data))
			elapsed = time.time() - start_time
			print("GET time:", str(int(elapsed * 1000)), "ms")

			return json.loads(response_data)
		else:
			print("An error occurred when getting the next pixel: HTTP", response.status)
	except Exception as e:
		print("An error occurred when getting the next pixel:", e)

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

	print(str(form_data))

	try:
		start_time = time.time()
		conn.request("PUT", url, body=form_data, headers=headers)
		response = conn.getresponse()

		response_data = response.read().decode()
		if response.status == 200:
			elapsed = time.time() - start_time
			print("PUT time:", str(int(elapsed * 1000)), "ms")
			print(response_data);

			return json.loads(response_data)
		else:
			print("An error occurred when saving the pixel state: HTTP", response.status)
	except Exception as e:
		print("An error occurred when saving the pixel state:", e)

# load config
with open('config.json') as config_file:
	config = json.load(config_file)

# init GPIO to read reflective sensor
pigpio = pigpio.pi()
if not pigpio.connected:
	print('could not init pigpio, did you run sudo pigpiod?')
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

# open HTTPS connection that will be re-used
conn = http.client.HTTPSConnection(config['api_host'])

# loop forever
keep_on_looping = 1
pixel = get_next_pixel()
while keep_on_looping == 1:
	if pixel['x'] is None or pixel['y'] is None:
		# do nothing
		time.sleep(5)
	else:
		print('next pixel: ' + str(pixel))
        
		if pixel['poke']:
			print('poking')
			poke_pixel(pixel['x'], pixel['y'])

		pixel_state = read_pixel(pixel['x'], pixel['y'])

		pixel = save_pixel_state(pixel['x'], pixel['y'], pixel_state)

	if not still_connected(grbl):
		print('lost connection')
		keep_on_looping = 0

# close grbl
grbl.close()

# close pigpio
pigpio.stop()
