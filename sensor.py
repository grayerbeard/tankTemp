#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# title           :sensor.py
# description     :get temperature of the temp sensor
# author          :David Torrens
# start date      :2019 12 12
# version         :0.1
# python_version  :3

# Standard library imports
# None

# Third party imports
from w1thermsensor import W1ThermSensor, Sensor
# Local application imports
from utility import fileExists
from config import class_config
from time import sleep as time_sleep
from inspect import currentframe as cf
from inspect import getframeinfo as gf


class class_my_sensors:
	def __init__(self,config):
		self.sensor4readings = config.sensor4readings
		self.lastTemp = round(config.maxTempDay0) + 0.4321
		self.errorCount = 0
		try:
			self.the_sensor = W1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=self.sensor4readings)
		except:
			print("Failed in sensor init id: ", self.sensor4readings)
			
	def getTheTemp(self):
		excRep = []
		tries = 0
		try:
			finfo = gf(cf())
			temp,tries = self.the_sensor.get_temperature()
			getTheTempError = False
			self.lastTemp = temp
		except Exception as err:
			exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err))
			excRep.append(exc)
			print(exc)
			temp = round(self.lastTemp) + 0.1111
			getTheTempError = True
			tries = 0
		return temp,tries,excRep

	def get_temp(self):
		# gets the temperature of the sensor for readings	
		found = False
		sensors = W1ThermSensor.get_available_sensors()
		for sensor in W1ThermSensor.get_available_sensors([Sensor.DS18B20]):
			sensor.id, sensor.get_temperature()
			if self.sensor4readings == sensor.id:
				found = True
				try:
					temp,tries = sensor.get_temperature()
					self.lastTemp = temp
					self.errorCount = 0
				except:
					print("Error in Reading temperature sensor.py line.49, error count : ",self.errorCount)
					temp = round(self.lastTemp,0) + 0.1234
					self.errorCount += 1
			else:
				print("Found other sensor code : ",sensor.id, "  please correct entry in config.cfg")
		#print("W1ThermSensor.tries : ",tries)
		if found  and (self.errorCount < 3):
			return temp,tries
		else:
			return -100

if __name__ == '__main__':

	from config import class_config

	#Set up Config file and read it in if present
	config = class_config()
	if fileexists(config.config_filename):		
		print( "will try to read Config File : " ,config.config_filename)
		config.read_file() # overwrites from file
	else : # no file so file needs to be writen
		config.write_file()
		print("New Config File Made with default values, you probably need to edit it")
	
	sensor = class_my_sensors(config)
	print("Sensor Class set up")
	print("\n")
	delay = 1
	limit = 10
	lastTemp = sensor.get_temp()
	time_sleep(delay)
	temp = sensor.get_temp()
	changeRate = temp - lastTemp
	for step in range(1,limit+1):
		temp = sensor.get_temp()
		tempChange = temp - lastTemp
		changeRate = changeRate + (0.25 * (tempChange - changeRate))
		predictedTemp = temp + 3 * changeRate
		lastTemp = temp	
		print("step ",step,"   temp ",temp,"   tempChange ",tempChange,"   changeRate " \
				,round(changeRate,4),"   predictedTemp ",predictedTemp)
		time_sleep(delay)
