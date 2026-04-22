import h5py
import json
import pickle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from abc import ABC, abstractmethod
from jarnsaxa import hdf_to_dict, dict_to_hdf, Packable
import pylogfile.base as plf
from ganymede import dict_summary
import matplotlib.font_manager as fm
import os
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import mpl_toolkits.mplot3d as mpl3d
from matplotlib.collections import QuadMesh
from matplotlib.image import AxesImage
from matplotlib.container import ErrorbarContainer
import warnings
import numpy as np
from colorama import Fore, Style

## TODO:
# 1. Add error bars or shading support
# 2. Add alpha to color specification
# 3. Add 3D support (lines)       -- DONE
# 4. Add 3D support (surface)     -- DONE
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

def sample_colormap(cmap_name:str=None, listed_cmap:mcolors.ListedColormap=None, N:int=20, trim_in:tuple=None):
	''' Discretizes a colormap, returning a list of rgb lists from the provided
	colormap.
	
	Args:
		cmap_name: Name of a standard matplotlib colormap
		listed_cmap: Matplotlib ListedColormap object. If provided, cmap_name is
			ignored.
		N: The number of colors to break the colormap into.
		trim_in: Optional tuple that trims the colormap inwards to eliminate the 
			extremes of the colormap. Format: (Number of samples to add to N, number of samples to 
			move in from the lower end). For example, if N is 5, you could send the tuple (2, 1) which
			would use 7 samples and eliminate the exteme most point on either edge. Or you could use
			(2, 2) to use 7 samples, keep the upper most extreme, but eliminate the lower two most
			extreme points.
	
	Returns:
		The list of rgb lists representing the provided colormap.
	'''
	
	# Check for trim conditions
	if trim_in is not None:
		
		try:
			
			# Validate trim_in data
			if trim_in[1] > trim_in[0]:
				trim_in = None
			elif trim_in[1] < 0:
				trim_in = None
			else:
				
				# Get cmap with additional steps
				cm = sample_colormap(cmap_name=cmap_name, listed_cmap=listed_cmap, N=N+trim_in[0])
				return cm[trim_in[1]:trim_in[1]+N]
		except:
			# Invalid tuple, skip
			trim_in = None
			pass 
	
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

class AutoColorMap:
	
	def __init__(self, color_data:list, N, log:plf.LogPile):
		
		self.N = N
		self.color_data = color_data
		
		self.idx = 0
		
		self.log = log
	
	def __call__(self):
		try:
			cd = self.color_data[self.idx]
			self.idx += 1
			if self.idx >= self.N:
				self.idx = 0
				self.log.debug(f"Colormap auto-reset.")
		except:
			self.idx = 0
			cd = (0, 0, 0)
		
		return cd
	
	def reset(self):
		self.idx = 0

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

