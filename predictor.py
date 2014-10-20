from progaconstants import WUPDATE_SECONDS, BETA_POS, BETA_TRK, NUMPARTICLES, GRIDBINS
from progaconstants import ECC, LOCRADIUS, PENAL_GLOBAL, PENAL_ANGLE, PENAL_DIST, ANGLE_GAP, BETA_DIST, BETA_ANGLE
import cherrypy
import numpy as np
import numpy.random as npr
import pdb


def projection(v, u):
    """
    Projector of v onto the line of u
    """
    return np.dot(u,v)/np.dot(u,u) * u

def norm(v):
    return np.sqrt(np.dot(v,v))

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
                        if vcrossu > 0 and vcrossw < 0:
                            vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                                 np.dot(v,w)/(norm(w) * norm(v))])
                            if vangles[0] < vangles[1]:
                                return (i, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[0]))
                            else:
                                return (j, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[1]))
                        elif vcrossu > 0 and vcrossw > 0:
                            return ( j, np.exp(- BETA_DIST * norm(p - turnPoint)) *  PENAL_ANGLE )
                        elif vcrossu < 0 and vcrossw < 0:
                            return ( i, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE )
                        else:
                            return (i, PENAL_DIST * PENAL_ANGLE)
                    else:
                        if vcrossu < 0 and vcrossw > 0:
                            vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                                 np.dot(v,w)/(norm(w) * norm(v))])
                            if vangles[0] < vangles[1]:
                                return (i, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[0]))
                            else:
                                return (j, np.exp(- BETA_DIST * norm(p - turnPoint) - BETA_ANGLE*vangles[1]))
                        elif vcrossu < 0 and vcrossw < 0:
                            return ( j, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE) 
                        elif vcrossu > 0 and vcrossw > 0:
                            return ( i, np.exp(- BETA_DIST * norm(p - turnPoint)) * PENAL_ANGLE) 
                        else:
                            return (i, PENAL_DIST * PENAL_ANGLE)
            else:
                distances = [norm(p - turnPoint) for turnPoint in [leg[0] for leg in track] ]
                turnPointIndex = distances.index( min(distances) )
                return (turnPointIndex, PENAL_GLOBAL)

