import urllib2

class geonames(object):
	def __init__(self, name):
		self.name = name
	
	def get_country(self, lat, lon):
		url = "http://api.geonames.org/countryCode?lat=%f&lng=%f&username=%s" % (lat, lon, self.name)
		response = urllib2.urlopen(url) 
		country = response.read().strip()
		return country