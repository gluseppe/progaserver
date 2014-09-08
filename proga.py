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

from cherrypy import log


class ProGA(object):

	def __init__(self):
		#mylogger = logging.getLogger('ProGA')
		cherrypy.log("Starting ProGA server")
		log.error(msg='This is ProGA logger. ', context='DEBUG')

	@cherrypy.expose
	def index(self):
		return 'Hello, this is the proga prototype'



if __name__ == '__main__':
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

	traffic_conf = {
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
                            'log.error_file': './error.log'})
        
	traffic = Traffic(cherrypy.engine,progaconstants.PLAYER_SLEEP_SECONDS)
	predictionEngine = PredictionEngine(cherrypy.engine,progaconstants.PREDICTION_SLEEP_SECONDS, traffic)


	cherrypy.tree.mount(ProGA(), '/', proga_conf)
	cherrypy.tree.mount(FSListener(), '/listener', listener_conf)
	cherrypy.tree.mount(traffic, '/traffic', traffic_conf)
	cherrypy.tree.mount(predictionEngine, '/prediction', traffic_conf)
	
	cherrypy.engine.start()
	cherrypy.engine.block()






