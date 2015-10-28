#!/usr/bin/env python
import os, os.path
import random
import string
import time

import cherrypy
import pdb
import simplejson as json
import progaconstants

from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log

from historyanalytics import HistoryAnalytics



class Planner(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time):
		plugins.Monitor.__init__(self, bus, self.plannerEngine(), sleeping_time)
		self.root_folder = "./db/history"
		

	@cherrypy.tools.accept(media='text/plain')
	def GET(self, item=None, queryname='query1'):
		if item == None or item == progaconstants.ITEM_HISTORY:
			ha = HistoryAnalytics(queryname)
			ha.loadAll(expunge=True)
			tl = ha.track_list
	
			elem =  ha.evaluateKDE(100, 100)
			#pdb.set_trace()
			return json.dumps(elem.tolist())
		elif item == progaconstants.ITEM_KNOWN_POINTS:
			#jpoints it is already a json string
			points = self.loadJPoints(queryname)
			return points


	def loadJPoints(self,queryname):
		complete_path = self.root_folder + "/" + queryname + "/" + progaconstants.KNOWN_POINTS_FILENAME
		points_file = open(complete_path)
		return points_file.read()
		


	def plannerEngine(self):
		pass

