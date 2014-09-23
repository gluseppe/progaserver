#!/usr/bin/env python
import progaconstants
import requests
import cherrypy
from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log
from track import Track
import simplejson as json
import time


class Automator(plugins.Monitor):


	#simulateself contiene False se non vogliamo simulare la nostra track
	#oppure contiene il nome del file della traccia se vogliamo simularla
	#la libreria delle tracks e' contenuta nella cartella selftracks
	def __init__(self, bus, scenarioName, selfTrackName=None, sleeping_time=0.5):
		plugins.Monitor.__init__(self, bus, self.automate, sleeping_time)
		self.bus.subscribe(progaconstants.PROGA_IS_READY_CHANNEL_NAME,self.progaReady)
		self.bus.subscribe(progaconstants.SCENARIO_LOADED_CHANNEL_NAME,self.scenarioLoaded)
		self.bus.subscribe(progaconstants.SIMULATION_STARTED_CHANNEL_NAME,self.simulationStarted)
		self.bus.subscribe(progaconstants.SIMULATION_STOPPED_CHANNEL_NAME,self.simulationFinished)
		self.bus.subscribe(progaconstants.SIMULATION_FINISHED_CHANNEL_NAME,self.simulationFinished)
		self.scenarioName = scenarioName
		self.s = requests.Session()
		self.selfTrackName = selfTrackName
		self.selfTrack = None
		self.scenariosfolder = progaconstants.SCENARIOS_FOLDER
		self.t0 = -1
		if self.selfTrackName != None:
			cherrypy.log("I have a selftrack",context="AUTO")
			self.selfTrack = self.loadTrack(self.selfTrackName,progaconstants.SELF_FLIGHT_ID,0)


	def automate(self):
		elapsed_time = time.time() - self.t0
		int_elapsed_seconds = int(elapsed_time)
		cherrypy.log("selftrack updating", context="AUTO")
		arrived = not self.selfTrack.next(elapsed_time,progaconstants.PLAYER_POINTER_INCREMENT)
		if arrived:
			return False
		else:
			state = self.selfTrack.getCurrentState()
			selfstate = {}
			selfstate['lat'] = state['lat']
			selfstate['lon'] = state['lon']
			selfstate['h'] = state['h']
			selfstate['vx'] = state['vx']
			selfstate['vy'] = state['vy']
			selfstate['vz'] = state['vz']
			jsonstate = json.dumps(selfstate)
			#payload = {'json_payload': jsonstate}
			url = "http://127.0.0.1:8080/listener"
			headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
			cherrypy.log("about to send state to listener", context="AUTO")
			r = self.s.put(url, data=jsonstate, headers=headers)





	def progaReady(self):
		cherrypy.log("PROGA IS READY, I AM GOING TO SEND LOAD SCENARIO COMMAND. LOADING:%s"%(self.scenarioName), context="AUTO")
		r = self.s.post('http://127.0.0.1:8080/traffic', params={'command':'loadscenario','scenario_name':self.scenarioName})


	def scenarioLoaded(self):
		cherrypy.log("A SCENARIO WAS LOADED, I AM GOING TO SEND START-SIMULATION COMMAND", context="AUTO")
		r = self.s.post('http://127.0.0.1:8080/traffic', params={'command':'start'})
		

	def simulationStarted(self,t0):
		cherrypy.log("i know simulation has started", context="AUTO")
		self.t0 = t0
		if self.selfTrackName != None:
			cherrypy.log("subscribing", context="AUTO")
			self.subscribe()
			self.start()

	def simulationFinished(self):
		self.unsubscribe()
		self.stop()




	def loadTrack(self, trackfilename, track_id, flight_start):
		#trackflilename does not include the path, it's only name and extesion
		#track = open("./Flight1.txt", "r")
		track = Track(track_id)
		cont = 0
		with open(self.scenariosfolder + "/" + self.scenarioName + "/" + trackfilename, "r") as trackfile:
			for line in trackfile:
				
				if (not (line.startswith('#') or line.startswith('/'))) and len(line)>30:
				#if cont >= 4 and len(line)>30:
					parts = line.split()
					timestamp = parts[0]
					lat = float(parts[1])
					lon = float(parts[2])
					altitude = float(parts[3])
					heading = float(parts[6])
					v_x = float(parts[8])
					v_y = float(parts[10])
					v_z = float(parts[9])
					track.addStep(timestamp, lat, lon, altitude, v_x, v_y, v_z, heading)
					cherrypy.log("%s,%s,%s,%s,%s,%s,%s,%s"%(timestamp, lat, lon, altitude, v_x, v_y, v_z, heading),context="EXPORT,")

				cont += 1
				
		track.setStart(flight_start)
		return track
