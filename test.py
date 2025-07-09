#!/usr/bin/env python

# MASTER CONTROL SCRIPT v0.01

import os
import sys
import time
import json
import serial
from random import randint

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
            print('Sending ', line)
            grbl.write(line + '\n')
            grbl_response = grbl.readline()
            print(' : ' + grbl_response.strip())

            # check status
            grbl.write('?')
            grbl_status = grbl.readline()
            while grbl_status.find('Idle') == -1:
                print('> ', grbl_status, "               \r",)
                grbl.write('?')
                grbl_status = grbl.readline()
                time.sleep(0.1)

def still_connected(grbl):
    grbl.write('$I\n')
    grbl_response = grbl.readline()
    print('> ', grbl_response, len(grbl_response))

    if len(grbl_response) > 0:
        return 1
    else:
        return 0

####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

# init grbl
print('init grbl')
grbl = serial.Serial('/dev/ttyUSB0', 115200)
grbl.write("\r\n\r\n")
print('...')
time.sleep(2)
grbl.flushInput()
print('...')

# clear any alarms (probably due to failed homing)
send_gcode(grbl, '$X')

# what's the version of grbl? kind of a sanity check here
send_gcode(grbl, '$I')

# run grbl config
# not sure if this needs to be run every time but it can't hurt
print('beginning setup gcode')
send_gcode_from_file(grbl, 'gcode/setup.gcode')
print('finished setup')

# report settings
# send_gcode(grbl, '$$')

print('sleeping...')
time.sleep(2)
print('finished sleep')

keep_on_looping = 1
while keep_on_looping == 1:
    send_gcode_from_file(grbl, 'test.gcode')

    time.sleep(2)

# close grbl
grbl.close()
