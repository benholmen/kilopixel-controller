#!/usr/bin/env python

# MASTER CONTROL SCRIPT v0.01

import os
import sys
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
            print 'Sending ', line
            grbl.write(line + '\n')
            grbl_response = grbl.readline()
            print ' : ' + grbl_response.strip()

            # check status
            grbl.write('?')
            grbl_status = grbl.readline()
            while grbl_status.find('Idle') == -1:
                print '> ', grbl_status, "               \r",
                grbl.write('?')
                grbl_status = grbl.readline()
                time.sleep(0.1)

def still_connected(grbl):
    grbl.write('$I')
    grbl_response = grbl.readline()

    if len(grbl_response) > 0:
        return 1
    else:
        return 0

def go_home(grbl):
    print 'Homing'
    # home the machine
    send_gcode(grbl, '$H')

    # save the work position
    send_gcode(grbl, 'G10 L20 P1 X0 Y0 Z0')


####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

# init grbl
print 'init grbl'
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write("\r\n\r\n")
print '...'
time.sleep(2)
grbl.flushInput()
print '...'

# clear any alarms (probably due to failed homing)
send_gcode(grbl, '$X')

# what's the version of grbl? kind of a sanity check here
send_gcode(grbl, '$I')

# run grbl config
# not sure if this needs to be run every time but it can't hurt
print 'beginning setup gcode'
send_gcode_from_file(grbl, 'gcode/setup.gcode')
print 'finished setup'

# report settings
send_gcode(grbl, '$$')

go_home(grbl)

# send_gcode(grbl, 'G0 X90 Y45')
# sys.exit()

count = 0
keep_on_looping = 1
while keep_on_looping == 1:
    pixel = (0, randint(0, config['dimensions']['x']), randint(0, config['dimensions']['y']), randint(0, 1))

    print 'next pixel: ' + str(pixel)

    pixel_queue_id = pixel[0]
    x = pixel[1]
    y = pixel[2]
    state = pixel[3]

    # generate gcode to go to this pixel
    x_real = x * config['pixel_width']
    y_real = y * config['pixel_height']

    # send gcode to grbl
    gcode = 'G0 X' + str(x_real) + ' Y' + str(y_real)
    send_gcode(grbl, gcode)

    # simulate actuating the pixel
    time.sleep(2)

    # check if still connected
#    if still_connected(grbl) == 0:
#        print 'lost connection'
#        sys.exit(0)

    count = count + 1
    if count > 100:
        keep_on_looping = 0

    # re-home the machine periodically to avoid lost steps becoming catastrophic
    if count % config['rehome_interval'] == 0:
        go_home(grbl)


# close grbl
grbl.close()
