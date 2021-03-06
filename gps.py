import datetime, time

class gps_decoder(object):
	def __init__(self, str):	
		self.gpsstring = str   
		data = self.gpsstring.split(',')
		
		if len(data) == 28:
			gpsdict = {}
			gpsdict['serial'] = data[0]
			gpsdict['authorized_numbers'] = data[1]
			gpsdict['gprmc'] = ','.join(data[2:15])
			gpsdict['fix_time'] = self.make_time(data[3])
			gpsdict['receiver_warning'] = data[4]
			gpsdict['latitude'] = int(float(data[5]) / 100) + ((float(data[5]) - (int(float(data[5]) / 100) * 100)) / 60)
			gpsdict['north_south'] = data[6]
			gpsdict['longitude'] = int(float(data[7]) / 100) + ((float(data[7]) - (int(float(data[7]) / 100) * 100)) / 60)
			gpsdict['east_west'] = data[8]
			gpsdict['speed_knots'] = data[9]
			gpsdict['speed_kmh'] = 1.85 * float(data[9])
			gpsdict['heading'] = data[10]
			gpsdict['datestamp'] = self.make_date(data[11])
			gpsdict['variation'] = data[12]
			gpsdict['variation_east_west'] = data[14][0:1]
			gpsdict['checksum'] = data[14][-2:]
			gpsdict['gps_signal'] = data[15]
			gpsdict['command'] = data[16]
			gpsdict['imei'] = data[17][6:]
			gpsdict['number_of_satellites'] = int(data[18])
			gpsdict['altitude'] = data[19]
			gpsdict['battery_power'] = float(data[20][2:6])
			gpsdict['battery_percentage'] = (1 - (4.15 - float(gpsdict['battery_power'])) / (4.2 - 3.6)) * 100 #max 4.2V and min 3.6V
			gpsdict['charging'] = data[21]
			gpsdict['gprmc_length'] = data[22]
			gpsdict['crc16'] = data[23]
			gpsdict['mobile_country_code'] = data[24]
			gpsdict['mobile_network_code'] = data[25]
			gpsdict['location_area_code'] = data[26]
			gpsdict['cell_id'] = data[27]

			self.dict = gpsdict
		else:
			raise Exception("Invalid gps data <%s>" % self.gpsstring)
	  
	#gps checksum calc
	def check_checksum(self):
		chk = ''
		ref = "0x%s" % self.dict['gprmc'][-2:]
	
		for c in self.dict['gprmc']:
			if c == '*':
				break
			elif chk == '':
				chk = ord(c)
			else:
				chk = chk ^ ord(c)
	
		return hex(chk).lower() == ref.lower()

	#create gps dict object
	def get_dict(self):
		return self.dict
	
	def make_time(self, timestr):
		return datetime.time(hour=int(timestr[0:2]), minute=int(timestr[2:4]), second=int(timestr[4:6]))
		
	def make_date(self, datestr):
		return datetime.date(day=int(datestr[0:2]), month=int(datestr[2:4]), year=2000+int(datestr[4:6]))