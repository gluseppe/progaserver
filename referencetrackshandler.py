import progaconstants
import simplejson as json
from referencetrack import Point3D, ReferenceTrack



"""
The ReferenceTracksHandler provides the information about the stored intents i.e. reference tracks.
It abstracts from the way this information is stored. For the moment reference tracks are stored inside
a json file. they should be in a geographic database, ideally we would use neo4j spatial
"""
class ReferenceTracksHandler(object):


	def __init__(self):
		allfile = ""
		complete_path = "./db/referencetrackrepository_manzato.json"
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

			r = ReferenceTrack(p_list,track_id)
			r.id = rt_id
			ret.append(r)

		return ret

	def getReferenceTrack(self, referenceTrackID):

		reference_tracks = self.jsonobj['reference_tracks']
		ret = None
		flight_intent_point_list = []
		for rt in reference_tracks:
			if rt['reference_track_id']==referenceTrackID:
				turning_points = rt['turning_points']
				for item in turning_points:
					flight_intent_point_list.append(Point3D(item['lat'],item['lon'],item['h']))
				ret = ReferenceTrack(flight_intent_point_list)

		return ret
		

