#!/usr/bin/env python
import urllib2, socket, os, json, time, logging, sys, threading
from datetime import datetime, timedelta

from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.protocols import basic
from twisted.python import log
from twisted.internet.threads import deferToThread

from notification import mailer
import gps, cdb, blam
from util import enum

#----------------------------------- Globals ---------------------------------#
CDB = None
MAILER = None
LOWBAT = None
LASTPOS = None
BLAM = None
BATTERY_THRESHOLD = None

GPS_STATUS = enum(NONE=0, CHARGING=1, BATTERY=2, EMPTY=3, SILENCE=4)

def load_configuration(config_file):
	'''
	I read the configfile and populate the config dict
	'''
	file = open(config_file)
	config = json.load(file)
	file.close()

	return config

#----------------------------------- Background checker------------------------#
def monitor():
	silent_vehicles = [k for (k,v) in LASTPOS.items() if v < (datetime.now()-timedelta(minutes=5))]
	for v in silent_vehicles:
		del LASTPOS[v]
	map(lambda v: BLAM.set_gps_status(v, GPS_STATUS.SILENCE), silent_vehicles)
	reactor.callLater(30, monitor)
#----------------------------------- Protocol ---------------------------------#
	
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
			
			#check position data for errors
			if gpsdecoder.check_checksum():				
				vehicle = CDB.get_name_from_imei(gpsdict['imei'])
				
				#check battery
				status = GPS_STATUS.BATTERY
				
				if gpsdict['charging'] == '1':
					status = GPS_STATUS.CHARGING
				elif float(gpsdict['battery_power']) < BATTERY_THRESHOLD:			
					status = GPS_STATUS.EMPTY
					
					if MAILER:
						#remove expired warnings from the dictionary
						LOWBAT = dict([(k,v) for (k,v) in LOWBAT.items() if v > (datetime.now()-timedelta(minutes=15))])
					
						#if not already send, send the notification
						if not vehicle in LOWBAT.keys():
							LOWBAT[vehicle] = datetime.now()
							MAILER.low_battery(vehicle)
				
				#update last received time
				LASTPOS[vehicle] = datetime.now()

				#post position to cdb
				response = CDB.post_position(gpsdict)
				
				#update the BLAM db
				BLAM.set_gps_status(vehicle, status)				
			else:
				log.msg("GPS Data Error")
		except Exception as e:
			log.msg("ERROR: %s" % str(e))

#----------------------------------- START OF APP ---------------------------------#
def stopMonitor():
	MONITOR.stop()
#----------------------------------- START OF APP ---------------------------------#

thisdir = os.path.dirname(__file__)
if not thisdir == '':
	thisdir += os.sep

# setup logging
log.startLogging(open(thisdir + 'BPS.log', 'w'))
log.msg("Logger loaded")

# read the config file
config = load_configuration(thisdir + 'config.json')
log.msg("Config loaded")

#setup the cdb connetion
CDB = cdb.cdb(config['json_domain'], config['json_path'], config['vehicle_service'], config['vehicle_app'], config['vehicle_password'], config['vehicle_refresh'])
log.msg("cdb connected")

#connect to blam
BLAM = blam.blam(config['mysql_server_host'],config['mysql_server_port'],config['mysql_server_user'],config['mysql_server_pw'],config['mysql_blam_db'])
log.msg("blam connected")

#if there are receivers create a mailer
if config['notify']:
	MAILER = mailer(config['smtp_server'], config['from_address'], config['notify'])
	log.msg("mailer created")
	
	LOWBAT = {}

#set the battery voltage that triggers lowbattery
BATTERY_THRESHOLD = float(config['battery_threshold'])

#Dict for last time position was received
LASTPOS = {}

#twisted code
factory = ServerFactory()
factory.protocol = lambda: TelnetTransport(BPSTelnetProtocol)

application = Application("BPS")

service = TCPServer(config['port'], factory)
service.setServiceParent(application)

reactor.callLater(30, monitor)
#reactor.run()