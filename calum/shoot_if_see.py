#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import numpy as np
import time

##logging.basicConfig(filename='example.log',level=logging.DEBUG)

class ServerMessageTypes(object):
	TEST = 0
	CREATETANK = 1
	DESPAWNTANK = 2
	FIRE = 3
	TOGGLEFORWARD = 4
	TOGGLEREVERSE = 5
	TOGGLELEFT = 6
	TOGGLERIGHT = 7
	TOGGLETURRETLEFT = 8
	TOGGLETURRETRIGHT = 9
	TURNTURRETTOHEADING = 10
	TURNTOHEADING = 11
	MOVEFORWARDDISTANCE = 12
	MOVEBACKWARSDISTANCE = 13
	STOPALL = 14
	STOPTURN = 15
	STOPMOVE = 16
	STOPTURRET = 17
	OBJECTUPDATE = 18
	HEALTHPICKUP = 19
	AMMOPICKUP = 20
	SNITCHPICKUP = 21
	DESTROYED = 22
	ENTEREDGOAL = 23
	KILL = 24
	SNITCHAPPEARED = 25
	GAMETIMEUPDATE = 26
	HITDETECTED = 27
	SUCCESSFULLHIT = 28
    
	strings = {
		TEST: "TEST",
		CREATETANK: "CREATETANK",
		DESPAWNTANK: "DESPAWNTANK",
		FIRE: "FIRE",
		TOGGLEFORWARD: "TOGGLEFORWARD",
		TOGGLEREVERSE: "TOGGLEREVERSE",
		TOGGLELEFT: "TOGGLELEFT",
		TOGGLERIGHT: "TOGGLERIGHT",
		TOGGLETURRETLEFT: "TOGGLETURRETLEFT",
		TOGGLETURRETRIGHT: "TOGGLETURRENTRIGHT",
		TURNTURRETTOHEADING: "TURNTURRETTOHEADING",
		TURNTOHEADING: "TURNTOHEADING",
		MOVEFORWARDDISTANCE: "MOVEFORWARDDISTANCE",
		MOVEBACKWARSDISTANCE: "MOVEBACKWARDSDISTANCE",
		STOPALL: "STOPALL",
		STOPTURN: "STOPTURN",
		STOPMOVE: "STOPMOVE",
		STOPTURRET: "STOPTURRET",
		OBJECTUPDATE: "OBJECTUPDATE",
		HEALTHPICKUP: "HEALTHPICKUP",
		AMMOPICKUP: "AMMOPICKUP",
		SNITCHPICKUP: "SNITCHPICKUP",
		DESTROYED: "DESTROYED",
		ENTEREDGOAL: "ENTEREDGOAL",
		KILL: "KILL",
		SNITCHAPPEARED: "SNITCHAPPEARED",
		GAMETIMEUPDATE: "GAMETIMEUPDATE",
		HITDETECTED: "HITDETECTED",
		SUCCESSFULLHIT: "SUCCESSFULLHIT"
	}
    
	def toString(self, id):
		if id in self.strings.keys():
			return self.strings[id]
		else:
			return "??UNKNOWN??"


