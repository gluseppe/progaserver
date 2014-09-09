from progaconstants import WUPDATE_SECONDS, BETA_POS, BETA_TRK, NUMPARTICLES, GRIDBINS
import cherrypy
import numpy as np
import numpy.random as npr


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
                self.tracks = initialWeights
                self.weights = {}
                for aircraft_id, L in self.tracks.items():
                        self.weights[aircraft_id] = np.array([refTrck.w for refTrck in L])
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
                cherrypy.log("asking for traffic at time " + str(elapsedSeconds))
                self.lastSeenTraffic = self.god.getTraffic()
                if int(elapsedSeconds) % WUPDATE_SECONDS == 0:
                        return self.updateWeights() # weights have been updated
                else:
                        return False # weights have not been updated

        def updateWeights(self):
                ## pass
                for aircraftDict in self.lastSeenTraffic:
                    aID = aircraftDict['flight_id']
                    p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                    v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                    a, d = self.angleAndDist(aID, p, v)
                    nw = self.newWeights(a, d) # Gibbsian weights
                    try:
                        self.weights[aID] *= nw # Bayes' rule
                    except KeyError:
                        cherrypy.log("KeyError in accessing weights disctionary.", context='ERROR')
                        return False
                    self.weights[aID] = self.weights[aID]/sum(self.weights[aID]) # Normalization
                    chk_str = "Check weights "+ str(self.weights["DAMIANO345"])
                    cherrypy.log(chk_str, context='DEBUG')
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
                

        def predictionRequested(self, flight_IDs, deltaT, nsteps):
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
                for aircraftDict in self.lastSeenTraffic:
                    aID = aircraftDict['flight_id']
                    if aID in flight_IDs:
                        p = np.array([aircraftDict['x'], aircraftDict['y'], aircraftDict['z']])
                        v = np.array([aircraftDict['vx'], aircraftDict['vy'], aircraftDict['vz']])
                        pred[aID] = self.binParticles(self.getParticles(p, v, deltaT, nsteps), deltaT)
                        cherrypy.log("%s" % (pred.keys()), context="TEST")
                return pred

        def binParticles(self, particlesList, dt, gridbins=GRIDBINS):
            Hlist = {}
            counter = 1
            for L in particlesList:
                H, edges = np.histogramdd(L, bins = gridbins)
                Hlist[counter*dt] = (H/np.sum(H), edges)
                counter += 1
            return Hlist

        def getParticles(self, currP, currV, dt, nsteps):
            L = []
            for j in range(nsteps):
                t = dt*j
                pp = np.empty((NUMPARTICLES, 3))
                for i in range(NUMPARTICLES):
                    pp[i] = currP + currV*t + npr.multivariate_normal(np.zeros(3), np.identity(3))
                L.append(pp)
            return L
