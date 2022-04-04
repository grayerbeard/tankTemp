##################################################

#           P26 ----> Relay_Ch1
#			P20 ----> Relay_Ch2
#			P21 ----> Relay_Ch3

##################################################
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time


class class_relay:
	def __init__(self):
		self.__relayPort = [26]
		self.__relayPort.append(20)
		self.__relayPort.append(21)
		for relayNumber in range(0,len(self.__relayPort)):
			print("Relay : " , (relayNumber + 1) , " is on Port :  " , self.__relayPort[relayNumber])

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)

		# Set Them Up
		GPIO.setup(self.__relayPort[0],GPIO.OUT)
		GPIO.setup(self.__relayPort[1],GPIO.OUT)
		GPIO.setup(self.__relayPort[2],GPIO.OUT)
		
		# Set all OFF
		GPIO.output(self.__relayPort[0],GPIO.HIGH)
		GPIO.output(self.__relayPort[1],GPIO.HIGH)
		GPIO.output(self.__relayPort[2],GPIO.HIGH)

	def relayOFF(self,relayNumber): # Relay number 1,2 or 3
		if 0 < int(relayNumber) < 4 :
			GPIO.output(self.__relayPort[relayNumber - 1],GPIO.HIGH)
			#print("Relay ",relayNumber," now off")
		else:
			print("Error with relayOFF : ",relayNumber)
		return False
			
	def relayON(self,relayNumber): # Relay number 1,2 or 3
		if 0 < int(relayNumber) < 4 :
			GPIO.output(self.__relayPort[relayNumber - 1],GPIO.LOW)
			#print("Relay ",relayNumber," now on")
		else:
			print("Error with relaON : ",relayNumber)
		return True

if __name__ == '__main__':
	relay = class_relay()
	print("Relay Class set up")
	print("\n")
	time.sleep(15)
	for relayNumber in range(1,4):
		relay.relayOFF(relayNumber)
		time.sleep(1)
		relay.relayON(relayNumber)
		time.sleep(1)
		relay.relayOFF(relayNumber)
		time.sleep(2)
		print("\n")	
	
	
	
	
