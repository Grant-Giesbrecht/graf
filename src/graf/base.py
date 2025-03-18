import h5py
import json
import pickle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from abc import ABC, abstractmethod
from jarnsaxa import hdf_to_dict, dict_to_hdf
import pylogfile.base as plf
import copy
from ganymede import dict_summary
import matplotlib.font_manager as fm
import os
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import mpl_toolkits.mplot3d as mpl3d
from matplotlib.collections import QuadMesh
from matplotlib.image import AxesImage
import warnings
import numpy as np
from colorama import Fore, Style

## TODO:
# 1. Add error bars or shading support
# 2. Add alpha to color specification
# 3. Add 3D support (lines)
# 4. Add 3D support (surface)
#

GRAF_VERSION = "0.0.0"
LINE_TYPES = ["-", "-.", ":", "--", "None"]
MARKER_TYPES = [".", "+", "^", "v", "o", "x", "[]", "|", "_", "*", "None"]
FONT_TYPES = ['regular', 'bold', 'italic']

try:
	# Requires Python >= 3.9
	import importlib.resources
	mod_path_mp = importlib.resources.files("graf")
	mod_path = str((mod_path_mp / ''))
except AttributeError as e:
	help_data = {}
	print(f"{Fore.LIGHTRED_EX}Upgrade to Python >= 3.9 for access to standardized fonts. ({e})")
except Exception as e:
	help_data = {}
	print(__name__)
	print(f"{Fore.LIGHTRED_EX}An error occured. ({e}){Style.RESET_ALL}")

def sample_colormap(cmap_name:str=None, listed_cmap:mcolors.ListedColormap=None, N:int=20):
	''' Discretizes a colormap, returning a list of rgb lists from the provided
	colormap.
	
	Args:
		cmap_name: Name of a standard matplotlib colormap
		listed_cmap: Matplotlib ListedColormap object. If provided, cmap_name is
			ignored.
		N: The number of colors to break the colormap into.
	
	Returns:
		The list of rgb lists representing the provided colormap.
	'''
	
	# Get a listed cmap and resample
	if listed_cmap is not None:
		cmap = listed_cmap.resampled(N) # Resample in requested resolution
		colors = [cmap(i) for i in range(N)]
	elif cmap_name is not None:
		cmap = plt.get_cmap(cmap_name) # Get ListedColormap from name
		colors = [cmap(i / (N - 1)) for i in range(N)]
	else:
		raise Exception("A colormap name or object must be provided")
	
	return colors

def load_fonts(conf_file:str):
	
	# Read conf data
	with open(conf_file, 'r') as fh:
		conf_data = json.load(fh)
	
	# Scan over all fonts
	for ff in conf_data['font-list']:
		
		# Get font-family name
		try:
			ff_name = ff['names'][0]
		except:
			print(f"font configuration file missing font name!.")
			continue
		
		# Read each font type
		for ft in FONT_TYPES:
			
			# Check valid data
			if ft not in ff:
				print(f"font configuration file missing parameter: {ft} in font-family {ff_name}.")
				continue
			
			# If path is valid, set font object to None
			if len(ff[ft]) == 0:
				ff[f'font-{ft}'] = None
			else:
				font_path = mod_path
				for fpd in ff[ft]:
					font_path = os.path.join(font_path, fpd)
			
			# Try to read font
			try:
				ff[f'font-{ft}'] = fm.FontProperties(fname=font_path)
			except:
				ff[f'font-{ft}'] = None
	
	return conf_data

font_data = load_fonts(os.path.join(mod_path, 'assets', 'portable_fonts.json'))

def hexstr_to_rgb(hexstr:str):
	''' Credit: https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python John1024'''
	hexstr = hexstr.lstrip('#')
	return tuple(int(hexstr[i:i+2], 16)/255 for i in (0, 2, 4))

def has_twinx(ax):
	''' Checks if a matplotlib axis has a twin-axis (specifically a 2nd Y that shares a common X). '''
	
	# Get list of siblings
	sibling_list = ax.get_shared_x_axes().get_siblings(ax)
	
	# Scan over all axes in figure
	for fig_ax in ax.figure.axes:
		
		# Skip axis if is original axis
		if fig_ax == ax:
			continue
		
		# Scan over all siblings 
		for sib_ax in sibling_list:
			
			# Return true if found a match
			if sib_ax == fig_ax:
				return True
	
	# No twin was found
	return False

