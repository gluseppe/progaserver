import progaconstants as pgc
import math
from referencetrack import Point3D
import pdb
import copy
import simplejson as json

"""
This is the Cluster class.
Each cluster aggregates particles of the same reference track. 
the reference track here is just an id. It doesn't really matter internally for the computation
we retain the id just to make it available later if needed
"""
class Cluster(object):

	c_lat = 0.0
	c_lon = 0.0
	c_h = 0.0

	center = None
	particles = list()
	#number of particles already inside the cluster
	n_particles = 0
	"""
	We use standard deviation measure from the current center of the cluster
	therefore the measure is computed as followinf
	uncertainty =  sqrt () (sum(distance(particle-i, center)**2)) / n_particles )
	"""
	uncertainty = -1.0 #meters
	time = -1
	group_id = -1

	#the f factor brings the new center closer to the old one 
	#as the number of particles inside increases
	f = 0.5


	def __init__(self,group_id,lat,lon,h,time):
		self.center = Point3D(lon,lat,h)
		self.group_id = group_id
		self.time = time
		self.n_particles = 1
		self.particles.append(Point3D(lon,lat,h))
		self.uncertainty = 0

	def addParticle(self,lat,lon,h):
		if self.n_particles > 0:
			self.updateCenter(lat,lon,h)
			self.f = self.f - (0.5/pgc.NUMPARTICLES)
		else:
			self.center = Point3D(lon,lat,h)

		self.n_particles += 1
		self.particles.append(Point3D(lon,lat,h))
		self.updateUncertaintyMeasure(lat,lon,h)
		##print "n_particle is " + str(self.n_particles)
		#print "len(particles)" + str(len(self.particles))

		

	"""
	based on the formulas here
	http://www.movable-type.co.uk/scripts/latlong.html intermediate point
	"""
	def updateCenter(self,lat,lon,h):
		#print "updating center"
		#print "f = " + str(self.f)
		distance = self.center.distance(lon,lat)
		angular_distance = distance/pgc.EARTHRADIUS
		lat = math.radians(lat)
		lon = math.radians(lon)
		a = math.sin((1-self.f)*angular_distance) / math.sin(angular_distance)
		b = math.sin(self.f*angular_distance) / math.sin(angular_distance) 
		x = a * math.cos(math.radians(self.center.lat)) * math.cos(math.radians(self.center.lon)) + b * math.cos(lat) * math.cos(lon)
		y = a * math.cos(math.radians(self.center.lat)) * math.sin(math.radians(self.center.lon)) + b * math.cos(lat) * math.sin(lon)
		z = a * math.sin(math.radians(self.center.lat)) + b * math.sin(lat)
		new_center_lat = math.atan2(z,math.sqrt(x**2+y**2))
		new_center_lon = math.atan2(y,x)


		self.center.lat = math.degrees(new_center_lat)
		self.center.lon = math.degrees(new_center_lon)
		self.center.z = (self.center.z + h) / 2


		

	"""
	We use standard deviation measure from the current center of the cluster
	therefore the measure is computed as followinf
	uncertainty =  sqrt () (sum(distance(particle-i, center)**2)) / n_particles )
	"""
	def updateUncertaintyMeasure(self,lat,lon,h):
		#pdb.set_trace()
		summ = 0
		for p in self.particles:
			d2 = p.distance(self.center.lon, self.center.lat)**2
			#print "distance^2 between particle and center is " + str(d2)
			summ = summ + d2

		#pdb.set_trace()
		self.uncertainty = math.sqrt(summ / (len(self.particles)))

	def toJSON(self):
		j = copy.copy(self.__dict__)
		j['lat'] = self.center.lat
		j['lon'] = self.center.lon
		j['h'] = self.center.z
		del(j['center'])
		return json.dumps(j)

	def toSerializableObject(self):
		j = copy.copy(self.__dict__)
		j['lat'] = self.center.lat
		j['lon'] = self.center.lon
		j['h'] = self.center.z
		del(j['center'])
		return j












