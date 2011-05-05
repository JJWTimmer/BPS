#!/usr/bin/env python
import urllib2, socket, os, json, time, logging, sys
from datetime import datetime, timedelta

from miniboa import TelnetServer
from daemon import Daemon

from notification import mailer
import gps, inet

#globals
GEONAMES_SERVICE = None
CDB = None
MAILER = None
CLIENT_LIST = []
LOGGER = logging.getLogger("bpslogger")
IP = socket.gethostbyname(socket.gethostname())

#read config file
def load_configuration(config_file):
    file = open(config_file)
    config = json.load(file)
    file.close()

    return config

#on connect of client do this
def my_on_connect(client):
  LOGGER.info("client connected: %s" % client.address)
  CLIENT_LIST.append(client)

#on disconnect of client to this
def my_on_disconnect(client):
  LOGGER.info("client disconnected: %s" % client.address)
  CLIENT_LIST.remove(client)
    
#every iteration do this
def process_clients():
  for client in CLIENT_LIST:
    if client.active and client.cmd_ready:
      try:
        data = client.get_command()
        gpsdecoder = gps.gps_decoder(data)
        gpsdict = gpsdecoder.get_dict()
        
        LOGGER.info("Timestamp: %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        LOGGER.info("IMEI: %s" % gpsdict['imei'])
        
        #check position data for errors
        if gpsdecoder.check_checksum():
          LOGGER.info("GPS Data OK")
          
          #check country
          country = GEONAMES_SERVICE.get_country(gpsdict['latitude'], gpsdict['longitude'])
          LOGGER.info("Countrycode = %s" % country)

          #check battery
          charge = False
          if gpsdict['charging'] == '1':
            charge = True
          LOGGER.info("battery = %.1f%% (%.1fV), charging = %s" % (gpsdict['battery_percentage'],gpsdict['battery_power'],charge))

          if float(gpsdict['battery_power']) < 3.7:
            LOGGER.info("WARNING, LOW BATTERY")
            MAILER.low_battery(gpsdict['imei'])
          
          #post position to cdb
          response = CDB.post_position(gpsdict)
          LOGGER.info("%s %s" %(response.status, response.reason))
          
        else:
          LOGGER.info("GPS Data Error")
      except Exception, e:
        LOGGER.info("ERROR: %s" % e)
      LOGGER.info("")
      
class BPS(Daemon):
  def run(self):
    server = TelnetServer(port=config['port'], address=IP, on_connect=my_on_connect, on_disconnect=my_on_disconnect)
    
    #loop until keyboard interupt
    while True:
      server.poll()
      process_clients()

#start of program
if __name__ == "__main__":
  
  config = load_configuration(os.path.dirname(__file__) + os.sep + 'config.json')
  
  LOGGER.setLevel(logging.INFO)
  hdlr = logging.FileHandler(os.path.dirname(__file__) + os.sep + 'log.txt')
  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
  hdlr.setFormatter(formatter)
  LOGGER.addHandler(hdlr)

  LOGGER.info("Config and logger loaded succesfully")
  
  CDB = inet.cdb(config['json_domain'], config['json_path'])
  GEONAMES_SERVICE = inet.geonames(config['geonames_username'])
  MAILER = mailer(config['smtp_server'], config['from_address'], config['notify'])
  IP = config['ip']
  
  bps = BPS(os.path.dirname(__file__) + os.sep + 'bps.pid')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      bps.start()
    elif 'stop' == sys.argv[1]:
      bps.stop()
    elif 'restart' == sys.argv[1]:
      bps.restart()
    elif 'run' == sys.argv[1]:
      bps.run()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|restart" % sys.argv[0]
    sys.exit(2)


