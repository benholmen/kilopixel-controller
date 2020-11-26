#!/usr/bin/env python

# MASTER CONTROL SCRIPT v0.01

import os
import time
import json
import serial
import mysql.connector
from random import randint

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

####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

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

x = 0
keep_on_looping = 1
while keep_on_looping == 1:
    if x > config['dimensions']['x']:
        x = 0

    # pixel = (0, randint(0, config['dimensions']['x']), randint(0, config['dimensions']['y']), randint(0, 1))
    pixel = (0, x, randint(0, config['dimensions']['y']), randint(0, 1))

    print 'next pixel: ' + str(pixel)

    pixel_queue_id = pixel[0]
    x = x + 1
    y = pixel[2]
    state = pixel[3]

    # generate gcode to go to this pixel
    x_real = x * config['pixel_width']
    y_real = y * config['pixel_height']

    # random numbers are more fun for testing
    x_real = randint(0, config['dimensions']['x'] * config['pixel_width'])
    y_real = randint(0, config['dimensions']['y'] * config['pixel_height'])

    # send gcode to grbl
    gcode = 'G0 X' + str(x_real) + ' Y' + str(y_real)
    print 'beginning move'
    send_gcode(grbl, gcode)
    print 'done with move'

    # check if still connected
#    if still_connected(grbl) == 0:
#        print 'lost connection'
#        exit(0)



# close grbl
grbl.close()
