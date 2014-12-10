#!/usr/bin/env python
import os, os.path
from track import Track
import glob
import progaconstants



class HistoryAnalitics(object):

	

	def __init__(self, query_name):
		self.root_folder = "./db/history"
		self.query_name = query_name
		self.track_list = []
		self.prefix_file_name = "flight"
		self.files_iterable = glob.glob(self.root_folder + "/" + query_name + "/" + self.prefix_file_name + "*[0-9].txt")
		self.loadAll()


	def loadAll(self):
		for name,i in zip(self.files_iterable,range(len(self.files_iterable))):
			self.track_list.append(self.loadTrack(name,i))






	def loadTrack(self, trackfilename, track_id):
			#trackflilename does not include the path, it's only name and extesion
			#track = open("./Flight1.txt", "r")
			track = Track(track_id)
			cont = 0
			with open(trackfilename, "r") as trackfile:
				for line in trackfile:
					
					if (not (line.startswith('#') or line.startswith('/'))) and len(line)>30:
						parts = line.split()
						timestamp = parts[0]
						lat = float(parts[1])
						lon = float(parts[2])
						altitude = float(parts[3])*progaconstants.FOOT2MT
						heading = float(parts[6])
						v_x = float(parts[8])*progaconstants.FOOT2MT
						v_y = float(parts[10])*progaconstants.FOOT2MT
						v_z = float(parts[9])*progaconstants.FOOT2MT
						pitch = float(parts[4])
						bank = float(parts[5])
	
						track.addStep(timestamp, lat, lon, altitude, v_x, v_y, v_z, heading, pitch, bank)
	
					cont += 1
					
			track.setStart(0)
			return track


if __name__ == '__main__':
	ha = HistoryAnalitics("query1")
	tl = ha.track_list
	print len(tl)
	print tl[0].path[:3]
	




