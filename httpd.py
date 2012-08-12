#!/usr/bin/env python

# Simple test server.

# Prereqs: apt-get install libev4 libev-dev
#          easy_install fapws3

import fapws._evwsgi as evwsgi
from fapws import base

from fapws.contrib import views

def start():
	evwsgi.start('0.0.0.0', '8080') 
	evwsgi.set_base_module(base)

	def proxy(baseurl):
		def f(environ, start_response):
			try:
				import urllib2
				resp = urllib2.urlopen(baseurl + environ["PATH_INFO"] + ("?" + environ["QUERY_STRING"] if environ["QUERY_STRING"] != "" else ""))
				if resp.code == 200:
					start_response('200 OK', [('Content-Type', resp.info().gettype())])
					return [resp.read()]
			except:
				start_response('403 ERROR', [('Content-Type', 'text/plain')])
				return ['Error loading request.']
		return f

	evwsgi.wsgi_cb(('/boundaries/', proxy("http://gis.govtrack.us/boundaries/")))
	evwsgi.wsgi_cb(('/map/tiles/', proxy("http://gis.govtrack.us/map/tiles/")))
	evwsgi.wsgi_cb(('/static/rep_photos/', proxy("http://www.govtrack.us/data/photos/")))
	
	staticfile = views.Staticfile('static', maxage=2629000)
	evwsgi.wsgi_cb(('/static', staticfile))

	staticfile = views.Staticfile('your_new_district.html', maxage=2629000)
	evwsgi.wsgi_cb(('/', staticfile))

	evwsgi.set_debug(0)	   
	evwsgi.run()
 
if __name__ == '__main__':
	start()
