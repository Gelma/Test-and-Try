#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
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

from utils import read_db, zodb_conn_open, zodb_conn_close, logit, lug_report
from multiprocessing import Process, Queue
from check import fetch_site, mp_fill_lug
import multiprocessing
import time
import config
import lug


#### VARIABLES

lug_db = dict()

### Queues
## lug_db_q	- is the queue where I put the info read from the db
##		  of the lugs
## lug_data_q	- is the queue where I put the result of my process
##		  fetching data
lug_db_q = Queue()
lug_data_q = Queue()

### Counter
## num_elem	- is the number of lug read from the db
## num_read	- is the number of result read the the lug_data_q
num_elem = 0
num_read = 0

## Database in ZODB
db, zodb = zodb_conn_open(config.ZODB_DB)

lug_db = read_db()

for row in lug_db.values():
	lug_db_q.put(row)
	num_elem = num_elem + 1

for num in range(config.P_NUMBER):
	lug_db_q.put('DIE')

## Start P_NUMBER process to fetch data
proc_list = list()
for num in range(config.P_NUMBER):
	proc_list.append(Process(target=mp_fill_lug, name=num, args=(lug_db_q, lug_data_q,)))
	proc_list[-1].start()


while num_read != num_elem:
	num_read = num_read+1
	read = lug_data_q.get()
	if read is not "ERROR" :
		name = read['name']
		url = read['url']
		if name not in zodb:
			zodb[name] = lug.LUG(name)
		zodb[name].update_data(read)
		if zodb[name].messages != [] :
			print("%s#%s:%s - %s" % (num_read,num_elem,name,url))
			lug_report(lug_db[name],zodb[name].messages)
		#for mesg in zodb[name].messages: print(mesg)
	time.sleep(0.1)

for num in range(config.P_NUMBER):
	proc_list[num].join(0.1)

zodb_conn_close(db)

