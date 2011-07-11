#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Per ogni Lug indicato nella LugMap effettuo un insieme di controlli di validità.
   Se qualcosa non torna, avverto chi di dovere.

   Copyright 2010-2011 - Andrea Gelmini (andrea.gelmini@gelma.net)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>."""

if True: # import dei moduli
	import sys
	if sys.version_info < (2,6):
		sys.exit("Necessito di un interprete Python dalla versione 2.6 in poi")

	try:
		import csv, datetime, glob, multiprocessing, os, socket, sys, smtplib, syslog, time
	except:
		sys.exit("Non sono disponibili tutti i moduli standard necessari")

	try:
		import ZODB, persistent, transaction
	except:
		sys.exit("Installa ZODB3: 'easy_install zodb3' oppyre 'apt-get install python-zodb'")

	try:
		import mechanize
	except:
		sys.exit("Installa mechanize: 'easy_install mechanize' oppure 'apt-get install python-mechanize'")


def logga(*args):
	"""Ricevo un testo o un array e lo butto nei log di sistema"""

	try:
		linea_log += ' '.join(args)
	except: # desumo che siano presenti argomenti non testuali
		linea_log = ''
		for item in args:
			linea_log += ' %s' % item

	syslog.syslog(syslog.LOG_INFO, linea_log)

logga('avviato')

try: # attiva DB
	from ZODB.FileStorage import FileStorage
	from ZODB.DB import DB
	storage = FileStorage(os.path.join(os.environ["HOME"], '.spazzino.db'))
	db = DB(storage)
	connection = db.open()
	zodb = connection.root()
except:
	logga('Problema sul DB')
	sys.exit('Problema sul DB')

if True: # variabili globali
	elenco_lug						= set() # usato per cancellare Lug rimossi da zodb e per controllare omonimie
	coda_risultati					= multiprocessing.Queue() # risposte dei thread con i dati aggiornati
	tempo_minimo_per_i_controlli	= 20 # secondi
	report 							= [] # linee del report finale
	report.append('Spazzino: report data (UTC) ' + str(datetime.datetime.utcnow()))
	report.append('')
	socket.setdefaulttimeout(tempo_minimo_per_i_controlli / 4) # Timeout in secondi del fetching delle pagine (onorato da urllib2, a sua volta usato da Mechanize)

def invia_report(body):
	"""I receive a body, and I send email"""
	return
	header_from   = "Spazzino <spazzino@gelma.net>"
	header_to     = "gelma@gelma.net"
	subject       = 'LugMap: report data (UTC) '+str(datetime.datetime.utcnow())

	msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (header_from, header_to, subject))
	msg = body + '\n\n'
	msg = msg.encode('utf-8')

	try:
		import smtplib
		server = smtplib.SMTP('localhost')
		server.sendmail(header_from, header_to, msg)
		server.quit()
	except:
		logga('Errore: impossibile inviare email')
		print 'Errore: impossibile inviare email'

class LUG(persistent.Persistent):
	def __init__(self, id):
		self.id = self.denominazione = id # blocco di informazioni che abbiamo nel db
		self.regione = None
		self.provincia = None
		self.zona = None
		self.url = None
		self.contatto = None

		self.dominio = None # informazioni specifiche per ogni Lug
		self.notifiche = [] # non puoi dichiararla volatile. Il pickling non la porterebbe nella coda_risultati
		self.numero_controlli = 0
		self.numero_errori = 0

	def aggiorna_campi(self, riga_csv, filedb):
		"""Se i dati nel CSV sono cambiati, li rifletto nell'oggetto"""

		self.notifiche = [] # ad ogni avvio dei check, azzero

		if self.provincia     != riga_csv[0]:
			self.provincia     = riga_csv[0]
			self.notifica('Attenzione provincia aggiornata: '+self.provincia)

		if self.denominazione != riga_csv[1]:
			self.denominazione = riga_csv[1]
			self.notifica('Attenzione denominazione aggiornata: '+self.denominazione) # prob. impossibile

		if self.zona          != riga_csv[2]:
			self.zona          = riga_csv[2]
			self.notifica('Attenzione zona aggiornata: '+self.zona)

		if self.url           != riga_csv[3]:
			self.url           = riga_csv[3]
			self.dominio		 = self.url.split('/')[2]
			self.notifica('Attenzione URL aggiornato: '+self.url)

		if self.contatto      != riga_csv[4]:
			self.contatto	   = riga_csv[4]
			self.notifica('Attenzione contatto aggiornato: '+self.contatto)

		if self.regione		  != filedb[5:-4]:
			self.regione	   = filedb[5:-4]
			self.notifica('Attenzione regione aggiornata: '+self.regione)

	def notifica(self, testo):
		self.numero_errori += 1
		self.notifiche.append(testo)
		logga('Lug <'+self.id+'>:',testo)
		self.aggiorna_dati()

	def controllo_dns(self):
		"""Controllo l'esistenza e la mappatura del dominio"""

		logga('Lug <'+self.id+'>: controllo DNS per '+self.dominio)
		try:
			DNS_attuali = [ IP[4][0] for IP in socket.getaddrinfo(self.dominio, 80, 0, 0, socket.SOL_TCP)]
		except:
			self.notifica("Errore DNS per "+self.dominio)
			return False

		try: # se si solleva l'eccezione, vuole dire che DNS_noti non esiste perché siamo al primo avvio
			for ip_dns_attuale in DNS_attuali:
				if ip_dns_attuale not in self.DNS_noti:
					self.notifica('Attenzione DNS: nuovo %s su %s' % (ip_dns_attuale, ' '.join(self.DNS_noti)))
					self.DNS_noti.add(ip_dns_attuale)
		except:
			self.DNS_noti = set([IP for IP in DNS_attuali])

		return True

	def controllo_homepage(self):
		"""Leggo lo URL e faccio una valutazione numerica. True/False di ritorno."""

		logga('Lug <'+self.id+'>: controllo web per '+self.url)

		self._v_browser = mechanize.Browser() # volatile per zodb
		self._v_browser.set_handle_robots(False) # evitiamo di richiedere robots.txt ogni volta
		self._v_browser.addheaders = [('User-agent', 'Bot: http://lugmap.linux.it - lugmap@linux.it')]

		try:
			self._v_Termini_Attuali = set(self._v_browser.open(self.url).read().split()) # Estrapolo parole
		except:
			self.notifica('Errore sito: errore lettura homepage')
			return False

		try: # per evitare segnalazione su un Lug nuovo, se self.Termini_Precedenti non esiste
			valore_magico = \
			  float(len(self.Termini_Precedenti.intersection(self._v_Termini_Attuali))*1.0/len(self.Termini_Precedenti.union(self._v_Termini_Attuali)))
		except:
			# si solleva l'eccezione e setto opportunamente il tutto
			valore_magico = 1.0

		self.Termini_Precedenti = self._v_Termini_Attuali

		if valore_magico <= 0.6:
			self.notifica('Attenzione: differenze contenuto homepage ('+str(valore_magico)+')')
		else:
			logga('Lug <'+self.id+'>: valore_magico a', valore_magico)

		return True

	def controllo_title(self):
		"""Leggo il title della pagina e controllo che non sia cambiato. True/False di ritorno"""

		logga('Lug <'+self.id+'>: controllo title per '+self.url)

		try:
			self._v_titolo_attuale = self.browser.title().encode('utf-8')
		except: # se non ho un title, mollo
			return True

		try:
			if self.title_homepage != self._v_titolo_attuale:
				self.notifica('Attenzione: title homepage cambiato da <'+self.title_homepage+'>   a   <'+titolo_attuale+'>')
		except: # se fallisce è perché non esiste title_homepage (prima esecuzione)
			pass
		self.title_homepage = self._v_titolo_attuale # in ogni caso salvo il nuovo valore

	def aggiorna_dati(self):
		if hasattr(self, '_v_coda_risultati'):
			self._v_coda_risultati.put({'id': self.id, 'oggetto': self })

	def controlli(self, coda_risultati):
		self._v_coda_risultati = coda_risultati # volatile per evitare save in zodb
		logga('Lug <'+self.id+'>: inizio controlli')
		if self.controllo_dns():
			if self.controllo_homepage():
				self.controllo_title()
		self.aggiorna_dati()
		logga('Lug <'+self.id+'>: fine controlli')

