#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime

import cherrypy
import simplejson as json
import progaconstants
from scenario import Scenario
from track import Track




class ScenarioLoader(object):

	def __init__(self, scenariosfolder):
		self.scenariosfolder = scenariosfolder
		self.tracks = []
		self.flight_ids = []
		self.scenarioLoaded = False
		self.scenario = None

	#it requires a track file recorded from flight simulator
	#see flight1.txt for example
	def loadTrack(self, trackfilename, track_id, flight_start):
		#trackflilename does not include the path, it's only name and extesion
		#track = open("./Flight1.txt", "r")
		track = Track(track_id)
		cont = 0
		with open(self.scenariosfolder + "/" + self.scenario + "/" + trackfilename, "r") as trackfile:
			for line in trackfile:
				
				if cont >= 9 and len(line)>30:
					parts = line.split()
					timestamp = parts[0]
					lat = parts[1]
					lon = parts[2]
					altitude = parts[3]
					heading = parts[6]
					v_x = parts[8]
					v_y = parts[9]
					v_z = parts[10]
					track.addStep(timestamp, lat, lon, altitude, v_x, v_y, v_z, heading)

				cont += 1
				
		track.setStart(flight_start)
		return track


	#the scenario parameter must match with the folder name containing the scenario files
	def loadScenario(self,scenario):
		allfile = ""
		self.scenario = scenario
		complete_path = self.scenariosfolder + "/" + scenario + "/" + progaconstants.SCENARIO_INFO_FILENAME
		cherrypy.log("opening the scenario file:" + complete_path)
		with open(complete_path) as scenariofile:
			for line in scenariofile:
				allfile += line

		cherrypy.log(allfile)
		jsonobj = json.loads(allfile)
		#cherrypy.log(jsonobj)

		scenario_name = jsonobj['scenario_name']
		cherrypy.log("\nLoading scenario: " + scenario_name)
		flights = jsonobj['flights']
		path1 = flights[0]['path']
		#print("paths: "+path1)

		for flights in jsonobj['flights']:
			flight_file_name = flights['path']
			flight_id = flights['flight_id']
			flight_start = flights['start']
			cherrypy.log("\nLoading track file: "+flight_file_name + " as " + flight_id + " starting: " + str(flight_start) + "secs after simulation start" )
			self.addTrack(flight_file_name,flight_id,flight_start)

		self.scenarioLoaded = True
		scenario = Scenario(self.tracks)
		cherrypy.log("Sono dentro scenario loader e ho " + str(len(self.tracks)) + "tracce")
		return scenario


	def addTrack(self, trackfilename, flight_id,flight_start):
		if flight_id not in self.flight_ids:
			#print "adding track"
			cherrypy.log("flight_start:" + str(flight_start))
			track = self.loadTrack(trackfilename,flight_id,flight_start)
			self.tracks.append(track)
			self.flight_ids.append(flight_id)
			return True
		return False

	def info(self):
		for t in self.tracks:
			print "lunghezza di " + t.getTrackId() + ": " + str(len(t.getPath()))

	def isAnythingLoaded(self):
		return self.scenarioLoaded





if __name__ == '__main__':
	sl = ScenarioLoader(progaconstants.SCENARIOS_FOLDER)
	sl.loadScenario("test_scenario")
	#ok = sl.addTrack("flight1.txt", 'AZ12453')
	#if ok:
	#	print 'az loaded'
	#	sl.info()
	#ok = sl.addTrack("flight2.txt", 'RYR4584')
	#if ok:
	#	print 'ryr loaded'
	#	sl.info()