def _parse_marker(mpl_marker_code) -> str:
	''' Converts a matplotlib marker code to a GrAF marker type string. '''
	if mpl_marker_code is None:
		return 'None'
	code = str(mpl_marker_code).lower()
	match code:
		case '.': return '.'
		case '+': return '+'
		case '^': return '^'
		case 'v': return 'v'
		case 's': return '[]'
		case 'o': return 'o'
		case 'none': return 'None'
		case '*': return '*'
		case '_': return '_'
		case '|': return '|'
		case 'x': return 'x'
		case _: return '.'

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

		self.has_colorbar = False
		self.colorbar_label = ""
		self.colorbar_orientation = "vertical"
		self.colorbar_ticks = []
		self.colorbar_tick_labels = []

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
	
	def _mimic_colorbar(self, mpl_source):
		''' Captures colorbar properties if the mappable has an associated colorbar. '''
		cb = getattr(mpl_source, 'colorbar', None)
		if cb is None:
			return
		self.has_colorbar = True
		self.colorbar_orientation = cb.orientation
		if cb.orientation == 'vertical':
			self.colorbar_label = cb.ax.get_ylabel()
			self.colorbar_tick_labels = [t.get_text() for t in cb.ax.get_yticklabels()]
		else:
			self.colorbar_label = cb.ax.get_xlabel()
			self.colorbar_tick_labels = [t.get_text() for t in cb.ax.get_xticklabels()]
		try:
			self.colorbar_ticks = [float(t) for t in cb.get_ticks()]
		except Exception:
			self.colorbar_ticks = []

	def _mimic_quadmesh(self, mpl_source):

		self.surf_type = Surface.SURF_IMAGE
		self.line_type = "None"

		# _coordinates has shape (M+1, N+1, 2): the corner positions of every quad cell.
		# Storing corners directly supports both uniform and non-uniform grids.
		coords = mpl_source._coordinates
		x_corners = coords[:, :, 0]  # (M+1, N+1)
		y_corners = coords[:, :, 1]  # (M+1, N+1)

		# A grid is uniform when x varies only with column and y only with row
		self.uniform_grid = (
			np.allclose(x_corners, x_corners[0:1, :]) and
			np.allclose(y_corners, y_corners[:, 0:1])
		)

		# Store corners — pcolormesh accepts (M+1)×(N+1) corner arrays directly
		self.x_grid = x_corners.tolist()
		self.y_grid = y_corners.tolist()
		self.z_grid = mpl_source.get_array().tolist()

		# Alpha
		self.alpha = mpl_source.get_alpha()
		if self.alpha is None:
			self.alpha = 1

		# Colormap
		self.cmap = sample_colormap(mpl_source.get_cmap(), N=30)

		# Colorbar
		self._mimic_colorbar(mpl_source)
	
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
		
		# Alpha
		self.alpha = mpl_source.get_alpha()
		if self.alpha is None:
			self.alpha = 1

		# Colormap
		self.cmap = sample_colormap(mpl_source.get_cmap(), N=30)

		# Colorbar
		self._mimic_colorbar(mpl_source)

	def mimic_poly3d(self, mpl_source):
		''' Mimics a matplotlib Poly3DCollection (produced by ax.plot_surface()).

		Reconstructs the original X/Y/Z grid by collecting all polygon vertices and
		finding unique X and Y coordinate values. This assumes the surface was created
		from a meshgrid-style input (the standard use case for plot_surface).
		'''

		self.surf_type = Surface.SURF_SURFACE

		# Extract all vertex coordinates. The internal storage format changed in
		# matplotlib 3.9: older versions used _segments3d (list of per-face arrays),
		# newer versions use _vec (4 x n_verts homogeneous matrix, rows = x, y, z, 1).
		if hasattr(mpl_source, '_vec') and hasattr(mpl_source, '_segslices'):
			# mpl >= 3.9: _vec rows are (x, y, z, 1), columns are all verts concatenated
			all_verts = mpl_source._vec[:3, :].T  # shape (n_verts, 3)
		elif hasattr(mpl_source, '_segments3d'):
			# mpl < 3.9: list of per-face vertex arrays
			all_verts = np.vstack([np.asarray(s) for s in mpl_source._segments3d])
		else:
			raise AttributeError(
				"Cannot extract vertex data from Poly3DCollection: "
				"neither '_vec' nor '_segments3d' attribute found. "
				"Unsupported matplotlib version."
			)

		# Unique x and y values define the two grid axes
		unique_x = np.unique(np.round(all_verts[:, 0], 8))
		unique_y = np.unique(np.round(all_verts[:, 1], 8))
		ncols = len(unique_x)
		nrows = len(unique_y)

		# Build fast index lookups: coordinate value → grid index
		x_to_idx = {round(float(x), 8): i for i, x in enumerate(unique_x)}
		y_to_idx = {round(float(y), 8): i for i, y in enumerate(unique_y)}

		# Walk every vertex and fill the Z grid
		Z_grid = np.full((nrows, ncols), np.nan)
		for vx, vy, vz in all_verts:
			xi = x_to_idx[round(float(vx), 8)]
			yi = y_to_idx[round(float(vy), 8)]
			Z_grid[yi, xi] = vz

		X_grid, Y_grid = np.meshgrid(unique_x, unique_y)
		self.uniform_grid = True
		self.x_grid = X_grid.tolist()
		self.y_grid = Y_grid.tolist()
		self.z_grid = Z_grid.tolist()

		# Colormap
		try:
			self.cmap = sample_colormap(mpl_source.get_cmap(), N=30)
		except Exception:
			self.cmap = sample_colormap('viridis', N=30)

		# Alpha
		self.alpha = mpl_source.get_alpha()
		if self.alpha is None:
			self.alpha = 1

		# Edge color (may be empty/broadcast for plot_surface defaults)
		try:
			ec = mpl_source.get_edgecolor()
			if ec is not None and len(ec) > 0:
				self.line_color = tuple(float(c) for c in np.asarray(ec[0])[:3])
		except Exception:
			pass

		# Edge line width
		try:
			lw = mpl_source.get_linewidth()
			self.line_width = float(lw[0]) if hasattr(lw, '__len__') else float(lw)
		except Exception:
			pass

		# Colorbar
		self._mimic_colorbar(mpl_source)

	def apply_to(self, ax, gstyle:GraphStyle):
		''' Applies this surface to the given axes. Returns the matplotlib mappable
		so the caller can attach a colorbar if needed. '''

		self.gs = gstyle

		if self.surf_type == Surface.SURF_IMAGE:
			return self._apply_to_image(ax)
		elif self.surf_type == Surface.SURF_SURFACE:
			return self._apply_to_surface(ax)
		else:
			self.log.error(f"Surface.apply_to(): Unrecognized surface type {self.surf_type}")
			return None

	def _apply_to_image(self, ax):
		x = np.array(self.x_grid)
		y = np.array(self.y_grid)
		z = np.array(self.z_grid)
		cmap = mcolors.ListedColormap(self.cmap)
		# shading='auto' correctly handles both old .graf files (center coordinates,
		# x.shape == z.shape) and new ones (corner coordinates, x.shape == z.shape+1)
		return ax.pcolormesh(x, y, z, cmap=cmap, shading='auto', alpha=self.alpha, antialiased=self.antialias)

	def _apply_to_surface(self, ax):
		''' Reconstructs a 3D surface via ax.plot_surface(). '''

		X = np.array(self.x_grid)
		Y = np.array(self.y_grid)
		Z = np.array(self.z_grid)
		cmap = mcolors.ListedColormap(self.cmap)
		return ax.plot_surface(X, Y, Z, cmap=cmap, alpha=self.alpha, linewidth=self.line_width)

	def apply_colorbar(self, fig, mappable, parent_ax):
		''' Attaches a colorbar to the figure using the stored colorbar properties. '''
		if not self.has_colorbar or mappable is None:
			return
		cb = fig.colorbar(mappable, ax=parent_ax, orientation=self.colorbar_orientation)
		if self.colorbar_orientation == 'vertical':
			cb.ax.set_ylabel(self.colorbar_label)
		else:
			cb.ax.set_xlabel(self.colorbar_label)
		if self.colorbar_ticks:
			cb.set_ticks(self.colorbar_ticks)
	
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

		self.manifest.append("has_colorbar")
		self.manifest.append("colorbar_label")
		self.manifest.append("colorbar_orientation")
		self.manifest.append("colorbar_ticks")
		self.manifest.append("colorbar_tick_labels")

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

		# Error bar fields
		self.has_error_bars = False
		self.x_err_neg = []
		self.x_err_pos = []
		self.y_err_neg = []
		self.y_err_pos = []
		self.err_line_color = (0.5, 0.5, 0.5)
		self.err_line_width = 1.0
		self.err_cap_size = 3.0
		self.err_cap_color = (0.5, 0.5, 0.5)
		self.err_cap_width = 1.0
		self.err_cap_visible = True

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
		self.marker_type = _parse_marker(mpl_line.get_marker())
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
		self.marker_type = _parse_marker(mpl_line.get_marker())
		if self.marker_type not in MARKER_TYPES:
			self.marker_type = MARKER_TYPES[0]

		#TODO: Normalize these to one somehow?
		self.marker_size = mpl_line.get_markersize()
		self.line_width = mpl_line.get_linewidth()
		self.display_name = str(mpl_line.get_label())
	
	def mimic_errorbar(self, container: ErrorbarContainer, use_twin: bool = False):
		''' Extracts data and styling from a matplotlib ErrorbarContainer. '''
		self.trace_type = Trace.TRACE_LINE2D
		self.has_error_bars = True
		self.use_yaxis_R = use_twin

		plotline, caplines, barlinecols = container.lines

		# Label lives on the container, not the plotline
		self.display_name = str(container.get_label())

		# fmt='none' yields plotline=None; fall back to defaults in that case
		if plotline is not None:
			self.x_data = [float(x) for x in plotline.get_xdata()]
			self.y_data = [float(y) for y in plotline.get_ydata()]
			self.z_data = []
			self.line_color = mcolors.to_rgb(plotline.get_color())
			self.alpha = plotline.get_alpha() or 1.0
			self.marker_color = mcolors.to_rgb(plotline.get_markerfacecolor())
			self.line_type = plotline.get_linestyle()
			if self.line_type not in LINE_TYPES:
				self.line_type = LINE_TYPES[0]
			self.marker_type = _parse_marker(plotline.get_marker())
			self.marker_size = float(plotline.get_markersize())
			self.line_width = float(plotline.get_linewidth())
		else:
			# Recover x/y from bar line segments when there is no plotline
			x_vals, y_vals = [], []
			for lc in barlinecols:
				for seg in lc.get_segments():
					cx = (seg[0][0] + seg[1][0]) / 2
					cy = (seg[0][1] + seg[1][1]) / 2
					x_vals.append(cx)
					y_vals.append(cy)
			self.x_data = sorted(set(round(v, 10) for v in x_vals))
			self.y_data = []  # cannot reliably recover y without plotline
			self.z_data = []
			self.line_type = 'None'
			self.marker_type = 'None'

		# Recover per-point error values from bar line collections.
		# When plotline is None (e.g. fmt='none') y_data is empty so skip.
		x_arr = np.array(self.x_data)
		y_arr = np.array(self.y_data)
		n = len(x_arr)
		if n == 0 or len(y_arr) == 0:
			return
		y_err_neg = np.zeros(n)
		y_err_pos = np.zeros(n)
		x_err_neg = np.zeros(n)
		x_err_pos = np.zeros(n)

		for lc in barlinecols:
			self.err_line_color = mcolors.to_rgb(lc.get_colors()[0])
			self.err_line_width = float(np.ravel(lc.get_linewidths())[0])
			for seg in lc.get_segments():
				x0, y0 = seg[0]
				x1, y1 = seg[1]
				if abs(x1 - x0) < abs(y1 - y0):
					# Vertical segment → y-error bar; match by nearest x
					ci = int(np.argmin(np.abs(x_arr - (x0 + x1) / 2)))
					cy = y_arr[ci]
					y_err_neg[ci] = cy - min(y0, y1)
					y_err_pos[ci] = max(y0, y1) - cy
				else:
					# Horizontal segment → x-error bar; match by nearest y
					ci = int(np.argmin(np.abs(y_arr - (y0 + y1) / 2)))
					cx = x_arr[ci]
					x_err_neg[ci] = cx - min(x0, x1)
					x_err_pos[ci] = max(x0, x1) - cx

		self.x_err_neg = x_err_neg.tolist()
		self.x_err_pos = x_err_pos.tolist()
		self.y_err_neg = y_err_neg.tolist()
		self.y_err_pos = y_err_pos.tolist()

		# Cap properties — capthick sets markeredgewidth, not linewidth
		if caplines:
			cap = caplines[0]
			self.err_cap_color = mcolors.to_rgb(cap.get_color())
			self.err_cap_width = float(cap.get_markeredgewidth())
			# matplotlib stores capsize as markersize = 2 × capsize, so halve it
			# so that apply_to_errorbar can pass it back as capsize= directly
			self.err_cap_size = float(cap.get_markersize()) / 2.0
			self.err_cap_visible = bool(cap.get_visible())
		else:
			self.err_cap_size = 0.0
			self.err_cap_visible = False

	def apply_to(self, ax, gstyle:GraphStyle):
		self.gs = gstyle

		if self.trace_type == Trace.TRACE_LINE2D:
			if self.has_error_bars:
				self.apply_to_errorbar(ax)
			else:
				self.apply_to_2dline(ax)
		elif self.trace_type == Trace.TRACE_LINE3D:
			self.apply_to_3dline(ax)
		else:
			self.warning(f"Unable to apply type: {self.trace_type}. Skipping.")
			return
	
	def apply_to_2dline(self, ax):

		#TODO: Error check line type, marker type, and sizes

		ax.add_line(matplotlib.lines.Line2D(self.x_data, self.y_data, linewidth=self.line_width, linestyle=self.line_type, color=self.line_color, marker=self.marker_type, markersize=self.marker_size, markerfacecolor=self.marker_color, label=self.display_name, alpha=self.alpha))

	def apply_to_errorbar(self, ax):
		''' Reconstructs an errorbar plot from stored data and styling. '''
		x = np.array(self.x_data)
		y = np.array(self.y_data)

		y_err_neg = np.array(self.y_err_neg)
		y_err_pos = np.array(self.y_err_pos)
		x_err_neg = np.array(self.x_err_neg)
		x_err_pos = np.array(self.x_err_pos)

		yerr = np.vstack([y_err_neg, y_err_pos]) if np.any(y_err_neg > 0) or np.any(y_err_pos > 0) else None
		xerr = np.vstack([x_err_neg, x_err_pos]) if np.any(x_err_neg > 0) or np.any(x_err_pos > 0) else None

		# Convert GrAF marker '[]' back to matplotlib 's'
		mpl_marker = 's' if self.marker_type == '[]' else self.marker_type

		ax.errorbar(
			x, y,
			yerr=yerr,
			xerr=xerr,
			fmt=mpl_marker,
			linestyle=self.line_type,
			linewidth=self.line_width,
			color=self.line_color,
			alpha=self.alpha,
			markerfacecolor=self.marker_color,
			markersize=self.marker_size,
			label=self.display_name,
			ecolor=self.err_line_color,
			elinewidth=self.err_line_width,
			capsize=self.err_cap_size,
			capthick=self.err_cap_width,
		)

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

		self.manifest.append("has_error_bars")
		self.manifest.append("x_err_neg")
		self.manifest.append("x_err_pos")
		self.manifest.append("y_err_neg")
		self.manifest.append("y_err_pos")
		self.manifest.append("err_line_color")
		self.manifest.append("err_line_width")
		self.manifest.append("err_cap_size")
		self.manifest.append("err_cap_color")
		self.manifest.append("err_cap_width")
		self.manifest.append("err_cap_visible")
	
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

		# Only treat as surface/image when real raster/mesh collections are present.
		# LineCollection objects (e.g. from ax.errorbar) live in ax.collections but
		# belong to line-type axes, so they are excluded from this check.
		has_real_surface = any(isinstance(c, (QuadMesh, Poly3DCollection)) for c in ax.collections)

		if has_real_surface or len(ax.images) > 0:
			# Distinguish a 3D surface (Poly3DCollection) from a 2D image/pcolormesh
			if any(isinstance(c, Poly3DCollection) for c in ax.collections):
				self.axis_type = Axis.AXIS_SURFACE
			else:
				self.axis_type = Axis.AXIS_IMAGE
			self.log.debug(f"Mimicing Surface object (axis_type={self.axis_type})")
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
		
		# Collect Line2D objects owned by ErrorbarContainers so they are not
		# double-counted in the plain-line pass below.
		errbar_lines: set = set()
		for container in main_ax.containers:
			if isinstance(container, ErrorbarContainer):
				plotline, caplines, barlinecols = container.lines
				errbar_lines.add(plotline)
				for cap in caplines:
					errbar_lines.add(cap)

		# Mimic each ErrorbarContainer as a single enriched Trace
		tr_idx = 0
		for container in main_ax.containers:
			if not isinstance(container, ErrorbarContainer):
				continue
			self.log.lowdebug(f"Mimicing errorbar container: {container}")
			t = Trace(log=self.log)
			t.mimic_errorbar(container, use_twin=False)
			self.traces[f'Tr{tr_idx}'] = t
			tr_idx += 1

		# Find and mimic all plain lines (2d and 3d), skipping errorbar-owned ones
		for mpl_trace in main_ax.lines:
			if mpl_trace in errbar_lines:
				continue
			self.log.lowdebug(f"Mimicing trace: {mpl_trace}")
			self.traces[f'Tr{tr_idx}'] = Trace(mpl_trace, log=self.log)
			tr_idx += 1

		# Get lines for twin
		if twin_ax is not None:
			twin_errbar_lines: set = set()
			for container in twin_ax.containers:
				if isinstance(container, ErrorbarContainer):
					plotline, caplines, barlinecols = container.lines
					twin_errbar_lines.add(plotline)
					for cap in caplines:
						twin_errbar_lines.add(cap)

			for container in twin_ax.containers:
				if not isinstance(container, ErrorbarContainer):
					continue
				t = Trace(log=self.log)
				t.mimic_errorbar(container, use_twin=True)
				self.traces[f'Tr{tr_idx}'] = t
				tr_idx += 1

			for mpl_trace in twin_ax.lines:
				if mpl_trace in twin_errbar_lines:
					continue
				self.traces[f'Tr{tr_idx}'] = Trace(mpl_trace, use_twin=True, log=self.log)
				tr_idx += 1
		
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
		
		# Check if grid is enabled (3D axes expose _draw_grid; 2D axes use gridlines)
		if hasattr(ax, '_draw_grid'):
			self.grid_on = ax._draw_grid
		elif len(ax.xaxis.get_gridlines()) == 0:
			self.grid_on = False
		else:
			self.grid_on = ax.xaxis.get_gridlines()[0].get_visible()

		self.title = str(ax.get_title())

		# Find and mimic all images (AxesImage)
		for idx, mpl_image in enumerate(ax.images):
			self.surfaces[f'Sf{idx}'] = Surface(mpl_image, log=self.log)

		# Find and mimic all recognised collections (QuadMesh and Poly3DCollection).
		# Other collection types (e.g. LineCollection from colorbar tick marks) are skipped.
		sf_idx = len(self.surfaces)
		for mpl_coll in ax.collections:
			if not isinstance(mpl_coll, (QuadMesh, Poly3DCollection)):
				self.log.warning(f"Skipping unrecognised collection type: {type(mpl_coll).__name__}")
				continue
			self.surfaces[f'Sf{sf_idx}'] = Surface(mpl_coll, log=self.log)
			sf_idx += 1

		# Get subplot position
		col_start = ax.get_subplotspec().colspan.start
		col_stop = ax.get_subplotspec().colspan.stop
		row_start = ax.get_subplotspec().rowspan.start
		row_stop = ax.get_subplotspec().rowspan.stop
		
		# Copy to local variables
		self.position = [row_start, col_start]
		self.span = [row_stop-row_start, col_stop-col_start]
	
	def apply_to(self, ax, gstyle:GraphStyle, twin_ax=None, fig=None):

		if self.axis_type == Axis.AXIS_LINE2D or self.axis_type == Axis.AXIS_LINE3D:
			self.line_apply_to(ax, gstyle=gstyle, twin_ax=twin_ax)
		else:
			self.image_apply_to(ax, gstyle=gstyle, fig=fig)
	
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
	
	def image_apply_to(self, ax, gstyle:GraphStyle, twin_ax=None, fig=None):

		self.gs = gstyle

		for sf in self.surfaces.keys():
			mappable = self.surfaces[sf].apply_to(ax, self.gs)
			if fig is not None:
				self.surfaces[sf].apply_colorbar(fig, mappable, ax)

		self.x_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_X)
		self.y_axis_L.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Y)
		if self.z_axis.is_valid:
			self.z_axis.apply_to(ax, self.gs, scale_id=Scale.SCALE_ID_Z)
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
		self.fig_width_cm = 6.4 * 2.54   # matplotlib default (6.4 in) in cm
		self.fig_height_cm = 4.8 * 2.54  # matplotlib default (4.8 in) in cm

		self.axes = {} # Has to be a dictinary so HDF knows how to handle it

		if fig is not None:
			self.mimic(fig)
	
	def set_manifest(self):
		self.obj_manifest.append("style")
		self.obj_manifest.append("info")
		self.manifest.append("supertitle")
		self.manifest.append("fig_width_cm")
		self.manifest.append("fig_height_cm")
		self.dict_manifest["axes"] = Axis(GraphStyle())
	
	def mimic(self, fig):
		''' Tells the Graf object to mimic the matplotlib figure as best as possible. '''
		
		print(self.log)
		print(self.log.terminal_level)
		self.log.debug(f"Mimicing figure {fig}")
		
		# self.style = ...
		# self.info = ...
		self.supertitle = str(fig.get_suptitle())
		w_in, h_in = fig.get_size_inches()
		self.fig_width_cm = float(w_in) * 2.54
		self.fig_height_cm = float(h_in) * 2.54
		
		#TODO: Determine where each subplot goes and what it's bounds are
		#can use Ax.get_gridspec() to get the object that defines stuff about the grid
		# can use ax.get_subplotspec() to get parameters about where the actual subplot sits. THIS is what I want.
		# ax.get_subplotspec().colspan and .rowspan will give a range() describing the span of the axes. It's weird but workable.
		# ax.get_
		
		# Find twin-axes and merge them here.
		sole_axes = [] # This is a list of axes
		twin_axes = [] # This is a list of lists of axes. Each sub-list contains a list of shared-axes
		for ax in fig.get_axes():

			# Skip colorbar axes — they are stored per-surface, not as independent axes
			if ax.get_label() == '<colorbar>':
				self.log.lowdebug(f"Skipping colorbar axis.")
				continue

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
		
		# Mimic all sole-axes (skip axes without a subplotspec, e.g. colorbar axes)
		self.axes = {}
		ax_idx = 0
		for ax in sole_axes:
			if ax.get_subplotspec() is None:
				self.log.warning(f"Skipping axis without subplotspec (e.g. colorbar).")
				continue
			self.axes[f'Ax{ax_idx}'] = Axis(self.style, ax, log=self.log)
			ax_idx += 1

		# Mimic all twin-axes
		idx_offset = ax_idx
		for idx, ax in enumerate(twin_axes):
			if len(ax) != 2:
				print(f"ERROR: Failed to properly identify twin axes. Skipping.")
				continue
			if ax[0].get_subplotspec() is None:
				self.log.warning(f"Skipping twin axis pair without subplotspec.")
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
	
	def to_fig(self, window_title:str=None, scale:float=1.0):
		''' Converts the Graf object to a matplotlib figure as best as possible.

		Args:
			window_title: Optional title for the figure window.
			scale: Uniform scale factor applied to the stored figure size.
				   1.0 reproduces the original size; 2.0 doubles both dimensions.
		'''

		figsize = (self.fig_width_cm / 2.54 * scale, self.fig_height_cm / 2.54 * scale)
		if window_title is None:
			gen_fig = plt.figure(figsize=figsize)
		else:
			gen_fig = plt.figure(window_title, figsize=figsize)
		
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
				self.axes[axkey].apply_to(new_ax, self.style, twin_ax=new_ax_twin, fig=gen_fig)
			else:
				self.axes[axkey].apply_to(new_ax, self.style, fig=gen_fig)
		
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
		try:
			dict_summary(datapacket, verbose=1) #TODO: Make this a flag
		except Exception:
			pass
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