class Packable(ABC):
	""" This class represents all objects that can be packed and unpacked and sent between the client and server
	
	manifest, obj_manifest, and list_template are all dictionaries. Each describes a portion of how to represent a class as a string,
	and how to convert back to the class from the string data.
	
	manifest: lists all variables that can be converted to/from JSON natively
	obj_manifest: lists all variables that are Packable objects or lists of packable objects. Each object will have
		pack() called, and be understood through its unpack() function.
	list_template: dictionary mapping item to pack/unpack to its class type, that way during unpack, Packable knows which
		class to create and call unpack() on.
	
	Populate all three of these variables as needed in the set_manifest function. set_manifest is called in super().__init__(), so
	it shouldn't need to be remembered in any of the child classes.
	"""
	
	def __init__(self, log:plf.LogPile=None):
		
		if log is None:
			print(f"{Fore.RED}Log object was not initialized in {type(self)} instance.!{Style.RESET_ALL}")
			self.log = plf.LogPile(use_mutex=False)
		else:
			self.log = log
			self.log.set_enable_mutex(False)
		
		self.log.lowdebug(f"Created object type={type(self)}")
		self.manifest = []
		self.obj_manifest = []
		self.list_manifest = {}
		self.dict_manifest = {}
		
		self.set_manifest()
	
	@abstractmethod
	def set_manifest(self):
		""" This function will populate the manifest and obj_manifest objects"""
		pass
	
	def pack(self):
		""" Returns the object to as a JSON dictionary """
		
		# Initialize dictionary
		d = {}
		
		# Add items in manifest to packaged data
		for mi in self.manifest:
			d[mi] = getattr(self, mi)
		
		# Scan over object manifest
		for mi in self.obj_manifest:
			# Pack object and add to output data
			try:
				d[mi] = getattr(self, mi).pack()
			except:
				raise Exception(f"'Packable' object had corrupt object manifest item '{mi}'. Cannot pack.", detail=f"Type = {type(self)}")
				
		# Scan over list manifest
		for mi in self.list_manifest:
				
			# Pack objects in list and add to output data
			d[mi] = [x.pack() for x in getattr(self, mi)]
		
		# Scan over dict manifest
		for mi in self.dict_manifest:
			
			mi_deref = getattr(self, mi)
			
			# Pack objects in dict and add to output data
			d[mi] = {}
			for midk in mi_deref.keys():
				d[mi][midk] = mi_deref[midk].pack()
				
		# Return data list
		return d
	
	def unpack(self, data:dict):
		""" Populates the object from a JSON dict """
		
		# Try to populate each item in manifest
		for mi in self.manifest:
			self.log.lowdebug(f"Unpacking manifest, item:>{mi}<")
			
			# Try to assign the new value
			try:
				setattr(self, mi, data[mi])
			except Exception as e:
				self.log.error(f"Failed to unpack item in object of type '{type(self).__name__}'. ({e})", detail=f"Type = {type(self)}")
				return
		
		# Try to populate each Packable object in manifest
		for mi in self.obj_manifest:
			self.log.lowdebug(f"Unpacking obj_manifest, item:>{mi}<")
			
			# Try to update the object by unpacking the item
			try:
				getattr(self, mi).unpack(data[mi])
			except Exception as e:
				self.log.error(f"Failed to unpack Packable in object of type '{type(self).__name__}'. ({e})", detail=f"Type = {type(self)}")
				return
			
		# Try to populate each list of Packable objects in manifest
		for mi in self.list_manifest.keys():
				
			# Scan over list, unpacking each element
			temp_list = []
			for list_item in data[mi]:
				self.log.lowdebug(f"Unpacking list_manifest, item:>{mi}<, element:>:a{list_item}<")
				
				# Try to create a new object and unpack a list element
				try:
					# Create a new object of the correct type
					new_obj = copy.deepcopy(self.list_manifest[mi])
					
					# Populate the new object by unpacking it, add to list
					new_obj.unpack(list_item)
					temp_list.append(new_obj)
				except Exception as e:
					self.log.error(f"Failed to unpack list of Packables in object of type '{type(self).__name__}'. Type={type(self)}. ({e})", detail=f"Type = {type(self)}")
					return
			setattr(self, mi, temp_list)
				# self.obj_manifest[mi] = copy.deepcopy(temp_list)
		
		# Scan over dict manifest
		for mi in self.dict_manifest.keys():
			
			# mi_deref = getattr(self, mi)
			
			# # Pack objects in list and add to output data
			# d[mi] = [mi_deref[midk].pack() for midk in mi_deref.keys()]
			
			# Scan over list, unpacking each element
			temp_dict = {}
			for dmk in data[mi].keys():
				self.log.lowdebug(f"Unpacking manifest, item:>{mi}<, element:>:a{dmk}<")
				
				# Try to create a new object and unpack a list element
				try:
					# Create a new object of the correct type
					try:
						new_obj = copy.deepcopy(self.dict_manifest[mi])
					except Exception as e:
						print("Dict Manifest:")
						print(self.dict_manifest)
						self.log.error(f"Failed to unpack dict_manifest[{mi}], ({e})")
						return
					
					# Populate the new object by unpacking it, add to list
					new_obj.unpack(data[mi][dmk])
					temp_dict[dmk] = new_obj
				except Exception as e:
					prob_item = data[mi][dmk]
					self.log.error(f"Failed to unpack dict of Packables in object of type '{type(self).__name__}'. ({e})", detail=f"Class={type(self)}, problem manifest item=(name:{dmk}, type:{type(prob_item)})")
					return
			setattr(self, mi, temp_dict)

class Font(Packable):
	
	def __init__(self, log:plf.LogPile=None):
		super().__init__(log)
		
		self.use_native = False
		self.size = 12
		self.font = "sanserif"
		self.bold = False
		self.italic = False
	
	def set_manifest(self):
		
		self.manifest.append("use_native")
		self.manifest.append("size")
		self.manifest.append("font")
		self.manifest.append("bold")
		self.manifest.append("italic")
	
	def to_tuple(self):
		
		#TODO: Apply a default font if family not found
		
		# Return None if instructed to use native font
		if self.use_native:
			return None
		
		# Otherwise look for font family
		for ff_stuct in font_data['font-list']:
			
			# Found font family
			if self.font in ff_stuct['names']:
				
				# Return bold if present and requested
				if self.bold and ff_stuct['font-bold'] is not None:
					return (ff_stuct['font-bold'], self.size)
				elif self.italic and ff_stuct['font-italic'] is not None:
					return (ff_stuct['font-italic'], self.size)
				elif ff_stuct['font-regular'] is not None:
					return (ff_stuct['font-regular'], self.size)
		
		return None
				
class GraphStyle(Packable):
	''' Represents style parameters for the graph.'''
	def __init__(self, log:plf.LogPile=None):
		super().__init__(log)
		
		self.supertitle_font = Font()
		self.title_font = Font()
		self.graph_font = Font()
		self.label_font = Font()
	
	def set_all_font_families(self, fontfamily:str):
		
		#TODO: Validate that font family exists
		self.title_font.font = fontfamily
		self.graph_font.font = fontfamily
		self.label_font.font = fontfamily
	
	def set_all_font_sizes(self, fontsize:int):
		
		#TODO: Validate that font family exists
		self.title_font.size = fontsize
		self.graph_font.size = fontsize
		self.label_font.size = fontsize
	
	def set_manifest(self):
		self.obj_manifest.append("supertitle_font")
		self.obj_manifest.append("title_font")
		self.obj_manifest.append("graph_font")
		self.obj_manifest.append("label_font")
	
