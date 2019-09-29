#!/usr/bin/env python

# MASTER CONTROL SCRIPT v0.01

import os
import time
import pigpio
import json
import serial
import mysql.connector
from random import randint

def check_pixel(x, y):
	print 'checking pixel state for ' + str(x) + ', ' + str('y')
	# TODO: maybe take a few readings, average them out, round up/down to get state?
	pigpio.set_mode(config['pins']['actuator_power'], pigpio.OUTPUT)
	pigpio.set_mode(config['pins']['actuator_sensor'], pigpio.INPUT)

	# Read value
	light_sensor = pigpio.read(config['pins']['actuator_sensor'])

	print 'light sensor: ' + str(light_sensor)

	pigpio.write(config['pins']['actuator_power'], pigpio.LOW)

	return light_sensor

def change_pixel(state):
	print 'turning pixel to state ' + str(state)
	pigpio.set_mode(config['pins']['actuator_power'], pigpio.OUTPUT)
	pigpio.set_mode(config['pins']['actuator_sensor'], pigpio.INPUT)

	pigpio.write(config['pins']['actuator_power'], pigpio.HIGH)

	turning = 1
	while turning > 0:
		turning += 1
		light_sensor = pigpio.read(config['pins']['actuator_sensor'])
		print 'light sensor: ' + str(light_sensor)
		time.sleep(0.2)
		if turning > 10:
			turning = 0

	pigpio.write(config['pins']['actuator_power'], pigpio.LOW)
	print 'done turning'

	return light_sensor

def send_gcode_from_file(grbl, filename):
	# note this probably wouldn't be a great idea for long gcode files. But this application should be VERY short gcode files
	print 'opening '+filename
	gcode_file = open(filename, 'r')
	gcode = gcode_file.read()
	gcode_file.close()

	send_gcode(grbl, gcode)

def send_gcode(grbl, gcode):
	for line in gcode.splitlines():
		line = line.strip()
		if len(line) > 1:
			print 'Sending ' + line
			grbl.write(line + '\n')
			grbl_response = grbl.readline()
			print ' : ' + grbl_response.strip()

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

def update_status():
	# update status
	mysql_cursor.execute("UPDATE kilopixel SET updated = UTC_TIMESTAMP() WHERE kilopixel_id = %s", (config['kilopixel_id'],))

####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

# connect to mysql
mysql = mysql.connector.connect(
  host = config['database']['host'],
  user = config['database']['username'],
  passwd = config['database']['password'],
  database = config['database']['database'],
  autocommit=True
)
mysql_cursor = mysql.cursor()

update_status()

# init pins if I want to use GPIO in this script
pigpio = pigpio.pi()
if not pigpio.connected:
  print 'could not init pigpio'
  exit(0)

# init grbl
print 'init grbl'
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write("\r\n\r\n")
print '...'
time.sleep(1)
grbl.flushInput()
print '...'

# what's the version of grbl?
send_gcode(grbl, '$I')

# run config grbl
# not sure if this needs to be run every time but it can't hurt
print 'beginning setup gcode'
send_gcode_from_file(grbl, 'gcode/setup.gcode')
print 'finished setup'

# home grbl which also unlocks it
# this doesn't really work without proper limit switches
# gcode = '$H'
# send_gcode(gcode)

keep_on_looping = 1
while keep_on_looping == 1:
	# get next pixel
	mysql_cursor.execute("SELECT pixel_queue_id, x, y, state FROM pixel_queue WHERE kilopixel_id = %s AND completed IS NULL LIMIT 1", (config['kilopixel_id'],))
	pixel = mysql_cursor.fetchone()

	# default mode: changing pixels
	mode = 'set state'

	if pixel is None:
		print 'next pixel is none, this would be a good time to update pixel state'
		mysql_cursor.execute("SELECT x, y FROM pixel_queue WHERE kilopixel_id = %s ORDER BY updated ASC LIMIT 1", (config['kilopixel_id'],))
		pixel = mysql_cursor.fetchone()
		mode = 'check state'
	else:
		mode = 'set state'
		pixel_queue_id = pixel[0]
		x = pixel[1]
		y = pixel[2]
		state = pixel[3]

	print 'next pixel: ' + str(pixel)

	# generate gcode to go to this pixel
	x_real = x * config['pixel_width']
	y_real = y * config['pixel_height']

	# random numbers are more fun for testing
	# x_real = randint(0, config['dimensions']['x'] * config['pixel_width'])
	# y_real = randint(0, config['dimensions']['y'] * config['pixel_height'])

	# send gcode to grbl
	gcode = 'G0 X' + str(x_real) + ' Y' + str(y_real)
	print 'beginning move'
	send_gcode(grbl, gcode)
	print 'done with move'

	if mode == 'check state':
		# check state
		state = check_pixel(x, y)
	else if mode == 'set state':
		# actuate pixel
		state = change_pixel(state)

		# mark the pixel as completed
		mysql_cursor.execute("UPDATE pixel_queue SET completed = UTC_TIMESTAMP() WHERE pixel_queue_id = %s", (pixel_queue_id,))

	# update pixel_state
	mysql_cursor.execute("REPLACE INTO pixel_state SET kilopixel_id = %s, x = %s, y = %s, updated = UTC_TIMESTAMP()", (config['kilopixel_id'], x, y, state))

	update_status()

	# check if still connected
#	if still_connected(grbl) == 0:
#		print 'lost connection'
#		exit(0)



# close grbl
grbl.close()

# close pigpio
pigpio.stop()

# close mysql
mysql.close()
