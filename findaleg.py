#!/usr/bin/env python

import numpy as np
from numpy.linalg import norm

ECC = 0.75
LOCRADIUS = .25 # meters
PENAL_GLOBAL = 0.1**6
PENAL_ANGLE = 0.1**2
PENAL_DIST = 0.1**2
ANGLE_GAP = np.pi/12 # 15. degrees
BETA_DIST = 0.01 # meters^{-1}
BETA_ANGLE = 0.5 


def projection(v, u):
    """
    Projector of v onto the line of u
    """
    return np.dot(u,v)/np.dot(u,u) * u


def legger(track, p):
    """
    Return a list of legs of track that are candidate legs
    according to the 'sausage' model
    """
    L = []
    for i, leg in zip(range(len(track)), track):
        c = .5 * (leg[1] + leg[0])
        a = .5 * norm(leg[1] - leg[0])
        b = np.sqrt(1-ECC**2)
        pproj = projection(p-c, leg[1]-c)
        px = norm(pproj)
        py = norm(p-c-pproj)
        if (px/a)**2 + (py/b)**2 <= 1:
            L.append(i)
    return L

## def findMyLeg(track, p, v):
##     candidateLegs = legger(track, p)
##     if len(candidateLegs) == 0:
##         # if no candidates, we look for the turning point that is closest to p and then decide based on v
##         dist = norm(p-track[0][0])
##         candidatePoint = -1
##         for i, leg in zip(range(len(track)), track):
##             newDist = norm(p-leg[1])
##             if  newDist < dist:
##                 dist = newDist
##                 candidate = i
##         if candidatePoint == -1:
##             return 0
##         elif candidatePoint == len(track)-1:
##             return candidatePoint + 1
##         else:
##             d = track[candidatePoint][1] - track[candidatePoint][0]
##             alpha0 = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
##             d = track[candidatePoint+1][1] - track[candidatePoint+1][0]
##             alpha1 = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
##             if abs(alpha0) < abs(alpha1):
##                 return candidatePoint
##             else:
##                 return candidatePoint +1
##     elif len(candidateLegs) == 1:
##         # if exactly one candidate is present, we return it
##         return candidateLegs[0]
##     else:
##         # if more than one candidate leg, we determine which to return based on v
##         directions = [track[leg][1]-track[leg][0] for leg in candidateLegs]
##         print "Directions ::", directions
##         alpha = 2*np.pi
##         indx = -1
##         for d,i in zip(directions, range(len(candidateLegs))):
##             newAlpha = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
##             if abs(newAlpha) < alpha:
##                 alpha = newAlpha
##                 indx = i
##         return candidateLegs[indx]

def findWeights(track, p, v):
    """
    Return index of leg that is most-likely flown and track weight
    based on position and velocity of the aircraft
    """
    candidateLegs = legger(track, p)
    if len(candidateLegs) == 1:
        # aircraft lies in only one sausage
        print 'in-leg',
        leg = track[candidateLegs[0]]
        legDirection = leg[1]-leg[0]
        distanceFromLeg = norm(p - leg[0] - projection(p-leg[0], legDirection))
        legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
        return (candidateLeg[0], np.exp( - BETA_DIST*distanceFromLeg - BETA_ANGLE*legTrackAngle ))
    else:
        # aircraft lies in multiple or no sausages
        # look around turning points
        if norm(p - track[0][0]) < LOCRADIUS:
            # aircraft lies around the departure airfield
            print 'appena partito',
            legDirection = track[0][1]-track[0][0]
            legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
            return (0, np.exp(- BETA_DIST * norm(p - track[0][0]) - BETA_ANGLE * legTrackAngle))
        elif norm(p - track[-1][1]) < LOCRADIUS:
            # aircraft lies around the arrival airfield
            print 'in arrivo',
            legDirection = track[-1][1]-track[-1][0]
            legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
            return (len(track)-1, np.exp(- BETA_DIST * norm(p - track[-1][1]) - BETA_ANGLE * legTrackAngle))
        else:
            # look around turning points
            for i, j in zip(range(len(track)-1), range(1, len(track))):
                # prevLeg is the leg that 'enters' in the turnpoint
                # nextLeg is the leg that 'exits' from the turnpoint
                prevLeg, nextLeg = track[i], track[j]
                turnPoint = nextLeg[0]
                if norm(p - turnPoint) < LOCRADIUS:
                    # the vector nextLeg[1]-prevLeg[0] joins the origin of prevLef with the destination of nextLeg
                    # it is the 'average' direction that should be followed around the turnpoint
                    u = prevLeg[1] - prevLeg[0]
                    w = nextLeg[1] - nextLeg[0]
                    vcrossu = v[0]*u[1] - v[1]*u[0]
                    vcrossw = v[0]*w[1] - v[1]*w[0]
                    ucrossw = u[0]*w[1] - u[1]*w[0]
                    if ucrossw < 0:
                        print 'virata clockwise'
                        if vcrossu > 0 and vcrossw < 0:
                            print 'virata'
                            vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                                 np.dot(v,w)/(norm(w) * norm(v))])
                            if vangles[0] < vangles[1]:
                                return (i, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[0]))
                            else:
                                return (j, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[1]))
                        elif vcrossu > 0 and vcrossw > 0:
                            print 'interno'
                            return ( j, np.exp(- BETA_DIST * norm(p - turnPoint)) *  PENAL_ANGLE )
                        elif vcrossu < 0 and vcrossw < 0:
                            print 'esterno'
                            return ( i, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE )
                        else:
                            print 'opposto'
                            return (i, PENAL_DIST * PENAL_ANGLE)
                    else:
                        print 'virata couterclockwise'
                        if vcrossu < 0 and vcrossw > 0:
                            print 'virata'
                            vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                                 np.dot(v,w)/(norm(w) * norm(v))])
                            if vangles[0] < vangles[1]:
                                return (i, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[0]))
                            else:
                                return (j, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[1]))
                        elif vcrossu < 0 and vcrossw < 0:
                            print 'interno'
                            return ( j, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE) 
                        elif vcrossu > 0 and vcrossw > 0:
                            print 'esterno'
                            return ( i, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE) 
                        else:
                            print 'opposto'
                            return (i, PENAL_DIST * PENAL_ANGLE)
            else:
                print 'no match found',
                distances = [norm(p - turnPoint) for turnPoint in [leg[0] for leg in track] ]
                turnPointIndex = distances.index( min(distances) )
                return (turnPointIndex, PENAL_GLOBAL)

if __name__ == '__main__':
    print  '-'*24 + '\nTHIS IS A TEST PROCEDURE\n' + '-'*24 
    ref1 = [np.array([0., 0.]), np.array([5000., 5000.]), np.array([4000., 12000.]), np.array([-5000., 7500.]), np.array([0., 3500.])]
    track = zip(ref1[:-1], ref1[1:])
    print 'Test Track:'
    for i in track:
        print i[0], '-->', i[1]
    print '-'*24
    point = np.array([5100., 4900.])
    velocity = np.array([56., 60.])
    print 'point:', point, '** velocity:', velocity
    print 'response:', findWeights(track, point, velocity)
    print  '-'*24
    point = np.array([3950., 12150.])
    velocity = np.array([11., 72.])
    print 'point:', point, '** velocity:', velocity
    print 'response:', findWeights(track, point, velocity)
    print  '-'*24