class Surface(Packable):
	''' Represents a surface or image that can be displayed on a set of axes. 
	Fundamentally what differentiates a surface from a Trace is if it has a single
	independent axis or two.'''
	
	SURF_IMAGE = "SURF_IMAGE"
	SURF_SURFACE = "SURF_SURFACE"
	
	def __init__(self, mpl_source=None, log:plf.LogPile=None):
		super().__init__(log)
		
		self.surf_type = Surface.SURF_SURFACE
		
		self.cmap = []
		
		self.uniform_grid = False
		self.x_grid = []
		self.y_grid = []
		self.z_grid = []
		self.line_type = LINE_TYPES[0]
		self.line_width = 1
		self.display_name = ""
		self.include_in_legend = True
		
		self.line_color = (1, 0, 0)
		self.alpha = 1
		
		self.antialias = False
		
		if mpl_source is not None:
			self.mimic(mpl_source=mpl_source)
	
	def mimic(self, mpl_source=None):
		
		if isinstance(mpl_source, Poly3DCollection):
			self.mimic_poly3d(mpl_source)
		elif isinstance(mpl_source, QuadMesh):
			self._mimic_quadmesh(mpl_source)
		elif isinstance(mpl_source, AxesImage):
			self._mimic_axesiamge(mpl_source)
		else:
			print(f"WARNING: Unrecognized data type {type(mpl_source)} will be ignored.")
	
	def _mimic_quadmesh(self, mpl_source):
		
		self.surf_type = Surface.SURF_IMAGE
		
		# mpl QuadMesh does not support lines
		self.line_type = "None"
		
		# Get X and Y coordinates
		self.uniform_grid = True # This x and y retrieval method assumes a uniform grid, however quadmesh objects CAN have nonuniform grids! TODO: Generalize this!
		x_list = mpl_source._coordinates[0,:-1,0] + np.diff(mpl_source._coordinates[0,:,0])/2
		y_list = mpl_source._coordinates[:-1, 0, 1] + np.diff(mpl_source._coordinates[:, 0, 1])/2
		
		# Create grids from lists
		_xg, _yg = np.meshgrid(x_list, y_list)
		self.x_grid = _xg.tolist()
		self.y_grid = _yg.tolist()
		self.z_grid = mpl_source.get_array().tolist()
		
		# Read transparency layer
		self.alpha = mpl_source.get_alpha()
		if self.alpha is None:
			self.alpha = 1
		
		# Get colormap
		self.cmap = sample_colormap(mpl_source.get_cmap(), N=30) #TODO: Make N adjustable with a flag
	
	def _mimic_axesiamge(self, mpl_source):
		''' Mimics a matplotlib AxesImage object (produced by imshow()).'''
		
		self.surf_type = Surface.SURF_IMAGE
		
		# # mpl QuadMesh does not support lines
		# self.line_type = "None"
		
		# Get Z data - dimensions will be used to find X and Y
		zg_raw = mpl_source.get_array()
		self.z_grid = zg_raw.tolist()
		
		# Get X and Y coordinates
		x_min, x_max, y_min, y_max = mpl_source.get_extent()
		x_list = np.linspace(x_min, x_max, zg_raw.shape[1])
		y_list = np.linspace(y_min, y_max, zg_raw.shape[0])
		
		self.uniform_grid = True # Imshow requires a uniform grid
		
		# Create grids from lists
		_xg, _yg = np.meshgrid(x_list, y_list)
		self.x_grid = _xg.tolist()
		self.y_grid = _yg.tolist()
		
		# Read transparency layer
		self.alpha = mpl_source.get_alpha()
		if self.alpha is None:
			self.alpha = 1
		
		# Get colormap
		self.cmap = sample_colormap(mpl_source.get_cmap(), N=30) #TODO: Make N adjustable with a flag
	
	# def mimic_poly3d(self, mpl_source):
		
	# 	#TODO: This is a SURFACE from plot_surface()
		
	# 	self.line_type = Trace.TRACE_LINE2D
	# 	self.use_yaxis_R = use_twin
		
	# 	# Get line color
	# 	self.line_color = mcolors.to_rgb(mpl_line.get_color())
	# 	# if type(mpl_line.get_color()) == tuple:
	# 	# 	self.line_color = mpl_line.get_color()
	# 	# else:
	# 	# 	self.line_color = hexstr_to_rgb(mpl_line.get_color())
		
	# 	# Get transparency
	# 	self.alpha = mpl_line.get_alpha()
	# 	if self.alpha is None:
	# 		self.alpha = 1
		
	# 	# Get marker color
	# 	self.marker_color = mcolors.to_rgb(mpl_line.get_markerfacecolor())
	# 	# if type(mpl_line.get_markerfacecolor()) == tuple:
	# 	# 	self.marker_color = mpl_line.get_markerfacecolor()
	# 	# else:
	# 	# 	self.marker_color = hexstr_to_rgb(mpl_line.get_markerfacecolor())
		
	# 	# Get x-data
	# 	self.x_data = [float(x) for x in mpl_line.get_xdata()]
	# 	self.y_data = [float(x) for x in mpl_line.get_ydata()]
		
	# 	# Get line type
	# 	self.line_type = mpl_line.get_linestyle()
	# 	if self.line_type not in LINE_TYPES:
	# 		self.line_type = LINE_TYPES[0]
		
	# 	# Get marker
	# 	mpl_marker_code = mpl_line.get_marker().lower()
	# 	match mpl_marker_code:
	# 		case '.':
	# 			self.marker_type = '.'
	# 		case '+':
	# 			self.marker_type = '+'
	# 		case '^':
	# 			self.marker_type = '^'
	# 		case 'v':
	# 			self.marker_type = 'v'
	# 		case 's':
	# 			self.marker_type = '[]'
	# 		case 'o':
	# 			self.marker_type = 'o'
	# 		case None:
	# 			self.marker_type = 'None'
	# 		case 'none':
	# 			self.marker_type = 'None'
	# 		case '*':
	# 			self.marker_type = '*'
	# 		case '_':
	# 			self.marker_type = '_'
	# 		case '|':
	# 			self.marker_type = '|'
	# 		case 'x':
	# 			self.marker_type = 'x'
	# 		case _:
	# 			self.marker_type = '.'
		
	# 	# Get marker
	# 	if self.marker_type == None:
	# 		self.marker_type = "None"
	# 	if self.marker_type not in MARKER_TYPES:
	# 		self.marker_type = MARKER_TYPES[0]
		
	# 	#TODO: Normalize these to one somehow?
	# 	self.marker_size = mpl_line.get_markersize()
	# 	self.line_width = mpl_line.get_linewidth()
	# 	self.display_name = str(mpl_line.get_label())
	
	def apply_to(self, ax, gstyle:GraphStyle):
		
		self.gs = gstyle
		
		if self.surf_type == Surface.SURF_IMAGE:
			self._apply_to_image(ax)
		else:
			self.log.error(f"Surface.apply_to(): Unrecognized surface type {self.surf_type}")
	
	def _apply_to_image(self, ax):
		
		ax.pcolormesh(self.x_grid, self.y_grid, self.z_grid, cmap=mcolors.ListedColormap(self.cmap), alpha=self.alpha, antialiased=self.antialias)
	
	def set_manifest(self):
		
		self.manifest.append("surf_type")
		self.manifest.append("cmap")
		
		self.manifest.append("uniform_grid")
		self.manifest.append("x_grid")
		self.manifest.append("y_grid")
		self.manifest.append("z_grid")
		self.manifest.append("line_type")
		self.manifest.append("line_width")
		self.manifest.append("display_name")
		self.manifest.append("include_in_legend")
		
		self.manifest.append("line_color")
		self.manifest.append("alpha")
		
		self.manifest.append("antialias")

class Trace(Packable):
	''' Represents a trace that can be displayed on a set of axes'''
	
	TRACE_LINE2D = "TRACE_LINE2D"
	TRACE_LINE3D = "TRACE_LINE3D"
	TRACE_COLOR = "TRACE_COLOR"
	TRACE_SURFACE = "TRACE_SURFACE"
	
	def __init__(self, mpl_line=None, mpl_img=None, mpl_surf=None, use_twin=False, log:plf.LogPile=None):
		super().__init__(log)
		
		self.trace_type = Trace.TRACE_LINE2D
		self.use_yaxis_R = use_twin # Only supported for Trace_line2D
		self.x_data = []
		self.y_data = []
		self.z_data = []
		self.line_type = LINE_TYPES[0]
		self.marker_type = MARKER_TYPES[0]
		self.marker_size = 1
		self.line_width = 1
		self.display_name = ""
		self.include_in_legend = True
		
		self.line_color = (1, 0, 0)
		self.alpha = 1
		
		self.marker_color = (1, 0, 0)
		
		if mpl_line is not None:
			
			self.mimic(mpl_line=mpl_line, use_twin=use_twin)
			# # Check for 2D vs 3D
			# if isinstance(mpl_line, mpl3d.art3d.Line3D):
			# 	self.mimic(mpl_line=mpl_line, use_twin=use_twin)
			# else:
			# 	self.mimic(mpl_line=mpl_line, use_twin=use_twin)
		elif mpl_img is not None:
			self.mimic(mpl_img=mpl_img)
		elif mpl_surf is not None:
			self.mimic(mpl_surf=mpl_surf)
	
	def mimic(self, mpl_line=None, mpl_img=None, mpl_surf=None, use_twin=False):
		
		if mpl_line is not None:
			# if isinstance(mpl_line, mlines.Line2D):
			if isinstance(mpl_line, mpl3d.art3d.Line3D):
				self.log.lowdebug(f"Detected line as 3D", detail=f"Type={type(mpl_line)}")
				self.mimic_3dline(mpl_line)
			else:
				self.log.lowdebug(f"Detected line as 2D", detail=f"Type={type(mpl_line)}")
				self.mimic_2dline(mpl_line, use_twin=use_twin)
				
	def mimic_2dline(self, mpl_line, use_twin=False):
	
		self.trace_type = Trace.TRACE_LINE2D
		self.use_yaxis_R = use_twin
		
		# Get line color
		self.line_color = mcolors.to_rgb(mpl_line.get_color())
		# if type(mpl_line.get_color()) == tuple:
		# 	self.line_color = mpl_line.get_color()
		# else:
		# 	self.line_color = hexstr_to_rgb(mpl_line.get_color())
		
		# Get transparency
		self.alpha = mpl_line.get_alpha()
		if self.alpha is None:
			self.alpha = 1
		
		# Get marker color
		self.marker_color = mcolors.to_rgb(mpl_line.get_markerfacecolor())
		# if type(mpl_line.get_markerfacecolor()) == tuple:
		# 	self.marker_color = mpl_line.get_markerfacecolor()
		# else:
		# 	self.marker_color = hexstr_to_rgb(mpl_line.get_markerfacecolor())
		
		# Get x-data
		self.x_data = [float(x) for x in mpl_line.get_xdata()]
		self.y_data = [float(x) for x in mpl_line.get_ydata()]
		self.z_data = []
		
		# Get line type
		self.line_type = mpl_line.get_linestyle()
		if self.line_type not in LINE_TYPES:
			self.line_type = LINE_TYPES[0]
		
		# Get marker
		mpl_marker_code = mpl_line.get_marker().lower()
		match mpl_marker_code:
			case '.':
				self.marker_type = '.'
			case '+':
				self.marker_type = '+'
			case '^':
				self.marker_type = '^'
			case 'v':
				self.marker_type = 'v'
			case 's':
				self.marker_type = '[]'
			case 'o':
				self.marker_type = 'o'
			case None:
				self.marker_type = 'None'
			case 'none':
				self.marker_type = 'None'
			case '*':
				self.marker_type = '*'
			case '_':
				self.marker_type = '_'
			case '|':
				self.marker_type = '|'
			case 'x':
				self.marker_type = 'x'
			case _:
				self.marker_type = '.'
		
		# Get marker
		if self.marker_type == None:
			self.marker_type = "None"
		if self.marker_type not in MARKER_TYPES:
			self.marker_type = MARKER_TYPES[0]
		
		#TODO: Normalize these to one somehow?
		self.marker_size = mpl_line.get_markersize()
		self.line_width = mpl_line.get_linewidth()
		self.display_name = str(mpl_line.get_label())
	
	def mimic_3dline(self, mpl_line):
	
		self.trace_type = Trace.TRACE_LINE3D
		self.use_yaxis_R = False
		
		# Get line color
		self.line_color = mcolors.to_rgb(mpl_line.get_color())
		# if type(mpl_line.get_color()) == tuple:
		# 	self.line_color = mpl_line.get_color()
		# else:
		# 	self.line_color = hexstr_to_rgb(mpl_line.get_color())
		
		# Get transparency
		self.alpha = mpl_line.get_alpha()
		if self.alpha is None:
			self.alpha = 1
		
		# Get marker color
		self.marker_color = mcolors.to_rgb(mpl_line.get_markerfacecolor())
		# if type(mpl_line.get_markerfacecolor()) == tuple:
		# 	self.marker_color = mpl_line.get_markerfacecolor()
		# else:
		# 	self.marker_color = hexstr_to_rgb(mpl_line.get_markerfacecolor())
		
		# Get all data
		data3d = mpl_line.get_data_3d()
		
		# Unpack into x, y and z
		self.x_data = data3d[0]
		self.y_data = data3d[1]
		self.z_data = data3d[2]
		# self.x_data = [float(xtup[0]) for xtup in data3d]
		# self.y_data = [float(xtup[1]) for xtup in data3d]
		# self.z_data = [float(xtup[2]) for xtup in data3d]
		
		# Get line type
		self.line_type = mpl_line.get_linestyle()
		if self.line_type not in LINE_TYPES:
			self.line_type = LINE_TYPES[0]
		
		# Get marker
		mpl_marker_code = mpl_line.get_marker().lower()
		match mpl_marker_code:
			case '.':
				self.marker_type = '.'
			case '+':
				self.marker_type = '+'
			case '^':
				self.marker_type = '^'
			case 'v':
				self.marker_type = 'v'
			case 's':
				self.marker_type = 's'
			case None:
				self.marker_type = 'None'
			case 'none':
				self.marker_type = 'None'
			case _:
				self.marker_type = '.'
		
		# Get marker
		if self.marker_type == None:
			self.marker_type = "None"
		if self.marker_type not in MARKER_TYPES:
			self.marker_type = MARKER_TYPES[0]
		
		#TODO: Normalize these to one somehow?
		self.marker_size = mpl_line.get_markersize()
		self.line_width = mpl_line.get_linewidth()
		self.display_name = str(mpl_line.get_label())
	
	def apply_to(self, ax, gstyle:GraphStyle):
		self.gs = gstyle
		
		if self.trace_type == Trace.TRACE_LINE2D:
			self.apply_to_2dline(ax)
		elif self.trace_type == Trace.TRACE_LINE3D:
			self.apply_to_3dline(ax)
		else:
			self.warning(f"Unable to apply type: {self.trace_type}. Skipping.")
			return
	
	def apply_to_2dline(self, ax):
		
		#TODO: Error check line type, marker type, and sizes
		
		ax.add_line(matplotlib.lines.Line2D(self.x_data, self.y_data, linewidth=self.line_width, linestyle=self.line_type, color=self.line_color, marker=self.marker_type, markersize=self.marker_size, markerfacecolor=self.marker_color, label=self.display_name, alpha=self.alpha))
	
	def apply_to_3dline(self, ax):
		
		#TODO: Error check line type, marker type, and sizes
		
		ax.add_line(mpl3d.art3d.Line3D(self.x_data, self.y_data, self.z_data, linewidth=self.line_width, linestyle=self.line_type, color=self.line_color, marker=self.marker_type, markersize=self.marker_size, markerfacecolor=self.marker_color, label=self.display_name, alpha=self.alpha))
	
	def set_manifest(self):
		self.manifest.append("trace_type")
		self.manifest.append("use_yaxis_R")
		self.manifest.append("x_data")
		self.manifest.append("y_data")
		self.manifest.append("z_data")
		self.manifest.append("line_type")
		self.manifest.append("marker_type")
		self.manifest.append("marker_size")
		self.manifest.append("line_width")
		self.manifest.append("display_name")
		self.manifest.append("include_in_legend")
		
		self.manifest.append("line_color")
		self.manifest.append("alpha")
		self.manifest.append("marker_color")
	
