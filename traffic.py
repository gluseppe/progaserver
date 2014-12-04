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
from referencetrackshandler import ReferenceTracksHandler
from scenario import Scenario
import simplejson as json
from predictor import Predictor

import progaconstants
import requests
import pdb

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
		self.scenarioloader = None
		self.scenario = None
		self.t0 = None
		self.tracks = None
		self.justStarted = True
		self.startedTracks = None
		self.finishedTracks = None
		self.referenceTracksHandler = ReferenceTracksHandler()
		self.simulationStarted = False


	def sendFinishedCommand(self):
		s = requests.Session()
		r = s.post('http://127.0.0.1:8080/traffic', params={'command':'stop'})





	def startSimulation(self):
		elapsed_seconds = time.time() - self.t0
		int_elapsed_seconds = int(elapsed_seconds)
		cherrypy.log("elapsed seconds:"+str(int_elapsed_seconds))

		
		if len(self.finishedTracks) == len(self.tracks):
			#cherrypy.engine.publish(progaconstants.SIMULATION_FINISHED_CHANNEL_NAME)
			pass
			#self.sendFinishedCommand()
		else:

		
			if len(self.startedTracks) != len(self.tracks):
		
				#in questo punto ci andranno gli aerei che si muovono
				if self.justStarted:
					#se abbiamo appena iniziato, passati 0 secondi, faccio partire tutte le tracce senza delay
					for track in self.tracks:
						#cherrypy.log("i'm track " + track.getTrackId() + " and my start is " + str(track.getStartTime()))
						if track.getStartTime() == 0 and track.hasStarted()==False:
							#cherrypy.log("starting track " + track.getTrackId())
							track.startTrack()
							self.startedTracks.append(track)
		
					self.justStarted = False
		
				else:
					for track in self.tracks:
						if track.getStartTime() == int_elapsed_seconds and track.hasStarted()==False:
							#cherrypy.log("starting track " + track.getTrackId())
							track.startTrack()
							self.startedTracks.append(track)
	
			#cherrypy.log('\nsono passati ' + str(elapsed_seconds) + 'secondi')
	
	
			for startedTrack in self.startedTracks[:]:
				if self.makeStep(startedTrack,elapsed_seconds) == True:
					self.startedTracks.remove(startedTrack)

			#pdb.set_trace()
	
			cherrypy.engine.publish(progaconstants.UPDATED_TRAFFIC_CHANNEL_NAME,elapsed_seconds)


	def makeStep(self, track, elapsed_seconds):
		#cherrypy.log("making step of track: " + track.getTrackId())
		arrived = not track.next(elapsed_seconds, progaconstants.PLAYER_POINTER_INCREMENT)
		if arrived:
			#pdb.set_trace()
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

		if item == progaconstants.ITEM_TRAFFIC4MFS:
			cherrypy.log("returning traffic for microsoft fsx", context="MFS")
			return self.getJSONTraffic(progaconstants.ITEM_TRAFFIC4MFS)

	
	#questo rende sempre una versione stringa della posizione
	def  getStrMyState(self):
		return json.dumps(self.myState)

		#return str(self.myState['lat']) + ' ' + str(self.myState['lon'])


	def getJSONTraffic(self,requestFrom=None):
		return json.dumps(self.getTraffic(requestFrom))

	def getTraffic(self, requestFrom=None):
		

		traffic = {}
		for track in self.startedTracks:
			if requestFrom == None:
				traffic[track.track_id] = track.getCurrentState()
			else:
				#pdb.set_trace()
				traffic[track.track_id] = track.getFutureState(4)
			
		return traffic

	
	def getIntent(self, track_id):
		return ''


	


	"""
	Computes the initial weights of the reference tracks for each flight in the scenario.
	Returns a dictionary made like the followinf
	['AZA1234' : (ReferenceTrack1, ReferenceTrack2, ReferenceTrack3 ... ReferenceTrackN) ]
	Each ReferenceTrack item in the value list is a ReferenceTrack object. You can access the computed weight by
	the ReferenceTrack.w field. 
	"""
	def computeInitialWeightsForReferenceTracks(self):
		weights = {}
		for track in self.tracks:

			if track.declaredIntent == None:

				#cherrypy.log("computing weights for track:" + track.track_id)
				#returns a list of referencetrack objects without any weight but already associated with the given id
				all_intents = self.referenceTracksHandler.getAllIntents(track.track_id)
				wt = []
				for intent in all_intents:
					intent.w = 1.0/len(all_intents)
					wt.append(intent)
				weights[track.track_id] = wt
			else:

				declared_intent = track.declaredIntent
				declared_intent.w = progaconstants.DECLARED_INTENT_PROBABILITY
				#cherrypy.log("computing weights for track:" + track.track_id)
				if declared_intent.refTrackID == None:
					#cherrypy.log("computing weights for track:" + track.track_id)
					all_intents = self.referenceTracksHandler.getAllIntents(track.track_id)
					wt = []
					wt.append(declared_intent)
					residual = 1.0 - progaconstants.DECLARED_INTENT_PROBABILITY
					for intent in all_intents:
						intent.w = residual/len(all_intents)
						wt.append(intent)
				 	weights[track.track_id] = wt

				else:
					cherrypy.log("computing weights for track:" + track.track_id)
					all_intents = self.referenceTracksHandler.getAllIntents(track.track_id)
					wt = []
					wt.append(declared_intent)
					residual = 1.0 - progaconstants.DECLARED_INTENT_PROBABILITY
					for intent in all_intents:
						pdb.set_trace
						if intent.refTrackID != declared_intent.refTrackID:
							intent.w = residual/(len(all_intents)-1)
							wt.append(intent)

					weights[track.track_id] = wt

		
		#pdb.set_trace()
		return weights



	


	def POST(self,command=None,scenario_name=None):
		if command == 'start':
			if self.scenarioloader is not None:
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
				cherrypy.engine.publish(progaconstants.SIMULATION_STARTED_CHANNEL_NAME, self.t0)
				self.simulationStarted = True
			else:
				cherrypy.log("\nNo scenario loaded. Can't start simulation")
				raise cherrypy.HTTPError(400,"Can't start simulation: no scenario was loaded. Use loadscenario as command and provide a scenario folder")

		if command == 'stop':
			cherrypy.log("simulation is finished")
			#pdb.set_trace();
			cherrypy.engine.publish(progaconstants.SIMULATION_STOPPED_CHANNEL_NAME)
			self.unsubscribe()
			self.stop()
			self.simulationStarted = False

		if command == 'loadscenario':
			if self.simulationStarted:
				cherrypy.log("Can't load scenario while simulation is running. Stop simulation first and then load new scenario")

			else:

				self.scenarioloader = ScenarioLoader(progaconstants.SCENARIOS_FOLDER, self.referenceTracksHandler)
				self.scenario = self.scenarioloader.loadScenario(scenario_name)
				self.tracks = self.scenario.getTracks()
				self.initialWeights = self.computeInitialWeightsForReferenceTracks()
				cherrypy.engine.publish(progaconstants.INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME,self.initialWeights)
					
				for flight_id, r_tracks in self.initialWeights.items():
					cherrypy.log(flight_id + " n references: " + str(len(r_tracks)))
					for t in r_tracks:
						cherrypy.log("ref_track:"+t.refTrackID+" w:"+str(t.w))
	
	
				self.startedTracks = []
				self.finishedTracks = []
				cherrypy.engine.publish(progaconstants.SCENARIO_LOADED_CHANNEL_NAME)
				#for track in self.tracks:
					#cherrypy.log("I'm " + track.getTrackId() + " and i'll start at " + str(track.getStartTime()))



		return "hello world"

	def setMyState(self, myState):
		cherrypy.log("state set")
		self.myState = myState
		#pdb.set_trace()

	


	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass

