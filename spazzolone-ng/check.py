#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2011  necro <necro@circolab.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import httplib2
import socket
import urlparse
import time
import config
socket.setdefaulttimeout(config.S_TIMEOUT)


def fetch_site(name, url_r):
	data = dict()
	h = httplib2.Http(cache=None,timeout=config.S_TIMEOUT)
	h.follow_all_redirects=True

	data['name'] = name
	if url_r.find("http://") is not 0 and url_r.find("https://") is not 0:
		url_r = "http://" + url_r
	url_p = urlparse.urlparse(url_r)
	data['url'] = url_p.netloc
	try:
		data['dns'] =  set(IP[4][0] for IP in socket.getaddrinfo(url_p.netloc, 80, 0, 0, socket.SOL_TCP))
	except:
		data['dns'] = "ERROR"
	if data['dns'] is not "ERROR":
		try:
			try:
				resp, page = h.request(url_r, method="GET", headers={"User-Agent":config.H_USER_AGENT})
			except:
				resp, page = h.request(url_r, method="GET", headers={"User-Agent":config.H_USER_AGENT,"Accept-Encoding":""})
			data['data'] = set(page.split())
			data['hfield'] = resp
		except:
			data['data'] = "ERROR"
			data['hfield'] = "ERROR"
	else:
		data['data'] = "ERROR"
		data['hfield'] = "ERROR"

	return data

def mp_fill_lug(q1,q2):
	lug_info = q1.get()
	while lug_info != "DIE":	 
		time_init = time.time()
		try:
			t = fetch_site(lug_info[1], lug_info[3])
			time_end = time.time()
			time_ite = time_end - time_init
			t['metadata'] = dict()
			t['metadata']['time'] = time_ite
			q2.put(t,False)
		except:
			print("%s" % lug_info)
			q2.put("ERROR",False)

		lug_info = q1.get()
		continue

	del q1,q2
	return 0