class Scale(Packable):
	''' Defines a singular axis/scale such as an x-axis.'''
	
	SCALE_ID_X = 0
	SCALE_ID_Y = 1
	SCALE_ID_Z = 2
	
	def __init__(self, gs:GraphStyle, valid:bool=True, ax=None, scale_id:int=SCALE_ID_X, log:plf.LogPile=None):
		super().__init__(log)
		''' Instead of making some unused Scales None, we mark them as not valid. '''
		
		# Pointer to Graf object's GraphStyle - so fonts can be appropriately initialized
		self.gs = gs
		
		self.is_valid = valid # Used so when axes aren't used (ex. Z-axis in 2D plot), GrAF knows to ignore this object. Using None isn't an option because HDF doesn't support NoneTypes.
		self.val_min = 0
		self.val_max = 1
		self.tick_list = []
		self.minor_tick_list = []
		self.tick_label_list = []
		self.label = ""
		
		if ax is not None:
			self.mimic(ax, scale_id)
	
	def set_manifest(self):
		
		self.manifest.append("is_valid")
		self.manifest.append("val_min")
		self.manifest.append("val_max")
		self.manifest.append("tick_list")
		self.manifest.append("minor_tick_list")
		self.manifest.append("tick_label_list")
		self.manifest.append("label")
		
	
	def mimic(self, ax, scale_id:int):
		
		print(f"scale mimicing axis.")
		
		if scale_id == Scale.SCALE_ID_X:
			self.is_valid = True
			xlim_tuple = ax.get_xlim()
			self.val_min = float(xlim_tuple[0])
			self.val_max = float(xlim_tuple[1])
			self.tick_list = [float(x) for x in ax.get_xticks()]
			self.minor_tick_list = []
			self.tick_label_list = [x.get_text() for x in ax.get_xticklabels()]
			self.label = str(ax.get_xlabel())
		
		elif scale_id == Scale.SCALE_ID_Y:
			self.is_valid = True
			ylim_tuple = ax.get_ylim()
			self.val_min = float(ylim_tuple[0])
			self.val_max = float(ylim_tuple[1])
			self.tick_list = [float(x) for x in ax.get_yticks()]
			self.minor_tick_list = []
			self.tick_label_list = [x.get_text() for x in ax.get_yticklabels()]
			self.label = str(ax.get_ylabel())
		
		elif scale_id == Scale.SCALE_ID_Z:
			self.is_valid = True
			zlim_tuple = ax.get_zlim()
			self.val_min = float(zlim_tuple[0])
			self.val_max = float(zlim_tuple[1])
			self.tick_list = [float(x) for x in ax.get_zticks()]
			self.minor_tick_list = []
			self.tick_label_list = [x.get_text() for x in ax.get_zticklabels()]
			self.label = str(ax.get_zlabel())
		else:
			print(f"ERROR: Unrecognized Scale-id: {scale_id}")
		#TODO: Add Z-version
	
	def apply_to(self, ax, gstyle:GraphStyle, scale_id:int):
		
		self.gs = gstyle
		
		local_font = self.gs.label_font.to_tuple()
		
		if scale_id == Scale.SCALE_ID_X:
			ax.set_xticks(self.tick_list)
			ax.set_xticklabels(self.tick_label_list)
			
			if local_font is not None:
				ax.set_xlabel(self.label, fontproperties=local_font[0], size=local_font[1])
			else:
				ax.set_xlabel(self.label)
			ax.set_xlim([self.val_min, self.val_max])
		elif scale_id == Scale.SCALE_ID_Y:
			
			ax.set_yticks(self.tick_list)
			ax.set_yticklabels(self.tick_label_list)
			
			if local_font is not None:
				ax.set_ylabel(self.label, fontproperties=local_font[0], size=local_font[1])
			else:
				ax.set_ylabel(self.label)
			ax.set_ylim([self.val_min, self.val_max])
		
		elif scale_id == Scale.SCALE_ID_Z:
			
			ax.set_zticks(self.tick_list)
			ax.set_zticklabels(self.tick_label_list)
			
			if local_font is not None:
				ax.set_zlabel(self.label, fontproperties=local_font[0], size=local_font[1])
			else:
				ax.set_zlabel(self.label)
			ax.set_zlim([self.val_min, self.val_max])
			

# TODO: Merge these with Axis.AXIS_LINE2D etc.
AXISTYPE_LINE = 0
AXISTYPE_SURFACE = 1
AXISTYPE_IMAGE = 2
AXISTYPE_UNKNOWN = -1

