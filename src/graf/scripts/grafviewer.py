#!/usr/bin/env python

import argparse
import os
from pylogfile.base import *
from graf.base import *

def build_parser():
	parser = argparse.ArgumentParser(
		prog="graf-viewer",
		description="View GrAF (.graf) figures and optionally restyle them.")
	parser.add_argument('filenames', nargs="+", help="GrAF files to view")
	parser.add_argument('--sanserif', help="Force use of SanSerif font family.", action='store_true')
	parser.add_argument('--serif', help="Force use of Serif font family.", action='store_true')
	parser.add_argument('--mono', help="Force use of Monospace font family.", action='store_true')
	parser.add_argument('--bold', help="Force use of bold fonts.", action='store_true')
	parser.add_argument('--italic', help="Force use of italic fonts.", action='store_true')
	parser.add_argument('-s', '--struct', help="Show internal structure of GrAF file.", action='store_true')
	parser.add_argument('-S', '--structure', help="Show internal structure of GrAF file, verbosely.", action='store_true')
	return parser


def main(argv=None):

	args = build_parser().parse_args(argv)
	log = LogPile()
	
	graphs = []
	figs = []
	
	# Get filename from arguments
	for filename in args.filenames:
	# filename = args.filename
	
		# GrAF is the only format this tool reads or writes.
		if not filename.upper().endswith(".GRAF"):
			print(f"Skipping '{filename}': not a GrAF file (expected a .graf extension).")
			continue

		if not os.path.isfile(filename):
			print(f"Skipping '{filename}': file not found.")
			continue

		graf1 = Graf()
		try:
			graf1.read_graf(filename)
		except Exception as e:
			print(f"Skipping '{filename}': could not be read as a GrAF file ({e}).")
			continue

		# Print structure if requested
		if args.structure:
			dict_summary(graf1.pack(), verbose=2)
		elif args.struct:
			dict_summary(graf1.pack(), verbose=1)
		
		# Apply styling
		if args.serif:
			graf1.style.set_all_font_families("serif")
		elif args.sanserif:
			graf1.style.set_all_font_families("sanserif")
		elif args.mono:
			graf1.style.set_all_font_families("monospace")
		
		if args.italic:
			graf1.style.title_font.italic = True
			graf1.style.graph_font.italic = True
			graf1.style.label_font.italic = True
		if args.bold:
			graf1.style.title_font.bold = True
			graf1.style.graph_font.bold = True
			graf1.style.label_font.bold = True
		
		graphs.append(graf1)
		
		# Generate plot
		figs.append(graf1.to_fig(filename))
	
	# # Make figure
	# pltfig = graphs[0].to_fig()
	# ax = pltfig.gca()
	# idx = 0
	# for grf in graphs[1:]:
	# 	idx += 1
	# 	ax.plot(grf.get_xdata(), grf.get_ydata(), linestyle=':', marker='.', label=args.filenames[idx])
	
	
	plt.show()

if __name__ == "__main__":
	main()