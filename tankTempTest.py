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
	
print ("0",config.program0)
print ("1",config.program1)
print ("2",config.program2)
print ("3",config.program3)
print ("4",config.program4)
print ("5",config.program5)
print ("6",config.program6)


program = [[0] for i in range(7)]

for item in config.program0:
	program[0].append(float(item))
for item in config.program1:
	program[1].append(float(item))
for item in config.program2:
	program[2].append(float(item))
for item in config.program3:
	program[3].append(float(item))
for item in config.program4:
	program[4].append(float(item))
for item in config.program5:
	program[5].append(float(item))
for item in config.program6:
	program[6].append(float(item))	
print (program)
		
	
config.scan_count = 0

logTime = datetime.now()
logType = "log"
headings = ["Hour in Day"," Tank Temp","Per 10 Mins","Predicted Temp","Target Temp","State",\
	"NewState","StateTime","Tries","Max Trie","Error Count","Get Temp Error Count","Reason","Message"]
logBuffer = class_text_buffer(headings,config,logType,logTime)

relay = class_relay()
sensor = class_my_sensors(config)

# Set The Initial Conditions
the_end_time = datetime.now()
loop_time = 0
correction = 7.5
# Ensure start right by inc buffer
#last_fan_state = True
buffer_increment_flag = False
if config.scan_delay > 9:
	refresh_time = config.scan_delay
else:
	refresh_time = 2*config.scan_delay

targetTemp = 0
programTemp = 0
increment = True
changeRate = 0
lastTemp,tries,getTheTempError = sensor.getTheTemp()
lastLogTime = logTime
predictedTemp = 0
overRun = False
#restartFlag = False
#overRunLogCount = 0

tempMeasureErrorCount = 0
maxTries = 0
triesCount = 0
getTheTempErrorCount = 0

message = ""
reason = ""

allOff = 0
allOn = 1
overRun = 2

state = allOff
newState = allOff
boilerOn = False
pumpOn = False
stateStart = logTime


while (config.scan_count <= config.max_scans) or (config.max_scans == 0):

		#			States					Names		Value
		#  (1)	AllOff					AllOff				0
		#  (2)	Boiler and Pump on		AllOn				1
		#  (3)	OverRun					OverRun				2

		#Actions Required:
		# Continue in (1)	(all off)
		#					Calculate Time since Boiler went Off
		#					turn off both Relays
		#					if temp < target
		#							next state is AllOn
		#							trigger log
		# Continue in (2)	(all on)
		#					Calculate Time since Boiler went on
		#					turn on both relays
		#					if temp > target
		#						next state is Overrun
		#						trigger log
		# Continue in (3)	(overRun)
		#					Calculate Time since Overrun Started
		#					turn on pump, turn off boiler
		#					if temp < Target
		#						next ste is AllOn
		#						trigger log
		#					Elif overRun > time required
		#						next state is AllOff
		#						trigger log

