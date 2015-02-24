#!/usr/bin/env python
import os, os.path
import random
import string
import time

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
from progaconstants import ALERT_DISTANCE, FOOT2MT



from datetime import datetime, date, time, timedelta
from math import cos, sqrt, ceil, radians




def distanceOnEllipsoidalEarthProjectedToAPlane(plat, plon, qlat, qlon):
	"""
	Compute distance on Ellipsoidal Earth projected to a plane, see
	http://en.wikipedia.org/wiki/Geographical_distance#Ellipsoidal_Earth_projected_to_a_plane
	"""
	meanlat = .5 * (plat + qlat)
	difflat = plat - qlat
	difflon = plon - qlon
	K1 = 111.13209 - .56605 * cos(radians(2*meanlat)) + .0012 * cos(radians(4*meanlat))
	K2 = 111.41513 * cos(radians(meanlat)) - .09455 * cos(radians(3*meanlat)) + .00012 * cos(radians(5*meanlat))
	return sqrt((K1*difflat)**2 + (K2*difflon)**2)


class HotSpotter(plugins.Monitor):
	exposed = True

	def __init__(self, bus, sleeping_time):
		plugins.Monitor.__init__(self, bus, self.hotSpotEngine(), sleeping_time)
		self.bus.subscribe(progaconstants.SCENARIO_LOADED_CHANNEL_NAME,self.scenarioLoaded)
		self.REFv = 0.051144# reference velocity in km/s
		self.HS_candidate_spatial_treshold = 1.5 # in km, change if needed
		self.HS_candidate_time_treshold = timedelta(0, 120) # in seconds, change if needed
		self.HS_spatial_treshold = 1.5 # in km, change if needed
		self.HS_time_treshold = timedelta(0, 120) # in seconds, change if needed
		self.howManyPointsPerIntent = 10.
		self.scenario = None


	def scenarioLoaded(self, loadedScenario):
		self.scenario = loadedScenario

	def hotSpotEngine(self):
		pass

	def get4DPointsFromIntent(self,reftrackobj, totime):
		"""
		reftrackobj must be an object of type ReferenceTrack
		totime must be a valid datetime.datetime object
		"""
		intent = zip(reftrackobj.line[:-1], reftrackobj.line[1:])
		listOf4DPoints = []
		noLegs = len(intent)
		pointsPerLeg = int(ceil(self.howManyPointsPerIntent/noLegs)) # modify here, if needed
		lasttime = totime
		for leg in intent:
			latitudes = np.linspace(leg[0].lat, leg[1].lat, pointsPerLeg)
			longitudes = np.linspace(leg[0].lon, leg[1].lon, pointsPerLeg)
			heights = np.linspace(leg[0].z, leg[1].z, pointsPerLeg)
			secondsToFlyTheLeg = sqrt(((leg[1].z-leg[0].z)*0.0003048)**2 + distanceOnEllipsoidalEarthProjectedToAPlane(leg[0].lat, leg[0].lon, leg[1].lat, leg[1].lon)**2 )/self.REFv
			passagetimes = [lasttime + timedelta(0, incremenT) for incremenT in np.linspace(0, secondsToFlyTheLeg, pointsPerLeg)]
			listOf4DPoints += zip(latitudes, longitudes, heights, passagetimes)
			lasttime = lasttime + timedelta(0, secondsToFlyTheLeg)
			#pdb.set_trace()

		#cherrypy.log("4D POINTS: %s"%(listOf4DPoints),context="HOTSPOT")
		return listOf4DPoints



	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		if self.scenario is None:
			return json.dumps(None)

		intents = [t.getDeclaredIntent() for t in self.scenario.getTracks()]
		intents = [i for i in intents if i is not None]

		ret = []
		for hs in self.findHotspots(intents):
			ret.append([list(hs[0])]+list(hs[1:4])+[hs[4].strftime("%d-%m-%Y %H:%M:%S.%f")])

		return json.dumps(ret)


	def findHotspots(self, intentData):
		"""
		intentData must be a list of (reftrackobj)
		"""
		n = len(intentData)
		hotspots = []
		aircraftIDs = [t.flight_id for t in intentData]
		plannedPoints = [self.get4DPointsFromIntent(rtObj, rtObj.departureTime) for rtObj in intentData]
		for i in range(n):
			#cherrypy.log('Working with %s' % (aircraftIDs[i]), context='HOTSPOT')
			iPath = plannedPoints[i]
			for j in range(i+1, n):
				#cherrypy.log('Checking against %s' % (aircraftIDs[j]), context='HOTSPOT')
				jPath = plannedPoints[j]
				for h in iPath:
					for k in jPath:
						spatialDistance = sqrt(distanceOnEllipsoidalEarthProjectedToAPlane(h[0], h[1], k[0], k[1])**2 + (h[2]-k[2])**2)
						timeDistance = max(h[3], k[3]) - min(h[3], k[3])
						if spatialDistance < self.HS_candidate_spatial_treshold and timeDistance < self.HS_candidate_time_treshold:
							candidateHS = (set((aircraftIDs[i], aircraftIDs[j])), 
										   .5*(k[0]+h[0]), 
										   .5*(k[1]+h[1]), 
										   .5*(k[2]+h[2]), 
										   min(k[3],h[3])+timeDistance)
							#cherrypy.log('Found candidate points (%.3f, %.3f, %.2f, %s)' % (h), context='HOTSPOT')
							#cherrypy.log('Found candidate points (%.3f, %.3f, %.2f, %s)' % (k), context='HOTSPOT')
							#cherrypy.log('Found candidate hotspot :: %s @ (%.3f, %.3f, %.2f, %s)' % (candidateHS), context='HOTSPOT')
							icount = 0
							for hs in hotspots:
								spatialDist = sqrt(distanceOnEllipsoidalEarthProjectedToAPlane(hs[1], hs[2], candidateHS[1], candidateHS[2])**2 + (hs[3]-candidateHS[3])**2)
								timeDist = max(hs[4], candidateHS[4]) - min(hs[4], candidateHS[4])
								if spatialDist < self.HS_spatial_treshold and timeDist < self.HS_time_treshold:
									hotspots[icount] = (hs[0] | candidateHS[0], 
															 .5*(hs[1]+candidateHS[1]), 
															 .5*(hs[2]+candidateHS[2]), 
															 .5*(hs[3]+candidateHS[3]), 
															 min(hs[4],candidateHS[4])+timeDist)
									break 
								icount += 1
							else:
								hotspots.append(candidateHS)
		return hotspots
