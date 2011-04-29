#!/usr/bin/env python
from miniboa import TelnetServer
import urllib2, time, socket, json, httplib, os
from datetime import datetime, timedelta

from notification import mailer
import gps, inet

#globals
JSON_DOMAIN = None
JSON_PATH = None
GEONAMES_SERVICE = None
MAILER = None
CLIENT_LIST = []

#read config file
def load_configuration(config_file):
    file = open(config_file)
    config = json.load(file)
    file.close()

    return config

def my_on_connect(client):
  print "client connected: %s" % client.address
  CLIENT_LIST.append(client)

def my_on_disconnect(client):
  print "client disconnected: %s" % client.address
  CLIENT_LIST.remove(client)
    
def process_clients():
  for client in CLIENT_LIST:
    if client.active and client.cmd_ready:
      data = client.get_command()
      gpsdecoder = gps.gps_decoder(data)
      gpsdict = gpsdecoder.get_dict()
      print gpsdict
      
      print "\n>>%s\n>>IMEI = %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), gpsdict['imei'])
      
      if gpsdecoder.check_checksum():
        print "GPS Data OK"       
        
        country = GEONAMES_SERVICE.get_country(gpsdict['latitude'], gpsdict['longitude'])
        print "Countrycode = %s" % country

        charge = False
        if gpsdict['charging'] == '1':
          charge = True
        print "battery = %.1f%% (%.1fV), charging = %s" % (gpsdict['battery_percentage'],gpsdict['battery_power'],charge)

        if gpsdict['battery_power'] < 3.7:
          print "WARNING, LOW BATTERY"
          MAILER.low_battery(message[17][6:])
           
        delta = timedelta(minutes=1)
        timestamp = (datetime.utcnow()-delta).isoformat()
        print "timestamp = %s" % timestamp
	
        output = {}
        output['id'] = gpsdict['imei']
        output['timestamp'] = timestamp
        output['latitude'] = "%f" % gpsdict['latitude']
        output['longitude'] = "%f" % gpsdict['longitude']
        output['speed'] = "%f" % gpsdict['speed_kmh']
        output['direction'] = gpsdict['heading']

        enc = json.JSONEncoder(indent = 4)
        json_out = enc.encode(output)
        
        headers = {"Content-type": "application/json", "Accept": "application/json; charset=utf8"}
        conn = httplib.HTTPConnection(JSON_DOMAIN)
        conn.request("POST", JSON_PATH, json_out, headers)
        response = conn.getresponse()
        print "%s %s" %(response.status, response.reason)
        
      else:
        print "GPS Data Error"
#===============================================================

if __name__ == "__main__":
  config = load_configuration('config.json')
  
  JSON_DOMAIN = config['json_domain']
  JSON_PATH = config['json_path']
  GEONAMES_SERVICE = inet.geonames(config['geonames_username'])
  MAILER = mailer(config['from_address'], config['notify'])
  
  server = TelnetServer(port=config['port'], address=socket.gethostbyname(socket.gethostname()), on_connect=my_on_connect, on_disconnect=my_on_disconnect)
  #server = TelnetServer(port=9999, address='192.168.2.137', on_connect=my_on_connect, on_disconnect=my_on_disconnect)
  
  print "\n\nStarting server on port %d.  CTRL-C to interrupt.\n" % server.port
  while True:
      server.poll()
      process_clients()
