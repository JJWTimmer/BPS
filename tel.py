#!/usr/bin/env python
from miniboa import TelnetServer
import urllib2


CLIENT_LIST = []

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
            for i in range(0,len(message)-1):
                print "%d = %s\n" % (i, message[i])
            url = "http://api.geonames.org/countryCode?lat=%f&lng=%f&username=batapositioning" % (float(message[5])/100,float(message[7])/100)
            response = urllib2.urlopen(url) 
            country = response.read()
            print "Countrycode = %s" % country

server = TelnetServer(port=9999, address='46.21.169.102', on_connect=my_on_connect, on_disconnect=my_on_disconnect)

print "\n\nStarting server on port %d.  CTRL-C to interrupt.\n" % server.port
while True:
    server.poll()
    process_clients()