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

# title           :config.py
# description     :pwm control for Sauna Electric Heater Control
# author          :David Torrens
# start date      :2019 12 12
# version         :0.1
# python_version  :3

# Standard library imports
from configparser import RawConfigParser
from csv import DictReader as csv_DictReader
from csv import DictWriter as csv_DictWriter
#from datetime import datetime
#from shutil import copyfile
#from ftplib import FTP
#from sys import argv as sys_argv
from sys import exit as sys_exit
#import socket
from os import path
from sys import argv as sys_argv

# Third party imports
#from w1thermsensor import W1ThermSensor

# Local application imports
#from utility import pr,make_time_text,send_by_ftp

class class_config:
	def __init__(self):
# Start of items set in config.cfg
	# Scan
		self.scan_delay = 10		# delay in seconds between each scan (not incl sensor responce times)
		self.max_scans = 0			# number of scans to do, set to zero to scan for ever (until type "ctrl C")
		self.mustLog = 30			# number of minutes minimum between logging
	# Log
		self.log_directory = "log/"	# where to store log files
		self.local_dir_www = "/var/www/html" # default value for local web folder
		self.log_buffer_flag = True	 # whether to generate the csv log file as well as the html text file	
		self.text_buffer_length = 30	# number of lines in the text buffer in the html file	
	# Tank
		self.program0 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Monday Times and temperatures
		self.program1 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Tuesday Times and temperatures
		self.program2 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Wednesday Times and temperatures
		self.program3 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Thursday Times and temperatures
		self.program4 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Friday Times and temperatures
		self.program5 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Saturday Times and temperatures
		self.program6 = (30, 6,45, 7,30, 19,45, 20,30)  # Edit Sunday Times and temperatures
		self.normal_temp =  50.0
		self.night_temp = 35.0
		self.boost_temp = 65
		self.hysteresis = 1
		self.day_start = 6
		self.night_start = 9
		self.boost_day = 1
		self.boost_hours = 4
		self.boilerRelayNumber = 1
		self.pumpRelayNumber = 2
		self.pumpOverRunMinutes = 3
		self.sensor4readings = "031565de91ff"
		
# End of items set in config.cfg	

# Start of parameters are not saved to the creport.append((onfig file
		# Based on the program name work out names for other files
		# First three use the program pathname	
		self.prog_path = path.dirname(path.realpath(__file__)) + "/"
		self.prog_name = str(sys_argv[0][:-3])
		self.config_filename = "config.cfg"
		self.logType = "log" # default log type
		print("Program Name is : ",self.prog_name)
		print("config file is : ",self.config_filename)

	def read_file(self):
		here = "config.read_file"
		config_read = RawConfigParser()
		config_read.read(self.config_filename)
		section = "Scan"
		self.scan_delay = float(config_read.get(section, 'scan_delay')) 
		self.max_scans = float(config_read.get(section, 'max_scans'))
		self.mustLog = float(config_read.get(section, 'mustLog'))
		section = "Log"
		self.log_directory = config_read.get(section, 'log_directory')
		self.local_dir_www = config_read.get(section, 'local_dir_www')
		self.log_buffer_flag = config_read.getboolean(section, 'log_buffer_flag')
		self.text_buffer_length  = int(config_read.get(section, 'text_buffer_length'))		
		section = "Tank"
		self.program0 =  config_read.get(section, 'program0').split(",")
		self.program1 =  config_read.get(section, 'program1').split(",")
		self.program2 =  config_read.get(section, 'program2').split(",")
		self.program3 =  config_read.get(section, 'program3').split(",")
		self.program4 =  config_read.get(section, 'program4').split(",")
		self.program5 =  config_read.get(section, 'program5').split(",")
		self.program6 =  config_read.get(section, 'program6').split(",")
		self.normal_temp =  float(config_read.get(section, 'normal_temp'))
		self.night_temp =  float(config_read.get(section, 'night_temp'))
		self.boost_temp =  float(config_read.get(section, 'boost_temp'))
		self.hysteresis =  float(config_read.get(section, 'hysteresis'))
		self.day_start =  int(config_read.get(section, 'day_start'))
		self.night_start =  int(config_read.get(section, 'night_start'))
		self.boost_day =  int(config_read.get(section, 'boost_day'))
		self.boost_hours =  int(config_read.get(section, 'boost_hours'))
		self.boilerRelayNumber =  int(config_read.get(section, 'boilerRelayNumber'))
		self.pumpRelayNumber =  int(config_read.get(section, 'pumpRelayNumber'))
		self.pumpOverRunMinutes =  int(config_read.get(section, 'pumpOverRunMinutes'))
		self.sensor4readings =  str(config_read.get(section, 'sensor4readings'))

		return

	def write_file(self):
		here = "config.write_file"
		config_write = RawConfigParser()
		section = "Scan"
		config_write.add_section(section)
		config_write.set(section, 'scan_delay',self.scan_delay)
		config_write.set(section, 'max_scans',self.max_scans)
		config_write.set(section, 'mustLog',self.mustLog)
		section = "Log"
		config_write.add_section(section)
		config_write.set(section, 'log_directory',self.log_directory)
		config_write.set(section, 'local_dir_www',self.local_dir_www)
		config_write.set(section, 'log_buffer_flag',self.log_buffer_flag)
		config_write.set(section, 'text_buffer_length',self.text_buffer_length)	
		section = "Tank"	
		config_write.add_section(section)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)
		program0AsString  =",".join(map(str,self.program0))
		config_write.set(section, 'program0',program0AsString)

		config_write.set(section, 'normal_temp',self.normal_temp)
		config_write.set(section, 'night_temp',self.night_temp)
		config_write.set(section, 'boost_temp',self.boost_temp)
		config_write.set(section, 'hysteresis',self.hysteresis)		
		config_write.set(section, 'day_start',self.day_start)
		config_write.set(section, 'night_start',self.night_start)
		config_write.set(section, 'boost_day',self.boost_day)
		config_write.set(section, 'boost_hours',self.boost_hours)
		config_write.set(section, 'boilerRelayNumber',self.boilerRelayNumber)
		config_write.set(section, 'pumpRelayNumber',self.pumpRelayNumber)
		config_write.set(section, 'pumpOverRunMinutes',self.pumpOverRunMinutes)
		config_write.set(section, 'sensor4readings',self.sensor4readings)

		# Writing our configuration file to 'self.config_filename'
		pr(self.dbug, here, "ready to write new config file with default values: " , self.config_filename)
		with open(self.config_filename, 'w+') as configfile:
			config_write.write(configfile)
		return 0

