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
from automator import Automator

from traffic import Traffic
from prediction import PredictionEngine
from listener import FSListener
from hotspots import HotSpotter

from cherrypy import log
import sys

class ProGA(object):

	def __init__(self):
		cherrypy.log("Starting ProGA server", context='AUTO')

	@cherrypy.expose
	def index(self):
		return 'Hello, this is the proga prototype'


def str2bool(str):
	return v.lower() in ("yes", "true", "t", "1")


if __name__ == '__main__':

	args = sys.argv




	proga_conf = {
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd()),
			#'tools.staticdir.dir': './',
			#'tools.staticdir.on': True,
			#'log.access_file' : "access.log",
			#'log.error_file' : "error.log",
			#'log.screen' : False
		},
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

	hotspots_conf = {
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

	auto_conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers' : [('Content-Type','text/plain')]
		}
	}

    
	cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': progaconstants.LISTEN_PORT,
                            'log.screen': False,
                            'log.access_file': './access.log',
                            'log.error_file': './proga.log'})
        
	traffic = Traffic(cherrypy.engine,progaconstants.PLAYER_SLEEP_SECONDS)
	predictionEngine = PredictionEngine(cherrypy.engine,progaconstants.PREDICTION_SLEEP_SECONDS, traffic)
	hotspots = HotSpotter(cherrypy.engine,progaconstants.HOTSPOTS_SLEEP_SECONDS)


	cherrypy.tree.mount(ProGA(), '/', proga_conf)
	cherrypy.tree.mount(FSListener(), '/listener', listener_conf)
	cherrypy.tree.mount(traffic, '/traffic', traffic_conf)
	cherrypy.tree.mount(predictionEngine, '/prediction', traffic_conf)
	cherrypy.tree.mount(hotspots, '/hotspots', hotspots_conf)


	automator = None
	if len(args)==2:
		#auto = args[1]
		
		scenario = args[1]
		automator = Automator(cherrypy.engine, scenario,None,progaconstants.PLAYER_SLEEP_SECONDS)
	elif len(args)==3:
		scenario = args[1]
		selfTrack = args[2]
		automator = Automator(cherrypy.engine, scenario, selfTrack,progaconstants.PLAYER_SLEEP_SECONDS)


	cherrypy.tree.mount(automator,'/automator',auto_conf)
	
	cherrypy.engine.start()
	cherrypy.engine.publish(progaconstants.PROGA_IS_READY_CHANNEL_NAME)
	cherrypy.engine.block()


	







