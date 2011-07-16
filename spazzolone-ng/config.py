#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Number of process launched for fetching data
P_NUMBER = 4
## Socket timeout
S_TIMEOUT = 20
## Where the ZoDB will be saved
ZODB_DB = "/tmp/spazzino"
## The directory where is the db of the lug
LUG_DB = "./db/"
## Magic number threshold before notify of changes
L_MN_HEADER = 0.8
L_MN_DATA = 0.4
## User Agent
H_USER_AGENT = "Bot: spazzolone/ng - http://lugmap.linux.it - lugmap@linux.it"

### Report section
## From who the report should be send 
R_FROM = ""
## To who the reprt should be send
R_TO = ""
## The subject of the report
R_SUBJECT = ""
