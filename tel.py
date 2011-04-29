#!/usr/bin/env python
from miniboa import TelnetServer
import urllib2, time, socket, json, httplib, os
from datetime import datetime, timedelta

from notification import mailer
import gps

#globals
JSON_DOMAIN = None
JSON_PATH = None
GEONAMES_USERNAME = None
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
      message = data.split(',')

      print "%s:\n IMEI = %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), message[17][6:])
      
      gps_str = ','.join(message[2:15])
      if gps.chk_chksum(gps_str):
        print "GPS Data OK"
        
        #===============
        # begin country retrieval      
        url = "http://api.geonames.org/countryCode?lat=%f&lng=%f&username=%s" % (float(message[5])/100,float(message[7])/100, GEONAMES_USERNAME)
        response = urllib2.urlopen(url) 
        country = response.read().strip()
        print "Countrycode = %s" % country
        # end country retrieval
        #===============
        
        
        #===============
        # begin battery calculation
        bat =  float(message[20][2:6]) - 3.65
        rest = bat / (4.15 - 3.65) * 100

        print "battery = %.1f%%" % rest

        if float(message[20][2:6]) < 3.7:
          print "WARNING, LOW BATTERY"
          MAILER.low_battery(message[17][6:])
        
        # end battery calculation
        #===============
        
        #================
        # start json object building    
        delta = timedelta(minutes=1)
        timestamp = (datetime.utcnow()-delta).isoformat()
        print "timestamp = %s" % timestamp

        lat = float(message[5])
        lon = float(message[7])

        lat = int(lat / 100) + ((lat - (int((lat / 100)) * 100)) / 60)
        lon = int(lon / 100) + ((lon - (int((lon / 100)) * 100)) / 60)
        speed = 1.85 * float(message[9])

        output = {}
        output['id'] = message[17][6:]
        output['timestamp'] = timestamp
        output['latitude'] = "%f" % lat
        output['longitude'] = "%f" % lon
        output['speed'] = "%f" % speed
        output['direction'] = message[10]

        enc = json.JSONEncoder(indent = 4)
        json_out = enc.encode(output)
        
        headers = {"Content-type": "application/json", "Accept": "application/json; charset=utf8"}
        conn = httplib.HTTPConnection(JSON_DOMAIN)
        conn.request("POST", JSON_PATH, json_out, headers)
        response = conn.getresponse()
        print "%s %s" %(response.status, response.reason)

        # end json
        #===============
        
      else:
        print "GPS Data Error"
#===============================================================

if __name__ == "__main__":
  config = load_configuration('config.json')
  
  JSON_DOMAIN = config['json_domain']
  JSON_PATH = config['json_path']
  GEONAMES_USERNAME = config['geonames_username']
  MAILER = mailer(config['from_address'], config['notify'])
  
  server = TelnetServer(port=config['port'], address=socket.gethostbyname(socket.gethostname()), on_connect=my_on_connect, on_disconnect=my_on_disconnect)
  #server = TelnetServer(port=9999, address='192.168.2.137', on_connect=my_on_connect, on_disconnect=my_on_disconnect)
  
  print "\n\nStarting server on port %d.  CTRL-C to interrupt.\n" % server.port
  while True:
      server.poll()
      process_clients()
