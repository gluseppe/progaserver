#!/usr/bin/env python
import requests
import sys

if __name__ == '__main__':

	args = sys.argv

	flight_id = args[1]
	dt = int(args[2])
	steps = int(args[3])
	raw = args[4]


	s = requests.Session()
	print raw
	r = s.get('http://127.0.0.1:8080/prediction', params={'flight_id':flight_id,'deltaT':dt,'nsteps':steps,'raw':raw})
	print r.text