def get_axis_type(mpl_axis):
	''' Returns a code for the type of data contained. '''
	
	# Check if lines is populated - 2D or 3D line plot
	if len(mpl_axis.lines) > 0:
		return AXISTYPE_LINE
	elif len(mpl_axis.collections) > 0: # From `plot_surface`
		return AXISTYPE_SURFACE
	elif len(mpl_axis.images) > 0: # From imagesc?
		return AXISTYPE_IMAGE

class Axis(Packable):
	'''' Defines a set of axes, including the x-y-(z), grid lines, etc. and contains
	data to display on the axes.'''
	
	AXIS_LINE2D = "AXIS_LINE2D"
	AXIS_LINE3D = "AXIS_LINE3D"
	AXIS_IMAGE = "AXIS_IMAGE"
	AXIS_SURFACE = "AXIS_SURFACE"
	
	def __init__(self, gs:GraphStyle, ax=None, twin_ax=None, log:plf.LogPile=None): #:matplotlib.axes._axes.Axes=None):
		super().__init__(log)
		
		self.gs = gs # Copy of GraphStyle in Graf class - do not add to manifest
		
		self.axis_type = Axis.AXIS_LINE2D
		self.position = [0, 0] # Position, as row-column from top-left
		self.span = [1, 1] # Row and column span of axes
		self.relative_size = []
		self.x_axis = Scale(gs)
		self.y_axis_L = Scale(gs)
		self.y_axis_R = Scale(gs)
		self.z_axis = Scale(gs)
		self.grid_on = False
		self.traces = {}
		self.surfaces = {}
		self.title = ""
		
		# Initialize with axes if possible
		if ax is not None:
			self.mimic(ax, twin=twin_ax)
	
	def set_manifest(self):
		self.manifest.append("axis_type")
		self.manifest.append("position")
		self.manifest.append("span")
		self.manifest.append("relative_size")
		self.obj_manifest.append("x_axis")
		self.obj_manifest.append("y_axis_L")
		self.obj_manifest.append("y_axis_R")
		self.obj_manifest.append("z_axis")
		self.manifest.append("grid_on")
		self.dict_manifest["traces"] = Trace()
		self.dict_manifest["surfaces"] = Surface()
		self.manifest.append("title")
	
	def mimic(self, ax, twin=None):
		
		#TODO: Detect axis type
		if (len(ax.collections) > 0) or (len(ax.images) > 0):
			self.axis_type = Axis.AXIS_IMAGE
			self.log.debug(f"Mimicing Surface object")
			self._mimic_surface(ax)
		else:
			self.log.debug(f"Mimicing Trace object")
			self._mimic_line(ax, twin=twin)
	
	def _mimic_line(self, ax, twin=None):
		
		# Identify main and twin axis
		if twin is None:
			main_ax = ax
			twin_ax = None
		else:
			if (ax._sharex is None) and (twin._sharex is not None):
				main_ax = ax
				twin_ax = twin
			elif (ax._sharex is not None) and (twin._sharex is None):
				main_ax = twin
				twin_ax = ax
			else:
				print(f"ERROR: Improperly paired axes associated as twins. Skipping.")
				return
		
		print(f"Initializing scales.")
		
		# self.relative_size = []
		self.x_axis = Scale(self.gs, ax=main_ax, scale_id=Scale.SCALE_ID_X, log=self.log)
		self.y_axis_L = Scale(self.gs, ax=main_ax, scale_id=Scale.SCALE_ID_Y, log=self.log)
		if twin_ax is not None:
			self.y_axis_R = Scale(self.gs, ax=twin_ax, scale_id=Scale.SCALE_ID_Y, log=self.log)
		else:
			self.y_axis_R = Scale(self.gs, valid=False, log=self.log)
		if hasattr(main_ax, 'get_zlim'):
			self.z_axis = Scale(self.gs, ax=main_ax, scale_id=Scale.SCALE_ID_Z, log=self.log)
			
			# This only works for 3D
			self.grid_on = ax._draw_grid
		else:
			self.z_axis = Scale(self.gs, valid=False, log=self.log)
			
			# This only works for 2D
			if len(main_ax.xaxis.get_gridlines()) == 0:
				self.grid_on = False
			else:
				self.grid_on = main_ax.xaxis.get_gridlines()[0].get_visible()
		
		# Find and mimic all lines (2d and 3d)
		for idx, mpl_trace in enumerate(main_ax.lines):
			self.log.lowdebug(f"Mimicing trace: {mpl_trace}")
			self.traces[f'Tr{idx}'] = Trace(mpl_trace, log=self.log)
		
		# Get lines for twin
		idx_offset = len(self.traces)
		if twin_ax is not None:
			for idx, mpl_trace in enumerate(twin_ax.lines):
				self.traces[f'Tr{idx+idx_offset}'] = Trace(mpl_trace, use_twin=True, log=self.log)
		
		self.title = str(main_ax.get_title())
		
		# Get subplot position
		col_start = main_ax.get_subplotspec().colspan.start
		col_stop = main_ax.get_subplotspec().colspan.stop
		row_start = main_ax.get_subplotspec().rowspan.start
		row_stop = main_ax.get_subplotspec().rowspan.stop
		
		# Copy to local variables
		self.position = [row_start, col_start]
		self.span = [row_stop-row_start, col_stop-col_start]
	
	def _mimic_surface(self, ax):
		
		# self.relative_size = []
		self.x_axis = Scale(self.gs, ax=ax, scale_id=Scale.SCALE_ID_X, log=self.log)
		self.y_axis_L = Scale(self.gs, ax=ax, scale_id=Scale.SCALE_ID_Y, log=self.log)
		self.y_axis_R = Scale(self.gs, valid=False, log=self.log)
		if hasattr(ax, 'get_zlim'):
			self.z_axis = Scale(self.gs, ax=ax, scale_id=Scale.SCALE_ID_Z, log=self.log)
		else:
			self.z_axis = Scale(self.gs, valid=False, log=self.log)
		
		# Check if grid is enabled
		if len(ax.xaxis.get_gridlines()) == 0:
			self.grid_on = False
		else:
			self.grid_on = ax.xaxis.get_gridlines()[0].get_visible()
		
		# Find and mimic all images (AxesImage)
		for idx, mpl_image in enumerate(ax.images):
			self.surfaces[f'Sf{idx}'] = Surface(mpl_image, log=self.log)
		
		# Find and mimic all "collections" (QuadMesh and Poly3DCollection)
		idx_offset = len(self.surfaces)
		for idx, mpl_coll in enumerate(ax.collections):
			self.surfaces[f'Sf{idx+idx_offset}'] = Surface(mpl_coll, log=self.log)
		
		# Get subplot position
		col_start = ax.get_subplotspec().colspan.start
		col_stop = ax.get_subplotspec().colspan.stop
		row_start = ax.get_subplotspec().rowspan.start
		row_stop = ax.get_subplotspec().rowspan.stop
		
		# Copy to local variables
		self.position = [row_start, col_start]
		self.span = [row_stop-row_start, col_stop-col_start]
	
	def apply_to(self, ax, gstyle:GraphStyle, twin_ax=None):
		
		if self.axis_type == Axis.AXIS_LINE2D or self.axis_type == Axis.AXIS_LINE3D:
			self.line_apply_to(ax, gstyle=gstyle, twin_ax=twin_ax)
		else:
			self.image_apply_to(ax, gstyle=gstyle)
	
	def line_apply_to(self, ax, gstyle:GraphStyle, twin_ax=None):
		
		self.gs = gstyle
		
		# Check for missing twin axis
		if self.y_axis_R.is_valid:
			if twin_ax is None:
				print(f"ERROR: Was not provided neccesary twin axis.")
				twin_ax = ax.twinx()
		
		# Apply traces
		for tr in self.traces.keys():
			if self.traces[tr].use_yaxis_R:
				self.traces[tr].apply_to(twin_ax, self.gs)
			else:
				self.traces[tr].apply_to(ax, self.gs)
		
		# self.relative_size = []
		self.x_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Y)
		if self.y_axis_R.is_valid:
			self.y_axis_R.apply_to(twin_ax, self.gs, scale_id=Scale.SCALE_ID_Y)
		if self.z_axis.is_valid:
			self.z_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Z)
		ax.grid(self.grid_on)
		
		local_font = self.gs.title_font.to_tuple()
		if local_font is not None:
			ax.set_title(self.title, fontproperties=local_font[0], size=local_font[1])
		else:
			ax.set_title(self.title)
	
	def image_apply_to(self, ax, gstyle:GraphStyle, twin_ax=None):
		
		self.gs = gstyle
		
		# Apply traces
		for sf in self.surfaces.keys():
			self.surfaces[sf].apply_to(ax, self.gs)
		
		# self.relative_size = []
		self.x_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Y)
		ax.grid(self.grid_on)
		
		local_font = self.gs.title_font.to_tuple()
		if local_font is not None:
			ax.set_title(self.title, fontproperties=local_font[0], size=local_font[1])
		else:
			ax.set_title(self.title)
		
	def get_size(self):
		''' Returns a tuple of (top left row, top left column, bottom right row, bottom right column)'''
		
		return [self.position[0], self.position[1], self.position[0]+self.span[0], self.position[1]+self.span[1]]
	
	def get_slice(self):
		''' Access the subplot position as a tuple of (RowSlice, ColSlice)'''
		
		return (slice(self.position[0], self.position[0]+self.span[0]), slice(self.position[1], self.position[1]+self.span[1]))
		
	def get_trace_idx(self, search_label:str):
		"""
		Finds the trace with the specified label
		
		Parameters:
			search_label (str): Label of trace to return
		
		Returns:
			Matching Trace object, None if no matching trace is found
		"""
		
		# Scan over all traces
		for idx, tr in enumerate(self.traces.values()):
			
			# Return index if match
			if tr.label == search_label:
				return idx
		
		return None
		
