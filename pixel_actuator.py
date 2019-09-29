import os
import time
import pigpio
import json

####################
### LOAD CONFIG  ###
with open('config.json') as config_file:
    config = json.load(config_file)

# init pins if I want to use GPIO in this script
pi = pigpio.pi()
if not pi.connected:
	print 'could not init pigpio'
	exit(0)

pi.set_mode(config['pins']['actuator_power'], pigpio.OUTPUT)
pi.set_mode(config['pins']['actuator_sensor'], pigpio.INPUT)

pi.write(config['pins']['actuator_power'], pigpio.HIGH)

while 1:
	light_sensor = pi.read(config['pins']['actuator_sensor'])
	print 'light sensor: ' + str(light_sensor)
	time.sleep(0.2)
