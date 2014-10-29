#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime
import pdb


import progaconstants
from referencetrack import Point3D
import cherrypy

class Track(object):


	def __init__(self, track_id = ''):
		self.track_id = track_id
		self.path = []
		self.pointer = None
		self.startAt = 0;
		self.started = False
		self.declaredIntent = None
		self.firstTime = True;


	def addStep(self, timestamp, lat, lon, altitude, vx, vy, vz, heading, pitch, bank):
		if len(self.path) == 0:
			self.pointer = 0

		p3d = Point3D(lon, lat, altitude)
		xy = p3d.xyFromLonLat(lon, lat)
		self.path.append({'timestamp':timestamp, 'float_timestamp':float(timestamp), 'x':xy[0], 'y':xy[1], 'z':altitude, 'lat':lat, 'lon':lon, 'h':altitude, 'vx':vx, 'vy':vy, 'vz':vz, 'heading':heading, 'pitch':pitch, 'bank':bank})

	def getPath(self):
		return self.path

	#sets when the flight is supposed to start moving.
	#startTime = 0 means it starts with no delay when the whole simulation starts
	#startTime = t (seconds), makes this flight start t seconds after the start of the simulation
	def setStart(self, startTime):
		#self.pointer = startTime
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

	def getFutureState(self, lookahead=4):
		if self.pointer == None:
			return False

		#se per la prima volta inviamo la futureposition, in realta inviamo quella attuale perche
		#il flight simulator la utilizzera solo per inizializzare l aereo
		if self.firstTime: return self.path[self.pointer]

		futurePointer = self.pointer+1
		found = False
		difference = 0

		while not found:
			try:
				p = self.path[self.pointer]['float_timestamp']
				n =  self.path[futurePointer]['float_timestamp']
	
			except IndexError:
				return False

			if n-p >=lookahead:
				found = True
			else:
				futurePointer += 1

		futureStatus = self.path[futurePointer]
		pdb.set_trace()
		return futureStatus


	def next(self, elapsedtime, increment=1):

		elapsedtime = elapsedtime - self.startAt
		found = False
		if self.pointer == None:
			self.pointer = 0
		
		while not found:
			try:
				p = self.path[self.pointer]['float_timestamp']
				n =  self.path[self.pointer+1]['float_timestamp']
				
			except IndexError:
				return False

			if elapsedtime <= p:
				found = True
				continue

			if (p <= elapsedtime and n > elapsedtime):
				found = True
			else:
				self.pointer += 1


		status = self.path[self.pointer]
		cherrypy.log("%s,%s,%f"%(self.track_id,status['timestamp'],elapsedtime),context="TRACK,")
		return status

		

		
		

	def getTrackId(self):
		return self.track_id

	def getStartTime(self):
		return self.startAt


	#intent must be a ReferenceTrack object
	def setDeclaredFlightIntent(self, intent):
		self.declaredIntent = intent

	def getDeclaredIntent(self):
		return self.declaredIntent





