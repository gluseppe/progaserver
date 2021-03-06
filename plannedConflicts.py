#!/usr/bin/env python

import numpy as np
from datetime import datetime, date, time, timedelta
from math import cos, sqrt, ceil


def distanceOnEllipsoidalEarthProjectedToAPlane(self, plat, plon, qlat, qlon):
	"""
	Compute distance on Ellipsoidal Earth projected to a plane, see
	http://en.wikipedia.org/wiki/Geographical_distance#Ellipsoidal_Earth_projected_to_a_plane
	"""
	meanlat = .5 * (plat + qlat)
	difflat = plat - qlat
	difflon = plon - qlon
	K1 = 111.13209 - .56605 * cos(2*meanlat) + .0012 * cos(4*meanlat)
	K2 = 111.41513 * cos(meanlat) - .09455 * cos(3*meanlat) + .00012 * cos(5*meanlat)
	return sqrt((K1*difflat)**2 + (K2*difflon)**2)

def get4DPointsFromIntent(reftrackobj, totime):
	"""
	reftrackobj must be an object of type ReferenceTrack
	totime must be a valid datetime.datetime object
	"""
	intent = zip(reftrackobj.line[:-1], reftrackobj.line[1:])
	listOf4DPoints = [(reftrackobj.line[0].lat, reftrackobj.line[0].lon, reftrackobj.line[0].z, totime)]
	noLegs = len(intent)
	pointsPerLeg = int(ceil(50./noLegs)) # modify here, if needed
	for leg in intent:
		deltaLat, deltaLon, deltaH = (leg[1].lat-leg[0].lat)/pointsPerLeg, (leg[1].lon-leg[0].lon)/pointsPerLeg, (leg[1].z-leg[0].z)/pointsPerLeg
		for point in range(pointsPerLeg):
			p = listOf4DPoints[-1]
			deltaT = sqrt(deltaH**2 + distanceOnEllipsoidalEarthProjectedToAPlane(p[0], p[1], p[0]+deltaLat, p[1]+deltaLon)**2 )/REFv
			listOf4DPoints.append((p[0]+deltaLat, p[1]+deltaLon, p[2]+deltaH, p[3]+timedelta(0, deltaT)))
	return listOf4DPoints

class HotSpotter(object):
	def __init__(self):
		self.REFv = 0.06111 # reference velocity in km/s
		self.HS_spatial_treshold = 1 # in km, change if needed
		self.HS_time_treshold = timedelta(0, 600) # in seconds, change if needed

	def findHotspots(self, intentData):
		"""
		intentData must be a list of couples (reftrackobj, takeofftime)
		"""
		n = len(intentData)
		self.hotspots = []
		aircraftIDs = [t[0].flight_id for t in intentData]
		plannedPoints = [self.get4DPointsFromIntent(rtObj, t) for rtObj,t in intentData]
		for i in range(n):
			iPath = plannedPoints[i]
			for j in range(i+1, n):
				jPath = plannedPoints[j]
				for h in iPath:
					for k in jPath:
						spatialDistance = sqrt(distanceOnEllipsoidalEarthProjectedToAPlane(h[0], h[1], k[0], k[1])**2 + (h[2]-k[2]**2))
						timeDistance = max(h[3], k[3]) - min(h[3], k[3])
						if spatialDistance < self.HS_spatial_treshold and timeDistance < self.HS_time_treshold:
							candidateHS = (set(aircraftIDs[i], aircraftIDs[j]), 
										   .5*(k[0]+j[0]), 
										   .5*(k[1]+j[1]), 
										   .5*(k[2]+j[2]), 
										   min(k[3],j[3])+timeDistance)
							icount = 0
							for hs in self.hotspots:
								spatialDist = sqrt(distanceOnEllipsoidalEarthProjectedToAPlane(hs[1], hs[2], candidateHS[1], candidateHS[2])**2 + (hs[3]-candidateHS[3]**2))
								timeDist = max(hs[4], candidateHS[4]) - min(hs[4], candidateHS[4])
								if spatialDistance < self.HS_spatial_treshold and timeDistance < self.HS_time_treshold:
									self.hotspots[icount] = (self.hotspots[0] | candidateHS[0], 
															 .5*(hs[1]+candidateHS[1]), 
															 .5*(hs[2]+candidateHS[2]), 
															 .5*(hs[3]+candidateHS[3]), 
															 min(hs[4],candidateHS[4])+timeDist)
									break 
								icount += 1
							else:
								self.hotspots.append(candidateHS)
