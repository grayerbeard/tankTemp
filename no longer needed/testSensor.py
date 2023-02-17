
from config import class_config
from sys import exit as sys_exit
from time import sleep as time_sleep
from sensor import class_my_sensors
from utility import fileexists,pr,make_time_text
from datetime import datetime
from text_buffer import class_text_buffer

tempMeasureErrorCount = 0
config = class_config()
if fileexists(config.config_filename):		
	print( "will try to read Config File : " ,config.config_filename)
	config.read_file() # overwrites from file
else : # no file so file needs to be writen
	config.write_file()
	print("New Config File Made with default values, you probably need to edit it")
sensor = class_my_sensors(config)
logType = "test"
headings = ["SinceStart","Scan Count","Temp","ReadTime","Error Count","Try Count","getTheTempErrorCount","Max Tries"]

startRunTime = datetime.now()
logBuffer = class_text_buffer(headings,config,logType,startRunTime)
lastTemp,tries = sensor.get_temp()
scan_count = 0
max_scans = 200000
errorCount = 0.0
maxTries = 0
tryCount = 0
getTheTempErrorCount = 0

while scan_count <= max_scans:
	startTime = datetime.now()
	try:
		temp,tries,getTheTempError = sensor.getTheTemp()
		lastTemp = temp
		if tries > maxTries:
			maxTries = tries
		if tries > 0:
			tryCount += 1
		if getTheTempError:
			getTheTempErrorCount += 1
	except:
		temp = round(lastTemp,0) + 0.1234
		errorCount += 1
	doneTime = datetime.now()
	readTime = (doneTime - startTime).total_seconds()
	sinceStart = (doneTime - startRunTime).total_seconds()
	#print(round(sinceStart,3),scan_count, temp, round(readTime,3))
	logBuffer.line_values["SinceStart"]  =  round(sinceStart,3)
	logBuffer.line_values["Scan Count"]  =  scan_count
	logBuffer.line_values["Temp"]  =  temp
	logBuffer.line_values["ReadTime"]  =  round(readTime,3)
	logBuffer.line_values["Error Count"]  =  errorCount
	logBuffer.line_values["Try Count"]  =  tryCount
	logBuffer.line_values["getTheTempErrorCount"]  = getTheTempErrorCount
	logBuffer.line_values["Max Tries"]  =  maxTries
	logBuffer.pr(True,0,startTime,5)
	if sensor.errorCount > 0 :
		tempMeasureErrorCount += 1
	if tempMeasureErrorCount > 0 :
		print(" TE" + str(tempMeasureErrorCount) + ", ")
	if temp < 0 : # No Senso Connected
		print("No Sensors will exit")
		#BoilerOn = relay.relayOFF(config.boilerRelayNumber)
		#pumpOn = relay.relayOFF(config.pumpRelayNumber)
		sys_exit()
	scan_count += 1
