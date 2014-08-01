#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime

import cherrypy
import simplejson as json
import progaconstants
from track import Track
from collections import defaultdict


class Scenario(object):

	def __init__(self, tracks):
		self.tracks = tracks
		cherrypy.log("Sono dentro scenario e ho " + str(len(self.tracks)) + "tracce")

	def getStartingTimes(self):
		times = {}
		for track in self.tracks:
			times[track.flight_id] = track.getStartTime()

		return times


	def getTracks(self):
		return self.tracks


	def getTracksToStart(self):
		toStart = defaultdict(list)
		for track in self.tracks:
			toStart[track.getStartTime].append(track)

		cherrypy.log()


		return toStart