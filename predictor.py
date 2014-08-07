import progaconstants
import cherrypy


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
		self.weights = initialWeights
		self.lastSeenTraffic = None
		self.t0 = -1.0




	def simulationStarted(self, t0):
		self.t0 = t0

	def simulationFinished(self):
		pass

	
	"""
	Questa funzione viene richiamata ogni progaconstants.PLAYER_SLEEP_SECONDS secondi. al momento e' uguale a 0.5
	Probabilmente non vorrai aggiornare i pesi ogni 0.5 ma puoi decidere tu ogni quanto fare questa operazione, 
	basta che ti fai un contatore interno. Se la cosa ti viene molto scomoda possiamo sempre cambiare la dinamica
	e tornare alla chiamata esplicita: decidiamo un tempo, tipo 5 secondi, e ogni 5 secondi ti dico dall'esterno di aggiornare i pesi
	"""
	def trafficUpdated(self, elapsedSeconds):

		cherrypy.log("asking for traffic at time " + str(elapsedSeconds))
		self.lastSeenTraffic = self.god.getTraffic()

		"""
		Qui potrebbe esserci qualcosa del 
		self.lastSeenTraffic = self.god.getTraffic()
		if hoDecisoDiAggiornareIPesi():
			self.weights = self.aggiornoPesi(self.lastSeenTraffic)
		else:
			grattata di pancia
			
		"""
		#pass


	"""
	Questa e' la funzione che chiamo quando ho bisogno di una predizione. Mentre dalle altre funzioni non mi aspetto
	nulla come valore di ritorno, da questa mi aspetto la famosa matrice. Ho messo tutti gli input che mi ritrovavo,
	fammi sapere se ne mancano o se c'e' qualcosa che non torna.
	"""
	def predictionRequested(self, flight_id, timehorizon, dt):
		#prendi l'ultimo stato del flight_id richiesto da self.lastSeenTraffic
		#manda le palline secondo i tuoi ultimi pesi
		#etc
		pass


