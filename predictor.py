from progaconstants import WUPDATE_SECONDS, BETA_POS, BETA_TRK, NUMPARTICLES, GRIDBINS
from progaconstants import ECC, LOCRADIUS, PENAL_GLOBAL, PENAL_ANGLE, PENAL_DIST, BETA_DIST, BETA_ANGLE
from progaconstants import ROTSCALE, ALTSCALE, XYSCALE, FOOT2MT
import cherrypy
import numpy as np
import numpy.random as npr
import pdb


def weightedValues(values, probabilities, size):
    # First using accumulate we create bins.
    # Then we create a bunch of random numbers (between 0, and 1) using random_sample
    # We use digitize to see which bins these numbers fall into.
    # And return the corresponding values.
    bins = np.add.accumulate(probabilities)
    return values[np.digitize(npr.random_sample(size), bins)]

def projection(v, u):
    """
    Projector of v onto the line of u
    """
    return np.dot(u,v)/np.dot(u,u) * u

def norm(v):
    return np.sqrt(np.dot(v,v))

def normL2(x):
    return np.sum(np.abs(x)**2,axis=-1)**(.5)

def legger(track, p):
    """
    Return a list of legs of track that are candidate legs
    according to the 'sausage' model
    """
    L = []
    for i, leg in zip(range(len(track)), track):
        c = .5 * (leg[1] + leg[0])
        a = .5 * norm(leg[1] - leg[0])
        b = a*np.sqrt(1-ECC**2)
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
    if norm(v) < 0.1**9:    
        return(0, 1.)
    if norm(p - track[0][0]) < LOCRADIUS:
        # aircraft lies around the departure airfield
        #cherrypy.log('appena partito', context='FINDWEIGHTS')
        legDirection = track[0][1]-track[0][0]
        legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
        return (0, 1. )
    elif norm(p - track[-1][1]) < LOCRADIUS:
        # aircraft lies around the arrival airfield
        #cherrypy('in arrivo', context='FINDWEIGHTS')
        legDirection = track[-1][1]-track[-1][0]
        legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
        return (len(track)-1, 1. )
    else:
        # aircraft lies in multiple or no sausages
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
                    #cherrypy.log('virata clockwise', context='FINDWEIGHTS')
                    if vcrossu > 0 and vcrossw < 0:
                        #cherrypy.log( 'virata', context='FINDWEIGHTS')
                        vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                             np.dot(v,w)/(norm(w) * norm(v))])
                        if vangles[0] < vangles[1]:
                            return (i, np.exp(- BETA_ANGLE*vangles[0]))
                        else:
                            return (j, np.exp(- BETA_ANGLE*vangles[1]))
                    elif vcrossu > 0 and vcrossw > 0:
                        #cherrypy.log('interno', context='FINDWEIGHTS')
                        return ( j, PENAL_ANGLE )
                    elif vcrossu < 0 and vcrossw < 0:
                    	#cherrypy.log('esterno', context='FINDWEIGHTS')
                        return ( i, PENAL_ANGLE )
                    else:
                        #cherrypy.log( 'opposto', context='FINDWEIGHTS')
                        return (i, PENAL_DIST * PENAL_ANGLE)
                else:
                    #cherrypy.log('virata couterclockwise', context='FINDWEIGHTS')
                    if vcrossu < 0 and vcrossw > 0:
                        #cherrypy.log( 'virata', context='FINDWEIGHTS')
                        vangles = np.arccos([np.dot(v,u)/(norm(u) * norm(v)),
                                             np.dot(v,w)/(norm(w) * norm(v))])
                        if vangles[0] < vangles[1]:
                            return (i, np.exp(- BETA_ANGLE*vangles[0]))
                        else:
                            return (j, np.exp(- BETA_ANGLE*vangles[1]))
                    elif vcrossu < 0 and vcrossw < 0:
                        #cherrypy.log('interno', context='FINDWEIGHTS')
                        return ( j, PENAL_ANGLE) 
                    elif vcrossu > 0 and vcrossw > 0:
                        #cherrypy.log('esterno', context='FINDWEIGHTS')
                        return ( i, PENAL_ANGLE) 
                    else:
                        #cherrypy.log('opposto', context='FINDWEIGHTS')
                        return (i, PENAL_DIST * PENAL_ANGLE)
        else:
        	if len(candidateLegs) == 1:
                # aircraft lies in only one sausage
        		#cherrypy.log('in-leg %d' % (candidateLegs[0]), context='FINDWEIGHTS')
        		leg = track[candidateLegs[0]]
        		legDirection = leg[1]-leg[0]
        		distanceFromLeg = norm(p - leg[0] - projection(p-leg[0], legDirection))
        		legTrackAngle = np.arccos( np.dot(v, legDirection)/(norm(v) * norm(legDirection)) )
        		return (candidateLegs[0], np.exp( - BETA_DIST*distanceFromLeg - BETA_ANGLE*legTrackAngle ))
        	else:
        		#cherrypy.log('no match found', context='FINDWEIGHTS')
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
                #pdb.set_trace()
                self.god = traffic
                self.tracks = {}
                self.weights = {}
                self.tracksID = {}
                self.legs = {}
                for aID, L in initialWeights.items():
                        self.weights[aID] = np.array([refTrck.w for refTrck in L])
                        self.tracks[aID] = np.array([np.array(refTrck.line) for refTrck in L])
                        self.tracksID[aID] = [refTrck.refTrackID for refTrck in L]
                        #cherrypy.log('%s' % (self.tracksID[aID]), context='CARLO') 
                        # questo messaggio di log mostra if flight_intent_IDs noti al sistema per ogni aircraft_ID
                        self.legs[aID] = None
                        

                self.lastSeenTraffic = None
                self.t0 = -1.0
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
                #cherrypy.log("asking for traffic at time " + str(elapsedSeconds))
                self.lastSeenTraffic = self.god.getTraffic()
                if int(elapsedSeconds) % WUPDATE_SECONDS == 0:
                        return self.updateWeights() # weights have been updated
                else:
                        return False # weights have not been updated

        def updateWeights(self):
                #cherrypy.log('update', context='CARLO')
                for aID, aircraftDict in self.lastSeenTraffic.items():
                    p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                    v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                    bar = [[a.getNumpyVector()[:2] for a in tt] for tt in self.tracks[aID]]
                    foo = [findWeights(zip(tt[:-1], tt[1:]), p[:2], v[:2]) for tt in bar]
                    nw = np.array([f[1] for f in foo])                    
                    try:
                        self.weights[aID] *= nw # Bayes' rule
                    except KeyError:
                        cherrypy.log("KeyError in accessing weights disctionary.", context='ERROR')
                        return False
                    self.weights[aID] = self.weights[aID]/sum(self.weights[aID]) # Normalization
                    #chk_str = "Check weights "+ str(self.weights["GIUS"])
                    #cherrypy.log(chk_str, context='CARLO')
                    self.legs[aID] = np.array([f[0] for f in foo])
                    #cherrypy.log("updated weights: %s"%(self.weights[aID]),context="PREDTEST")
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
                    #cherrypy.log("lat:%.4f lon:%.4f"%(aircraftDict['lat'],aircraftDict['lon']),context="PREDTEST")
                    #cherrypy.log("x:%.4f y:%.4f"%(aircraftDict['x'],aircraftDict['y']),context="PREDTEST")
                    #cherrypy.log("vx:%.4f vy:%.4f"%(aircraftDict['vx'],aircraftDict['vy']),context="PREDTEST")
                    p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                    v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                    if raw:
                        #pdb.set_trace()
                        pred[aID] = self.getParticles(p, v, NUMPARTICLES, deltaT, nsteps, aID)
                    else:
                        pred[aID] = self.binParticles(self.getParticles(p, v, NUMPARTICLES, deltaT, nsteps, aID), deltaT)
                    
                    #pdb.set_trace()

                    #cherrypy.log("%s" %(pred[aID][0]), context="PREDTEST")
                return pred

        def binParticles(self, particleList, dt, gridbins=GRIDBINS):
            Hlist = {}
            counter = 1
            for L in particleList[0].values():
                H, edges = np.histogramdd(L, bins = gridbins)
                Hlist[counter*dt] = [H/np.sum(H), edges]
                counter += 1
            return [Hlist, particleList[1]]
            # ritorna una tupla:
            # Hlist e' un dizionario le cui chiavi sono i tempi di preidizione e i valori sono coppie (matrice di frequenze e edges)
            # il secondo elemento, ovvero particleTuple[1], e' una lista dei reference track IDs usati nella predizione

        def getParticles(self, currP, currV, numParticles, dt, nsteps, aircraft_ID):
            #pdb.set_trace()
            L = {}
            pparticles = bunchOfParticles(currP, currV, numParticles, dt, self.tracks[aircraft_ID], self.weights[aircraft_ID], self.legs[aircraft_ID])
            #usedIDs = [self.tracksID[i] for i in pparticles.tracksUsed]
            usedIDs = [self.tracksID[aircraft_ID][i] for i in pparticles.tracksUsed]
            #pdb.set_trace()

            for j in range(1,nsteps+1):
                pparticles.takeAmove()
                copyPositions = np.array(pparticles.positions)
                for q in copyPositions:
                    q[2] /= FOOT2MT
                L[j*dt] = copyPositions
            return [L, usedIDs]
            # ritorna una tupla:
            # L e' un dizionario le cui chiavi sono i tempi di preidizione e i valori sono liste di posizioni 3D 
            # il secondo elemento, ovvero usedIDs, e' una lista dei reference track IDs usati nella predizione

