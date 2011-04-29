# gps checksum calc
def chk_chksum(gprmc_str):
  chk = ''
  ref = "0x%s" % gprmc_str[-2:]
  
  for c in gprmc_str:
    if c == '*':
      break
    elif chk == '':
      chk = ord(c)
    else:
      chk = chk ^ ord(c)
  
  return hex(chk).lower() == ref.lower()