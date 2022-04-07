#!/usr/bin/env python3
# This is for controlling a Hot Water Tank Temperature
# Copyright (C) 2015 Ivmech Mechatronics Ltd. <bilgi@ivmech.com>
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the OnTimeGNU General Public License as published by
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
boilerTurnOffTime = logTime
boilerTurnOnTime = logTime
onTime = 0
offTime = 0

logType = "log"
headings = ["Hour in Day"," Tank Temp","Per 10 Mins","Predicted Temp","Target Temp","Boiler Status","offTime","onTime","Message"]
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
if config.scan_delay > 9:
	refresh_time = config.scan_delay
else:
	refresh_time = 2*config.scan_delay
message = "No Message"
print("at Start up Turn Boiler Off")
boilerON = relay.relayOFF(config.relayNumber)

startHold = True
lastHoldMin = logTime.minute 
lastHoldSec = 0
targetTemp = 0
programTemp = 0
increment = True
changeRate = 0
lastTemp = sensor.get_temp()
lastLogTime = logTime
predictedTemp = 0

while (config.scan_count <= config.max_scans) or (config.max_scans == 0):
	try:
		while startHold:
		#while False:
			logTime = datetime.now()
			holdMin = logTime.minute
			holdSec = logTime.second
			if holdMin != lastHoldMin:
				startHold = False
				break
			if holdSec > (lastHoldSec + 5):
				print("Waiting for next Minute : ",(60 - holdSec))
				lastHoldSec = holdSec
		# Sort out Time in Day and Day in week etc
		logTime= datetime.now()
		dayInWeek = logTime.weekday()
		hourInDay = logTime.hour + (logTime.minute/60)
		dayTime = config.day_start <= hourInDay <= config.night_start
		#print("Hour in Time",hourInDay,config.day_start)
		#if config.day_start  <= hourInDay:
		#	print("greater tha or equal start")
		#	if hourInDay <= config.night_start:
		#		print("less than night start")
		#		dayTime = True
		#else:
		#	print(hourInDay,"    not greater than   ",config.day_start)
		boostTime = (dayInWeek == config.boost_day) and \
			( config.day_start < hourInDay < (config.day_start + config.boost_hours))
			
		#print("dayInWeek : ",dayInWeek,"  hourInDay : ",hourInDay, \
		#		"  dayTime : ",dayTime, "  boostTime : ",boostTime)
		
		# Work out Target Temperature
		if boostTime:
			if programTemp == config.boost_temp:
				message = "On Boost, "
			else:
				message = "Change to Boost, "
				increment = True
				#print("Change to Boost")
			programTemp = config.boost_temp
		elif dayTime:
			if programTemp == config.normal_temp:
				message = "On Day Temp, "
			else:
				message = "Change to Day, "
				#print("Change to Day")
			programTemp = config.normal_temp
		else:
			if programTemp == config.night_temp:
				message = "On Night Temp, "
			else:
				message = "Change to Night, "
				increment = True
				#print("Change to Night")
			programTemp = config.night_temp

		# Adjust Target using Hysterises depending if Boiler on
		if boilerON:
			targetTemp = programTemp + config.hysteresis
		else:
			targetTemp = programTemp - config.hysteresis
		
		# Do Control
		
		temp = sensor.get_temp()
		if temp < 0 : # No Senso Connected
			print("no Senso connected will turn Boiler Off")
			boilerON = relay.relayOFF(config.relayNumber)
		else:
			tempChange = temp - lastTemp
			changeRate = changeRate + (0.1 * (tempChange - changeRate))
			predictedTemp = temp + 15 * changeRate
			lastTemp = temp
			
			if predictedTemp >= targetTemp:
				if boilerON : # This is a change from ON to OFF
					#print("Temp NOW > Target so turn boiler off")
					boilerTurnOffTime = logTime
					offTime = (boilerTurnOffTime - boilerTurnOnTime).total_seconds() / 60.0
					increment = True
					message = message + " Boiler Turned OFF"
				boilerON = relay.relayOFF(config.relayNumber)
			else:
				if not boilerON : # This is a change from OFF to ON
					#print("Temp < Target so turn boiler ON")
					boilerTurnOnTime = logTime
					onTime = (boilerTurnOnTime - boilerTurnOffTime).total_seconds() / 60.0
					increment = True
					message = message + "Boiler Turned ON"
				boilerON = relay.relayON(config.relayNumber)

		# Do Logging
		#" Tank Temp","Target Temp","Boiler Status","Message"]
		logBuffer.line_values["Hour in Day"]  =  round(hourInDay,2)
		logBuffer.line_values["TankTemp"]  = temp
		logBuffer.line_values["Per 10 Mins"] = round(changeRate*10*60/config.scan_delay,2)
		logBuffer.line_values["Predicted Temp"] = round(predictedTemp,2)
		logBuffer.line_values["Target Temp"]  = targetTemp
		if boilerON:
			logBuffer.line_values["Boiler Status"]  = "ON"
		else:
			logBuffer.line_values["Boiler Status"]  = "OFF"
		logBuffer.line_values["onTime"]  = round(onTime,2)
		logBuffer.line_values["offTime"]  = round(offTime,2)
		logBuffer.line_values["Message"]  = message

		#Ensure logs at least every config.mustLog minutes 
		timeSinceLog = (logTime - lastLogTime).total_seconds() / 60.0
		if timeSinceLog > config.mustLog - (config.scan_delay/120):
			increment = True


		if config.scan_count < 5:
			increment = True
		logBuffer.pr(increment,0,logTime,refresh_time)
		if increment:
			lastLogTime = logTime
		increment = False
		message = ""

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
				boilerON = relay.relayOFF(config.relayNumber)
				print("  ##############  Boiler OFF ################ ")
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

	
