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

import os
import glob
import csv
import syslog
import config


def read_db():
	lug_dict = dict()
	for filedb in glob.iglob(config.LUG_DB+'*.txt'):
		for row in csv.reader(open(filedb, "r"), delimiter='|', quoting=csv.QUOTE_NONE):
			#print(filedb)
			lug_name = row[1]

			if lug_dict.has_key(lug_name):
				print("%s already present" % lug_name)
				continue
			lug_dict[lug_name] = row
	return lug_dict


def logit(*args):
	try:
		log_line += ' '.join(args)
	except:
		log_line = ''
		for item in args:
			log_line+= ' %s' % item
	syslog.syslog(syslog.LOG_INFO, log_line)

def zodb_conn_open(path):
	from ZODB.FileStorage import FileStorage
	from ZODB.DB import DB
	storage = FileStorage(path)
	db = DB(storage)
	connection = db.open()
	zodb = connection.root()
	return db,zodb

def zodb_conn_close(db):
	import transaction
	transaction.commit()
	db.close()
	return 0

def lug_report(db_entry, messages):
	prov = db_entry[0]
	name = db_entry[1]
	zone = db_entry[2]
	url = db_entry[3]
	email = db_entry[4]
	print("## %s BEGIN REPORT ##" % name)
	print("- LUG DATA ---")
	print("name: %s" % name)
	print("url: %s" % url)
	print("zone: %s" % zone)
	print("province: %s" % prov)
	print("email contact: %s" % email)
	print("- ERROR DATA -")
	for msg in messages:
		print(msg)
	print("## %s END REPORT ##" % name)


def send_report(body):
	return 0
