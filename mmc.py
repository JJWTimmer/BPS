import csv

class mmc(object):
	def __init__(self):
		codes = {}
		codefile = csv.reader(open('mmc_country_codes.csv', 'r'), delimiter=';', quotechar='|')
		
		for row in codefile:
			codes[ row[0] ] = row[2]
		
		self.codes = codes

	def get(self, mmc):
		key = str(mmc)
		if key in self.codes.keys():
			return self.codes[key]
		else:
			return "UNKNOWN COUNTRY"