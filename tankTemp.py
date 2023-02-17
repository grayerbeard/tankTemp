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
from textBuffer import class_text_buffer
from relay import class_relay
from utility import fileExists,pr,makeTimeText
# Note use of sensor_test possible on next line
from sensor import class_my_sensors

#Set up Config file and read it in if present
config = class_config("config.cfg")
#if fileexists(config.config_filename):		
#	print( "will try to read Config File : " ,config.config_filename)
#	config.read_file() # overwrites from file
#else : # no file so file needs to be writen
#	config.write_file()
#	print("New Config File Made with default values, you probably need to edit it")
	
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
config.maxTempDay0 = max(program[0])
config.scan_count = 0

logTime = datetime.now()
logType = "log"
logBuffer = class_text_buffer(config,logTime)

relay = class_relay()
sensor = class_my_sensors(config)

# Set The Initial Conditions
the_end_time = datetime.now()
loop_time = 0
correction = 7.5
# Ensure start right by inc buffer
#last_fan_state = True
saveThis = False
#if config.scanDelay > 9:
#	refresh_time = config.scanDelay
#else:
#	refresh_time = 2*config.scanDelay

targetTemp = 0
programTemp = 0
saveThis = True
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


while (config.scan_count <= config.maxScans) or (config.maxScans == 0):

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
			temp,tries,excRep = sensor.getTheTemp()
			if tries > maxTries:
				maxTries = tries
			if sensor.errorCount > 0 :
				tempMeasureErrorCount += 1
			if getTheTempError:
				getTheTempErrorCount += 1
			lastTempReading = temp
		except:
			temp = round(lastTempReading,0) + 0.1234
			saveThis = True
			reason = reason + str(excRep)
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
				saveThis = True
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
				saveThis = True
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
				saveThis = True
				newState = allOn
				reason = reason + "Temp Drop During OverRun"
				message = message + " Boiler Back On"
			elif stateTime > config.pumpOverRunMinutes:
				saveThis = True
				newState = allOff
				reason = reason + "End OverRun"
				message = message + " "

		# Do Logging
		logBuffer.lineValues["Time"] =makeTimeText(logTime)
		logBuffer.lineValues["Hour in Day"]  =  round(hourInDay,2)
		logBuffer.lineValues["Tank Temp"]  = temp
		logBuffer.lineValues["Per 10 Mins"] = round(changeRate*10*60/config.scanDelay,2)
		logBuffer.lineValues["Predicted Temp"] = round(predictedTemp,2)
		logBuffer.lineValues["Target Temp"]  = targetTemp
		if state == allOff:
			logBuffer.lineValues["State"]  = "Boiler Off"
		elif state == allOn:
			logBuffer.lineValues["State"]  = "Boiler On"
		elif state == overRun:
			logBuffer.lineValues["State"]  = "Pump OverRun"
		else:
			logBuffer.lineValues["State"]  = "State Error "
			saveThis = True
			print("stare error",state, allOff, allOn, overRun)
		if newState == allOff:
			logBuffer.lineValues["NewState"]  = "Boiler Off"
		elif newState == allOn:
			logBuffer.lineValues["NewState"]  = "Boiler On"
		elif newState == overRun:
			logBuffer.lineValues["NewState"]  = "Pump OverRun"
		else:
			print("state error",newState, allOff, allOn, overRun)
			logBuffer.lineValues["NewState"]  = "State Error"
			saveThis = True
		logBuffer.lineValues["StateTime"] = str(round(stateTime,2))
		logBuffer.lineValues["Tries"]  = tries
		logBuffer.lineValues["Max Tries"]  = maxTries
		logBuffer.lineValues["Error Count"]  = tempMeasureErrorCount
		logBuffer.lineValues["Get Temp Error Count"] = getTheTempErrorCount

		#Ensure logs at least every config.mustLog minutes 
		timeSinceLog = (logTime - lastLogTime).total_seconds() / 60.0

		if timeSinceLog > config.mustLog - (config.scanDelay/120):
			lastLogTime = logTime
			
			saveThis = True
			reason = reason + "aMustLog,"
			
		if (config.scan_count < 5) or (tries > 0) or (sensor.errorCount > 0) or getTheTempError:
			
			saveThis = True
			if (config.scan_count < 5):
				reason = reason + "start,"
			if (tries > 0):
				reason = reason + "tries,"
			if (sensor.errorCount > 0):
				reason = reason + "errors,"
			if getTheTempError:
				reason = reason + "temperror,"

		logBuffer.lineValues["Reason"]  = reason
		logBuffer.lineValues["Message"]  = message

		logBuffer.pr(saveThis,logTime)
		saveThis = False
		reason = ""
		message = ""

		# Loop Managemnt
		loop_end_time = datetime.now()
		loop_time = (loop_end_time - logTime).total_seconds()
		config.scan_count += 1
		
		# Adjust the sleep time to aceive the target loop time and apply
		# with a slow acting correction added in to gradually improve accuracy
		if loop_time < (config.scanDelay - (correction/1000)):
			sleep_time = config.scanDelay - loop_time - (correction/1000)
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
				print("Will do sleep using config.scanDelay and reset correction to 7.5msec")
				correction = 7.5
				time_sleep(config.scanDelay)
			except Exception:
				print("some other error with time_sleep try with config.scanDelay")
				time_sleep(config.scanDelay) 
		else:
			time_sleep(config.scanDelay)
		last_end = the_end_time
		the_end_time = datetime.now()
		last_total = (the_end_time - last_end).total_seconds()
		error = 1000*(last_total - config.scanDelay)
		if error > 250*(config.scanDelay):
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
