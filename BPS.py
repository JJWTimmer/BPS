#!/usr/bin/env python
import urllib2, socket, os, json, time, logging, sys
from datetime import datetime, timedelta

from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.protocols import basic
from twisted.python import log

from notification import mailer
import gps, inet

#globals
GEONAMES_SERVICE = None
CDB = None
MAILER = None
IP = None


def load_configuration(config_file):
	'''
	I read the configfile and populate the config dict
	'''
	file = open(config_file)
	config = json.load(file)
	file.close()

	return config
		
class BPSTelnetProtocol(basic.LineReceiver, TelnetProtocol):
	'''
	I am the BPS Telnet Protocol for twisted. I act on received lines via telnet
	'''
	
	#line ending
	delimiter = '\n'

	#startstate (and only state)
	state = 'Process_GPS'

	def connectionMade(self):
		log.msg("Client connected: %s" % self.transport.getPeer())
	
	def connectionLost(self, reason):
		log.msg("Client lost: %s (%s)" % (self.transport.getPeer(), reason) )
		basic.LineReceiver.connectionLost(self, reason)
		TelnetProtocol.connectionLost(self, reason)

	def lineReceived(self, line):
		oldState = self.state
		newState = getattr(self, "telnet_" + oldState)(line)
		if newState is not None:
			if self.state == oldState:
				self.state = newState
			else:
				log.msg("Warning: state changed and new state returned")

	def telnet_Process_GPS(self, line):
		try:
			gpsdecoder = gps.gps_decoder(line)
			gpsdict = gpsdecoder.get_dict()
			
			log.msg("received data from: %s" % self.transport.getPeer() )
			log.msg("Timestamp: %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
			log.msg("IMEI: %s" % gpsdict['imei'])
			
			#check position data for errors
			if gpsdecoder.check_checksum():
				log.msg("GPS Data OK")
				
				#check country
				country = GEONAMES_SERVICE.get_country(gpsdict['latitude'], gpsdict['longitude'])
				log.msg("Countrycode = %s" % country)

				#check battery
				charge = False
				if gpsdict['charging'] == '1':
					charge = True
					log.msg("battery = %.1f%% (%.1fV), charging = %s" % (gpsdict['battery_percentage'],gpsdict['battery_power'],charge))

				if float(gpsdict['battery_power']) < 3.7:
					log.msg("WARNING, LOW BATTERY")
					MAILER.low_battery(gpsdict['imei']) # refactor to lowBattery notification in general
				
				#post position to cdb
				response = CDB.post_position(gpsdict)
				log.msg("%s %s" %(response.status, response.reason))
				
			else:
				log.msg("GPS Data Error")
		except Exception as e:
			log.msg("ERROR: %s" % str(e))

#----------------------------------- START OF APP ---------------------------------#

# read the config file
config = load_configuration(os.path.dirname(gps.__file__) + os.sep + 'config.json')

# setup logging
log.startLogging(open(os.path.dirname(gps.__file__) + os.sep + 'BPS.log', 'w'))
log.msg("Config and logger loaded succesfully")

#setup the cdb connetion
CDB = inet.cdb(config['json_domain'], config['json_path'])

#the Geonames country lookup
GEONAMES_SERVICE = inet.geonames(config['geonames_username'])

#the email notifier
MAILER = mailer(config['smtp_server'], config['from_address'], config['notify'])

#the IP to bind to
IP = config['ip']

#twisted code
factory = ServerFactory()
factory.protocol = lambda: TelnetTransport(BPSTelnetProtocol)
service = TCPServer(config['port'], factory)

application = Application("Telnet GPS Server")
service.setServiceParent(application)