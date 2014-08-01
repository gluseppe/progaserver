#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime


import progaconstants

class Track(object):


	def __init__(self, track_id = ''):
		self.track_id = track_id
		self.path = []
		self.pointer = None
		self.startAt = 0;
		self.started = False


	def addStep(self, timestamp, lat, lon, altitude, vx, vy, vz, heading):
		if len(self.path) == 0:
			self.pointer = 0
		self.path.append({'timstamp':timestamp, 'lat':lat, 'lon':lon, 'altitude':altitude, 'vx':vx, 'vy':vy, 'vz':vz, 'heading':heading})

	def getPath(self):
		return self.path

	#sets when the flight is supposed to start moving.
	#startTime = 0 means it starts with no delay when the whole simulation starts
	#startTime = t (seconds), makes this flight start t seconds after the start of the simulation
	def setStart(self, startTime):
		self.pointer = startTime
		self.startAt = startTime



	def hasStarted(self):
		return self.started

	def startTrack(self):
		self.started = True

	def getCurrentState(self):
		if self.pointer != None:
			ret = self.path[self.pointer]
			ret['track_id'] = self.track_id
			return ret
		return None

	def next(self, increment=1):
		
		if self.pointer != None:
			self.pointer += increment
			if self.pointer >= len(self.path):
				return False
		
			return self.path[self.pointer]

	def getTrackId(self):
		return self.track_id

	def getStartTime(self):
		return self.startAt