"""
Questa e' la tua classe, qui tentro puoi fare quasi tutto quello che vuoi.
Io istanziero' questa classe una volta che avro' caricato lo scenario e in attesa dell'inizio 
della simulazione (cioe', prima di far partire gli aerei).
Il concetto e' che io do da mangiare a questa classe (ti passo i pesi iniziali e gli aggiornamenti sul traffico) 
per tenerla allenata e, quando me lo richiede l'utente, io a mia volta chiedero' la predizione chiamando
il metodo "predictionRequested"
"""
class Predictor(object):
        """
        Quando istanzio questa classe, ti passero' un oggetto di tipo Traffic (che contiene i metodi di Dio) e il dizionario
        dei pesi iniziali. Stai attento! Don't fuck with God: tecnicamente puoi chiamare tutti i metodi, in realta' puoi solo
        affidarti a questo metodo
        getTraffic() => ti rende una list di dizionari. Ogni dizionario rappresenta lo stato di uno degli aerei.
        Al momento il dizionario ha le seguenti chiavi
        {'flight_id':'AZA12345', 'started':True/False 'lat':42.0, 'lon':12.2, 'h':300, 'vx':230.3, 'vy':12.4, 'vz':3.4, 'heading':45.0}

        in teoria dovresti richiamare getTraffic() ogni volta che decidi di aggiornare i pesi. Il metodo rende sempre un'info
        aggiornata all'ultimo passo di simulazione. Non puoi avere dati piu freschi. Rende solo le tracce che sono in volo in quel momento
        Quelle arrivate o non ancora partite non compaiono qui, infatti del campo started non te ne fai nulla, perche' sara' sempre
        a True

        se chiami altri metodi potrebbe crashare e in seguito potresti subire un'invasione di locuste
        """
        def __init__(self, traffic, initialWeights):
                self.god = traffic
                self.tracks = {}
                self.weights = {}
                pdb.set_trace()
                cherrypy.log('init', context='CARLO')
                for aID, L in initialWeights.items():
                        self.weights[aID] = np.array([refTrck.w for refTrck in L])
                        self.tracks[aID] = np.array([np.array(refTrck.line) for refTrck in L])
                self.lastSeenTraffic = None
                self.t0 = -1.0
                cherrypy.log('end init', context='CARLO')
                npr.seed()

        def simulationStarted(self, t0):
                self.t0 = t0

        def simulationFinished(self):
                pass

        def trafficUpdated(self, elapsedSeconds):
                """
                Questa funzione viene richiamata ogni progaconstants.PLAYER_SLEEP_SECONDS secondi. al momento e' uguale a 0.5
                Probabilmente non vorrai aggiornare i pesi ogni 0.5 ma puoi decidere tu ogni quanto fare questa operazione,
                basta che ti fai un contatore interno. Se la cosa ti viene molto scomoda possiamo sempre cambiare la dinamica
                e tornare alla chiamata esplicita: decidiamo un tempo, tipo 5 secondi, e ogni 5 secondi ti dico dall'esterno di aggiornare i pesi
                """
                cherrypy.log("asking for traffic at time " + str(elapsedSeconds))
                self.lastSeenTraffic = self.god.getTraffic()
                if int(elapsedSeconds) % WUPDATE_SECONDS == 0:
                        return self.updateWeights() # weights have been updated
                else:
                        return False # weights have not been updated

        def updateWeights(self):
                cherrypy.log('update', context='CARLO')
                for aID, aircraftDict in self.lastSeenTraffic.items():
                    cherrypy.log('update 2', context='CARLO')
                    p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                    v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                    bar = [[a.getNumpyVector()[:2] for a in tt] for tt in self.tracks[aID]]
                    pdb.set_trace()
                    foo = [findWeights(zip(tt[:-1], tt[1:]), p[:2], v[:2]) for tt in bar]
                    nw = np.array([f[1] for f in foo])                    
                    try:
                        self.weights[aID] *= nw # Bayes' rule
                    except KeyError:
                        cherrypy.log("KeyError in accessing weights disctionary.", context='ERROR')
                        return False
                    self.weights[aID] = self.weights[aID]/sum(self.weights[aID]) # Normalization
                    chk_str = "Check weights "+ str(self.weights["GIUS"])
                    cherrypy.log(chk_str, context='CARLO')
                    return True
                    

        def newWeights(self, alpha, dist):
                nw = np.exp(-BETA_POS*dist -BETA_TRK*alpha)
                return nw/sum(nw)

        def angleAndDist(self, aID, p, v):
                """
                To be adjusted
                """
                # Let L be the vector which contains (for each flight intent) a reference to the leg that the aircraft is following
                # compute d, the vector of distances of p from each leg in L
                # compute a, the vector of angles between v and the leg in L
                return (np.ones(len(self.weights[aID])), np.ones(len(self.weights[aID])))
                

        def predictionRequested(self, flight_IDs, deltaT, nsteps, raw):
                """
                Questa e' la funzione che chiamo quando ho bisogno di una predizione. Mentre dalle altre funzioni non mi aspetto
                nulla come valore di ritorno, da questa mi aspetto la famosa matrice. Ho messo tutti gli input che mi ritrovavo,
                fammi sapere se ne mancano o se c'e' qualcosa che non torna.
                """
                #prendi l'ultimo stato del flight_id richiesto da self.lastSeenTraffic
                #manda le palline secondo i tuoi ultimi pesi
                #etc
                self.lastSeenTraffic = self.god.getTraffic()
                self.updateWeights()
                pred = {}
                for aID in flight_IDs:
                    aircraftDict = self.lastSeenTraffic[aID]
                    p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                    v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                    if raw:
                        pred[aID] = self.getParticles(p, v, deltaT, nsteps)
                    else:
                        pred[aID] = self.binParticles(self.getParticles(p, v, deltaT, nsteps), deltaT)
                    
                    cherrypy.log("%s" % (pred.keys()), context="TEST")
                return pred

        def binParticles(self, particlesList, dt, gridbins=GRIDBINS):
            Hlist = {}
            counter = 1
            for L in particlesList:
                H, edges = np.histogramdd(L, bins = gridbins)
                Hlist[counter*dt] = [H/np.sum(H), edges]
                counter += 1
            return Hlist

        def getParticles(self, currP, currV, dt, nsteps):
            L = []
            for j in range(nsteps):
                t = dt*j
                pp = np.empty((NUMPARTICLES, 3))
                for i in range(NUMPARTICLES):
                    pp[i] = currP + currV*t + npr.multivariate_normal(np.zeros(3), np.identity(3)*(50+t*t))
                L.append(pp)
            return L
