#!/usr/bin/env python

import numpy as np
import progaconstants as pgc
import math

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
                self.id = None
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


        def getDirectionsList(self):
                if len(self.line) > 0:
                        return [t[1].getNumpyVector() - t[0].getNumpyVector() for t in zip(self.line[:-1], self.line[1:])]

        def __repr__(self):
                return "Line of %d points form %s to %s" % (len(self.line), self.line[0], self.line[-1])

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





if __name__ == '__main__':
        p1 = Point3D(pgc.LON0, pgc.LAT0, 0)
        p2 = Point3D(pgc.LON0, pgc.LAT0, 100)
        p3 = Point3D(pgc.LON0, pgc.LAT0 + 0.01, 100)
        p4 = Point3D(pgc.LON0 + 0.01, pgc.LAT0 + 0.01, 100)
        p5 = Point3D(pgc.LON0 + 0.01, pgc.LAT0, 100)
        L = [p1, p2, p3 , p4, p5]
        track = ReferenceTrack(L)

        print track.getDirectionsList()











