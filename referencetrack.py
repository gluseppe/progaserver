#!/usr/bin/env python
class Point3D(object):
	
	def __init__(self, lon, lat, z):
		self.lon = lon
		self.lat = lat
		self.z = z

		self.x,self.y = self.xyFromLonLat(self.lon,self.lat)


	def xyFromLonLat(self,lon,lat):
		pass


	def lonLatFromXY(self,lon,lat):
		pass


	#def getNumPYVector(self):
	#	return 




class ReferenceTrack(object):

	#pointList e' una list di Point3D	
	def __init__(self, pointList):
		self.line = pointList


	def cicciobello(self):
		if len(self.line) > 0:
			return [t[1]-t[0] for t in zip(self.line[:-1], self.line[1:])]




if __name__ == '__main__':
	l = [1,2,3,5,5,6,7]
	track = ReferenceTrack(l)

	print track.cicciobello()











