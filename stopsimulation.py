#!/usr/bin/env python
import requests
s = requests.Session()
r = s.post('http://127.0.0.1:8080/traffic', params={'command':'stop'})