class ServerComms(object):
	'''
	TCP comms handler
	
	Server protocol is simple:
	
	* 1st byte is the message type - see ServerMessageTypes
	* 2nd byte is the length in bytes of the payload (so max 255 byte payload)
	* 3rd byte onwards is the payload encoded in JSON
	'''
	ServerSocket = None
	MessageTypes = ServerMessageTypes()
	
	
	def __init__(self, hostname, port):
		self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ServerSocket.connect((hostname, port))

	def readTolength(self, length):
		messageData = self.ServerSocket.recv(length)
		while len(messageData) < length:
			buffData = self.ServerSocket.recv(length - len(messageData))
			if buffData:
				messageData += buffData
		return messageData

	def readMessage(self):
		'''
		Read a message from the server
		'''
		messageTypeRaw = self.ServerSocket.recv(1)
		messageLenRaw = self.ServerSocket.recv(1)
		messageType = struct.unpack('>B', messageTypeRaw)[0]
		messageLen = struct.unpack('>B', messageLenRaw)[0]
		
		if messageLen == 0:
			messageData = bytearray()
			messagePayload = {'messageType': messageType}
		else:
			messageData = self.readTolength(messageLen)
			logging.debug("*** {}".format(messageData))
			messagePayload = json.loads(messageData.decode('utf-8'))
			messagePayload['messageType'] = messageType
			
		logging.debug('Turned message {} into type {} payload {}'.format(
			binascii.hexlify(messageData),
			self.MessageTypes.toString(messageType),
			messagePayload))

		return messagePayload
		
	def sendMessage(self, messageType=None, messagePayload=None):
		'''
		Send a message to the server
		'''
		message = bytearray()
		
		if messageType is not None:
			message.append(messageType)
		else:
			message.append(0)
		
		if messagePayload is not None:
			messageString = json.dumps(messagePayload)
			message.append(len(messageString))
			message.extend(str.encode(messageString))
			    
		else:
			message.append(0)
		
		logging.debug('Turned message type {} payload {} into {}'.format(
			self.MessageTypes.toString(messageType),
			messagePayload,
			binascii.hexlify(message)))
		return self.ServerSocket.send(message)

def getheading(pos1, pos2):
	heading = np.arctan2(pos2[1] - pos1[1], pos2[0] - pos1[0])
	heading = np.degrees(heading)
	heading = (-heading)%360
	return np.abs(heading)

def distance(pos1, pos2):
 	return np.sqrt((pos2[1] - pos1[1])**2 + (pos2[0] - pos1[0])**2)

def update():
	target_pos = (0,0)
	target = False
	my_pos = (0,0)
	my_heading = 0
	while True:
		start_time = time.time()
		message = GameServer.readMessage()
		end_time = time.time()
	
		if message['messageType'] == 18:
			if message['Type'] == 'Tank':
				if message['Name'] == args.name:
					my_pos = (message['X'],message['Y'])
					my_heading = message['Heading']
					logging.info("my pos")

				else:
					logging.info("other pos")
					target_pos = (message['X'],message['Y'])
					target = True
					GameServer.sendMessage(ServerMessageTypes.STOPTURN)

		logging.info(end_time - start_time)
		if (end_time - start_time) > 0.1:
			break

	return my_pos, my_heading, target_pos, target
              
        

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='TeamA:RandomBot', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)


# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

# Spawn our tank

logging.info("Creating tank with name '{}'".format(args.name))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})

# Main loop - read game messages, ignore them and randomly perform actions
target_pos = (0,0)
target = False
my_pos = (0,0)

my_heading = 0

while True:
	if target == False:
		GameServer.sendMessage(ServerMessageTypes.TOGGLELEFT)
		message = GameServer.readMessage()
		if message['messageType'] == 18 && message['Type'] == 'Tank' && message['Name'] == args.name:
			my_pos = (message['X'],message['Y'])
			my_heading = message['Heading']
			logging.info("my pos")
		else:
			logging.info("other pos")
			target_pos = (message['X'],message['Y'])
			target = True
			GameServer.sendMessage(ServerMessageTypes.STOPTURN)
			
		# was merge conflict, james' problem now
		my_pos, my_heading, target_pos, target = update()
					

	else:
		heading = getheading(my_pos, target_pos)
		GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': heading})
		time.sleep(2)
		if distance(my_pos, target_pos) >= 50:
			logging.info("{} meters from target".format(distance(my_pos, target_pos)))
			GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': 20})
		else:
			GameServer.sendMessage(ServerMessageTypes.FIRE)
		time.sleep(1)
		target = False
	



### Logically split the game mechanics into different functions

# def searchFor(Enemy, Ammo, Health)

# most basic turn function, turns 
# def turnTo(message, int id) # where id determines 
#		heading = getheading(my_pos, target_pos) # get my_pos and target_pos from message
#		GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': heading})