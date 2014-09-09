#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime


import progaconstants
from referencetrack import Point3D

class Track(object):


	def __init__(self, track_id = ''):
		self.track_id = track_id
		self.path = []
		self.pointer = None
		self.startAt = 0;
		self.started = False
		self.declaredIntent = None


	def addStep(self, timestamp, lat, lon, altitude, vx, vy, vz, heading):
		if len(self.path) == 0:
			self.pointer = 0

		p3d = Point3D(lon, lat, altitude)
		xy = p3d.xyFromLonLat(lon, lat)
		self.path.append({'timstamp':timestamp, 'x':xy[0], 'y':xy[1], 'z':altitude, 'lat':lat, 'lon':lon, 'h':altitude, 'vx':vx, 'vy':vy, 'vz':vz, 'heading':heading})

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
			ret['flight_id'] = self.track_id
			ret['started'] = self.started
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


	#intent must be a ReferenceTrack object
	def setDeclaredFlightIntent(self, intent):
		self.declaredIntent = intent

	def getDeclaredIntent(self):
		return self.declaredIntent





