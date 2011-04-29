import smtplib
from email.mime.text import MIMEText

class mailer(object):
  def __init__(self, send_addr, recvs):
    self.send_addr = send_addr
    self.recvs = recvs.split()
    
  def low_battery(self, imei):
    msg = MIMEText("LOW BATTERY")
    
    msg['Subject'] = 'BATTERY OF GPS WITH IMEI %s IS RUNNING LOW' % imei
    msg['From'] = self.send_addr
    msg['To'] = ','.join(self.recvs)

    self.send(msg)

  def send(self, msg):
    s = smtplib.SMTP('127.0.0.1')
    s.set_debuglevel(1)
    s.sendmail(self.send_addr, self.recvs, msg.as_string())
    s.quit()
