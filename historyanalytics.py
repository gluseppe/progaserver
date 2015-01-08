#!/usr/bin/env python
import os, os.path
from track import Track
import glob
import progaconstants
import numpy as np
from scipy import stats
from math import cos, sqrt
from progaconstants import AIRFIELD_CUTOFF_DISTANCE

def distanceOnEllipsoidalEarthProjectedToAPlane(plat, plon, qlat, qlon):
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

def bubblePop(t, clat, clon, r):
	while True:
		lon = t[-1][0]
		lat = t[-1][1]
		distance = distanceOnEllipsoidalEarthProjectedToAPlane(clat, clon, lat, lon)
		if distance < r:
			t.pop()
		else:
			break
	return t

class HistoryAnalitics(object):
	"""
	I will help Timothy, Dumbo's helper
	"""
	def __init__(self, query_name):
		self.root_folder = "./db/history"
		self.query_name = query_name
		self.track_list = []
		self.prefix_file_name = "flight"
		self.files_iterable = glob.glob(self.root_folder + "/" + query_name + "/" + self.prefix_file_name + "*[0-9].txt")
		#self.loadAll()


	def loadAll(self, expunge=True, expRadius=AIRFIELD_CUTOFF_DISTANCE):
		"""
		Creates a list of tracks
		Each tracks is a list of 3D numpy vectors (LON, LAT, ALT)
		"""
		for name in self.files_iterable:
			self.track_list.append(self.loadTrack(name, expunge, expRadius))


	def loadTrack(self, trackfilename, expunge=True, expRadius=AIRFIELD_CUTOFF_DISTANCE):
		"""
		Reads flight data from trackfilename and returns a list of 3D numpy vectors (LON, LAT, ALT)
		"""
		track = []
		with open(trackfilename, "r") as trackfile:
			for line in trackfile:
				if (not (line.startswith('#') or line.startswith('/'))) and len(line)>30:
					parts = line.split()
					lat = float(parts[1])
					lon = float(parts[2])
					altitude = float(parts[3])*progaconstants.FOOT2MT
					track.append(np.array([lon, lat, altitude], dtype=np.float64))
		if expunge:
			track = self.expungeAroundDepArrAirfields(track, expRadius)
		return track

	def expungeAroundDepArrAirfields(self, track, expRadius=AIRFIELD_CUTOFF_DISTANCE):
		"""
		This function excludes pops out from track those points 
		that are less than expRadius km away from departing and arrival airfields
		"""
		dep_lon = track[0][0]
		dep_lat = track[0][1]
		arr_lon = track[-1][0]
		arr_lat = track[-1][1]
		track = bubblePop(track, arr_lat, arr_lon, expRadius)
		track.reverse()
		track = bubblePop(track, dep_lat, dep_lon, expRadius)
		return track



	def summary(self):
		"""
		Display a summary of loaded data
		"""
		message = []
		message.append('Summary of loaded dataset:\n' + '-'*20)
		llen = len(self.track_list)
		message.append('%d flown traces' % (llen))
		ppoints = sum([len(i) for i in self.track_list])
		message.append(('%d 3D recorded points' % (ppoints)))
		message.append('%.3f points per track on average' % (float(ppoints)/float(llen)))

		return '\n'.join(message)

	def computeKDE(self):
		"""
		Compute Kernel Density Estimation of lat-lon data in track_list
		"""
		lon = np.array([track[i][1] for track in self.track_list for i in range(len(track))])
		lat = np.array([track[i][0] for track in self.track_list for i in range(len(track))])
		minlon = lon.min()
		minlat = lat.min()
		maxlon = lon.max()
		maxlat = lat.max()
		values = np.vstack([lat, lon])
		kernel = stats.gaussian_kde(values) # this is the KDE
		return (kernel, minlon, minlat, maxlon, maxlat)

	def evaluateKDE(self, nrow, ncol):
		"""
		Evaluate Kernel Density Estimation on a 2D grid of nrow x ncol 
		elements between minlat, maxlat, minlon, maxlon
		"""
		kernel, minlon, minlat, maxlon, maxlat = self.computeKDE()
		X, Y = np.mgrid[minlat:maxlat:nrow*1j, minlon:maxlon:ncol*1j]
		positions = np.vstack([X.ravel(), Y.ravel()])
		# kernel must be evaluated on a grid!
		Z = np.reshape(kernel(positions).T, X.shape)
		return np.vstack([X.ravel(), Y.ravel(), Z.ravel()]).T


def debug():
	"""
	Just for testing purposes
	"""
	ha = HistoryAnalitics("query1")
	ha.loadAll(expunge=True)
	tl = ha.track_list
	print ha.evaluateKDE(100, 100).shape


if __name__ == '__main__':
	debug()
	




