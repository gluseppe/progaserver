#!/usr/bin/env python
import os, os.path
from track import Track
import glob
import progaconstants
import numpy as np
from scipy import stats
from math import cos, sqrt

DEFAULT_RADIUS = 10 # distance in Km

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
		self.loadAll()


	def loadAll(self):
		"""
		Creates a list of tracks
		Each tracks is a list of 3D numpy vectors (LON, LAT, ALT)
		"""
		for name in self.files_iterable:
			self.track_list.append(self.loadTrack(name))


	def loadTrack(self, trackfilename, expunge=True, expRadius=DEFAULT_RADIUS):
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

	def expungeAroundDepArrAirfields(self, track, expRadius=DEFAULT_RADIUS):
		"""
		Whanasget?
		"""
		dep_lon = track[0][0]
		dep_lat = track[0][1]
		arr_lon = track[-1][0]
		arr_lat = track[-1][1]
		while True:
			lon = track[-1][0]
			lat = track[-1][1]
			meanlat = .5 * (arr_lat + lat)
			difflat = arr_lat - lat
			difflon = arr_lon - lon
			K1 = 111.13209 - .56605 * cos(2*meanlat) + .0012 * cos(4*meanlat)
			K2 = 111.41513 * cos(meanlat) - .09455 * cos(3*meanlat) + .00012 * cos(5*meanlat)
			distance = sqrt((K1*difflat)**2 + (K2*difflon)**2)
			if distance < expRadius:
				track.pop()
			else:
				break
		track.reverse()
		while True:
			lon = track[-1][0]
			lat = track[-1][1]
			meanlat = .5 * (dep_lat + lat)
			difflat = dep_lat - lat
			difflon = dep_lon - lon
			K1 = 111.13209 - .56605 * cos(2*meanlat) + .0012 * cos(4*meanlat)
			K2 = 111.41513 * cos(meanlat) - .09455 * cos(3*meanlat) + .00012 * cos(5*meanlat)
			distance = sqrt((K1*difflat)**2 + (K2*difflon)**2)
			if distance < expRadius:
				track.pop()
			else:
				break
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

	def plotKDE(self):
		"""
		Plot Kernel Density Estimation of lat-lon data in track_list
		"""
		import matplotlib.pyplot as plt
		kernel, minlon, minlat, maxlon, maxlat = self.computeKDE()
		X, Y = np.mgrid[minlat:maxlat:100j, minlon:maxlon:100j]
		positions = np.vstack([X.ravel(), Y.ravel()])
		# kernel must be evaluated on a grid!
		Z = np.reshape(kernel(positions).T, X.shape)
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.imshow(np.rot90(Z), cmap=plt.cm.gist_earth_r, extent=[minlat, maxlat, minlon, maxlon])
		#ax.plot(lon, lat, 'k.', markersize=2)
		ax.set_xlim([minlat, maxlat])
		ax.set_ylim([minlon, maxlon])
		plt.show()


def debug():
	"""
	Just for testing purposes
	"""
	ha = HistoryAnalitics("query1")
	tl = ha.track_list
	ha.plotKDE()


if __name__ == '__main__':
	debug()
	




