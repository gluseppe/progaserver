import progaconstants as pgc
import math
from referencetrack import Point3D
import pdb
import copy
import simplejson as json

"""
This is the Cluster class.
Each cluster aggregates particles of the same reference track, and time horizon. 
the reference track here is just an id. It doesn't really matter internally for the computation
we retain the id just to make it available later if needed
"""
class Cluster(object):

	center = None
	
	#number of particles already inside the cluster
	n_particles = 0
	"""
	We use standard deviation measure from the current center of the cluster
	therefore the measure is computed as followinf
	uncertainty =  sqrt ( (sum(distance(particle-i, center)**2)) / n_particles )  )
	"""
	uncertainty = -1.0 #meters
	time = -1
	group_id = -1
	particles = None
	proximity = -1.0
	dangerous = False
	

	#the f factor brings the new center closer to the old one 
	#as the number of particles inside increases
	f = 0.5


	def __init__(self,group_id,lat,lon,h,time):
		self.center = Point3D(lon,lat,h)
		self.group_id = group_id
		self.time = time
		self.n_particles = 1
		self.particles = list()
		self.particles.append(Point3D(lon,lat,h))
		self.uncertainty = 0
		self.dangerous = False
		self.proximity = -1.0
		

	def addParticle(self,lat,lon,h):
		self.n_particles += 1
		if self.n_particles > 0:
			self.updateCenter(lat,lon,h)
			self.f = self.f - (0.5/pgc.NUMPARTICLES)
		else:
			self.center = Point3D(lon,lat,h)

		
		self.particles.append(Point3D(lon,lat,h))
		self.updateUncertaintyMeasure(lat,lon,h)
		##print "n_particle is " + str(self.n_particles)
		#print "len(particles)" + str(len(self.particles))

		

	"""
	based on the formulas here
	http://www.movable-type.co.uk/scripts/latlong.html intermediate point
	The f factor tends to the current center of the cluster as the cluster aggregates more particles
	f starts from 0.5, which is neutral and gives exactly the intermediate point. But every time a particle
	is added to the cluster, it is reduced by 1/tot_particles where tot_particles is the total number of particles
	used for the prediction
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
	praticamente e' la deviazione standard dell'insieme di particelle in cui
	- la media e' rappresentata dal centro del cluster
	- la differenza tra media e valore e' rappresentata dalla distanza

	we can draw circles of a given measure (uncertainty?) using the formula here
	http://wiki.openstreetmap.org/wiki/Zoom_levels

	The distance represented by one pixel (S) is given by
	S=C*cos(y)/2^(z+8)
	
	where...

	C is the (equatorial) circumference of the Earth
	z is the zoom level
	y is the latitude of where you're interested in the scale.

	"""
	def updateUncertaintyMeasure(self,lat,lon,h):
		#pdb.set_trace()
		summ = 0
		for p in self.particles:
			d2 = p.distance(self.center.lon, self.center.lat)**2
			#print "distance^2 between particle and center is " + str(d2)
			summ = summ + d2
			#print "sum:",summ

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
		del(j['particles'])
		return j












