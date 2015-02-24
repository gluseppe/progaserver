#!/usr/bin/env python
import os, os.path
import random
import string
import time

import cherrypy
import pdb
import simplejson as json

from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log

from historyanalytics import HistoryAnalytics



class Planner(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time):
		plugins.Monitor.__init__(self, bus, self.plannerEngine(), sleeping_time)
		

	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		ha = HistoryAnalytics("query1")
		ha.loadAll(expunge=True)
		tl = ha.track_list

		elem =  ha.evaluateKDE(100, 100)
		#pdb.set_trace()
		return json.dumps(elem.tolist())


	def plannerEngine(self):
		pass

