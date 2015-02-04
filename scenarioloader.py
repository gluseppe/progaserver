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
import referencetrackshandler
import pdb





class ScenarioLoader(object):

	def __init__(self, scenariosfolder, referenceTrackHandler):
		self.scenariosfolder = scenariosfolder
		self.tracks = []
		self.flight_ids = []
		self.flight_intents = {}
		self.scenarioLoaded = False
		self.scenario = None
		self.referenceTrackHandler = referenceTrackHandler
		self.ownship_id = None
		self.ownship_intent_id = None

	#it requires a track file recorded from flight simulator
	#see flight1.txt for example
	#if you
	def loadTrack(self, trackfilename, track_id, flight_start):
		#trackflilename does not include the path, it's only name and extesion
		#track = open("./Flight1.txt", "r")
		track = Track(track_id)
		cont = 0
		with open(self.scenariosfolder + "/" + self.scenario + "/" + trackfilename, "r") as trackfile:
			for line in trackfile:
				
				if (not (line.startswith('#') or line.startswith('/'))) and len(line)>30:
					parts = line.split()

					timestamp = float(parts[0])

					#cherrypy.log("timestamp:%s"%(timestamp),context="ANTICIPATE")
					#pdb.set_trace()
					simulation_timestamp = -1;
					if (flight_start < 0):
						simulation_timestamp = timestamp-abs(flight_start)
					else:
						simulation_timestamp = timestamp
						
					
					if (flight_start >= 0 or timestamp >= abs(flight_start)):
						#cherrypy.log("importing line with timestamp:%s and simulation_timestamp %f"%(timestamp,simulation_timestamp),context="ANTICIPATE");
						lat = float(parts[1])
						lon = float(parts[2])
						altitude = float(parts[3])*progaconstants.FOOT2MT
						heading = float(parts[6])
						v_x = float(parts[8])*progaconstants.FOOT2MT
						v_y = float(parts[10])*progaconstants.FOOT2MT
						v_z = float(parts[9])*progaconstants.FOOT2MT
						pitch = float(parts[4])
						bank = float(parts[5])
						onground = int(parts[7])
						airspeed = int(float(parts[19]))
	
						track.addStep(simulation_timestamp, lat, lon, altitude, v_x, v_y, v_z, heading, pitch, bank, onground, airspeed)

				cont += 1
				
		track.setStart(flight_start)
		#pdb.set_trace()
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
		self.ownship_id = jsonobj['ownship_id']
		self.ownship_intent_id = jsonobj['ownship_intent_id']
		#cherrypy.log("\nLoading scenario: " + scenario_name)
		flights = jsonobj['flights']
		#path1 = flights[0]['path']
		#print("paths: "+path1)

		for flights in jsonobj['flights']:
			flight_file_name = flights['path']
			flight_id = flights['flight_id']
			#cherrypy.log("loading flight id:"+flight_id)
			flight_start = flights['start']

			raw_flight_intent = flights['flight_intent']
			flight_intent_point_list = None
			flight_intent = None

			#pdb.set_trace()


			
			#se l intent e' stato specificato, allora abbiamo altri due casi
			if raw_flight_intent != None:
				reference_track_id = raw_flight_intent['reference_track_id']
				departure_time = raw_flight_intent['departure_time']
				departure_time = datetime.datetime.strptime(departure_time,"%d-%m-%Y %H:%M:%S")
				
				#caso in cui e' stato specificato un intent relativo ad una referencetrack che abbiamo gia' nel db
				#allora recuper loe info della referencetrack tramite il referencetrackhandler
				#e aggiungo la traccia
				if reference_track_id != None:
					#cherrypy.log("reference_trackid: "+reference_track_id, context="DEBUG")
					rt = self.referenceTrackHandler.getReferenceTrack(reference_track_id)
					rt.refTrackID = reference_track_id
					rt.departureTime = departure_time
					rt.flight_id = flight_id
					self.addTrack(flight_file_name,flight_id,flight_start,rt)

				#caso in cui e' stato specificato un intent ma questo non era nel nostro db, quindi lo troviamo sottoforma 
				#di turning points. in realta' questo caso e' da migliorare
				else:
					flight_intent_point_list = []
					#cherrypy.log("ref track id:"+reference_track_id)
					turning_points = raw_flight_intent['turning_points']
					for item in turning_points:
						flight_intent_point_list.append(Point3D(item['lon'],item['lat'],item['h']))
				

					flight_intent = ReferenceTrack(flight_intent_point_list,flight_id)
					flight_intent.refTrackID = reference_track_id
					flight_intent.departureTime = departure_time
					#cherrypy.log("\nLoading track file: "+flight_file_name + " as " + flight_id + " starting: " + str(flight_start) + "secs after simulation start" )
					self.addTrack(flight_file_name,flight_id,flight_start,flight_intent)

			
			

		self.scenarioLoaded = True
		scenario = Scenario(self.tracks, self.ownship_id, self.ownship_intent_id)
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