class MetaInfo(Packable):
	
	def __init__(self, description:str="", conditions:dict={}, log:plf.LogPile=None):
		super().__init__(log)
		
		self.version = GRAF_VERSION
		self.source_language = "Python"
		self.source_library = "GrAF"
		self.source_version = "0.0.0"
		self.description = description
		self.conditions = conditions
	
	def set_manifest(self):
		self.manifest.append("version")
		self.manifest.append("source_language")
		self.manifest.append("source_library")
		self.manifest.append("source_version")
		self.manifest.append("description")
		self.manifest.append("conditions")
	
class Graf(Packable):
	""" Class used to read, write and extract data from GrAF files.
	"""
	
	def __init__(self, fig=None, description:str="", conditions:dict={}, log:plf.LogPile=None):
		super().__init__(log)
		
		self.style = GraphStyle(log=self.log)
		self.info = MetaInfo(description=description, conditions=conditions, log=self.log)
		self.supertitle = ""
		
		self.axes = {} # Has to be a dictinary so HDF knows how to handle it
		
		if fig is not None:
			self.mimic(fig)
	
	def set_manifest(self):
		self.obj_manifest.append("style")
		self.obj_manifest.append("info")
		self.manifest.append("supertitle")
		self.dict_manifest["axes"] = Axis(GraphStyle())
	
	def mimic(self, fig):
		''' Tells the Graf object to mimic the matplotlib figure as best as possible. '''
		
		print(self.log)
		print(self.log.terminal_level)
		self.log.debug(f"Mimicing figure {fig}")
		
		# self.style = ...
		# self.info = ...
		self.supertitle = str(fig.get_suptitle())
		
		#TODO: Determine where each subplot goes and what it's bounds are
		#can use Ax.get_gridspec() to get the object that defines stuff about the grid
		# can use ax.get_subplotspec() to get parameters about where the actual subplot sits. THIS is what I want.
		# ax.get_subplotspec().colspan and .rowspan will give a range() describing the span of the axes. It's weird but workable.
		# ax.get_
		
		# Find twin-axes and merge them here.
		sole_axes = [] # This is a list of axes
		twin_axes = [] # This is a list of lists of axes. Each sub-list contains a list of shared-axes
		for ax in fig.get_axes():
			
			# Check if axis is twinned
			if has_twinx(ax):
				self.log.lowdebug(f"Adding axis ({ax}) to twin-axes.")
				
				# Check if its the main or secondary axis - add to list accordingly
				if ax._sharex is None:
					# If primary - add to twins list
					twin_axes.append([ax])
				else:
					# Scan over twin axes lists
					for tals in twin_axes:
						if ax._sharex in tals:
							tals.append(ax)
			else:
				self.log.lowdebug(f"Adding axis ({ax}) to sole-axes.")
				
				# No twin - add to list
				sole_axes.append(ax)
		
		#TODO: Iterate over twin vs sole axes differently
		
		# Mimic all sole-axes
		self.axes = {}
		for idx, ax in enumerate(sole_axes):
			self.axes[f'Ax{idx}'] = Axis(self.style, ax, log=self.log)
		
		# Mimic all twin-axes
		idx_offset = len(self.axes)
		for idx, ax in enumerate(twin_axes):
			if len(ax) != 2:
				print(f"ERROR: Failed to properly identify twin axes. Skipping.")
				continue
			self.axes[f'Ax{idx+idx_offset}'] = Axis(self.style, ax[0], twin_ax=ax[1], log=self.log)
	
	def get_axis(self, axis_pos:tuple=(0,0)):
		'''
		Returns the Axis object at the specified position.
		
		Parameters:
			axis_pos (tuple): Position in (row, column) format of axis.
		
		Returns:
			Specified Axis object, or None if invalid position specified
		'''
		
		# Scan over axes
		for ax in self.axes.values():
			
			# Move on to next axis if either row or column misses box
			if ax.position[0] > axis_pos[0] or ax.position[0]+ax.span[0]-1 < axis_pos[0]:
				continue
			if ax.position[1] > axis_pos[1] or ax.position[1]+ax.span[1]-1 < axis_pos[1]:
				continue
		
			# Return axis
			return ax
		
		return None
	
	def get_trace(self, axis_pos:tuple=(0, 0), trace_idx:int=None, trace_label:str=None):
		
		# Get specified axis
		ax = self.get_axis(axis_pos)
		
		# If neither index nor label is specified, use idx=0
		if trace_idx is None and trace_label is None:
			trace_idx = 0
		
		# Get trace index from label
		if trace_label is not None:
			trace_idx = ax.get_trace_idx(trace_label)
		
		# Return trace
		try:
			return ax.traces[f'Tr{trace_idx}']
		except:
			return None
	
	def get_xdata(self, axis_pos:tuple=(0, 0), trace_idx:int=None, trace_label:str=None, use_np_array:bool=True):
		"""
		Returns the X-data of the specified trace on the specified axes.
		
		Parameters:
			axis_pos (tuple): Position in (row, column) format of axis
			trace_idx (int): Index of trace to access. Alternative to trace_label
			trace_label (str): Label of trace to access. Alternative to trace_idx
			use_np_array (bool): Return data in np array format
		
		Returns:
			X-data of specified trace
		"""
		
		# Get trace
		tr = self.get_trace(axis_pos=axis_pos, trace_idx=trace_idx, trace_label=trace_label)
		if tr is None:
			return None
		
		# Return data list
		if use_np_array:
			return np.array(tr.x_data)
		else:
			return list(tr.x_data)
		
	def get_ydata(self, axis_pos:tuple=(0, 0), trace_idx:int=None, trace_label:str=None, use_np_array:bool=True):
		"""
		Returns the X-data of the specified trace on the specified axes.
		
		Parameters:
			axis_pos (tuple): Position in (row, column) format of axis
			trace_idx (int): Index of trace to access. Alternative to trace_label
			trace_label (str): Label of trace to access. Alternative to trace_idx
			use_np_array (bool): Return data in np array format
		
		Returns:
			X-data of specified trace
		"""
		
		# Get trace
		tr = self.get_trace(axis_pos=axis_pos, trace_idx=trace_idx, trace_label=trace_label)
		if tr is None:
			return None
		
		# Return data list
		if use_np_array:
			return np.array(tr.y_data)
		else:
			return list(tr.y_data)
	
	def to_fig(self, window_title:str=None):
		''' Converts the Graf object to a matplotlib figure as best as possible.'''
		
		# TODO: Make the figure size/aspeect ratio set-able
		if window_title is None:
			gen_fig = plt.figure()
		else:
			print(window_title)
			gen_fig = plt.figure(window_title)
		
		gen_fig.suptitle(self.supertitle)
		
		# Check for empty graf
		if len(self.axes) == 0:
			return gen_fig
		
		# Determine grid size from subplots
		row_min = None
		row_max = None
		col_min = None
		col_max = None
		for axkey in self.axes.keys():
			print(axkey, flush=True)
			ax_size = self.axes[axkey].get_size()
			if row_min == None:
				row_min = ax_size[0]
				row_max = ax_size[2]
				col_min = ax_size[1]
				col_max = ax_size[3]
			else:
				row_min = np.min([ax_size[0], row_min])
				row_max = np.max([ax_size[2], row_max])
				col_min = np.min([ax_size[1], col_min])
				col_max = np.max([ax_size[3], col_max])
		
		# Make gridspec which can be used to assign subplot positions
		gs = GridSpec(row_max, col_max, figure=gen_fig)
		
		for axkey in self.axes.keys():
			
			# Get subplot slices to apply to gs object
			slc = self.axes[axkey].get_slice()
			
			# CHeck if axis should be 2d or 3d
			if self.axes[axkey].z_axis.is_valid: 
				# Create new axes, specifying position on GridSpec
				new_ax = gen_fig.add_subplot(gs[slc[0], slc[1]], projection='3d')
			else:
				# Create new axes, specifying position on GridSpec
				new_ax = gen_fig.add_subplot(gs[slc[0], slc[1]])
			
			# Check for twin axes
			if self.axes[axkey].y_axis_R.is_valid:
				new_ax_twin = new_ax.twinx()
				self.axes[axkey].apply_to(new_ax, self.style, twin_ax=new_ax_twin)
			else:
				self.axes[axkey].apply_to(new_ax, self.style)
		
		# Configure warnings to get caught like errors
		warnings.filterwarnings("error")
		try:
			gen_fig.tight_layout()
		except UserWarning as uw:
			self.log.warning(f"Tight layout was not applied.", detail=f"UserWarning: {uw}")
			
		# Reset warning handling to standard
		warnings.resetwarnings()
		
		# Return newly created figure
		return gen_fig
	
	def save_hdf(self, filename:str):
		datapacket = self.pack()
		# print(datapacket)
		dict_summary(datapacket, verbose=1) #TODO: Make this a flag
		dict_to_hdf(datapacket, filename, show_detail=False)
	
	def load_hdf(self, filename:str):
		datapacket = hdf_to_dict(filename)
		self.unpack(datapacket)

def write_pfig(figure, file_handle): #:matplotlib.figure.Figure, file_handle):
	''' Writes the contents of a matplotlib figure to a pfig file. '''
	
	pickle.dump(figure, file_handle)

def write_GrAF(figure, file_handle, description:str="", conditions:dict={}):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	temp_graf = Graf(figure, description=description, conditions=conditions)
	temp_graf.save_hdf(file_handle)

def read_GrAF(file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	temp_graf = Graf()
	temp_graf.load_hdf(file_handle)
	return temp_graf.to_fig()

# def write_json_GrAF(figure, file_handle):
# 	''' Writes the contents of a matplotlib figure to a GrAF file. '''
# 	pass
