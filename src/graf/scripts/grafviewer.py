#!/usr/bin/env python

import argparse
from pylogfile.base import *
from graf.base import *

parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('--sanserif', help="Force use of SanSerif font family.", action='store_true')
parser.add_argument('--serif', help="Force use of Serif font family.", action='store_true')
parser.add_argument('--mono', help="Force use of Monospace font family.", action='store_true')
parser.add_argument('--bold', help="Force use of bold fonts.", action='store_true')
parser.add_argument('--italic', help="Force use of italic fonts.", action='store_true')
parser.add_argument('--structure', help="Show internal strucutre of GrAF file.", action='store_true')
args = parser.parse_args()

def main():
	
	log = LogPile()
	
	# Get filename from arguments
	filename = args.filename
	
	len_gt5 = len(filename) > 5
	len_gt7 = len(filename) > 7
	
	# Read file
	if len_gt5 and filename[-5:].upper() == ".GRAF":
		graf1 = Graf()
		graf1.load_hdf(filename)
	elif len_gt5 and filename[-5:].upper() == ".JSON":
		print(f"JSON")
		# if not log.load_hdf(filename):
		# 	print("\tFailed to read JSON file.")
		pass
	elif len_gt7 and filename[-7:].upper() == ".PKLFIG":
		print(f"PklFig")
		pass
	else:
		print(f"Other")
	
	# Apply styling
	if args.serif:
		print("Setting to serif")
		graf1.style.set_all_font_families("serif")
	elif args.sanserif:
		print("Setting to sanserif")
		graf1.style.set_all_font_families("sanserif")
	elif args.mono:
		print("Setting to monospace")
		graf1.style.set_all_font_families("monospace")
	
	if args.italic:
		# print("Setting to serif")
		graf1.style.title_font.italic = True
		graf1.style.graph_font.italic = True
		graf1.style.label_font.italic = True
	if args.bold:
		# print("Setting to sanserif")
		graf1.style.title_font.bold = True
		graf1.style.graph_font.bold = True
		graf1.style.label_font.bold = True
	
	# Generate plot
	pltfig = graf1.to_fig()
	plt.show()
	