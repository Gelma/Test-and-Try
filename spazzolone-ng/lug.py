#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2010-2011 Andrea Gelmini <andrea.gelmini@gelma.net>
Copyright (C) 2011  necro@circolab.net

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

import persistent
import config
import time

class LUG(persistent.Persistent):
	def __init__(self, name):
		self.name = name
		self.url = str()
		self.dns = set()
		self.data = set()
		self.hfield = dict()
		self.data_magnum = float(1.0)
		self.hfield_magnum = float(1.0)

		
		self.messages = None
		self.error_num = 0
		self.passage = 0
		self.errors = dict()

	def update_data(self, d_data):
		self.passage += 1
		self.messages = list()
		self.error_num = 0
		url = d_data['url']
		dns = d_data['dns']
		data = d_data['data']
		hfield = d_data['hfield']

		if dns == "ERROR":
			self.notify("E: Error DNS resolving")
			self.set_error("DNS",1)
		else:
			if dns.issubset(self.dns) == False:
				for x in dns.difference(self.dns):
					self.notify("U: DNS %s added" % x)
				self.dns = dns.union(self.dns)
			self.set_error("DNS",0)

			if hfield == "ERROR":
				self.notify("E: Error fetching header")
				self.set_error("HTTP_HEADER",1)
			else:
				if self.hfield == dict():
					self.hfield = hfield	
					self.notify("I: header initialized")

				elif self.hfield != hfield:
					set_sh=set(self.hfield.items())
					set_h=set(hfield.items())
					self.hfield_magnum = 1 - float(len(set_h & set_sh))/float(len(set_h|set_sh))
					self.hfield = hfield	
					if self.hfield_magnum >= config.L_MN_HEADER:
						self.notify("U: deviation from old header %s" % self.hfield_magnum)
				self.set_error("HTTP_HEADER",0)
				

			if data == "ERROR":
				self.notify("E: Error fetching data")
				self.set_error("HTTP_DATA",1)
			else:
				if self.data == set():
					self.data = data
					self.notify("I: data initialized")
				elif self.data != data:
					self.data_magnum = 1 - float(len(data & self.data))/float(len(data | self.data))
					self.data = data
					if self.data_magnum >= config.L_MN_DATA:
						self.notify("U: deviation from old homepage %s" % self.data_magnum)
				self.set_error("HTTP_DATA",0)

		#self.notify("D: passage %s" % self.passage)

	def set_error(self, e_type, state):
		if state == 0:
			if e_type in self.errors:
				del self.errors[e_type]
		elif state == 1:
			if e_type in self.errors:
				self.notify("  E: error present since %s (UTC)" % time.asctime(time.gmtime(self.errors[e_type])))
			else:
				self.errors[e_type] = time.time()
		return 0

	def notify(self, text):
		self.error_num += 1
		self.messages.append(text)
