#!/usr/bin/env python

import numpy as np
import progaconstants as pgc
import math
import progaconstants
import pdb

class Point3D(object):
        
        def __init__(self, lon=0, lat=0, z=0):
                self.lon = lon
                self.lat = lat
                self.z = z
                self.setXY(*self.xyFromLonLat(self.lon,self.lat))
                self.w = 0.0

        def __repr__(self):
                return "3Dpoint %s" % (self.getNumpyVector())

        def xyFromLonLat(self, lon, lat):
                lat = math.radians(lat)
                lon = math.radians(lon)
                return (pgc.EARTHRADIUS*math.cos(lat)*math.sin(lon-pgc.LON0R),
                        pgc.EARTHRADIUS*(math.cos(pgc.LAT0R)*math.sin(lat) - math.sin(pgc.LAT0R)*math.cos(lat)*math.cos(lon-pgc.LON0R)))

        def invlat(self, x, y, rho, c):
                return math.asin(math.cos(c)*math.sin(pgc.LAT0R)+(y*math.sin(c)*math.cos(pgc.LAT0R))/rho)

        def invlon(self, x, y, rho, c):
                return pgc.LON0R + math.atan(x*math.sin(c)/(rho*math.cos(pgc.LAT0R)*math.cos(c)\
                                                            - y*math.sin(pgc.LAT0R)*math.sin(c)))
        
        def lonLatFromXY(self, x, y):
                rho = math.sqrt(x**2+y**2)
                if rho == 0.0:
                        return (pgc.LON0, pgc.LAT0)
                else:
                        c = math.asin(rho/pgc.EARTHRADIUS)
                        return (math.degrees(self.invlon(x,y,rho,c)),
                                math.degrees(self.invlat(x,y,rho,c)))

        def lonLatAltFromXYZ(self, x, y,z):
                rho = math.sqrt(x**2+y**2)
                if rho == 0.0:
                    return (pgc.LON0, pgc.LAT0,0)
                else:
                    c = math.asin(rho/pgc.EARTHRADIUS)
                    return (math.degrees(self.invlon(x,y,rho,c)),math.degrees(self.invlat(x,y,rho,c)),z)


        def setLonLat(self, lon, lat):
            self.lon = lon
            self.lat = lat

        def setXY(self, x, y):
            self.x = x
            self.y = y

        def getNumpyVector(self):
                return np.array([self.x, self.y, self.z], dtype=np.float64)

        def __eq__(self,other):
            return self.lat == other.lat and self.lon == other.lon and self.z == other.z



