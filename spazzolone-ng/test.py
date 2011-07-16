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

import lug
import config
import time
import utils
from check import fetch_site

db, zodb = utils.zodb_conn_open("/tmp/zodb_test")

name="ansa"
url="http://www.ansa.it"

b = fetch_site(name,url)
if not zodb.has_key(name):
	zodb[name] = lug.LUG(name) 

zodb[name].update_data(b)
for mesg in zodb[name].messages: print(mesg)
utils.zodb_conn_close(db)
