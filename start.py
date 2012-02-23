from twisted.scripts.twistd import run
from os.path import join, dirname
from sys import argv

import gps

if __name__ == "__main__":
	argv[1:] = ['-n', '-y', join(dirname(gps.__file__), "BPS.py")]
	run()