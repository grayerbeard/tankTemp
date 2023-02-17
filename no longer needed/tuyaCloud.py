  # Standard library imports
from time import sleep as time_sleep
from os import path
from datetime import datetime
from sys import exit as sys_exit
from operator import itemgetter
import json
from configHp import class_config
from utilityTest import prd as debugPrint

# These used to get info on exceptions see "getStatus"
from inspect import currentframe as cf
from inspect import getframeinfo as gf

import tinytuya

class class_tuyaCloud:
	def __init__(self,config):
		self.numberDevices = len(config.names)
		self.numberCommandSets = config.numberCommandSets
		# tinyTuya uses info in tinytuya.json to sign in to cloud
		self.cloud = tinytuya.Cloud()  

		self.ids = config.ids
		self.names = config.names
		self.debug = config.debug
		debug = self.debug

		if(len(self.ids) != self.numberDevices) or \
			(len(self.names) != self.numberDevices) or \
			(len(self.names) != self.numberDevices):
			print("Error TuyaCloud line 28 lengths")
			print(len(self.ids),self.numberDevices,":",len(self.names),self.numberDevices, \
				len(self.names),":",self.numberDevices,int(self.values[device][ind]))
			sys_exit()

		self.commandPairs = [[]]*config.numberCommandSets

		# combine codes values and types
		self.codes = []
		self.codes.append(config.codes0)
		self.codes.append(config.codes1)
		self.values = []
		self.values.append(config.values0)
		self.values.append(config.values1)
		self.valuesTypes = []
		self.valuesTypes.append(config.values0Types)
		self.valuesTypes.append(config.values1Types)

		debugPrint(debug,"Codes: ",self.codes)
		debugPrint(debug,"values: ",self.values)
		debugPrint(debug,"ValueTypes: ",self.valuesTypes)

		#Following line for when checking read in of codes,values and types
		#sys_exit()

		# Following assumes all switched off at start
		self.switchOn = [False]*self.numberDevices

		# Create blank dictionaries to hold status info
		self.devicesStatus = [{}]*self.numberDevices

		# Get status for all the divices whoes ids are in the config file
		for device in range(0,self.numberDevices):
			status = self.cloud.getstatus(self.ids[device])
			deviceStatus =  {}

			# "Translate" the jsnn in "status" into a simple dictionary
			for item in status['result']:
				deviceStatus[item["code"]] = item["value"]
				if item["code"][:6] == "switch":
					self.switchOn[device] = item["value"]
			# Put dictionary for this device into master list
			self.devicesStatus[device] = deviceStatus

		codesLength = len(self.codes[1])
		valuesLength = len(self.values[1])
		debugPrint(debug,"test  ",codesLength,valuesLength)

		for device in range(self.numberCommandSets):
			#self.commandPairs.append([])
			codesLength = len(self.codes[device])
			valuesLength = len(self.values[device])
			if codesLength != valuesLength:
				debugPrint(debug,"Error with device command pairs : ","")
				debugPrint(debug,"device : ",device)
				debugPrint(debug,"codesLength : ",codesLength," codes : ",self.codes[device])
				debugPrint(debug,"codesLength : ",codesLength," values : ",self.values[device])
				sys_exit()

			debugPrint(debug,self.codes,"\n",self.valuesTypes)
			debugPrint(debug,"Command Pairs: ",self.commandPairs[device])
			debugPrint(debug,"length self.codes",len(self.codes[device]))
			self.commandPairs[device] = []*len(self.codes[device])

			# Ensure the command iis the right data type Boolean, String or Integer
			for ind  in range(len(self.codes[device])):
				debugPrint(debug,"Device: ",device," Ind: ",ind)
				# Boolean True
				if str(self.values[device][ind]) == 'True':
					self.commandPairs[device].append(dict(code = self.codes[device][ind],value = True))
				#Boolean False
				elif str(self.values[device][ind]) == 'False':
					debugPrint(debug,"self.commandPairs[device] ",self.commandPairs[device])
					debugPrint(debug,"self.codes[device] ",self.codes[device])
					debugPrint(debug,"self.codes[device][ind] ",self.codes[device][ind])
					self.commandPairs[device].append(dict(code = self.codes[device][ind],value = False))
					debugPrint(debug,"###self.commandPairs[device] ",self.commandPairs[device])
				# String
				elif self.valuesTypes[device][ind] == "s":
					self.commandPairs[device].append(dict(code = self.codes[device][ind],value = str(self.values[device][ind])))
				# Integer
				elif self.valuesTypes[device][ind] == "i":
					self.commandPairs[device].append(dict(code = self.codes[device][ind],value = int(self.values[device][ind])))
				else:
					debugPrint(debug,"THE Missing or incorrect code type", self.valuesTypes[device],self.codes[device]) ,
					sys_exit()
		debugPrint(debug,"\n \n Command Pairs\n",self.commandPairs),"\n"
		debugPrint(debug,"\n \n Command Pairs\n",json.dumps(self.commandPairs,indent = 4),"\n")
		for device in range(self.numberCommandSets):
			for ind  in range(len(self.codes[device])):
				debugPrint(debug,"Command Pairs: ",device,"/",ind," : ",self.commandPairs[device][ind])	
		debugPrint(debug,"\nInitial status \n",json.dumps(self.devicesStatus,indent = 4))

	def amendCommands(self,device,code,value):
		numberCommands = len(self.commandPairs[device])
		result = False
		for commandIndex in range(0,numberCommands):
			commandCode = self.commandPairs[device][commandIndex]["code"]
			if commandCode == code:
				if str(value) == 'True': 
					self.commandPairs[device][commandIndex]["value"] = True
				elif str(value) == 'False':
					self.commandPairs[device][commandIndex]["value"] = False
				elif self.valuesTypes[device][commandIndex] == "s": 
					self.commandPairs[device][commandIndex]["value"] = str(value)
				elif self.valuesTypes[device][commandIndex] == "i":
					self.commandPairs[device][commandIndex]["value"] = int(value)
				else:
					print("Missing or incorrect code type",commandIndex,self.valuesTypes[device],code)
					sys_exit()
				result = True # to signal found code
		#print("amended command Pairs: Target: ", device,code,value," \n",json.dumps(self.commandPairs[device],indent = 4),"\n")
		return result

	def upDateDevice(self,device):    # sets device to match values in commands

		# Assume online until get bad result and offline confirmed
		reason = ".."
		numberCommands =  len(self.commandPairs[device])
		success = [True]*self.numberDevices  
		#print(json.dumps(self.commandPairs[device]))
		for commandIndex in range(0,numberCommands):
			commandCode = self.commandPairs[device][commandIndex]["code"]
			statusValue = str(self.devicesStatus[device][commandCode])
			command = self.commandPairs[device][commandIndex]

			commandValue = str(command['value'])
			if (statusValue != commandValue) or (commandIndex == 0):
				commands = { 'commands' : command}
				try:
					status = self.cloud.sendcommand(self.ids[device],commands)
					success[commandIndex] = status['success']
					if status.get('msg','device is online') == 'device is offline':
						reason += self.names[device] + "is offLine"
					if not(success[commandIndex]):
						reason += self.names[device]+ "/" + commandCode + " cmnd  fail msg: " + status.get('msg','no msg')
						print("send command fail",reason)
				except:	
					reason += "Send Command : " +str(device) + "/" + str(commandIndex) + " Failed"
					success[commandIndex] = False

		# Delay neede to allow time to act on Command
		time_sleep(1)

		try:
			status = self.cloud.getstatus(self.ids[device])
			stSuccess = status['success']
		except:
			print("Exception at tuyacloud line 125")
			reason += " Exception at tuyacloud line 125 "
			stSuccess = False
		if stSuccess:
			statusValues = {}
			for item in status['result']:
				statusValues[item["code"]] = item["value"]
				if item["code"][:6] == "switch":
					 self.switchOn[device] = item["value"]
			self.devicesStatus[device] = statusValues
		else:
			reason += " Get Status Fail (result) " + self.names[device] + " "
			print("get status fail",reason)
		if status.get('msg','device is online') == 'device is offline':
			reason += self.names[device] + " is offLine"
			stSuccess = False
		return success,stSuccess,reason

	def getStatus(self):
		stSuccess = [False]*self.numberDevices
		status = []
		excRep = []
		finfo = gf(cf())
		for device in range(0,self.numberDevices):
			if True:
				reason = [""]*self.numberDevices
				try:
					finfo = gf(cf())
					status = self.cloud.getstatus(self.ids[device])
					stSuccess[device] = status.get('success',False)
				except Exception as err:
					exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err)," Device: " + str(device))
					excRep.append(exc)
					print(exc)
					stSuccess[device] = False
				if stSuccess[device]:
					statusValues = {}
					for item in status['result']:
						if (item["code"] == "switch") or (item["code"] == "switch_1"):
							if str(item["value"]) == "True":
								self.switchOn[device] = True
								statusValues[item["code"]] = True
							elif str(item["value"]) == "False":
								self.switchOn[device] = False
								statusValues[item["code"]] = False
							else:

								print("error TuyaCloud 182  ",item["code"],item["value"])
								sys_exit()
						else:
							statusValues[item["code"]] = item["value"]
					self.devicesStatus[device] = statusValues
				else:
					try:
						finfo = gf(cf())
						reason[device] += " Get Status Fail (result) " + \
								self.names[device] + " "
					except Exception as err:
						exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err)," Device: " + str(device))
						excRep.append(exc)
						print(exc)
						reason[device] += exc
				try:
					finfo = gf(cf())
					if status.get('msg','device is online') == 'device is offline':
						reason[device] += self.names[device] + " is offLine"
						stSuccess[device] = False
				except:
					exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err)," Device: " + str(device))
					excRep.append(exc)
					print(exc)
					reason[device] += exc
					print("exception line 251 in tuyaCloud")
		return stSuccess,reason,self.devicesStatus,excRep

	def listDevices(self):

		# Get info all accessable devices from the cloud account
		devices = self.cloud.getdevices()

		# Prepare Blank Lists
		deviceNames = [".."]*len(devices)
		deviceId = [".."]*len(devices)
		key = [".."]*len(devices)
		mac = [".."]*len(devices)

		# Put the basic info (names ids etc) into easily accessable lists.
		for i in range(len(devices)):
			deviceNames[i] = devices[i]["name"]
			deviceId[i] = devices[i]["id"]
			key[i] = devices[i]["key"]
			mac[i] = devices[i]["mac"]
		return devices,deviceNames,deviceId,key,mac

	def deviceProperties(self,id):
		properties = self.cloud.getproperties(id)
		return properties

	def deviceStatus(self,id):
		status = self.cloud.getstatus(id)
		return status

