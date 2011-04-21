import urllib2

message = ['110419125953', '+31614153814', 'GPRMC', '115953.886', 'A', '5221.7086', 'N', '00456.6793', 'E', '0.00', '0.00', '190411', '', '', 'A*6F', 'F', '', ' imei:354778031964284', '03', '10.9', 'F:3.89V', '0', '137', '35523', '204', '16', '0096', '2955']

url = "http://api.geonames.org/countryCode?lat=%f&lng=%f&username=batapositioning" % (float(message[5])/100,float(message[7])/100)
response = urllib2.urlopen(url) 
print response.read()