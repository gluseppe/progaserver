#!/usr/bin/env python

import numpy as np
from numpy.linalg import norm
import numpy.random as npr
import pdb

ECC = 0.75
LOCRADIUS = .25 # meters #ADJUST
PENAL_GLOBAL = 0.1**6
PENAL_ANGLE = 0.1**2
PENAL_DIST = 0.1**2
BETA_DIST = 0.01 # meters^{-1}
BETA_ANGLE = 0.5 
ROTSCALE = 0.0175 # around 1 degrees
ALTSCALE = .005 # 5 centimeters
XYSCALE = .001 # meters #ADJUST


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

def normL2(x):
    return np.sum(np.abs(x)**2,axis=-1)**(.5)

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
        return (candidateLegs[0], np.exp( - BETA_DIST*distanceFromLeg - BETA_ANGLE*legTrackAngle ))
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

def weightedValues(values, probabilities, size):
    # First using accumulate we create bins.
    # Then we create a bunch of random numbers (between 0, and 1) using random_sample
    # We use digitize to see which bins these numbers fall into.
    # And return the corresponding values.
    bins = np.add.accumulate(probabilities)
    return values[np.digitize(npr.random_sample(size), bins)]

def rotation(alpha):                              
    def rot(v):
        return np.array([v[0]*np.cos(alpha)-v[1]*np.sin(alpha), v[1]*np.cos(alpha)+v[0]*np.sin(alpha),v[2]])
    return rot

class bunchOfParticles(object):
    def __init__(self, p, v, size, dt, referenceTracks):
        """
        referenceTracks deve essere passato come predictor.tracks[aircraft_ID]
        """
        self.dt = dt
        self.numPart = size
        self.positions = np.tile(p, size).reshape( (size,3) )
        self.velocities = np.tile(v, size).reshape( (size,3) )
        # Questa e' la riga buona
        # bar = [[a.getNumpyVector()[:2] for a in tt] for tt in referenceTracks]
        # Questa e' solo per debug
        bar = [[a[:2] for a in tt] for tt in referenceTracks.values()]
        #
        foo = [findWeights(zip(tt[:-1], tt[1:]), p[:2], v[:2]) for tt in bar]
        self.tracks = [zip(tt[:-1], tt[1:]) for tt in bar] # self.tracks[i] contiene la traccia i-esima 
        tLegs = np.array([f[0] for f in foo]) # tLegs[i] contiene il leg di riferimento della traccia i-esima
        tWeights = np.array([f[1] for f in foo]) # tWeights[i] contiene il leg di riferimento della traccia i-esima
        tWeights /= sum(tWeights)
        sampledTracks = weightedValues(np.arange(len(bar)), tWeights, self.numPart)
        # next line is just for testing
        sampledTracks = np.array([0, 0, 1])
        self.partReference = np.vstack( (sampledTracks, [tLegs[i] for i in sampledTracks]) )
        # self.partReference[0,j] = indice della traccia di riferimento della particella j-esima
        # self.partReference[1,j] = indice del leg di riferimento della particella j-esima
        
    def takeAmove(self):
        simulTimes = self.simulationTime(self.dt)
        # randomly rotate velocities
        for i, alpha in zip(range(self.numPart), alphaToNextTurnPoint):
            angle = np.random.normal(loc=alpha, scale=ROTSCALE, self.numPart)
            rrot = rotation(angle)
            self.velocities[i] = rrot(self.velocities[i])
        #
        self.velocities[:, :2] *= (1. + np.random.normal(scale=XYSCALE, self.numPart))
        self.velocities[:, 2] += np.random.normal(scale=ALTSCALE, self.numPart)
        self.positions = self.positions + np.dot(np.diag(simulTimes[0]), self.velocities)
        indices = simulTimes[1].nonzero()[0]
        curLeg = self.getLeg(indices)
        self.setNextLeg(indices)
        nextLeg = self.getLeg(indices)
        uu = [(leg[1] - leg[0])/norm(leg[1][:2] - leg[0][:2]) for leg in curLeg]
        vv = [(leg[1] - leg[0])/norm(leg[1][:2] - leg[0][:2]) for leg in nextLeg]
        alphasin = [u[0]*v[1] - u[1]*v[0] for u, v in zip(uu, vv)]
        alphacos = [np.dot(u,v) for u, v in zip(uu, vv)]
        alphasign = np.sign(alphasin)
        for i in range(len(alphasign)):
            rrot = rotation( alphasign[i] * np.arctan2(abs(alphasin[i]), alphacos[i]) )
            self.velocities[i, :] = rrot(self.velocities[i, :])
        # rotate velocity for particle-index in simulTimes[1].nonzero()
        pdb.set_trace()
        self.positions = self.positions + np.dot(np.diag(simulTimes[1]), self.velocities)

    def getLeg(self, indices):
        # leggo j in indices, 
        # vado a prendere in self.partReference[0,j] l'indice della traccia che sta seguendo la particella j
        # self.tracks[ self.partReference[0,j] ] e' la traccia che sta seguendo la particella j
        # vado a prendere in self.partReference[1,j] l'indice del leg che sta seguendo la particella j
        return [ self.tracks[ self.partReference[0,j] ][self.partReference[1,j]] for j in indices ]

    def setNextLeg(self, indices):
        for i in indices:
            self.partReference[1, i] = min(len(self.tracks[ self.partReference[0,i] ]) - 1, self.partReference[1,i] + 1)

    def timeToNextTurnPoint(self):
        nextTP = np.array([ leg[1] for leg in self.getLeg(np.arange(self.numPart)) ] )
        return normL2(self.positions[:,:2] -  nextTP)/normL2(self.velocities[:,:2])
        #return norm(self.getPositionsAsList() -  nextTP)/self.getVelocitiesAsList()

    def alphaToNextTurnPoint(self):
        nextTP = np.array([ leg[1] for leg in self.getLeg(np.arange(self.numPart)) ] )
        foo = (nextTP - self.positions[:,:2]).T
        pdb.set_trace()
        return np.arctan2(foo[1], foo[0])

    def simulationTime(self, dt):
        timesToNextTP = self.timeToNextTurnPoint()
        dtVec = dt * np.ones( self.numPart )
        tau = np.minimum(timesToNextTP,  dtVec)
        return (tau, dtVec-tau)


if __name__ == '__main__':
    print  '-'*24 + '\nTHIS IS A TEST PROCEDURE\n' + '-'*24 
    ref1 = [np.array([0., 0., 0.]), np.array([5., 5., 10.]), np.array([4., 12., 10.]), np.array([-5., 7.5, 10.]), np.array([0., 3.5, 0.])]
    ref2 = [np.array([0., 0., 0.]), np.array([6., 6., 10.]), np.array([-4., 7., 10.]), np.array([-5., 10., 10.]), np.array([0., 7, 0.])]
    trkDict = {0: ref1, 1: ref2}
    point = np.array([5.1, 4.9, 10])
    velocity = np.array([.56, .51, .1])
    bop = bunchOfParticles(point, velocity, 3, 1, trkDict)
    pdb.set_trace()