if __name__ == "__main__":
	for filedb in glob.glob( os.path.join('./db/', '*.txt') ): # piglio ogni file db
		for riga in csv.reader(open(filedb, "r"), delimiter='|', quoting=csv.QUOTE_NONE): # e per ogni riga/Lug indicato
			id = riga[1]

			if id in elenco_lug: # controllo univocita' nome lug
				report.append('Errore: omonimia tra più Lug: '+id) # metti in reportistica generale
				logga('Dramma, omonimia per i Lug che si chiamano', id)
				continue
			else:
				elenco_lug.add(id)

			if not zodb.has_key(id): # se il Lug non è gia' presente nel DB
				zodb[id] = LUG(id) # lo creo

			zodb[id].aggiorna_campi(riga, filedb) # controllo eventuali cambiamenti nei campi del db

	for voce in zodb.keys(): # elimino da zodb le voci non piu' presenti
		if voce not in elenco_lug:
			del zodb[voce]
			report.append('Warn: '+voce+' eliminato da ZODB')
			logga('rimosso <'+voce+'> da ZODB')

	for id in sorted(zodb.keys()):
		fred = multiprocessing.Process(target=zodb[id].controlli, name=id, args=(coda_risultati,))
		fred.start()
		fred.join(tempo_minimo_per_i_controlli)

	logga('inizio commit dei risultati in zodb')
	while True:
		try:
			risultati = coda_risultati.get_nowait() # dalla coda prendo il pickle delle classi aggiornate
		except: # se la coda è vuota vado in timeout
			break
		zodb[risultati['id']] = risultati['oggetto'] # diversamente aggiorno zodb
		logga('Lug: <'+risultati['id']+'> commit dei dati')
	logga('fine commit dei risultati in zodb')

	# controllo stato dei thread
	for id in multiprocessing.active_children():
		report.append('Warn: check incompleto '+id.name+'    '+zodb[id.name].url)
		logga('Lug: <'+id.name+'> thread appeso')
		id.terminate()

	logga('inizio invio notifiche')
	for id in zodb.keys():
		if zodb[id].notifiche:
			logga('Lug <'+id+'> invio notifiche')
			report.append(30*'-')
			report.append('Lug: '+zodb[id].id+' ('+str(zodb[id].numero_controlli)+'/'+str(zodb[id].numero_errori)+')')
			for rigo in zodb[id].notifiche: report.append(rigo)
			report.append('- - - Dati - - -')
			report.append('Regione: '+zodb[id].regione)
			report.append('Provincia: '+zodb[id].provincia)
			report.append('Zona: '+zodb[id].zona)
			report.append('Url: '+zodb[id].url)
			report.append('Contatto: '+zodb[id].contatto)
	logga('fine invio notifiche')

	invia_report('\n'.join(report))
	print '\n'.join(report)

transaction.commit()
#db.pack()
db.close()
logga('concluso')
