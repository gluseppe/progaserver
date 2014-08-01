#!/usr/bin/env python

import numpy as np
import progaconstants as pgc
import math

class Point3D(object):
        
        def __init__(self, lon, lat, z):
                self.lon = lon
                self.lat = lat
                self.z = z
                self.setXY(*self.xyFromLonLat(self.lon,self.lat))

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

        def setLonLat(self, lon, lat):
            self.lon = lon
            self.lat = lat

        def setXY(self, x, y):
            self.x = x
            self.y = y

        def getNumpyVector(self):
                return np.array([self.x, self.y, self.z], dtype=np.float64)


class ReferenceTrack(object):

        #pointList e' una list di Point3D       
        def __init__(self, pointList):
                self.line = pointList


        def getDirectionsList(self):
                if len(self.line) > 0:
                        return [t[1].getNumpyVector() - t[0].getNumpyVector() for t in zip(self.line[:-1], self.line[1:])]

        def __repr__(self):
                return "Line of %d points form %s to %s" % (len(self.line), self.line[0], self.line[-1])




if __name__ == '__main__':
        p1 = Point3D(pgc.LON0, pgc.LAT0, 0)
        p2 = Point3D(pgc.LON0, pgc.LAT0, 100)
        p3 = Point3D(pgc.LON0, pgc.LAT0 + 0.01, 100)
        p4 = Point3D(pgc.LON0 + 0.01, pgc.LAT0 + 0.01, 100)
        p5 = Point3D(pgc.LON0 + 0.01, pgc.LAT0, 100)
        L = [p1, p2, p3 , p4, p5]
        track = ReferenceTrack(L)

        print track.getDirectionsList()











