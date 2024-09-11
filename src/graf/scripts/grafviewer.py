#!/usr/bin/env python

import argparse
from pylogfile.base import *
from graf.base import *

parser = argparse.ArgumentParser()
parser.add_argument('filename')
args = parser.parse_args()

def main():
	
	log = LogPile()
	
	# Get filename from arguments
	filename = args.filename
	
	len_gt5 = len(filename) > 5
	len_gt7 = len(filename) > 7
	
	# Read file
	if len_gt5 and filename[-4:].upper() == ".GRAF":
		graf1 = Graf()
		graf1.load_hdf(filename)
		pltfig = graf1.to_fig()
		plt.show()
		# if not log.load_hdf(filename):
		# 	print("\tFailed to read GRAF")
	elif len_gt5 and filename[-5:].upper() == ".JSON":
		# if not log.load_hdf(filename):
		# 	print("\tFailed to read JSON file.")
		pass
	elif len_gt7 and filename[-5:].upper() == ".PKLFIG":
		pass