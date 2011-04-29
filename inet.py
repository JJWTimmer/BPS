import urllib2, json, httplib
from datetime import timedelta, datetime

class geonames(object):
  def __init__(self, name):
    self.name = name
  
  def get_country(self, lat, lon):
    url = "http://api.geonames.org/countryCode?lat=%f&lng=%f&username=%s" % (lat,lon, self.name)
    response = urllib2.urlopen(url) 
    country = response.read().strip()
    return country
 
class cdb(object):
  def __init__(self, url, path):
    self.url = url
    self.path = path
  
  def post_position(self, dict):
    #vps is one minute ahead of cdb
    delta = timedelta(minutes=1)
    timestamp = (datetime.utcnow()-delta).isoformat()

    output = {}
    output['id'] = dict['imei']
    output['timestamp'] = timestamp
    output['latitude'] = "%f" % dict['latitude']
    output['longitude'] = "%f" % dict['longitude']
    output['speed'] = "%f" % dict['speed_kmh']
    output['direction'] = dict['heading']

    enc = json.JSONEncoder(indent = 4)
    json_out = enc.encode(output)
    
    headers = {"Content-type": "application/json", "Accept": "application/json; charset=utf8"}
    conn = httplib.HTTPConnection(self.url)
    conn.request("POST", self.path, json_out, headers)
    response = conn.getresponse()
    
    return response
