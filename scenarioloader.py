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
from referencetrack import ReferenceTrack, Point3D




class ScenarioLoader(object):

	def __init__(self, scenariosfolder):
		self.scenariosfolder = scenariosfolder
		self.tracks = []
		self.flight_ids = []
		self.flight_intents = {}
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
					lat = float(parts[1])
					lon = float(parts[2])
					altitude = float(parts[3])
					heading = float(parts[6])
					v_x = float(parts[8])
					v_y = float(parts[9])
					v_z = float(parts[10])
					track.addStep(timestamp, lat, lon, altitude, v_x, v_y, v_z, heading)

				cont += 1
				
		track.setStart(flight_start)
		return track


	#the scenario parameter must match with the folder name containing the scenario files
	def loadScenario(self,scenario):
		allfile = ""
		self.scenario = scenario
		complete_path = self.scenariosfolder + "/" + scenario + "/" + progaconstants.SCENARIO_INFO_FILENAME
		#cherrypy.log("opening the scenario file:" + complete_path)
		with open(complete_path) as scenariofile:
			for line in scenariofile:
				allfile += line

		#cherrypy.log(allfile)
		jsonobj = json.loads(allfile)
		#cherrypy.log(jsonobj)

		scenario_name = jsonobj['scenario_name']
		#cherrypy.log("\nLoading scenario: " + scenario_name)
		flights = jsonobj['flights']
		path1 = flights[0]['path']
		#print("paths: "+path1)

		for flights in jsonobj['flights']:
			flight_file_name = flights['path']
			flight_id = flights['flight_id']
			#cherrypy.log("loading flight id:"+flight_id)
			flight_start = flights['start']
			raw_flight_intent = flights['flight_intent']
			flight_intent_point_list = None
			flight_intent = None
			if raw_flight_intent != None:
				flight_intent_point_list = []
				reference_track_id = raw_flight_intent['reference_track_id']
				#cherrypy.log("ref track id:"+reference_track_id)
				turning_points = raw_flight_intent['turning_points']
				for item in turning_points:
					flight_intent_point_list.append(Point3D(item['lat'],item['lon'],item['h']))
				flight_intent = ReferenceTrack(flight_intent_point_list,flight_id)
				flight_intent.id = reference_track_id

			#cherrypy.log("\nLoading track file: "+flight_file_name + " as " + flight_id + " starting: " + str(flight_start) + "secs after simulation start" )
			self.addTrack(flight_file_name,flight_id,flight_start,flight_intent)

		self.scenarioLoaded = True
		scenario = Scenario(self.tracks)
		#cherrypy.log("Sono dentro scenario loader e ho " + str(len(self.tracks)) + "tracce")
		return scenario


	def addTrack(self, trackfilename, flight_id,flight_start, flight_intent):
		if flight_id not in self.flight_ids:
			#print "adding track"
			#cherrypy.log("flight_start:" + str(flight_start))
			track = self.loadTrack(trackfilename,flight_id,flight_start)
			track.setDeclaredFlightIntent(flight_intent)
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







