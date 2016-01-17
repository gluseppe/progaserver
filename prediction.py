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

import numpy as np
from predictor import findWeights, norm
from cluster import Cluster
from progaconstants import ALERT_DISTANCE, FOOT2MT, NUMPARTICLES, WARNING_RADIUS




def euclideanDistance(p, q):
	return np.sqrt(np.dot(p-q, p-q))

def futurePositions(ownPos, ownVel, ownInt, timeHorizons):
	"""
	Works with numpy 3D array.
	Returns the future position of the ownship, considering
	speed, intent and given timeHorizon
	timeHorizons must be an iterable containing times in seconds
	"""
	if ownInt is None:
		#cherrypy.log('ownVel is %.3f' % (np.sqrt(np.dot(ownVel, ownVel))), context='MONITOR')
		#pdb.set_trace()
		return [ownPos + t*ownVel for t in timeHorizons]
	else:
		# generate list of turn points
		# find next turn point
		# generate list of times to next turning points
		# propagate position
		vel = norm(ownVel)
		L = [p.getNumpyVector() for p in ownInt.line]
		ownIntent = zip(L[:-1], L[1:])
		legIndex, weight = findWeights(ownIntent, ownPos, ownVel)
		timeToTurn = [norm(ownIntent[legIndex][1] - ownPos)/norm(ownVel)]
		#pdb.set_trace()
		#print "time to turn",timeToTurn,"seconds maybe"
		#for i in range(legIndex+1, len(ownIntent)+1):
		for i in range(legIndex+1, len(ownIntent)+1):
			print "i:",i
			#timeToNextTP = norm(ownIntent[legIndex][1] - ownPos)/norm(ownVel)
			#timeToNextTP = norm(ownIntent[legIndex][1] - ownIntent[legIndex][0])/vel
			timeToNextTP = norm(ownIntent[i][1] - ownPos)/vel
			print "ownIntent[i][1]",ownIntent[i][1]
			print "timeToNextTP:",timeToNextTP
			if timeToNextTP > timeHorizons[-1]:
				#pdb.set_trace()
				break
			else:
				timeToTurn.append(timeToNextTP)
		timeToFly = list(timeHorizons)
		print "timeToFly (horizons):",timeToFly
		print "timeToTurn (intent points):",timeToTurn
		fp = []
		p = np.array(ownPos)
		while len(timeToFly) > 0  and legIndex < len(ownIntent):
			if len(timeToTurn) > 0 and timeToTurn[0] < timeToFly[0]:
				t = timeToTurn[0]
				timeToFly = [s-t for s in timeToFly]
				timeToTurn = [s-t for s in timeToTurn]
				timeToTurn.pop(0)
				p = p + t*(ownIntent[legIndex][1] - ownIntent[legIndex][0])/norm(ownIntent[legIndex][1] - ownIntent[legIndex][0])*vel
				legIndex += 1
			else:
				t = timeToFly[0]
				timeToFly = [s-t for s in timeToFly]
				timeToTurn = [s-t for s in timeToTurn] #forse da errore 
				timeToFly.pop(0)
				p = p + t*(ownIntent[legIndex][1] - ownIntent[legIndex][0])/norm(ownIntent[legIndex][1] - ownIntent[legIndex][0])*vel
				fp.append(p)
		# while len(timeToFly) > 0 and len(timeToTurn) > 0 and legIndex < len(ownIntent):
		# 	if timeToTurn[0] < timeToFly[0]:
		# 		t = timeToTurn[0]
		# 		timeToFly = [s-t for s in timeToFly]
		# 		timeToTurn = [s-t for s in timeToTurn]
		# 		timeToTurn.pop(0)
		# 		p = p + t*(ownIntent[legIndex][1] - ownIntent[legIndex][0])/norm(ownIntent[legIndex][1] - ownIntent[legIndex][0])*vel
		# 		legIndex += 1
		# 	else:
		# 		t = timeToFly[0]
		# 		timeToFly = [s-t for s in timeToFly]
		# 		timeToTurn = [s-t for s in timeToTurn]
		# 		timeToFly.pop(0)
		# 		p = p + t*(ownIntent[legIndex][1] - ownIntent[legIndex][0])/norm(ownIntent[legIndex][1] - ownIntent[legIndex][0])*vel
		# 		fp.append(p)
		return fp