#############################################################################################################

class bunchOfParticles(object):
    def __init__(self, p, v, size, dt, referenceTracks, weights, legs):
        """
        referenceTracks deve essere passato come predictor.tracks[aircraft_ID]
        """
        self.dt = dt
        self.numPart = size
        self.positions = np.tile(p, size).reshape( (size,3) )
        if abs(v[2]) < 0.2:
            v[2] = 0
        self.velocities = np.tile(v, size).reshape( (size,3) )
        bar = [[a.getNumpyVector()[:2] for a in tt] for tt in referenceTracks]
        # foo = [findWeights(zip(tt[:-1], tt[1:]), p[:2], v[:2]) for tt in bar]
        self.tracks = [zip(tt[:-1], tt[1:]) for tt in bar] # self.tracks[i] contiene la traccia i-esima 
        # tLegs = np.array([f[0] for f in foo]) # tLegs[i] contiene il leg di riferimento della traccia i-esima
        # tWeights = np.array([f[1] for f in foo]) # tWeights[i] contiene il leg di riferimento della traccia i-esima
        # tWeights /= sum(tWeights)
        sampledTracks = weightedValues(np.arange(len(referenceTracks)), weights, self.numPart)
        self.partReference = np.vstack( (sampledTracks, [legs[i] for i in sampledTracks]) )
        # self.partReference[0,j] = indice della traccia di riferimento della particella j-esima
        # self.partReference[1,j] = indice del leg di riferimento della particella j-esima
        self.tracksUsed = np.unique(sampledTracks)
        
    def takeAmove(self):
        simulTimes = self.simulationTime(self.dt)
        # randomly rotate velocities
        for i, alpha in zip(range(self.numPart), self.alphaToNextTurnPoint()):
            angle = np.random.normal(loc=alpha, scale=ROTSCALE)
            rrot = rotation(angle)
            self.velocities[i] = rrot(self.velocities[i])
        #
        self.velocities[:, :2] *= 1. + np.random.normal(scale=XYSCALE, size=self.numPart).reshape((self.numPart,1))
        self.velocities[:, 2] += np.random.normal(scale=ALTSCALE, size=self.numPart)
        self.positions = self.positions + np.dot(np.diag(simulTimes[0]), self.velocities)
        indices = simulTimes[1].nonzero()[0]
        curLeg = self.getLeg(indices)
        self.setNextLeg(indices)
        nextLeg = self.getLeg(indices)
        uu = [(leg[1] - leg[0])[:2]/norm((leg[1] - leg[0])[:2]) for leg in curLeg]
        vv = [(leg[1] - leg[0])[:2]/norm((leg[1] - leg[0])[:2]) for leg in nextLeg]
        alphasin = [u[0]*v[1] - u[1]*v[0] for u, v in zip(uu, vv)]
        alphacos = [np.dot(u,v) for u, v in zip(uu, vv)]
        for i in range(len(indices)):
            rrot = rotation( np.arctan2(alphasin[i], alphacos[i]) )
            self.velocities[i, :] = rrot(self.velocities[i, :])
        # rotate velocity for particle-index in simulTimes[1].nonzero()
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
        uu = [(leg[1] - leg[0])[:2]/norm((leg[1] - leg[0])[:2]) for leg in self.getLeg(np.arange(self.numPart)) ]
        #pdb.set_trace()
        vv = [self.velocities[i,:2]/norm(self.velocities[i,:2]) for i in range(self.numPart)]
        #cherrypy.log("uu0:%s vv0:%s"%(uu[0],vv[0]),context="PREDTEST")
        alphasin = [v[0]*u[1] - v[1]*u[0] for u, v in zip(uu, vv)]
        alphacos = [np.dot(u,v) for u, v in zip(uu, vv)]
        return np.arctan2(alphasin, alphacos)

    def simulationTime(self, dt):
        timesToNextTP = self.timeToNextTurnPoint()
        dtVec = dt * np.ones( self.numPart )
        tau = np.minimum(timesToNextTP,  dtVec)
        return (tau, dtVec-tau)