# test routine run when script run direct instaed of being used as a module
if __name__ == '__main__':
	config = class_config("configHp.cfg")
	config.scan_count = 0	
	cloud = class_tuyaCloud(config)

	# Get Basic info all devices on the account
	devices,deviceNames,deviceId,key,mac = cloud.listDevices()

	# Set up a text file to write to
	devicesFile = open("devicesList.txt",'w')

	# Get all available info and write to the text file
	for i in range(len(devices)):
		devicesFile.write("\n"+"Device Name: "+deviceNames[i])
		devicesFile.write("\nid :" + deviceId[i])
		devicesFile.write("\nkey : " + key[i])
		devicesFile.write("\nmac : " + mac[i])
		devicesFile.write("\n Properties of device named : " + deviceNames[i] + "\n" + json.dumps(cloud.deviceProperties(deviceId[i]),indent = 4))
		devicesFile.write("\n Status of device named : " + deviceNames[i] + "\n" + json.dumps(cloud.deviceStatus(deviceId[i]),indent = 4))
		devicesFile.write("\n")
	
	devicesFile.flush()

	print("All Tuya devices information output output to file 'devices.txt'")
	sys_exit()

	dHp = config.deviceNumberHp
	dHtrs = config.deviceNumberHeaters
	cloud.amendCommands(dHp,"temp_set",27)


	print("\n set to default")
	suess,stSuccess,failreason = cloud.upDateDevice(dHp)
	print("Reason : ",failreason)
	time_sleep(10)

	if cloud.amendCommands(dHp,"switch_1",True):
		print("found  ",code )
	else:
		print("error  ", code)
	print("\n set switch on")
	success,stSuccess,failreason = cloud.upDateDevice(dHp)
	print("Reason : ",failreason)
	time_sleep(10)

	code = "temp_set"
	value = 22
	cloud.amendCommands(dHp,code,value)
	print("\n set temp 22")
	success,stSuccess,failreason = cloud.upDateDevice(dHp)
	print("Reason : ",failreason)

	sys_exit()

	commandPairs[1][0]["value"] = False
	print(commandPairs[1][0]["code"]," set to ",commandPairs[1][0]["value"])
	commandPairs[1][4]["value"] = 25
	print(commandPairs[1][4]["code"]," set to ",commandPairs[1][4]["value"])
	listCodes = []
	for ind in range(0,len(commandPairs[1])):
		listCodes.append(commandPairs[1][ind]["code"] + " is " + str(commandPairs[1][ind]["value"]))
	print(listCodes)

	success,stSuccess,opFail,stOpFail,printMessage,reason = cloud.sendCommands(dHp,commandPairs[1],start,end)
	print(success,stSuccess,opFail,stOpFail,printMessage,reason)

	sys_exit()

	start = 0
	end = 0	
	success,stSuccess,opFail,stOpFail,printMessage,reason = cloud.sendCommands(dHp,commandPairs[1],start,end)
	print(success,stSuccess,opFail,stOpFail,printMessage,reason)

	start = 4
	end = 4
	success,stSuccess,opFail,stOpFail,printMessage,reason = cloud.sendCommands(dHp,commandPairs[1],start,end)
	print(success,stSuccess,opFail,stOpFail,printMessage,reason)
	sys_exit()


	# uncomment line below to get list of devices
	#cloud.listDevices()
	
	# uncomment three lines below and set id to check a particular device 
	#cloud.deviceProperties(ids[1])
	#cloud.deviceStatus(id)

	# uncomment three lines below and set id to check a particular device 
	#id = 'bf6f1291cc4b30aa8d1wsv'
	#properties = cloud.deviceProperties(id)

	#switchOn,opFail,printMessage,reason = cloud.operateSwitch(1,False)
	 
	#properties = cloud.deviceProperties(id)
	
	#print("\n \n ")
	#print(status)
	#print("\n \n")
	
	#print(online)


	count = 0

	while count < 5  :
		#status = cloud.deviceStatus(id)
	# print("Properties:"	, propertiecommandPairss)
	# print("Status:",status)
		temp, humidity, battery = cloud.getTH(id)
		print(temp,humidity,battery)
		print(datetime.now())
		count += 1
		#time_sleep(10 * 60)
		print(count)

	# uncomment three lines below and set id to check a particular device 
	#id = "01303121a4e57cb7ca0c"  
	#cloud.deviceProperties(id)
	#cloud.deviceStatus(id)	


	# test power switch that has a switch code of "switch_1"
	# Using id found from print out doing above
	# note we use switchNumber 0

	print("Test power switch")

	switchNumber = 0
	id = "bf5723e4b65de4a64fteqz"
	code = "switch_1"

	stateWanted = False
	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")
		if offLine:
			print("Device is Offline")
	time_sleep(5)

	stateWanted = True
	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")
		if offLine:
			print("Device is Offline")
	time_sleep(5)

	stateWanted = False
	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")	
		if offLine:
			print("Device is Offline")

	# test power on off of heat pump that has power switch code of "switch"
	# Using id found from print out doing above
	# note we use switchNumber 1

	print("Test power switch on/off of Heat Pump")

	switchNumber = 1
	id = "01303121a4e57cb7ca0c"
	code = "switch"
	stateWanted = False

	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")
		if offLine:
			print("Device is Offline")

	time_sleep(5)

	stateWanted = True
	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")

		if offLine:
			print("Device is Offline")

	time_sleep(20)

	stateWanted = False
	switchOn, successfullResult, offLine = cloud.operateSwitch(switchNumber,id,code,stateWanted)
	if successfullResult:
		print("worked ok")
		if switchOn:
			print("Switch On")
		else:
			print("Switch off")
	else:
		print("Switch Operation failed")	
		if offLine:
			print("Device is Offline")
  
    
