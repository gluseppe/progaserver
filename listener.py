#!/usr/bin/env python
import os, os.path
import random
import string
import time
import datetime

import cherrypy
from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import Monitor
from cherrypy import log

import progaconstants



class FSListener(object):
	exposed = True

	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		pass

	def POST(self,length=8):
		pass	

	@cherrypy.tools.json_in()
	def PUT(self):
		state = cherrypy.request.json
		cherrypy.log('received position: '+ str(state['lat']))
		cherrypy.engine.publish(progaconstants.MYSTATE_CHANNEL_NAME,state)
		#lat = state['lat']
		#return lat


	def DELETE(self):
		pass
