import json, httplib
from datetime import timedelta, datetime
from suds import WebFault
from suds.client import Client


class cdb(object):
	def __init__(self, url, jsonpath, vehicleurl, vehicleapp, vehiclepassword, vehiclerefresh):
		#post json position setup
		self.url = url
		self.jsonpath = jsonpath
		self.encoder = json.JSONEncoder(indent = 4)
		self.connection = httplib.HTTPConnection(self.url)
		
		#vehicle lookup setup
		self.refresh = vehiclerefresh
		self.client = Client(vehicleurl)
		
		authHeader = self.client.factory.create('AuthHeader')
		authHeader.Editie = -1
		authHeader.Applicatie = vehicleapp
		authHeader.Wachtwoord = vehiclepassword

		self.client.set_options(soapheaders=authHeader)
		
		self.get_vehicles()
	
	def post_position(self, dict):
		timestamp = datetime.utcnow().isoformat() + 'Z'

		output = {}
		output['id'] = dict['imei']
		output['timestamp'] = timestamp
		output['latitude'] = "%f" % dict['latitude']
		output['longitude'] = "%f" % dict['longitude']
		output['speed'] = "%f" % dict['speed_kmh']
		output['direction'] = dict['heading']

		json_out = self.encoder.encode(output)
		
		headers = {"Content-type": "application/json", "Accept": "application/json; charset=utf8"}
		
		self.connection.request("POST", self.jsonpath, json_out, headers)
		
		return self.connection.getresponse()
	
	def get_vehicles(self):
		vehicle_count = self.client.service.getVoertuigCount()
		self.vehicles = self.client.service.getVoertuigList(0, vehicle_count)[0]
		self.last_vehicle_request = datetime.now()
	
	def get_name_from_imei(self, imei):
		if (datetime.now() - self.last_vehicle_request) > timedelta(seconds=self.refresh):
			self.get_vehicles()

		for vehicle in self.vehicles:
		   if 'vt_gps_imei' in vehicle and vehicle['vt_gps_imei'] == imei:
			   return vehicle['vt_naam']
		return "UNKNOWN GPS"