#!/usr/bin/env python
from miniboa import TelnetServer
import urllib2, time, socket, json, httplib, os
from datetime import datetime, timedelta

from notification import mailer
import gps, inet

#globals
GEONAMES_SERVICE = None
CDB = None
MAILER = None
CLIENT_LIST = []

#read config file
def load_configuration(config_file):
    file = open(config_file)
    config = json.load(file)
    file.close()

    return config

#on connect of client do this
def my_on_connect(client):
  print "client connected: %s" % client.address
  CLIENT_LIST.append(client)

#on disconnect of client to this
def my_on_disconnect(client):
  print "client disconnected: %s" % client.address
  CLIENT_LIST.remove(client)
    
#every iteration do this
def process_clients():
  for client in CLIENT_LIST:
    if client.active and client.cmd_ready:
      data = client.get_command()
      gpsdecoder = gps.gps_decoder(data)
      gpsdict = gpsdecoder.get_dict()
      
      print "\n>>%s\n>>IMEI = %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), gpsdict['imei'])
      
      #check position data for errors
      if gpsdecoder.check_checksum():
        print "GPS Data OK"       
        
        #check country
        country = GEONAMES_SERVICE.get_country(gpsdict['latitude'], gpsdict['longitude'])
        print "Countrycode = %s" % country

        #check battery
        charge = False
        if gpsdict['charging'] == '1':
          charge = True
        print "battery = %.1f%% (%.1fV), charging = %s" % (gpsdict['battery_percentage'],gpsdict['battery_power'],charge)

        if float(gpsdict['battery_power']) < 3.7:
          print "WARNING, LOW BATTERY"
          MAILER.low_battery(message[17][6:])
        
        #post position to cdb
        response = CDB.post_position(gpsdict)
        print "%s %s" %(response.status, response.reason)
        
      else:
        print "GPS Data Error"
        
#start of program
if __name__ == "__main__":
  config = load_configuration('config.json')
  
  CDB = inet.cdb(config['json_domain'], config['json_path'])
  GEONAMES_SERVICE = inet.geonames(config['geonames_username'])
  MAILER = mailer(config['from_address'], config['notify'])
  
  server = TelnetServer(port=config['port'], address=socket.gethostbyname(socket.gethostname()), on_connect=my_on_connect, on_disconnect=my_on_disconnect)
  
  print "\n\nStarting server on port %d.  CTRL-C to interrupt.\n" % server.port
  
  #loop until keyboard interupt
  while True:
      server.poll()
      process_clients()