#ReferenceTrack modella l'intent del pilota. Un oggetto di questo tipo viene istanziato ed poi
#passato ad una track id. IMPORTANTE: due track che seguono lo stesso intent (a livello di punti), non condividono
#lo stesso oggetto ReferenceTrack anche se quei punti sono uguali. Questo vuol dire che ogni volo conserva la sua copia personale della
#reference track. questo vuol dire anche che l'oggetto che contiene i pesi, contiene tutte le track reference per ogni volo
class ReferenceTrack(object):

        #pointList e' una list di Point3D       
        def __init__(self, pointList, flight_id=None):
                self._line = pointList
                self._refTrackID = None
                self.w = -1
                self._flight_id = flight_id

        @property
        def line(self):
            return self._line

        @property
        def flight_id(self):
            return self._flight_id

        @flight_id.setter
        def flight_id(self, flightID):
            self._flight_id = flightID

        @property
        def refTrackID(self):
            return self._refTrackID

        @refTrackID.setter
        def refTrackID(self, refTrackID):
            self._refTrackID = refTrackID


        def getDirectionsList(self):
                if len(self.line) > 0:
                        return [t[1].getNumpyVector() - t[0].getNumpyVector() for t in zip(self.line[:-1], self.line[1:])]

        def __repr__(self):
                #return "Line of %d points form %s to %s" % (len(self.line), self.line[0], self.line[-1])
                return "%s"%([p for p in self.line])

        def __eq__(self,other):
            if other == None or other.__class__.__name__ != 'ReferenceTrack':
                return False

            otherline = other.getLine()
            if len(self.line) != len(otherline):
                return False

            for thispoint, otherpoint in zip(self.line, otherline):
                if thispoint != otherpoint:
                    return False

            return True

        def lineAsListOfLegs(self):
        	return [(t[0].getNumpyVector(), t[1].getNumpyVector()) for t in zip(self.line[:-1], self.line[1:])]

        def distanceFromGivenPoint(self, p):
            distfromLeg = np.inf
            minDistLeg = -1
            line = self.lineAsListOfLegs()
            point = p.getNumpyVector()
            leftOrRight = 0.
            for leg, index in zip(line, range(len(line))):
                t = np.dot(leg[1]-leg[0], point-leg[0])/np.dot(leg[1]-leg[0], leg[1]-leg[0])
                if t >= 0 and t <= 1:
                    candidateDist = np.sqrt( np.dot(leg[0] + t*(leg[1]-leg[0]) - point, leg[0] + t*(leg[1]-leg[0]) - point ) )
                    u = p.getNumpyVector()-leg[0]
                    v = leg[1]-leg[0]
                    leftOrRight = int(np.sign( u[0]*v[1] - v[0]*u[1] )) # right is +1, left is -1
                    if candidateDist <= distfromLeg:
                        distfromLeg = candidateDist
                        minDistLeg = index
            return (distfromLeg, minDistLeg, leftOrRight)


def trackSetAnalyzer(trackSet, objReferenceTrack):
    """
    trackSet must be a dictionry of the form
    {
    'id_1': [point3D_1, point3D_2, ...],
    'id_2': [point3D_1, point3D_2, ...],
    .
    .
    .
    'id_n': [point3D_1, point3D_2, ...]
    }
    """
    data = dict( zip( ['leg'+str(i) for i in range( len(objReferenceTrack.line)-1 )], [[] for i in range( len(objReferenceTrack.line)-1 )] ) )

    for track in trackSet.values():
        for point in track:
            d, l, s = objReferenceTrack.distanceFromGivenPoint(point)
            if l < -1: print l
            try:
                data['leg'+str(l)].append(s*d)
            except KeyError:
                continue
    for k, L in data.items():
        print k, ':: mean = ', np.mean(L), 'sd = ', np.std(L)


def loadTrack(trackfilename, track_id, flight_start):
    #trackflilename does not include the path, it's only name and extesion
    #track = open("./Flight1.txt", "r")
    path = []
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

                p = Point3D(lon, lat, altitude)

                path.append(p)

            cont += 1
            
    return path


if __name__ == '__main__':
        p1 = Point3D(2.0664806, 48.8136806, 113.0808)
        print 'P1', p1
        p2 = Point3D(1.9450000, 48.9983333,  113.0808)
        print 'P2', p2
        p3 = Point3D(1.1761917, 49.3852111,  156.0576)
        print 'P3', p3
        p4 = Point3D(0.5666667, 49.1027778,  168.8592)
        print 'P4', p4
        L = [p1, p2, p3 , p4]
        refTrack = ReferenceTrack(L)
        ppp = Point3D(2.017732, 48.984049, 113.)
        print refTrack.distanceFromGivenPoint(ppp)
        pathToFlownTraces = '/Users/clancia/Google Drive/ProGA/Flight Simulator Tracks/'
        flights = ['Flight3.txt', 'Flight5.txt']
        flightFiles = [a + b for (a,b) in zip([pathToFlownTraces]*len(flights), flights)]
        flightIDs = ['Hello_World_' + str(i+1) for i in range(len(flights))]
        flightStarts = [0]*len(flights) # fix
        flightObjects = [loadTrack(a,b,c) for (a,b,c) in zip(flightFiles, flightIDs, flightStarts) ]
        trackSet = dict( zip(flightIDs, flightObjects) )
        trackSetAnalyzer(trackSet, refTrack)
