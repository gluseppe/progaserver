#!/usr/bin/env python
import progaconstants
import requests
import cherrypy
from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log


class Automator(plugins.Monitor):


	def __init__(self, bus, scenarioName):
		plugins.Monitor.__init__(self, bus, self.automate, 1)
		self.bus.subscribe(progaconstants.PROGA_IS_READY_CHANNEL_NAME,self.progaReady)
		self.bus.subscribe(progaconstants.SCENARIO_LOADED_CHANNEL_NAME,self.scenarioLoaded)
		self.scenarioName = scenarioName
		self.s = requests.Session()


	def automate(self):
		cherrypy.log("Automator", context="AUTO")


	def progaReady(self):
		cherrypy.log("PROGA IS READY, I AM GOING TO SEND LOAD SCENARIO COMMAND. LOADING:%s"%(self.scenarioName), context="AUTO")
		r = self.s.post('http://127.0.0.1:8080/traffic', params={'command':'loadscenario','scenario_name':self.scenarioName})



	def scenarioLoaded(self):
		cherrypy.log("A SCENARIO WAS LOADED, I AM GOING TO SEND START-SIMULATION COMMAND", context="AUTO")
		r = self.s.post('http://127.0.0.1:8080/traffic', params={'command':'start'})