# Get information needed which is:
#		time since state changes
#		target temperature
#		water temperature

					#######################################
					#   Get time and Target Temperature   #
					#######################################
	try:
		if state != newState:
			stateStart = logTime
			state = newState
		stateTime = round((logTime - stateStart).total_seconds() / 60,2)
		
		dayInWeek = logTime.weekday()
		hourInDay = logTime.hour + (logTime.minute/60)
		#dayTime = config.day_start <= hourInDay <= config.night_start
		#if boilerOn and pumpOn:
		#	pumpOverRunTime = config.pumpOverRunMinutes + 1
		#elif pumpOn:
		#	pumpOverRunTime = (logTime - overRunStartTime).total_seconds() / 60.0
	
		numValues = len(program[dayInWeek])
		ind = 0
		while ind<(numValues):
			progHour = program[dayInWeek][ind]
			if (ind + 2) < numValues:
				nextProgHour = program[dayInWeek][ind + 2]
			else:
				nextProgHour = 24
			progTemp = program[dayInWeek][ind + 1]
			if progHour < hourInDay < nextProgHour:
				targetTemp = progTemp
			ind +=2
			
		if state == allOn:
			targetTemp += config.hysteresis
		else:
			targetTemp -= config.hysteresis
			
		message = "day: " + str(dayInWeek) + " hour: " + str(round(hourInDay,2)) + " TargTemp: " + str(targetTemp)
	
						#############################################
						#  Get Water Temperature and Predicted temp #
						#############################################
	
		try:
			temp,tries,getTheTempError = sensor.getTheTemp()
			if tries > maxTries:
				maxTries = tries
			if sensor.errorCount > 0 :
				tempMeasureErrorCount += 1
			if getTheTempError:
				getTheTempErrorCount += 1
			lastTempReading = temp
		except:
			temp = round(lastTempReading,0) + 0.1234
			increment = True
			reason = reason + "TempReadError,"
		if temp < 0 : # No Senso Connected
			print("no Senso connected will turn Boiler Off")
			boilerOn = relay.relayOFF(config.boilerRelayNumber)
			pumpOn = relay.relayOFF(config.pumpRelayNumber)
			sys_exit()
		else:
			tempChange = temp - lastTemp
			changeRate = changeRate + (0.1 * (tempChange - changeRate))
			predictedTemp = temp + 10 * changeRate
			lastTemp = temp
	
						#######################################
						#  Do actions required based on State #
						#######################################	
	
		if state == allOff:
			#					(all off)
			#					Calculate Time since Boiler went Off
			#					turn off both Relays
			#					if temp < target
			#							next state is AllOn
			#							trigger log
			pumpOn = relay.relayOFF(config.pumpRelayNumber)
			boilerOn = relay.relayOFF(config.boilerRelayNumber)
			if predictedTemp <= targetTemp:
				increment = True
				newState = allOn
				reason = reason + "Boiler On"
				message = message + " Boiler and Pump on"
	
		if state == allOn:
			#               	(all on)
			#					Calculate Time since Boiler went on
			#					turn on both relays
			#					if temp > target
			#						next state is Overrun
			#						trigger log
			pumpOn = relay.relayON(config.pumpRelayNumber)
			boilerOn = relay.relayON(config.boilerRelayNumber)
			if predictedTemp > targetTemp:
				increment = True
				newState = overRun
				reason = reason + "Boiler Off Overrun On"
				message = message + " Pump on OverRun"
	
		if state == overRun:
			#					(overRun)
			#					Calculate Time since Overrun Started
			#					turn on pump, turn off boiler
			#					if temp < Target
			#						next ste is AllOn
			#						trigger log
			#					Elif overRun > time required
			#						next state is AllOff
			#						trigger log
			pumpOn = relay.relayON(config.pumpRelayNumber)
			boilerOn = relay.relayOFF(config.boilerRelayNumber)
			if predictedTemp <= targetTemp:
				increment = True
				newState = allOn
				reason = reason + "Temp Drop During OverRun"
				message = message + " Boiler Back On"
			elif stateTime > config.pumpOverRunMinutes:
				increment = True
				newState = allOff
				reason = reason + "End OverRun"
				message = message + " "

		# Do Logging
		logBuffer.line_values["Hour in Day"]  =  round(hourInDay,2)
		logBuffer.line_values["TankTemp"]  = temp
		logBuffer.line_values["Per 10 Mins"] = round(changeRate*10*60/config.scan_delay,2)
		logBuffer.line_values["Predicted Temp"] = round(predictedTemp,2)
		logBuffer.line_values["Target Temp"]  = targetTemp
		if state == allOff:
			logBuffer.line_values["State"]  = "Boiler Off"
		elif state == allOn:
			logBuffer.line_values["State"]  = "Boiler On"
		elif state == overRun:
			logBuffer.line_values["State"]  = "Pump OverRun"
		else:
			logBuffer.line_values["State"]  = "State Error "
			increment = True
			print("stare error",state, allOff, allOn, overRun)
		if newState == allOff:
			logBuffer.line_values["newState"]  = "Boiler Off"
		elif newState == allOn:
			logBuffer.line_values["newState"]  = "Boiler On"
		elif newState == overRun:
			logBuffer.line_values["newState"]  = "Pump OverRun"
		else:
			print("state error",newState, allOff, allOn, overRun)
			logBuffer.line_values["newState"]  = "State Error"
			increment = True
		logBuffer.line_values["stateTime"] = str(round(stateTime,2))
		logBuffer.line_values["Tries"]  = tries
		logBuffer.line_values["Max Tries"]  = maxTries
		logBuffer.line_values["Error Count"]  = tempMeasureErrorCount
		logBuffer.line_values["Get Temp Error Count"] = getTheTempErrorCount

		#Ensure logs at least every config.mustLog minutes 
		timeSinceLog = (logTime - lastLogTime).total_seconds() / 60.0

		if timeSinceLog > config.mustLog - (config.scan_delay/120):
			lastLogTime = logTime
			
			increment = True
			reason = reason + "aMustLog,"
			
		if (config.scan_count < 5) or (tries > 0) or (sensor.errorCount > 0) or getTheTempError:
			
			increment = True
			if (config.scan_count < 5):
				reason = reason + "start,"
			if (tries > 0):
				reason = reason + "tries,"
			if (sensor.errorCount > 0):
				reason = reason + "errors,"
			if getTheTempError:
				reason = reason + "temperror,"

		logBuffer.line_values["Reason"]  = reason
		logBuffer.line_values["Message"]  = message

		logBuffer.pr(increment,0,logTime,refresh_time)
		increment = False
		reason = ""
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
				if boilerOn or pumpOn:
					boilerOn = relay.relayOFF(config.boilerRelayNumber)
					pumpOn = relay.relayON(config.pumpRelayNumber)
					print("Running Pump for 60 seconds because boiler was on")
					time_sleep(60) 
				else:
					print("Switching off Pump and Boiler")
					boilerOn = relay.relayOFF(config.boilerRelayNumber)
					pumpOn = relay.relayOFF(config.pumpRelayNumber)			
					time_sleep(10)
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
		if boilerOn or pumpOn:
			boilerOn = relay.relayOFF(config.boilerRelayNumber)
			pumpOn = relay.relayON(config.pumpRelayNumber)
			print("Running Pump for 60 seconds because boiler was on")
			time_sleep(60) 
		else:
			boilerOn = relay.relayOFF(config.boilerRelayNumber)
			pumpOn = relay.relayOFF(config.pumpRelayNumber)			
			time_sleep(10)
		sys_exit()
	logTime = datetime.now()
