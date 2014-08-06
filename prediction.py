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


"""Questa classe fa gestisce le richieste verso il ramo di predizione

"""
class PredictionEngine(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time, traffic):
		plugins.Monitor.__init__(self, bus, self.startPredictionEngine, sleeping_time)
		self.bus.subscribe(progaconstants.UPDATED_TRAFFIC_CHANNEL_NAME,self.trafficUpdated)
		self.bus.subscribe(progaconstants.INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME,self.initialWeightsComputed)
		self.sleeping_time = sleeping_time
		self.traffic = traffic
		self.predictor = None

	def startPredictionEngine(self):
		cherrypy.log("asking for traffic")
		currentState = self.traffic.getTraffic()


	def initialWeightsComputed(self, initialWeights):
		#create Predictor Object
		self.predictor = Predictor(self.traffic,initialWeights)


	def trafficUpdated(self, elapsedSeconds):
		self.predictor.trafficUpdated(elapsedSeconds)




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