"""
Questa classe gestisce le richieste verso il ramo di predizione

"""
class PredictionEngine(plugins.Monitor):
	exposed = True
	clusters = None

	def __init__(self, bus, sleeping_time, traffic):
		plugins.Monitor.__init__(self, bus, self.predictionEngine, sleeping_time)
		self.bus.subscribe(progaconstants.UPDATED_TRAFFIC_CHANNEL_NAME,self.trafficUpdated)
		self.bus.subscribe(progaconstants.INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME,self.initialWeightsComputed)
		self.bus.subscribe(progaconstants.SIMULATION_STOPPED_CHANNEL_NAME,self.simulationFinished)
		self.bus.subscribe(progaconstants.SIMULATION_FINISHED_CHANNEL_NAME,self.simulationFinished)
		self.bus.subscribe(progaconstants.SIMULATION_STARTED_CHANNEL_NAME,self.simulationStarted)


		self.monitor_active = False;
		self.sleeping_time = sleeping_time
		self.traffic = traffic
		self.predictor = None
		self.clusters = dict()
		

	"""
	prediction engine viene richiamata ogni sleeping_time secondi (vedi file progaconstant alla voce PREDICTION_SLEEP_SECONDS)
	per il momento e' impostata a 2. Possiamo usare questo hook per svolgere attivita' di contorno relative alla predizione.
	In teoria tutte quelle diverse dall'aggiornamento pesi che viene fatto dal Predictor su stimolo della funzione trafficUpdated
	"""
	def predictionEngine(self):
		pass
		#cherrypy.log("prediction engine running", context='DEBUG')
		#pass
		#cherrypy.log("asking for traffic", context='DEBUG')
		#currentState = self.traffic.getTraffic()


	def initialWeightsComputed(self, initialWeights):
		#create Predictor Object
		#cherrypy.log("initial weights computed", context='DEBUG')
		self.predictor = Predictor(self.traffic,initialWeights)


	def trafficUpdated(self, elapsedSeconds):
		#cherrypy.log("Updating traffic", context='DEBUG')
		v = self.traffic.getTraffic()
		#for t in v.values():
			#cherrypy.log("id:"+str(t['flight_id']) + " x:" + str(t['x']) + " y:"+str(t['y']) + " z:"+str(t['z']) + " lat:"+str(t['lat'])+ " lon:"+str(t['lon']), context='TRAFFIC')
		self.predictor.trafficUpdated(elapsedSeconds)


	def simulationFinished(self):
		#cherrypy.log("I AM PREDICTION ENGINE AND I KNOW SIMULATION IT'S FINISHED", context='DEBUG')
		self.unsubscribe()
		self.stop()

	def simulationStarted(self, t0):
		self.subscribe()
		self.start()
		cherrypy.log("SIMULATION ENGINE STARTING", context='AUTO')
		self.predictor.simulationStarted(t0)

	def toBool(self, s):
		return s.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']

	
	'''
	in questa funzione mettiamo il risultato del sensing di potenziali conflitti
	il monitoraggio non verra fatto automaticamente dal server ma richiesto continuamente
	dal client per tutta la durata di attivazione della funzione
	in altre parole ci pensa il client a tenersi informato sullo stato dei conflitti potenziali
	'''
	def checkConflicts(self, ownPos, ownVel, flight_IDs, deltaT, nsteps, ownIntent=None):
		"""
		Input:
		- ownPos, current position of monitored aircraft
		- ownVel, current velocity of monitored aircraft
		- ownIntent, flight intent of monitored aircraft
		- ownID, flight ID of monitored aircraft
		- flight_IDs, flight intent of surrounding traffic
		- deltaT, prediction unit time interval
		- nsteps, number of predictions
		"""
		potentialConflicts = {}
		timeHorizons = [i*deltaT for i in range(1, nsteps+1)]
		#pdb.set_trace()
		fp = futurePositions(ownPos, ownVel, ownIntent, timeHorizons)
		prediction = self.predictor.predictionRequested(flight_IDs, deltaT, nsteps, True)
		ztp = zip(timeHorizons, fp)
		#ztp.sort()
		#pdb.set_trace()
		for aID, foo in prediction.items():
			predDict = foo[0]
			for t, p in ztp:
				#cherrypy.log("Ownship will be at %s in %d seconds" % (p, t),context="MONITOR")
				#cherrypy.log("%s will be at %s in %d seconds" % (aID, sum(predDict[t])/len(predDict[t]), t),context="MONITOR")
				for q in predDict[t]:
					if euclideanDistance(p,q) < ALERT_DISTANCE:
						potentialConflicts.setdefault(t, []).append(aID)
						break
		#pdb.set_trace()
		return potentialConflicts


	@cherrypy.tools.accept(media='text/plain')
	def GET(self, flight_id, deltaT, nsteps, raw, coords_type=progaconstants.COORDS_TYPE_GEO, cluster=False, ownshipPrediction=False):
		if flight_id == progaconstants.MONITOR_ME_COMMAND:
			ownship_state = self.traffic.getMyState()
			v = np.array([ownship_state['vx'],ownship_state['vy'],ownship_state['vz']])*FOOT2MT
			p = Point3D(ownship_state['lon'], ownship_state['lat'], ownship_state['h']*FOOT2MT).getNumpyVector()
			#pdb.set_trace()
			fids = self.traffic.getActiveFlightIDs()
			ownship_intent = self.traffic.getOwnshipIntent()
			intruders = self.checkConflicts(p,v,fids,int(deltaT),int(nsteps),ownship_intent)
			#pdb.set_trace()
			return json.dumps(intruders)
		else:
			flight_IDs = [flight_id]
			deltaT = int(deltaT)
			nsteps = int(nsteps)
			rawPrediction = self.toBool(raw)
			prediction_matrix = self.predictor.predictionRequested(flight_IDs, deltaT, nsteps,rawPrediction)
			#pdb.set_trace()
			#RAW PREDICTION WAS REQUESTED, WE PROVIDE PARTICLES POSITIONS
			if rawPrediction:
				for flight in prediction_matrix:
					for times in prediction_matrix[flight][0]:
						#prediction_matrix[flight][0] e' l'elemento che contiene i valori di predizione
						#mentre [1] contiene le leg utilizzate per predire quel volo
						for i in range(0,len(prediction_matrix[flight][0][times])):
							#for tris in range(0,len(prediction_matrix[flight][0][times][i])):
								#pdb.set_trace()
							if (coords_type == progaconstants.COORDS_TYPE_GEO):
								p3d = Point3D()
								#pdb.set_trace()
								vect = p3d.lonLatAltFromXYZ(prediction_matrix[flight][0][times][i][0], prediction_matrix[flight][0][times][i][1], prediction_matrix[flight][0][times][i][2])
								prediction_matrix[flight][0][times][i] = vect
	
						prediction_matrix[flight][0][times] = prediction_matrix[flight][0][times].tolist()
				if cluster==False:
					jmat = json.dumps(prediction_matrix)
					cherrypy.log("%s" % (jmat), context="PREDICTION")
					return jmat
				else:
					#if clusters are true, automatically produce the ownship prediction
					ownship_prediction = self.predictOwnship(deltaT,nsteps)
					clusters = self.makeClusters(ownship_prediction, prediction_matrix, flight_id, deltaT, nsteps)
					#pdb.set_trace()


					prediction_matrix['ownship'] = ownship_prediction
					prediction_matrix['clusters'] = clusters
					
					jmat = json.dumps(prediction_matrix)
					
					
					
					return jmat
	
			#NORMAL PREDICTION WAS REQUESTED, WE PROVIDE BINS OF PROBABILITY
			else:
				#pdb.set_trace()
				for flight in prediction_matrix:
					for dt in prediction_matrix[flight]:
						prediction_matrix[flight][dt][0] = prediction_matrix[flight][dt][0].tolist()
						for i in range(0,len(prediction_matrix[flight][dt][1])):
							prediction_matrix[flight][dt][1][i] = prediction_matrix[flight][dt][1][i].tolist()
				jmat = json.dumps(prediction_matrix)
				cherrypy.log("%s" % (jmat), context="PREDICTION")
		
		
				
				#scrivi qui codice di test
				#cherrypy.log("%s" % prediction_matrix[flight_IDs[0]][deltaT][0], context="TEST")
				return jmat


	def predictOwnship(self,deltaT,nsteps):
		ownship_state = self.traffic.getMyState()
		ownship_v = np.array([ownship_state['vx'],ownship_state['vy'],ownship_state['vz']])*FOOT2MT
		ownship_p = Point3D(ownship_state['lon'], ownship_state['lat'], ownship_state['h']*FOOT2MT).getNumpyVector()
		ownship_intent = self.traffic.getOwnshipIntent()
		timeHorizons = [i*deltaT for i in range(1, nsteps+1)]
		fp = futurePositions(ownship_p, ownship_v, ownship_intent, timeHorizons)
		#pdb.set_trace()
		ztp = zip(timeHorizons, fp)
		#pdb.set_trace()
		p3d = Point3D()
		for i, item in enumerate(ztp):
			ztp[i] = list(ztp[i])
			ztp[i][1] = ztp[i][1].tolist()
			ztp[i][1] = p3d.lonLatAltFromXYZ(ztp[i][1][0],ztp[i][1][1],ztp[i][1][2])
		#pdb.set_trace()
		return ztp

	def isItDangerous(self, cluster, ownship_prediction, time):
		for ownship_clusters in ownship_prediction:
			if ownship_clusters[0] == time:
				lon = ownship_clusters[1][0]	
				lat = ownship_clusters[1][1]
				h = ownship_clusters[1][2]
				#p3d = Point3D(lon,lat,h)
				dist = cluster.center.distance(lon,lat)
				#pdb.set_trace()
				if (dist <= WARNING_RADIUS):
					return [True, dist]

		return [False, dist]


	def makeClusters(self,ownship_prediction, prediction_matrix, flight_id, deltaT, nsteps):
		#pdb.set_trace()
		self.clusters.clear()

		#you need to iterate particles according to deltaT and nsteps
		particles = prediction_matrix[flight_id][0]
		reference_groups = prediction_matrix[flight_id][2]
		reference_set = set(reference_groups)
