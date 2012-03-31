import MySQLdb

class blam(object):
	def __init__(self, host, port, user, pw, db):
		self.host = host
		self.port = port
		self.user = user
		self.pw = pw
		self.db = db
	
	def __del__(self):
		if (self.db):
			self.db.close()
	
	def set_gps_status(self, vehicle_name, status):
		db = None
		try:
			db = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.pw, db=self.db)
			cur = db.cursor()
			cur.execute("UPDATE handles SET gps_status=%d WHERE handle_name='%s' OR description='%s'" % (status, vehicle_name, vehicle_name))
			
		except MySQLdb.Error, e:
			raise Exception("DB error: <%s>" % e)
		finally:
			if (db):
				db.close()