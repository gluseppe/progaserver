import numpy as np
from numpy.linalg import norm

ECC = 0.

def projection(v, u):
    return np.dot(u,v)/np.dot(u,u) * u


def legger(track, p):
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
    print "Legger ::", L
    return L

def findMyLeg(track, p, v):
    candidateLegs = legger(track, p)
    if len(candidateLegs) == 0:
        # if no candidates, we look for the turning point that is closest to p and then decide based on v
        dist = norm(p-track[0][0])
        candidatePoint = -1
        for i, leg in zip(range(len(track)), track):
            newDist = norm(p-leg[1])
            if  newDist < dist:
                dist = newDist
                candidate = i
        if candidatePoint == -1:
            return 0
        elif candidatePoint == len(track)-1:
            return candidatePoint + 1
        else:
            d = track[candidatePoint][1] - track[candidatePoint][0]
            alpha0 = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
            d = track[candidatePoint+1][1] - track[candidatePoint+1][0]
            alpha1 = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
            if abs(alpha0) < abs(alpha1):
                return candidatePoint
            else:
                return candidatePoint +1
    elif len(candidateLegs) == 1:
        # if exactly one candidate is present, we return it
        return candidateLegs[0]
    else:
        # if more than one candidate leg, we determine which to return based on v
        directions = [track[leg][1]-track[leg][0] for leg in candidateLegs]
        print "Directions ::", directions
        alpha = 2*np.pi
        indx = -1
        for d,i in zip(directions, range(len(candidateLegs))):
            newAlpha = np.arccos(np.dot(d,v)/(norm(d)*norm(v)))
            if abs(newAlpha) < alpha:
                alpha = newAlpha
                indx = i
        return candidateLegs[indx]
            
    

if __name__ == '__main__':
    ref1 = [np.array([0., 0.]), np.array([1., 1.]), np.array([1., 2.]), np.array([-1, 2.]), np.array([0., 1.5])]
    track = zip(ref1[:-1], ref1[1:])
    point = np.array([1., 1.])
    velocity = np.array([.75, .75])
    print findMyLeg(track, point, velocity)
