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

from traffic import Traffic
import progaconstants
from predictor import Predictor
import pdb

"""
Questa classe gestisce le richieste verso il ramo di predizione

"""
class PredictionEngine(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time, traffic):
		plugins.Monitor.__init__(self, bus, self.predictionEngine, sleeping_time)
		self.bus.subscribe(progaconstants.UPDATED_TRAFFIC_CHANNEL_NAME,self.trafficUpdated)
		self.bus.subscribe(progaconstants.INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME,self.initialWeightsComputed)
		self.bus.subscribe(progaconstants.SIMULATION_STOPPED_CHANNEL_NAME,self.simulationFinished)
		self.bus.subscribe(progaconstants.SIMULATION_FINISHED_CHANNEL_NAME,self.simulationFinished)
		self.bus.subscribe(progaconstants.SIMULATION_STARTED_CHANNEL_NAME,self.simulationStarted)


		self.sleeping_time = sleeping_time
		self.traffic = traffic
		self.predictor = None

	"""
	prediction engine viene richiamata ogni sleeping_time secondi (vedi file progaconstant alla voce PREDICTION_SLEEP_SECONDS)
	per il momento e' impostata a 2. Possiamo usare questo hook per svolgere attivita' di contorno relative alla predizione.
	In teoria tutte quelle diverse dall'aggiornamento pesi che viene fatto dal Predictor su stimolo della funzione trafficUpdated
	"""
	def predictionEngine(self):
		cherrypy.log("prediction engine running", context='DEBUG')
		#pass
		#cherrypy.log("asking for traffic", context='DEBUG')
		#currentState = self.traffic.getTraffic()


	def initialWeightsComputed(self, initialWeights):
		#create Predictor Object
		cherrypy.log("initial weights computed", context='DEBUG')
		self.predictor = Predictor(self.traffic,initialWeights)


	def trafficUpdated(self, elapsedSeconds):
		cherrypy.log("Updating traffic", context='DEBUG')
		v = self.traffic.getTraffic()
		for t in v.values():
			cherrypy.log("id:"+str(t['flight_id']) + " x:" + str(t['x']) + " y:"+str(t['y']) + " z:"+str(t['z']) + " lat:"+str(t['lat'])+ " lon:"+str(t['lon']), context='TRAFFIC')
		self.predictor.trafficUpdated(elapsedSeconds)


	def simulationFinished(self):
		cherrypy.log("I AM PREDICTION ENGINE AND I KNOW SIMULATION IT'S FINISHED", context='DEBUG')
		self.unsubscribe()
		self.stop()

	def simulationStarted(self, t0):
		self.subscribe()
		self.start()
		cherrypy.log("SIMULATION ENGINE STARTING", context='DEBUG')
		self.predictor.simulationStarted(t0)




	@cherrypy.tools.accept(media='text/plain')
	def GET(self, flight_id, deltaT, nsteps):
		flight_IDs = [flight_id]
		deltaT = int(deltaT)
		nsteps = int(nsteps)
		prediction_matrix = self.predictor.predictionRequested(flight_IDs, deltaT, nsteps)
		pdb.set_trace()
		#scrivi qui codice di test
		cherrypy.log("%s" % prediction_matrix[flight_IDs[0]][deltaT][0], context="TEST")
		return "prediction"
	
	def POST(self,command=''):
		if command == 'start':
			cherrypy.log("starting prediction engine", context='DEBUG')
			self.subscribe()
			self.start()

		if command == 'stop':
			self.unsubscribe()
			self.stop()

	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass
