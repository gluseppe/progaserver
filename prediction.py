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
import pdb
import simplejson as json
from referencetrack import Point3D

"""
Questa classe gestisce le richieste verso il ramo di predizione

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
		cherrypy.log("prediction engine running", context='DEBUG')
		#pass
		#cherrypy.log("asking for traffic", context='DEBUG')
		#currentState = self.traffic.getTraffic()


	def initialWeightsComputed(self, initialWeights):
		#create Predictor Object
		cherrypy.log("initial weights computed", context='DEBUG')
		self.predictor = Predictor(self.traffic,initialWeights)


	def trafficUpdated(self, elapsedSeconds):
		cherrypy.log("Updating traffic", context='DEBUG')
		v = self.traffic.getTraffic()
		for t in v.values():
			cherrypy.log("id:"+str(t['flight_id']) + " x:" + str(t['x']) + " y:"+str(t['y']) + " z:"+str(t['z']) + " lat:"+str(t['lat'])+ " lon:"+str(t['lon']), context='TRAFFIC')
		self.predictor.trafficUpdated(elapsedSeconds)


	def simulationFinished(self):
		cherrypy.log("I AM PREDICTION ENGINE AND I KNOW SIMULATION IT'S FINISHED", context='DEBUG')
		self.unsubscribe()
		self.stop()

	def simulationStarted(self, t0):
		self.subscribe()
		self.start()
		cherrypy.log("SIMULATION ENGINE STARTING", context='DEBUG')
		self.predictor.simulationStarted(t0)

	def toBool(self, s):
		return s.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']


	@cherrypy.tools.accept(media='text/plain')
	def GET(self, flight_id, deltaT, nsteps, raw, coords_type=progaconstants.COORDS_TYPE_GEO):
		flight_IDs = [flight_id]
		deltaT = int(deltaT)
		nsteps = int(nsteps)
		rawPrediction = self.toBool(raw)
		prediction_matrix = self.predictor.predictionRequested(flight_IDs, deltaT, nsteps,rawPrediction)
		#pdb.set_trace()

		#RAW PREDICTION WAS REQUESTED, WE PROVIDE PARTICLES POSITIONS
		if rawPrediction:
			for flight in prediction_matrix:
				for i in range(0,len(prediction_matrix[flight])):
					for tris in range(0,len(prediction_matrix[flight][i])):
						#pdb.set_trace()
						if (coords_type == progaconstants.COORDS_TYPE_GEO):
							p3d = Point3D();
							vect = p3d.lonLatAltFromXYZ(prediction_matrix[flight][i][tris][0], prediction_matrix[flight][i][tris][1], prediction_matrix[flight][i][tris][2])
							prediction_matrix[flight][i][tris] = vect

					prediction_matrix[flight][i] = prediction_matrix[flight][i].tolist()

			#pdb.set_trace()
			jmat = json.dumps(prediction_matrix)
			return jmat

		#NORMAL PREDICTION WAS REQUESTED, WE PROVIDE BINS OF PROBABILITY
		else:		
			for flight in prediction_matrix:
				for dt in prediction_matrix[flight]:
					prediction_matrix[flight][dt][0] = prediction_matrix[flight][dt][0].tolist()
					for i in range(0,len(prediction_matrix[flight][dt][1])):
						prediction_matrix[flight][dt][1][i] = prediction_matrix[flight][dt][1][i].tolist()
	
			#pdb.set_trace()
			jmat = json.dumps(prediction_matrix)
			cherrypy.log("prediction ready", context="PREDICTION")
	
	
			
			#scrivi qui codice di test
			#cherrypy.log("%s" % prediction_matrix[flight_IDs[0]][deltaT][0], context="TEST")
			return jmat
	
	def POST(self,command=''):
		if command == 'start':
			cherrypy.log("starting prediction engine", context='DEBUG')
			self.subscribe()
			self.start()

		if command == 'stop':
			self.unsubscribe()
			self.stop()

	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass
