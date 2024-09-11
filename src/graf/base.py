import h5py
import pickle
import matplotlib
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from jarnsaxa import hdf_to_dict, dict_to_hdf
from pylogfile.base import *
import copy
from ganymede import dict_summary
import matplotlib.font_manager as fm
import os

logging = LogPile()

GRAF_VERSION = "0.0.0"
LINE_TYPES = ["-", "-.", ":", "--", "None"]
MARKER_TYPES = [".", "+", "^", "v", "o", "x", "[]", "None"]
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
	
	def __init__(self):
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
			d[mi] = getattr(self, mi).pack()
		
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
			# Try to assign the new value
			try:
				setattr(self, mi, data[mi])
			except Exception as e:
				logging.error(f"Failed to unpack item in object of type '{type(self).__name__}'. ({e})")
				return
		
		# Try to populate each Packable object in manifest
		for mi in self.obj_manifest:
			# Try to update the object by unpacking the item
			try:
				getattr(self, mi).unpack(data[mi])
			except Exception as e:
				logging.error(f"Failed to unpack Packable in object of type '{type(self).__name__}'. ({e})")
				return
			
		# Try to populate each list of Packable objects in manifest
		for mi in self.list_manifest.keys():
				
			# Scan over list, unpacking each element
			temp_list = []
			for list_item in data[mi]:
				# Try to create a new object and unpack a list element
				try:
					# Create a new object of the correct type
					new_obj = copy.deepcopy(self.list_manifest[mi])
					
					# Populate the new object by unpacking it, add to list
					new_obj.unpack(list_item)
					temp_list.append(new_obj)
				except Exception as e:
					logging.error(f"Failed to unpack list of Packables in object of type '{type(self).__name__}'. ({e})")
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
				# Try to create a new object and unpack a list element
				try:
					# Create a new object of the correct type
					new_obj = copy.deepcopy(self.dict_manifest[mi])
					
					# Populate the new object by unpacking it, add to list
					new_obj.unpack(data[mi][dmk])
					temp_dict[dmk] = new_obj
				except Exception as e:
					logging.error(f"Failed to unpack dict of Packables in object of type '{type(self).__name__}'. ({e})")
					return
			setattr(self, mi, temp_dict)

class Font(Packable):
	
	def __init__(self):
		super().__init__()
		
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
	def __init__(self):
		super().__init__()
		
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
	
class Trace(Packable):
	''' Represents a trace that can be displayed on a set of axes'''
	def __init__(self, mpl_line=None):
		super().__init__()
		
		self.use_yaxis_L = False
		self.color = (1, 0, 0)
		self.x_data = []
		self.y_data = []
		self.z_data = []
		self.line_type = LINE_TYPES[0]
		self.marker_type = MARKER_TYPES[0]
		self.marker_size = 1
		self.line_width = 1
		self.display_name = ""
		
		if mpl_line is not None:
			self.mimic(mpl_line)
	
	def mimic(self, mpl_line):
	
		# self.use_yaxis_L = False
		if type(mpl_line.get_color()) == tuple:
			self.color = mpl_line.get_color()
		else:
			self.color = hexstr_to_rgb(mpl_line.get_color())
		self.x_data = [float(x) for x in mpl_line.get_xdata()]
		self.y_data = [float(x) for x in mpl_line.get_ydata()]
		# self.z_data = []
		
		# Get line type
		self.line_type = mpl_line.get_linestyle()
		if self.line_type not in LINE_TYPES:
			self.line_type = LINE_TYPES[0]
		
		# Get marker
		mpl_marker_code = mpl_line.get_marker()
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
		
		#TODO: Error check line type, marker type, and sizes
		
		ax.add_line(matplotlib.lines.Line2D(self.x_data, self.y_data, linewidth=self.line_width, linestyle=self.line_type, color=self.color, marker=self.marker_type, markersize=self.marker_size, label=self.display_name))
	
	def set_manifest(self):
		self.manifest.append("use_yaxis_L")
		self.manifest.append("color")
		self.manifest.append("x_data")
		self.manifest.append("y_data")
		self.manifest.append("z_data")
		self.manifest.append("line_type")
		self.manifest.append("marker_type")
		self.manifest.append("marker_size")
		self.manifest.append("line_width")
		self.manifest.append("display_name")
	
class Scale(Packable):
	''' Defines a singular axis/scale such as an x-axis.'''
	
	SCALE_ID_X = 0
	SCALE_ID_Y = 1
	SCALE_ID_Z = 2
	
	def __init__(self, gs:GraphStyle, ax=None, scale_id:int=SCALE_ID_X):
		super().__init__()
		
		# Pointer to Graf object's GraphStyle - so fonts can be appropriately initialized
		self.gs = gs
		
		self.is_valid = False # Used so when axes aren't used (ex. Z-axis in 2D plot), GrAF knows to ignore this object. Using None isn't an option because HDF doesn't support NoneTypes.
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
	
	def apply_to(self, ax, gstyle:GraphStyle, scale_id:int):
		
		self.gs = gstyle
		
		local_font = self.gs.label_font.to_tuple()
		
		if scale_id == Scale.SCALE_ID_X:
			ax.set_xlim([self.val_min, self.val_max])
			ax.set_xticks(self.tick_list)
			ax.set_xticklabels(self.tick_label_list)
			
			if local_font is not None:
				ax.set_xlabel(self.label, fontproperties=local_font[0], size=local_font[1])
			else:
				ax.set_xlabel(self.label)
				
		elif scale_id == Scale.SCALE_ID_Y:
			ax.set_ylim([self.val_min, self.val_max])
			ax.set_yticks(self.tick_list)
			ax.set_yticklabels(self.tick_label_list)
			
			if local_font is not None:
				ax.set_ylabel(self.label, fontproperties=local_font[0], size=local_font[1])
			else:
				ax.set_ylabel(self.label)
			
class Axis(Packable):
	'''' Defines a set of axes, including the x-y-(z), grid lines, etc.'''
	
	def __init__(self, gs:GraphStyle, ax=None): #:matplotlib.axes._axes.Axes=None):
		super().__init__()
		
		self.gs = gs
		
		self.relative_size = []
		self.x_axis = Scale(gs)
		self.y_axis_L = Scale(gs)
		self.y_axis_R = Scale(gs)
		self.z_axis = Scale(gs)
		self.grid_on = False
		self.traces = {}
		self.title = ""
		
		# Initialize with axes if possible
		if ax is not None:
			self.mimic(ax)
	
	def set_manifest(self):
		self.manifest.append("relative_size")
		self.obj_manifest.append("x_axis")
		self.obj_manifest.append("y_axis_L")
		self.obj_manifest.append("y_axis_R")
		self.obj_manifest.append("z_axis")
		self.manifest.append("grid_on")
		self.dict_manifest["traces"] = Trace()
		self.manifest.append("title")
	
	def mimic(self, ax):
		
		# self.relative_size = []
		self.x_axis = Scale(self.gs, ax, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L = Scale(self.gs, ax, scale_id=Scale.SCALE_ID_Y)
		# self.y_axis_R = None #TODO: How does MPL handle this?
		if hasattr(ax, 'get_zlim'):
			self.z_axis = Scale(self.gs)
		else:
			self.z_axis = Scale(self.gs)
		self.grid_on = ax.xaxis.get_gridlines()[0].get_visible()
		# self.traces = []
		
		for idx, mpl_trace in enumerate(ax.lines):
			self.traces[f'Tr{idx}'] = Trace(mpl_trace)
		
		self.title = str(ax.get_title())
	
	def apply_to(self, ax, gstyle:GraphStyle):
		
		self.gs = gstyle
		
		# self.relative_size = []
		self.x_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Y)
		# self.y_axis_R = None
		# self.z_axis = None
		ax.grid(self.grid_on)
		
		for tr in self.traces.keys():
			self.traces[tr].apply_to(ax, self.gs)
		
		print(self.gs.title_font.font)
		local_font = self.gs.title_font.to_tuple()
		if local_font is not None:
			ax.set_title(self.title, fontproperties=local_font[0], size=local_font[1])
		else:
			ax.set_title(self.title)
		
class MetaInfo(Packable):
	
	def __init__(self):
		super().__init__()
		
		self.version = GRAF_VERSION
		self.source_language = "Python"
		self.source_library = "GrAF"
		self.source_version = "0.0.0"
	
	def set_manifest(self):
		self.manifest.append("version")
		self.manifest.append("source_language")
		self.manifest.append("source_library")
		self.manifest.append("source_version")
	
class Graf(Packable):
	
	def __init__(self, fig=None):
		super().__init__()
		
		self.style = GraphStyle()
		self.info = MetaInfo()
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
		
		# self.style = ...
		# self.info = ...
		self.supertitle = str(fig.get_suptitle())
		
		self.axes = {}
		for idx, ax in enumerate(fig.get_axes()):
			self.axes[f'Ax{idx}'] = Axis(self.style, ax)
	
	
	def to_fig(self):
		''' Converts the Graf object to a matplotlib figure as best as possible.'''
		
		gen_fig = plt.figure()
		
		gen_fig.suptitle(self.supertitle)
		
		for axkey in self.axes.keys():
			new_ax = gen_fig.add_subplot()
			
			self.axes[axkey].apply_to(new_ax, self.style)
	
	def save_hdf(self, filename:str):
		datapacket = self.pack()
		# print(datapacket)
		# dict_summary(datapacket)
		dict_to_hdf(datapacket, filename, show_detail=False)
	
	def load_hdf(self, filename:str):
		datapacket = hdf_to_dict(filename)
		self.unpack(datapacket)

def write_pfig(figure, file_handle): #:matplotlib.figure.Figure, file_handle):
	''' Writes the contents of a matplotlib figure to a pfig file. '''
	
	pickle.dump(figure, file_handle)

def write_GrAF(figure, file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	temp_graf = Graf(figure)
	temp_graf.save_hdf(file_handle)

def read_GrAF(file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	temp_graf = Graf()
	temp_graf.load_hdf(file_handle)
	return temp_graf.to_fig()
	
# def write_json_GrAF(figure, file_handle):
# 	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
# 	pass