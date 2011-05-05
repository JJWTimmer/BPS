import smtplib
from email.mime.text import MIMEText

class mailer(object):
  def __init__(self, smtp_svr, send_addr, recvs):
    self.smtp_svr = smtp_svr
    self.send_addr = send_addr
    self.recvs = recvs.split()
    
  def low_battery(self, imei):
    msg = MIMEText("LOW BATTERY")
    
    msg['Subject'] = 'BATTERY OF GPS WITH IMEI %s IS RUNNING LOW' % imei
    msg['From'] = self.send_addr
    msg['To'] = ','.join(self.recvs)

    self.send(msg)

  def send(self, msg):
    s = smtplib.SMTP(self.smtp_svr)
    s.sendmail(self.send_addr, self.recvs, msg.as_string())
    s.quit()
