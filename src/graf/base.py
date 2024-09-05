import h5py
import pickle
import matplotlib

GRAF_VERSION = "0.0.0"
LINE_TYPES = ["-", "-.", ":", "--", "None"]
MARKER_TYPES = [".", "+", "^", "v", "o", "x", "[]", "None"]

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
	def __init__(self):
		
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

class Scale:
	''' Defines a singular axis/scale such as an x-axis.'''
	
	def __init__(self):
		self.val_min = 0
		self.val_max = 1
		self.tick_list = []
		self.minor_tick_list = []
		self.tick_label_list = []
		self.label = ""
	
	def mimic(self, ax):
		
		xlim_tuple = ax.get_xlim()
		self.val_min = xlim_tuple[0]
		self.val_max = xlim_tuple[1]

class Axis:
	'''' Defines a set of axes, including the x-y-(z), grid lines, etc.'''
	
	def __init__(self, ax:matplotlib.axes._axes.Axes=None):
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
		pass
		# self.relative_size = []
		# self.x_axis = Scale()
		# self.y_axis_L = Scale()
		# self.y_axis_R = None
		# self.z_axis = None
		# self.grid_on = False
		# self.traces = []
		# self.title = ""
	
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
		

def write_pfig(figure:matplotlib.figure.Figure, file_handle):
	''' Writes the contents of a matplotlib figure to a pfig file. '''
	
	pickle.dump(figure, file_handle)

def write_GrAF(figure, file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	pass
	
def write_json_GrAF(figure, file_handle):
	''' Writes the contents of a matplotlib figure to a GrAF file. '''
	
	pass