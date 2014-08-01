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

from traffic import Traffic
from prediction import PredictionEngine
from listener import FSListener


class ProGA(object):

	def __init__(self):
		cherrypy.log("Starting ProGA server")

	@cherrypy.expose
	def index(self):
		return 'Hello, this is the proga prototype'



if __name__ == '__main__':
	proga_conf = {
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd())
		}
	}


	listener_conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers' : [('Content-Type','text/plain')]
		}
	}

	prediction_conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers' : [('Content-Type','text/plain')]
		}
	}

	traffic_conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers' : [('Content-Type','text/plain')]
		}
	}


	cherrypy.tree.mount(ProGA(), '/', proga_conf)
	cherrypy.tree.mount(FSListener(), '/listener', listener_conf)
	cherrypy.tree.mount(Traffic(cherrypy.engine,progaconstants.PLAYER_SLEEP_SECONDS), '/traffic', traffic_conf)
	cherrypy.tree.mount(PredictionEngine(cherrypy.engine,progaconstants.PREDICTION_SLEEP_SECONDS), '/prediction', traffic_conf)

	cherrypy.config.update({'server.socket_host': '0.0.0.0',
		'server.socket_port': progaconstants.LISTEN_PORT})


	cherrypy.engine.start()
	cherrypy.engine.block()






