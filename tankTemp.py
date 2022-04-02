#!/usr/bin/env python3
# This file is part of pwm_fanshim.
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
# description     :pwm control for R Pi Cooling Fan, main progrm
# author          :David Torrens
# start date      :2019 12 12
# version         :0.2 May 2020
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
# Note use of pwm_test possible on next line
from pwm import class_pwm
from utility import fileexists,pr,make_time_text
from algorithm import class_control
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

headings = ["Count","Temp","Throttle","Heater Pwm","Pwm Freq","Change","SDLC","Debug Message"]
log_buffer = class_text_buffer(headings,config)

pwm = class_pwm(config)
control = class_control(config)
sensor = class_my_sensors(config)

# Set The Initial Conditions
the_end_time = datetime.now()
last_total = 0
loop_time = 0
correction = 7.5
# Ensure start right by inc buffer
last_fan_state = True
buffer_increment_flag = False
refresh_time = 4.2*config.scan_delay
shut_down_logic_target_reached = False
shut_down_logic_last_temp_reading = 20
shut_down_logic_temp_reducing_count = False
shut_down_logic_count = 0
message = "Not Yet"
print("########################################################################### !!!!! May 11th")

while (config.scan_count <= config.max_scans) or (config.max_scans == 0):
	try:
		# Loop Management and Watchdog
		loop_start_time = datetime.now()
		
		# Control
		temp = sensor.get_temp()
		control.calc(temp)
		pwm.control_heater(control.freq,control.speed)
		
		# Shutdown Logics
		change = round(temp - shut_down_logic_last_temp_reading,3)
		if temp > config.min_temp:
			shut_down_logic_target_reached = True
			message = "Over Min Temp and loop time Correction is: " + str(round(correction,2))
			shut_down_logic_count = 0 
		else:
			message = "Under Min Temp and loop time Correction is: " + str(round(correction,2))
		if (control.throttle == 100) and shut_down_logic_target_reached and (temp < shut_down_logic_last_temp_reading):
			shut_down_logic_count += 1

		shut_down_logic_last_temp_reading = temp
		
		# Logging
		log_buffer.line_values[0] = str(round(config.scan_count,3))
		log_buffer.line_values[1] = str(round(temp,2)) + "C"
		log_buffer.line_values[2] = str(round(control.throttle,1))+ "%"
		log_buffer.line_values[3] = str(round(control.speed,1)) + "%"
		log_buffer.line_values[4] = str(round(control.freq,3)) + "Hz"
		log_buffer.line_values[5] = str(round(change,2)) + " Shut Down Count: "
		log_buffer.line_values[6] = str(shut_down_logic_count)
		log_buffer.line_values[7] = message
		log_buffer.pr(True,0,loop_start_time,refresh_time)
		
		#do Shutdown if temperature keeps dropping and target reached
		if  shut_down_logic_count > 10 :
			call("sudo shutdown -h now", shell=True)
	
		# Loop Managemnt
		loop_end_time = datetime.now()
		loop_time = (loop_end_time - loop_start_time).total_seconds()
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
		pwm.control_heater(control.freq,0)
		time_sleep(10) 
		sys_exit()

	
