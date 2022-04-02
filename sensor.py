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
from w1thermsensor import W1ThermSensor

# Local application imports
from utility import pr,make_time_text,send_by_ftp

class class_my_sensors:
	def __init__(self,config):
		self.sensor4readings = config.sensor4readings

	def get_temp(self):
		# gets the temperature of the sensor for readings	
		found = False
		sensors = W1ThermSensor.get_available_sensors()
		for individual_sensor in W1ThermSensor.get_available_sensors():
			if self.sensor4readings == individual_sensor.id:
				temp = individual_sensor.get_temperature()
				found = True
			else:
				print("Found other sensor code : ",individual_sensor.id, "  please correct entry in config.cfg")
		if found:
			return temp
		else:
			return -100


