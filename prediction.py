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


"""Questa classe gestisce le richieste verso il ramo di predizione

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
		cherrypy.log("prediction engine running")
		#pass
		#cherrypy.log("asking for traffic")
		#currentState = self.traffic.getTraffic()


	def initialWeightsComputed(self, initialWeights):
		#create Predictor Object
		self.predictor = Predictor(self.traffic,initialWeights)


	def trafficUpdated(self, elapsedSeconds):
		self.predictor.trafficUpdated(elapsedSeconds)

	def simulationFinished(self):
		cherrypy.log("I AM PREDICTION ENGINE AND I KNOW SIMULATION IT'S FINISHED")
		self.unsubscribe()
		self.stop()

	def simulationStarted(self, t0):
		self.subscribe()
		self.start()
		cherrypy.log("SIMULATION ENGINE STARTING")
		self.predictor.simulationStarted(t0)




	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		pass
	
	def POST(self,command=''):
		if command == 'start':
			cherrypy.log("starting prediction engine")
			self.subscribe()
			self.start()

		if command == 'stop':
			self.unsubscribe()
			self.stop()

	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass
