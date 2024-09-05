import h5py
import pickle
import matplotlib
import matplotlib.pyplot as plt

GRAF_VERSION = "0.0.0"
LINE_TYPES = ["-", "-.", ":", "--", "None"]
MARKER_TYPES = [".", "+", "^", "v", "o", "x", "[]", "None"]

def hexstr_to_rgb(hexstr:str):
	''' Credit: https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python John1024'''
	hexstr = hexstr.lstrip('#')
	return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

class Font:
	
	def __init__(self):
		
		self.size = 12
		self.font = "./assets/SUSE"
		self.bold = False
		self.italic = False

class Style:
	''' Represents style parameters for the graph.'''
	def __init__(self):
		
		self.supertitle_font = Font()
		self.title_font = Font()
		self.graph_font = Font()
		self.label_font = Font()

class Trace:
	''' Represents a trace that can be displayed on a set of axes'''
	def __init__(self, mpl_line=None):
		
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
		self.color = hexstr_to_rgb(mpl_line.get_color())
		self.x_data = mpl_line.get_xdata()
		self.y_data = mpl_line.get_ydata()
		# self.z_data = []
		
		# Get line type
		self.line_type = mpl_line.get_linestyle()
		if self.line_type not in LINE_TYPES:
			self.line_type = LINE_TYPES[0]
		
		# Get marker
		self.marker_type = mpl_line.get_marker()
		if self.marker_type == None:
			self.marker_type = "None"
		if self.marker_type not in MARKER_TYPES:
			self.marker_type = MARKER_TYPES[0]
		
		#TODO: Normalize these to one somehow?
		self.marker_size = mpl_line.get_markersize()
		self.line_width = mpl_line.get_linewidth()
		self.display_name = mpl_line.get_label()

class Scale:
	''' Defines a singular axis/scale such as an x-axis.'''
	
	SCALE_ID_X = 0
	SCALE_ID_Y = 1
	SCALE_ID_Z = 2
	
	def __init__(self, ax=None, scale_id:int=SCALE_ID_X):
		self.val_min = 0
		self.val_max = 1
		self.tick_list = []
		self.minor_tick_list = []
		self.tick_label_list = []
		self.label = ""
		
		if ax is not None:
			self.mimic(ax, scale_id)
	
	def mimic(self, ax, scale_id:int):
		
		if scale_id == Scale.SCALE_ID_X:
			xlim_tuple = ax.get_xlim()
			self.val_min = xlim_tuple[0]
			self.val_max = xlim_tuple[1]
			self.tick_list = ax.get_xticks()
			self.minor_tick_list = []
			self.tick_label_list = ax.get_xticklabels()
			self.label = ax.get_xlabel()
		
		elif scale_id == Scale.SCALE_ID_Y:
			ylim_tuple = ax.get_ylim()
			self.val_min = ylim_tuple[0]
			self.val_max = ylim_tuple[1]
			self.tick_list = ax.get_yticks()
			self.minor_tick_list = []
			self.tick_label_list = ax.get_yticklabels()
			self.label = ax.get_ylabel()
	
	def apply_to(self, ax, scale_id:int):
		
		if scale_id == Scale.SCALE_ID_X:
			ax.set_xlim([self.val_min, self.val_max])
			ax.set_xticks(self.tick_list)
			ax.set_xticklabels(self.tick_label_list)
			ax.set_xlabel(self.label)
		
		elif scale_id == Scale.SCALE_ID_Y:
			ax.set_ylim([self.val_min, self.val_max])
			ax.set_yticks(self.tick_list)
			ax.set_yticklabels(self.tick_label_list)
			ax.set_ylabel(self.label)
			
class Axis:
	'''' Defines a set of axes, including the x-y-(z), grid lines, etc.'''
	
	def __init__(self, ax=None): #:matplotlib.axes._axes.Axes=None):
		self.relative_size = []
		self.x_axis = Scale()
		self.y_axis_L = Scale()
		self.y_axis_R = None
		self.z_axis = None
		self.grid_on = False
		self.traces = []
		self.title = ""
		
		# Initialize with axes if possible
		if ax is not None:
			self.mimic(ax)
	
	def mimic(self, ax):
		print(ax)
		
		# self.relative_size = []
		self.x_axis = Scale(ax, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L = Scale(ax, scale_id=Scale.SCALE_ID_Y)
		# self.y_axis_R = None #TODO: How does MPL handle this?
		if hasattr(ax, 'get_zlim'):
			self.z_axis = Scale()
		else:
			self.z_axis = None
		self.grid_on = ax.xaxis.get_gridlines()[0].get_visible()
		# self.traces = []
		
		for mpl_trace in ax.lines:
			self.traces.append(Trace(mpl_trace))
		
		self.title = ax.get_title()
	
	def apply_to(self, ax):
		
		# self.relative_size = []
		self.x_axis.apply_to(ax, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L.apply_to(ax, scale_id=Scale.SCALE_ID_Y)
		# self.y_axis_R = None
		# self.z_axis = None
		ax.grid(self.grid_on)
		# self.traces = []
		ax.set_title(self.title)
		
		
		
class MetaInfo:
	
	def __init__(self):
		self.version = GRAF_VERSION
		self.source_language = "Python"
		self.source_library = "GrAF"

class Graf:
	
	def __init__(self, fig=None):
		
		self.style = Style()
		self.info = MetaInfo()
		self.supertitle = ""
		
		self.axes = []
		
		if fig is not None:
			self.mimic(fig)
	
	def mimic(self, fig):
		''' Tells the Graf object to mimic the matplotlib figure as best as possible. '''
		
		# self.style = ...
		# self.info = ...
		self.supertitle = fig.get_suptitle()
		
		self.axes = []
		for ax in fig.get_axes():
			self.axes.append(Axis(ax))
	
	
	def to_fig(self):
		''' Converts the Graf object to a matplotlib figure as best as possible.'''
		
		gen_fig = plt.figure()
		
		gen_fig.suptitle(self.supertitle)
		
		for ax in self.axes:
			new_ax = gen_fig.add_subplot()
			
			ax.apply_to(new_ax)

def write_pfig(figure, file_handle): #:matplotlib.figure.Figure, file_handle):
	''' Writes the contents of a matplotlib figure to a pfig file. '''
	
	pickle.dump(figure, file_handle)

def write_GrAF(figure, file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	pass
	
def write_json_GrAF(figure, file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	pass