#		times = particles.keys()
		for ref in reference_set:
			self.clusters[ref] = dict()

		#pdb.set_trace()

		for x in range(1,nsteps+1):
		#x = 1
		#while x<=nsteps:
			time = x*deltaT
			print time
			
			particles_in_time = particles[time]
			#pdb.set_trace()
			for i,part in enumerate(particles_in_time):
				lat = part[1]
				lon = part[0]
				h = part[2]
				p_group = reference_groups[i]
				if self.clusters[p_group].has_key(time):
					self.clusters[p_group][time].addParticle(lat, lon, h)
				else:
					self.clusters[p_group][time] = Cluster(p_group, lat, lon, h, time)

				#pdb.set_trace()

				
		
		#pdb.set_trace()

		for pg, timedict in self.clusters.items():
			for t, clus in timedict.items():
				dangerousness = self.isItDangerous(self.clusters[pg][t],ownship_prediction,t)
				dangerous = dangerousness[0]
				dist = dangerousness[1]
				self.clusters[pg][t].dangerous = dangerous
				self.clusters[pg][t].proximity = dist

				self.clusters[pg][t] = self.clusters[pg][t].toSerializableObject()

		##temporary for test purposes particles vs clusters
		return self.clusters
		#return prediction_matrix

		#ripristina questo dopo che hai fatto test
		#return json.dumps(self.clusters)

	
	def POST(self,command=''):
		if command == 'start':
			cherrypy.log("starting prediction engine", context='AUTO')
			self.subscribe()
			self.start()

		if command == 'stop':
			self.unsubscribe()
			self.stop()

	def PUT(self,another_string):
		pass

	def DELETE(self):
		pass
