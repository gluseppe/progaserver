import progaconstants
import simplejson as json
from referencetrack import Point3D, ReferenceTrack
import pdb
import cherrypy



"""
The ReferenceTracksHandler provides the information about the stored intents i.e. reference tracks.
It abstracts from the way this information is stored. For the moment reference tracks are stored inside
a json file. they should be in a geographic database, ideally we would use neo4j spatial
"""
class ReferenceTracksHandler(object):


	def __init__(self, scenario_name):
		allfile = ""
		complete_path = "./db/repository_uncertainty_l1.json"
		#cherrypy.log("scenario name: %s"%(scenario_name))
		if scenario_name == "sc_4_uncertainty_l1":
			#cherrypy.log("loading repository for uncertainty l1", context="UNCERTAINTY")
			complete_path = "./db/repository_uncertainty_l1.json"


		if scenario_name == "sc_4_uncertainty_l2":
			#cherrypy.log("loading repository for uncertainty l2", context="UNCERTAINTY")
			complete_path = "./db/repository_uncertainty_l2.json"


		if scenario_name == "sc_4_uncertainty_l3":
			#cherrypy.log("loading repository for uncertainty l3", context="UNCERTAINTY")
			complete_path = "./db/repository_uncertainty_l3.json"

		if (scenario_name == "sc_1_turns") or (scenario_name == "sc_1_turns_bln"):
			#cherrypy.log("loading repository for sc_1_turns", context="phd")
			complete_path = "./db/repository_sc_1_turns.json"

		if (scenario_name == "sc_2_lfoe") or (scenario_name == "sc_2_lfoe_bln"):
			#cherrypy.log("loading repository for sc_1_turns", context="phd")
			complete_path = "./db/repository_sc_2_lfoe.json"	


		#cherrypy.log("loading complete path %s"%(complete_path), context="UNCERTAINTY")


		with open(complete_path) as referencetracksfile:
			for line in referencetracksfile:
				allfile += line

		print allfile
		
		self.jsonobj = json.loads(allfile)


	"""
	Provides all the stored intents and assign them a flight_id which is the given one as parameter
	"""
	def getAllIntents(self, track_id):		
		ret = []
		reference_tracks = self.jsonobj['reference_tracks']
		for rt in reference_tracks:
			rt_id = rt['reference_track_id']
			points =  rt['turning_points']
			p_list = []
			for p in points:
				p_list.append(Point3D(p['lon'],p['lat'],p['h']))

			refTrack = ReferenceTrack(p_list,track_id)
			#pdb.set_trace()
			refTrack.refTrackID = rt_id
			ret.append(refTrack)

		return ret

	def getReferenceTrack(self, referenceTrackID):

		reference_tracks = self.jsonobj['reference_tracks']
		ret = None
		flight_intent_point_list = []
		for rt in reference_tracks:
			if rt['reference_track_id']==referenceTrackID:
				turning_points = rt['turning_points']
				for item in turning_points:
					flight_intent_point_list.append(Point3D(item['lon'],item['lat'],item['h']))
				ret = ReferenceTrack(flight_intent_point_list)

		return ret
		

