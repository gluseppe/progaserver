#!/usr/bin/env python
import requests
import sys

if __name__ == '__main__':

	#args = sys.argv

	#flight_id = args[1]
	#dt = int(args[2])
	#steps = int(args[3])
	#raw = args[4]
	item = "traffic4mfs"


	s = requests.Session()
	#print raw
	r = s.get('http://127.0.0.1:8080/traffic', params={'item':item})
	print r.text