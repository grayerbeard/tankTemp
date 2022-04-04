#!/usr/bin/env python3
# This is for controlling a Hot Water Tank Temperature
# Copyright (C) 2015 Ivmech Mechatronics Ltd. <bilgi@ivmech.com>
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# title           :tankTemp.py
# description     :For controlling Hot water Tank Temperature so as to minimise heating costs
# author          :David Torrens
# start date      :2022 04 04
# version         :0.1 April 2022
# python_version  :3

# Standard library imports
from time import sleep as time_sleep
from os import path
from datetime import datetime
from sys import exit as sys_exit
from subprocess import call

# Third party imports
# None
# Local application imports
from config import class_config
from text_buffer import class_text_buffer
from relay import class_relay
from utility import fileexists,pr,make_time_text
# Note use of sensor_test possible on next line
from sensor import class_my_sensors

#Set up Config file and read it in if present
config = class_config()
if fileexists(config.config_filename):		
	print( "will try to read Config File : " ,config.config_filename)
	config.read_file() # overwrites from file
else : # no file so file needs to be writen
	config.write_file()
	print("New Config File Made with default values, you probably need to edit it")
	
config.scan_count = 0
logTime= datetime.now()
logType = "log"
headings = [" Tank Temp","Target Temp","Boiler Status","Message"]
logBuffer = class_text_buffer(headings,config,logType,logTime)

relay = class_relay()
sensor = class_my_sensors(config)

# Set The Initial Conditions
the_end_time = datetime.now()
loop_time = 0
correction = 7.5
# Ensure start right by inc buffer
last_fan_state = True
buffer_increment_flag = False
refresh_time = 2*config.scan_delay
message = "No Message"
print("at Start up Turn Boiler Off")
boilerON = relay.relayOFF(config.relayNumber)

while (config.scan_count <= config.max_scans) or (config.max_scans == 0):
	try:
		# Sort out Time in Day and Day in week etc
		logTime= datetime.now()
		dayInWeek = logTime.weekday()
		hourInDay = logTime.hour
		dayTime = config.day_start < hourInDay < config.night_start
		boostTime = (dayInWeek == config.boost_day) and \
			( config.day_start < hourInDay < (config.day_start + config.boost_hours))
		
		# Work out Target Temperature
		if boostTime:
			targetTemp = config.boost_temp
		elif dayTime:
			targetTemp = config.normal_temp
		else:
			targetTemp = config.night_temp

		# Adjust Target using Hysterises depending if Boiler on
		if boilerON:
			targetTemp = targetTemp + config.hysteresis
		else:
			targetTemp = targetTemp - config.hysteresis
		
		# Do Control
		temp = sensor.get_temp()
		if temp >= targetTemp:
			print("Temp > Target so turn boiler off")
			boilerON = relay.relayOFF(config.relayNumber)
		else:
			print("Temp < Target so turn boiler ON")
			boilerON = relay.relayON(config.relayNumber)

		# Do Logging
		#" Tank Temp","Target Temp","Boiler Status","Message"]
		logBuffer.line_values["TankTemp"]  = temp
		logBuffer.line_values["Target Temp"]  = targetTemp
		if boilerON:
			logBuffer.line_values["Boiler Status"]  = "ON"
		else:
			logBuffer.line_values["Boiler Status"]  = "OFF"
		logBuffer.line_values["Message"]  = message

		logBuffer.pr(True,0,logTime,refresh_time)

		# Loop Managemnt
		loop_end_time = datetime.now()
		loop_time = (loop_end_time - logTime).total_seconds()
		config.scan_count += 1
		
		# Adjust the sleep time to aceive the target loop time and apply
		# with a slow acting correction added in to gradually improve accuracy
		if loop_time < (config.scan_delay - (correction/1000)):
			sleep_time = config.scan_delay - loop_time - (correction/1000)
			try:
				time_sleep(sleep_time)
			except KeyboardInterrupt:
				print(".........Ctrl+C pressed... Output Off")
				pwm.control_heater(control.freq,0)
				time_sleep(10)
				sys_exit()
			except ValueError:
				print("sleep_Time Error value is: ",sleep_time, "loop_time: ",
				      loop_time,"correction/1000 : ",correction/1000)
				print("Will do sleep using config.scan_delay and reset correction to 7.5msec")
				correction = 7.5
				time_sleep(config.scan_delay)
			except Exception:
				print("some other error with time_sleep try with config.scan_delay")
				time_sleep(config.scan_delay) 
		else:
			time_sleep(config.scan_delay)
		last_end = the_end_time
		the_end_time = datetime.now()
		last_total = (the_end_time - last_end).total_seconds()
		error = 1000*(last_total - config.scan_delay)
		if error > 250*(config.scan_delay):
			print("Large Error ignored it was : ",error)
		else:
			correction = correction + (0.15*error)
			# Following for looking at error correctoion
			# print("Error correcting OK, Error : ",error,"  Correction : ", correction)
	except KeyboardInterrupt:
		print(".........Ctrl+C pressed... Output Off")
		time_sleep(10) 
		sys_exit()

	
