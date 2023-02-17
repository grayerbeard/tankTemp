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

# title           :buffer_log.py
# description     :pwm control for R Pi Cooling Fan
# author          :David Torrens
# start date      :2019 11 20
# version         :0.1
# python_version  :3

# Standard library imports
#from configparser import RawConfigParser
from csv import DictReader as csvDictReader
from csv import DictWriter as csvDictWriter
from datetime import datetime
from shutil import copyfile
from ftplib import FTP
from sys import argv as sysArgv
from sys import exit as sysExit

import socket

# Third party importstemp_log
# none
 
# Local application imports
from utility import pr,makeTimeText,sendByFtp

class class_buffer_log:
	def __init__(self,config,logTime):
		self.dbug = False
		self.sendPlainCount = 5
		self.noHeadingYet = True
		self.config = config
		timestamp = makeTimeText(logTime)
		self.logFileName = timestamp + "_" + self.config.progName + "_" + self.config.logType + ".csv"
		self.logFileNameSaveAs = self.config.progPath + self.config.logDirectory + self.logFileName
		self.localWwwLogFileName = self.config.localDirWww + "/" + self.config.logDirectory + self.logFileName
		if config.debug:
			print("self.log_filename : ",self.logFileName)
			print("self.log_filename_save_as : ",self.logFileNameSaveAs)
			print("self.local_www_log_filename : ",self.localWwwLogFileName)

	def logToFile(self,log_values):
		here = 	"log_cpu_data_to_file"
		#write the time at the start of the line in logging file
	
		if self.noHeadingYet:
			self.noHeadingYet = False
			self.logFile = open(self.logFileNameSaveAs,'w')
			#for hdg_ind in range(0,len(log_headings)):
			#	self.log_file.write(log_headings[hdg_ind] + ",")
			
			for heading  in self.config.headings:
				
				self.logFile.write(heading + ",")
			self.logFile.write("\n")
		#print("string made by Buffer Log")
		madeString = ""
		#for z in range(0,len(log_values),1):
		#	self.log_file.write(str(log_values[z]) + ",")
		#	madeString += str(log_values[z]) + ","
		#filedRecord = {}
		for heading in self.config.headings:
			#filedRecord[heading] = str(log_values[heading]) + ","
			self.logFile.write(str(log_values[heading]) + ",")
		#print("Logged as :",filedRecord)
		self.logFile.write("\n")
		self.logFile.flush()
		
		return
		
	def sendLogByFtp(self,FTP_dbug_flag,remote_log_dir,ftp_timeout):
		ftp_result = send_by_ftp(FTP_dbug_flag,self.config.ftp_creds_filename, self.log_filename_save_as, \
			self.log_filename,remote_log_dir,ftp_timeout)
		for pres_ind in range(0,len(ftp_result)):
			pr(FTP_dbug_flag,here, str(pres_ind) + " : ", ftp_result[pres_ind])
		if self.send_plain_count < 0 :
			ftp_result = send_by_ftp(FTP_dbug_flag,self.config.ftp_creds_filename, self.log_filename_save_as, \
				"log.csv",remote_log_dir,ftp_timeout)
			for pres_ind in range(0,len(ftp_result)):
				pr(FTP_dbug_flag,here, str(pres_ind) + " : ", ftp_result[pres_ind])
			self.send_plain_count = 10
		else:
			self.send_plain_count -= 1
			#print("Send plain count : ",self.send_plain_count)
		return
					
	def copyLogToWww(self,dbug_flag):
		try:
			if dbug_flag:
				print("Will try to copy : ",self.logFileNameSaveAs, " to ",self.localWwwLogFileName)
			copyfile(self.logFileNameSaveAs, self.localWwwLogFileName)
			if dbug_flag:
				print("Copied : ",self.logFileNameSaveAs, " to ",self.localWwwLogFileName)			#print( "Sent : " + self.log_filename_save_as + " to : ", self.local_www_log_filename)
		except:
			print("111 Fail with copy " + self.logFileNameSaveAs + " to : ", self.localWwwLogFileName)


