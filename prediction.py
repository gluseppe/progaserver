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


#this was just to test the second commit on git
class PredictionEngine(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time, traffic):
		plugins.Monitor.__init__(self, bus, self.startPredictionEngine, sleeping_time)
		self.sleeping_time = sleeping_time
		self.traffic = traffic

	def startPredictionEngine(self):
		cherrypy.log("asking for traffic")
		currentState = self.traffic.getTraffic()


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
