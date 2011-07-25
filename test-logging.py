import sys, logging, StringIO
import logging.handlers

filememory = StringIO.StringIO('ciao')

class mio:
	def __init__(self):
		self.righe = []
	def write(self, riga):
		self.righe.append(riga)
	def flush(self):
		return True

filememory = mio()

print "logger"
logger = logging.getLogger("mechanize.http_redirects")
handler = logging.StreamHandler(filememory)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

print "mechanize"
import mechanize
b=mechanize.Browser()
b.set_debug_redirects(True)
b.open('http://lugman.net')

handler.flush()
print "fine"

print filememory.righe
