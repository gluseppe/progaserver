#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime

import cherrypy
from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log
from scenarioloader import ScenarioLoader
from scenario import Scenario
import simplejson as json

import progaconstants

"""
The Traffic object is istanciated by proga and it handles the dynamic evolution of the aircraft
during the simulation. It is constructed as a cherrypy Monitor, this means one of its function is 
called periodically to update the traffic situation
"""
class Traffic(plugins.Monitor):
	exposed = True


	def __init__(self, bus, sleeping_time):
		#chiama costruttore super-classe e registra la funzione che viene ripetuta
		plugins.Monitor.__init__(self, bus, self.startSimulation, sleeping_time)
		self.sleeping_time = sleeping_time
		self.myState = None
		self.scenarioloader = ScenarioLoader(progaconstants.SCENARIOS_FOLDER)
		self.scenario = None
		self.t0 = None
		self.tracks = None
		self.justStarted = True
		self.startedTracks = None
		self.finishedTracks = None



	def startSimulation(self):
		elapsed_seconds = time.time() - self.t0
		int_elapsed_seconds = int(elapsed_seconds)
		cherrypy.log("elapsed seconds:"+str(int_elapsed_seconds))

		if len(self.finishedTracks) == len(self.tracks):
			cherrypy.log("simulation is over bitch")

		
		if len(self.startedTracks) != len(self.tracks):
	
			#in questo punto ci andranno gli aerei che si muovono
			if self.justStarted:
				#se abbiamo appena iniziato, passati 0 secondi, faccio partire tutte le tracce senza delay
				for track in self.tracks:
					cherrypy.log("i'm track " + track.getTrackId() + " and my start is " + str(track.getStartTime()))
					if track.getStartTime() == 0 and track.hasStarted()==False:
						cherrypy.log("starting track " + track.getTrackId())
						track.startTrack()
						self.startedTracks.append(track)
	
				self.justStarted = False
	
			else:
				for track in self.tracks:
					if track.getStartTime() == int_elapsed_seconds and track.hasStarted()==False:
						cherrypy.log("starting track " + track.getTrackId())
						track.startTrack()
						self.startedTracks.append(track)

		cherrypy.log('\nsono passati ' + str(elapsed_seconds) + 'secondi')


		for startedTrack in self.startedTracks[:]:
			if self.makeStep(startedTrack) == True:
				self.startedTracks.remove(startedTrack)


	def makeStep(self, track):
		cherrypy.log("making step of track: " + track.getTrackId())
		arrived = not track.next(progaconstants.PLAYER_POINTER_INCREMENT*20)
		if arrived:
			self.finishedTracks.append(track)
		return arrived




	@cherrypy.tools.accept(media='text/plain')
	def GET(self, item=None):
		cherrypy.log("position requested")
		#ci va una condizione per ogni item che vogliamo esporre
		#in questo caso my-state
		if item == None or item == progaconstants.ITEM_MY_STATE:
			cherrypy.log("returning position")
			return self.getStrMyState()

		if item == None or item == progaconstants.ITEM_TRAFFIC:
			cherrypy.log("returning traffic")
			return self.getJSONTraffic()

	
	#questo rende sempre una versione stringa della posizione
	def  getStrMyState(self):
		return str(self.myState['lat']) + ' ' + str(self.myState['lon'])


	def getTraffic(self):
		traffic = []
		for track in self.startedTracks:
			traffic.append(track.getCurrentState())

		return traffic

	def getIntent(self, track_id):
		return ''


	#probabilmente sto usando una logica troppo intricata.
	#l obiettivo e' portare fuori un dictionary fatto cosi'
	# 'track_id' : (reference_track1, w1), (reference_track2, w2) eccetera
	# credo che anche la struttura dati sia sbagliata perche' non mi sembra che contenga bene
	# le informazioni che ci servono. bisogna ripensare ad una logica per identificare le referencetrack
	def computeInitialWeightsForReferenceTracks(self):
		weights = {}
		n_tracks_in_universe = 10
		storedReferenceTracks = []
		for track in self.tracks:
			ref_track = track.getDeclaredFlightIntent()
			if ref_track != None:
				all_reference_tracks = self.mergeReferenceTrackSets(storedReferenceTracks, ref_track)
				delta = 1 - progaconstants.DECLARED_INTENT_PROBABILITY
				uniform = delta / (n_tracks_in_universe-1)
				for reference_track in all_reference_tracks:
					weights[track.track_id] = ref_track_list





	def getJSONTraffic(self):
		return json.dumps(self.getTraffic())


	def POST(self,command=None,scenario_name=None):
		if command == 'start':
			if (self.scenarioloader.isAnythingLoaded()):
				cherrypy.log("\nStarting simulation")
				#si iscrive 
				self.subscribe()
				#si iscrive anche agli aggiornamenti di posizione pubblicati nel canale MYPOSITION_CHANNEL_NAME
				#e gli associa una funzione di gestione
				self.bus.subscribe(progaconstants.MYSTATE_CHANNEL_NAME,self.setMyState)
				#fa partire tutto
				self.t0 = time.time()
				self.startedTracks = []
				

				self.start()
			else:
				cherrypy.log("\nNo scenario loaded. Can't start simulation")
				raise cherrypy.HTTPError(400,"Can't start simulation: no scenario was loaded. Use loadscenario as command and provide a scenario folder")

		if command == 'stop':
			self.unsubscribe()
			self.stop()

		if command == 'loadscenario':
			self.scenario = self.scenarioloader.loadScenario(scenario_name)
			self.tracks = self.scenario.getTracks()
			self.startedTracks = []
			self.finishedTracks = []
			for track in self.tracks:
				cherrypy.log("I'm " + track.getTrackId() + " and i'll start at " + str(track.getStartTime()))



		return "hello world"

	def setMyState(self, myState):
		cherrypy.log("state set")
		self.myState = myState

	


	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass

