import MySQLdb

class blam(object):
	def __init__(self, host, port, user, pw, db):
		try:
			self.db = MySQLdb.connect(host=host, port=port, user=user, passwd=pw, db=db)
		except MySQLdb.Error, e:
			raise Exception("DB Connect error: <%s>" % e)
	
	def __del__(self):
		if (self.db):
			self.db.close()
	
	def set_gps_status(self, vehicle_name, status):
		try:
			cur = self.db.cursor()
			cur.execute("UPDATE handles SET gps_status=%d WHERE handle_name='%s' OR description='%s'" % (status, vehicle_name, vehicle_name))
			
		except MySQLdb.Error, e:
			raise Exception("DB Connect error: <%s>" % e)
	