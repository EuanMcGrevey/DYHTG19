#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import threading
import numpy as np
import math

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

def getheading(pos1, pos2):
	heading = np.arctan2(pos2[1] - pos1[1], pos2[0] - pos1[0])
	heading = np.degrees(heading)
	heading = (-heading)%360
	return np.abs(heading)


def logic(name,port):

	# Connect to game server
    GameServer = ServerComms(args.hostname, port)

    GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': name})

	# Spawn our tank
    logging.info("Creating tank with name '{}'".format(name))

    my_pos = (0,0)
    my_heading = 0
    targ_pos = (0,0)
    targ_heading = 0
    aiming = False
    point = False

    while True:
        message = GameServer.readMessage()

        if message['messageType'] == 18:
            if message['Type'] == 'Tank':
                if message['Name'] == args.name:
                    my_pos = (message['X'],message['Y'])
                    my_heading = message['Heading']
                else:
                    #could change to check team
                    GameServer.sendMessage(ServerMessageTypes.STOPTURN)
                    targ_pos = (message['X'],message['Y'])
                    targ_heading = getheading(my_pos,targ_pos)
                    aiming = True

        if aiming:
            print("My bearing is {}. Target at {}".format(my_heading,targ_heading))
            if math.fabs(my_heading - targ_heading) < .1:
                print("Firing {}".format(targ_heading))
                GameServer.sendMessage(ServerMessageTypes.FIRE)
                aiming = False
            else:
                GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": targ_heading})
                print("turning to {}".format(targ_heading))
        else:
            #probably looking for something
            GameServer.sendMessage(ServerMessageTypes.TOGGLELEFT)

class Tank(threading.Thread):
    def __init__(self, threadID, name,port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port = 25565# + port

        def run(self):
            print ("creating {} on port {}".format(self.name,self.port))
            logic(self.name,self.port)

# Create 4 Tanks, each on a separate thread, and give them the AI corresponding to the logic function
threads = []

for i in range(1,5):
	threads.append(Tank(i, "lo-pressure:tank"+str(i),i))
	print(threads[i-1].name)
	threads[i-1].start()
	print(threads[i-1].name + " started\n")

for t in threads:
	t.join() # threads should never terminate - get killed when game ends and manually closed
