#!/usr/bin/env python
import os, os.path
from track import Track
import glob
import progaconstants
import numpy as np



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


	def loadTrack(self, trackfilename):
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
		return track

def debug():
	"""
	Just for testing purposes
	"""
	ha = HistoryAnalitics("query1")
	tl = ha.track_list
	print len(tl)
	print tl[0][:3]


if __name__ == '__main__':
	debug()
	




