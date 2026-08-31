''' GUI wrapper for matplotlib figures.

Embeds a Figure in a Qt window using matplotlib's own Qt toolbar
(NavigationToolbar2QT - the same toolbar plt.show() uses with the "qtagg"
backend), so the window matches the native look, includes matplotlib's
full button set (including "Customize", which the Tk backend never
implemented), and inherits the OS's dark/light theme automatically. On
top of that toolbar we add:

* "Save Graf" - opens a native save dialog (format chosen via the
  filetype filter, defaulting to .graf) and calls save_graf(fig, filename).
* "Edit Axes" - opens a popup window with entry fields for editing the
  x/y bounds of every Axes in the figure (changes apply on Enter or when
  a field loses focus), plus Grid / Legend checkboxes, a Reset Axes
  button (restores every Axes to the limits it had when the window was
  first built), and a Close button.

Every window also gets a menu bar (File / View / Window) carrying the
platform-standard shortcuts - Cmd-W / Ctrl-W closes the focused window,
Cmd-Q / Ctrl-Q quits every window - and the cursor's x/y readout lives in
the window's status bar rather than in the toolbar (where it used to push
the Edit Axes / Save GrAF buttons around as the numbers changed width).

The application-level name and icon used by the menu bar, window titles,
and the taskbar/dock are configurable module-wide:

	gw.set_app_title("Plots")   # set before the first figure, ideally
	gw.set_app_icon("/path/to/icon.png")
	gw.set_show_coordinates(False)   # hide the x/y readout entirely
'''

import os
import sys

# PyQt6 and mplcursors are OPTIONAL dependencies -- they ship with the 'gui'
# extra, not the base install, because nothing in GrAF's save/load path needs a
# GUI toolkit. Only this module does. The bare ImportError names a module the
# user never asked for, so it is translated into an instruction they can act on.
try:
	from mplcursors import cursor

	from PyQt6.QtWidgets import (
		QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
		QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog, QMessageBox, QComboBox,
	)
	from PyQt6.QtCore import QSettings
	from PyQt6.QtGui import QIcon, QAction, QActionGroup, QKeySequence
except ImportError as e:
	raise ImportError(
		f"GrAF's interactive viewer needs the optional GUI dependencies, which "
		f"are not installed ({e.name} is missing).\n\n"
		f"    pip install 'graf-format[gui]'\n\n"
		f"Reading and writing .graf files does not require them; only "
		f"graf.widgets, rich_show() and the graf-viewer command do."
	) from e

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib._pylab_helpers import Gcf

from graf.base import save_graf as _save_graf, CURSOR_MARKER_GID


# Save-dialog filter string, in display order. "GrAF format" is listed
# first so it's the dialog's default selection.
_GRAF_FILTER = "GrAF format (*.graf);;PNG image (*.png);;SVG vector (*.svg);;PDF document (*.pdf);;JPEG image (*.jpg)"

_EXT_BY_FILTER = {
	"GrAF format (*.graf)": ".graf",
	"PNG image (*.png)": ".png",
	"SVG vector (*.svg)": ".svg",
	"PDF document (*.pdf)": ".pdf",
	"JPEG image (*.jpg)": ".jpg",
}

_DEFAULT_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "grs.png")
_ICON_PATH = _DEFAULT_ICON_PATH

# Application-wide presentation, adjustable via set_app_title/set_app_icon.
# _APP_TITLE names the app in the menu bar and prefixes every window title
# ("GrAF Rich Show: Figure 1"); _APP_ICON is the window/taskbar/dock icon.
_DEFAULT_APP_TITLE = "GrAF Rich Show"
_APP_TITLE = _DEFAULT_APP_TITLE
_APP_ICON = _DEFAULT_ICON_PATH
_SHOW_COORDINATES = True

# Persisted (QSettings) UI scale, applied on top of the figure's own dpi.
# Lets a user compensate for e.g. an over/under-sized default on their display
# without editing rcParams; see GrafWindow._apply_scale.
_SETTINGS_ORG = "GrAF"
_SETTINGS_APP = "GrafWidgets"
_SCALE_SETTINGS_KEY = "ui_scale"
_SCALE_OPTIONS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
_DEFAULT_SCALE = 1.0


def _objc_messenger():
	''' Returns a helper for sending Objective-C messages via ctypes, or None
	if the runtime can't be loaded. Used only on macOS, and only to set names
	the OS reads from the process itself (see _apply_macos_app_name); doing it
	this way avoids taking a dependency on pyobjc. '''

	import ctypes
	import ctypes.util

	lib = ctypes.util.find_library("objc")
	if lib is None:
		return None

	objc = ctypes.cdll.LoadLibrary(lib)
	objc.objc_getClass.restype = ctypes.c_void_p
	objc.objc_getClass.argtypes = [ctypes.c_char_p]
	objc.sel_registerName.restype = ctypes.c_void_p
	objc.sel_registerName.argtypes = [ctypes.c_char_p]

	# objc_msgSend must be called through a prototype matching each message's
	# actual signature (its declared argtypes are per-call, not global), so we
	# rebuild a function pointer from its address for every send.
	send_address = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value

	def send(receiver, selector, *args, restype=ctypes.c_void_p, argtypes=()):
		if not receiver:
			return None
		prototype = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)
		return prototype(send_address)(receiver, objc.sel_registerName(selector.encode()), *args)

	return objc, send


def _apply_macos_app_name(name:str):
	''' Makes macOS itself call the process `name`: the bold entry at the left
	of the menu bar and the Dock's hover tooltip come from the running app's
	CFBundleName / process name, not from anything Qt exposes. For a plain
	(un-bundled) Python process both would otherwise read "Python".

	The menu bar reads CFBundleName once, while the app menu is built - which
	Qt does when the QApplication is constructed - so this has to run before
	then to take effect; set_app_title() called ahead of the first rich_show()
	does exactly that. Everything here is best-effort: a failure just leaves
	the default OS-supplied name in place. '''

	try:
		import ctypes

		messenger = _objc_messenger()
		if messenger is None:
			return
		objc, send = messenger

		def nsstring(text):
			return send(objc.objc_getClass(b"NSString"), "stringWithUTF8String:",
					text.encode("utf-8"), argtypes=(ctypes.c_char_p,))

		ns_name = nsstring(name)

		# CFBundleName -> the menu bar's application name. mainBundle's info
		# dictionary is mutable in practice for an un-bundled process, but
		# check before mutating rather than risk an ObjC exception.
		bundle = send(objc.objc_getClass(b"NSBundle"), "mainBundle")
		info = send(bundle, "infoDictionary")
		responds = send(info, "respondsToSelector:", objc.sel_registerName(b"setObject:forKey:"),
				restype=ctypes.c_bool, argtypes=(ctypes.c_void_p,))
		if responds:
			send(info, "setObject:forKey:", ns_name, nsstring("CFBundleName"),
					argtypes=(ctypes.c_void_p, ctypes.c_void_p))

		# Process name -> the Dock tooltip (and Activity Monitor / Force Quit).
		process_info = send(objc.objc_getClass(b"NSProcessInfo"), "processInfo")
		send(process_info, "setProcessName:", ns_name, argtypes=(ctypes.c_void_p,))

		# If the menu bar already exists (set_app_title called after a window
		# was opened), retitle the app menu in place so at least the running
		# session picks the new name up.
		if QApplication.instance() is not None:
			app = send(objc.objc_getClass(b"NSApplication"), "sharedApplication")
			main_menu = send(app, "mainMenu")
			item = send(main_menu, "itemAtIndex:", 0, argtypes=(ctypes.c_long,))
			send(item, "setTitle:", ns_name, argtypes=(ctypes.c_void_p,))
			send(send(item, "submenu"), "setTitle:", ns_name, argtypes=(ctypes.c_void_p,))

	except Exception:
		pass


def _apply_windows_app_id(name:str):
	''' Gives the process an explicit AppUserModelID so the Windows taskbar
	treats our windows as one app of our own (with our icon and name) rather
	than grouping them under the Python interpreter. Best-effort. '''

	try:
		import ctypes

		app_id = "GrAF.RichShow." + "".join(c for c in name if c.isalnum() or c in "._-")
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
	except Exception:
		pass


def _apply_app_identity():
	''' Pushes the current app title down to the places the OS - rather than
	Qt - decides what to call us: the macOS menu bar and Dock, the Windows
	taskbar, and the Linux taskbar/dock (which matches windows to apps by
	WM_CLASS / desktop file name, both of which Qt derives from these). '''

	app = QApplication.instance()
	if app is not None:
		app.setApplicationName(_APP_TITLE)

	QApplication.setDesktopFileName(_APP_TITLE)

	if sys.platform == "darwin":
		_apply_macos_app_name(_APP_TITLE)
	elif sys.platform.startswith("win"):
		_apply_windows_app_id(_APP_TITLE)


def set_app_title(title:str):
	''' Sets the application's name: the bold entry in the macOS menu bar, the
	name shown by the Dock / Windows / Linux taskbar, and the prefix of every
	window title (e.g. set_app_title("Plots") gives "Plots: Figure 1").
	Passing None restores the default, "GrAF Rich Show".

	Call this before the first rich_show() of the session. Window titles pick
	up a later change too (for windows opened afterwards), but the macOS menu
	bar reads the name once, when the first window's menu bar is created. '''

	global _APP_TITLE
	_APP_TITLE = _DEFAULT_APP_TITLE if title is None else str(title)

	_apply_app_identity()


def get_app_title() -> str:
	''' Returns the current application title (see set_app_title). '''

	return _APP_TITLE


def set_app_icon(icon):
	''' Sets the window/taskbar/dock icon, given either a path to an image
	file or a QIcon. Passing None restores GrAF's built-in icon. Applies to
	the running application immediately, and to windows opened afterwards. '''

	global _APP_ICON
	_APP_ICON = _DEFAULT_ICON_PATH if icon is None else icon

	app = QApplication.instance()
	if app is not None:
		app.setWindowIcon(_load_icon())


def get_app_icon():
	''' Returns the currently configured icon (a path or a QIcon). '''

	return _APP_ICON


def set_show_coordinates(show:bool):
	''' Controls whether the cursor's x/y readout is shown in the status bar
	at the bottom of each window. Applies to windows opened afterwards. '''

	global _SHOW_COORDINATES
	_SHOW_COORDINATES = bool(show)


def _load_icon() -> QIcon:
	''' Loads the window/taskbar/dock icon shared by every window we open. '''

	if isinstance(_APP_ICON, QIcon):
		return _APP_ICON
	return QIcon(str(_APP_ICON))


def _load_saved_scale() -> float:
	''' Reads the user's last-chosen UI scale from QSettings (1.0 if never set). '''

	settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
	try:
		return float(settings.value(_SCALE_SETTINGS_KEY, _DEFAULT_SCALE))
	except (TypeError, ValueError):
		return _DEFAULT_SCALE


def _save_scale(scale: float):
	''' Persists the user's chosen UI scale via QSettings so it's remembered next launch. '''

	QSettings(_SETTINGS_ORG, _SETTINGS_APP).setValue(_SCALE_SETTINGS_KEY, scale)


def _ensure_qapp() -> QApplication:
	''' Returns the existing QApplication instance, creating one if none exists yet.
	Also sets the app-wide icon (used as the taskbar/dock icon on most platforms)
	since the qtagg backend may have already created the QApplication before we
	get a chance to configure it. '''

	app = QApplication.instance()
	if app is None:
		# Name the process before the QApplication exists: Qt builds the macOS
		# menu bar (whose app entry comes from CFBundleName) during
		# construction, so afterwards would be too late.
		_apply_app_identity()
		app = QApplication(sys.argv)

	app.setWindowIcon(_load_icon())
	app.setApplicationName(_APP_TITLE)
	return app


class _FocusLineEdit(QLineEdit):
	''' QLineEdit that also applies on focus-out, matching the behavior of
	applying edits when a field loses focus (not just on Enter). '''

	def __init__(self, *args, on_focus_out=None, **kwargs):
		super().__init__(*args, **kwargs)
		self._on_focus_out = on_focus_out

	def focusOutEvent(self, event):
		super().focusOutEvent(event)
		if self._on_focus_out is not None:
			self._on_focus_out()


class AxisBoundsDialog(QDialog):
	''' Popup window for editing the x/y limits of every Axes in a figure.
	Each row applies independently when its fields are submitted (Enter)
	or lose focus (clicking elsewhere). Also hosts the Grid/Legend toggles
	and the Reset Axes button, since they act on the same Axes set. '''

	def __init__(self, parent, fig:Figure, on_apply=None, on_reset=None,
			grid_checked=False, legend_checked=False, on_toggle_grid=None, on_toggle_legend=None):
		super().__init__(parent)
		self.setWindowTitle("Edit Axis Bounds")
		self.setWindowIcon(_load_icon())

		self.fig = fig
		self.on_apply = on_apply
		self.on_reset = on_reset
		self.on_toggle_grid = on_toggle_grid
		self.on_toggle_legend = on_toggle_legend
		self.entries = {}  # Axes -> (x_min, x_max, y_min, y_max) QLineEdit widgets

		self._build(grid_checked, legend_checked)

	def _build(self, grid_checked, legend_checked):

		axes = self.fig.get_axes()

		grid = QGridLayout()
		header = ("", "x min", "x max", "y min", "y max")
		for col, text in enumerate(header):
			label = QLabel(text)
			font = label.font()
			font.setBold(True)
			label.setFont(font)
			grid.addWidget(label, 0, col)

		for row, ax in enumerate(axes, start=1):

			label_text = ax.get_title() or ax.get_label() or f"Axes {row}"
			grid.addWidget(QLabel(label_text), row, 0)

			x_min, x_max = ax.get_xlim()
			y_min, y_max = ax.get_ylim()

			field_entries = []
			for col, value in enumerate((x_min, x_max, y_min, y_max), start=1):
				entry = _FocusLineEdit(f"{value:g}", on_focus_out=lambda ax=ax: self._apply_axes(ax))
				entry.setFixedWidth(70)
				entry.returnPressed.connect(lambda ax=ax: self._apply_axes(ax))
				grid.addWidget(entry, row, col)
				field_entries.append(entry)

			self.entries[ax] = tuple(field_entries)

		controls = QHBoxLayout()

		self.grid_checkbox = QCheckBox("Grid")
		self.grid_checkbox.setChecked(grid_checked)
		self.grid_checkbox.toggled.connect(self._on_grid_toggled)
		controls.addWidget(self.grid_checkbox)

		self.legend_checkbox = QCheckBox("Legend")
		self.legend_checkbox.setChecked(legend_checked)
		self.legend_checkbox.toggled.connect(self._on_legend_toggled)
		controls.addWidget(self.legend_checkbox)

		reset_button = QPushButton("Reset Axes")
		reset_button.setAutoDefault(False)
		reset_button.setDefault(False)
		reset_button.clicked.connect(self._on_reset_clicked)
		controls.addWidget(reset_button)
		controls.addStretch()

		close_button = QPushButton("Close")
		close_button.setAutoDefault(False)
		close_button.setDefault(False)
		close_button.clicked.connect(self.close)

		layout = QVBoxLayout()
		layout.addLayout(grid)
		layout.addLayout(controls)
		layout.addWidget(close_button)
		self.setLayout(layout)

	def _on_grid_toggled(self, checked):

		if self.on_toggle_grid is not None:
			self.on_toggle_grid(checked)

	def _on_legend_toggled(self, checked):

		if self.on_toggle_legend is not None:
			self.on_toggle_legend(checked)

	def _on_reset_clicked(self):

		if self.on_reset is not None:
			self.on_reset()

	def _apply_axes(self, ax):

		e_xmin, e_xmax, e_ymin, e_ymax = self.entries[ax]
		try:
			x_min = float(e_xmin.text())
			x_max = float(e_xmax.text())
			y_min = float(e_ymin.text())
			y_max = float(e_ymax.text())
		except ValueError:
			# Leave the figure untouched while a field is mid-edit / invalid.
			return

		ax.set_xlim(x_min, x_max)
		ax.set_ylim(y_min, y_max)

		if self.on_apply is not None:
			self.on_apply()

	def refresh(self):
		''' Re-reads each Axes' current limits into the entry fields
		(used after an external change, e.g. the Reset Axes button). '''

		for ax, (e_xmin, e_xmax, e_ymin, e_ymax) in self.entries.items():
			x_min, x_max = ax.get_xlim()
			y_min, y_max = ax.get_ylim()
			for entry, value in zip((e_xmin, e_xmax, e_ymin, e_ymax), (x_min, x_max, y_min, y_max)):
				entry.setText(f"{value:g}")


class _NavigationToolbar(NavigationToolbar2QT):
	''' NavigationToolbar2QT with its built-in x/y readout removed.

	The stock toolbar puts that readout in an expanding QLabel wedged into
	the toolbar itself, so every mouse move over the canvas re-widths the
	label and shoves the buttons we append after it ("Edit Axes", "Save
	GrAF", the scale selector) sideways. We build the toolbar with
	coordinates=False and forward the message to a callback instead, so the
	host window can park it in a status bar (or drop it entirely). '''

	# Class-level default: NavigationToolbar2.__init__ can emit messages
	# before __init__ gets a chance to assign the instance attribute.
	_message_target = None

	def __init__(self, canvas, parent=None, message_target=None):
		super().__init__(canvas, parent, coordinates=False)
		self._message_target = message_target

	def set_message(self, s):

		if self._message_target is not None:
			self._message_target(s)


class GrafWindow(QMainWindow):
	''' Embeds a matplotlib Figure in a Qt window with matplotlib's own
	Qt toolbar (NavigationToolbar2QT), plus buttons to save the figure and
	edit its axis bounds (with grid/legend toggles and reset inside that
	popup).

	Args:
		fig (Figure): Figure to display.
		save_graf (callable): Function called as save_graf(fig, filename)
			when the "Save Graf" button is pressed. Defaults to the
			GrAF package's save_graf.
		title (str): Window title. Defaults to "<app title>: Figure N",
			where the app title comes from set_app_title().
		default_filename (str): Filename suggested in the save dialog.
		figure_number (int): Figure number used in the default title.
	'''

	def __init__(self, fig:Figure, save_graf=None, title:str=None, default_filename:str="figure",
			figure_number:int=None):

		self._app = _ensure_qapp()
		super().__init__()

		self.fig = fig
		self.write_graf = save_graf if save_graf is not None else _save_graf
		self.default_filename = default_filename
		self._axis_dialog = None

		if title is None:
			number = figure_number if figure_number is not None else getattr(fig, "number", None)
			title = f"{_APP_TITLE}: Figure {number}" if number is not None else _APP_TITLE
		self.setWindowTitle(title)
		self.setWindowIcon(_load_icon())

		self._build_canvas()
		self._original_limits = {ax: (ax.get_xlim(), ax.get_ylim()) for ax in fig.get_axes()}
		self.grid_checked = self._grid_is_on()
		self.legend_checked = self._legend_is_on()
		self.scale = _load_saved_scale()
		self._apply_scale(self.scale)
		self._build_toolbar()
		self._build_menubar()

	def _build_canvas(self):

		# Reuse the figure's existing Qt canvas if it already has one (e.g.
		# pyplot attached one via plt.subplots()) rather than attaching a
		# second one. matplotlib records figure._original_dpi the moment any
		# canvas is attached (FigureCanvasBase.__init__), then multiplies it
		# by the screen's device pixel ratio on HiDPI displays. Attaching a
		# second canvas to a figure whose dpi was already scaled up (e.g. by
		# an earlier canvas's Retina handshake) makes that already-doubled
		# dpi the new "original", so our own canvas's HiDPI handshake doubles
		# it again - fonts/linewidths end up ~4x instead of ~2x. This is
		# what caused everything to render oversized on macOS Retina displays.
		if isinstance(self.fig.canvas, FigureCanvasQTAgg):
			self.canvas = self.fig.canvas
		else:
			if hasattr(self.fig, "_original_dpi"):
				self.fig.dpi = self.fig._original_dpi
			self.canvas = FigureCanvasQTAgg(self.fig)

		self._true_base_dpi = self.fig._original_dpi
		self.setCentralWidget(self.canvas)

		# If pyplot still has a figure manager (and hidden window) for this
		# figure - e.g. it was created via plt.subplots() - detach it now
		# that we've taken over the canvas, rather than leaving it dangling.
		# That orphaned window only gets torn down much later, at
		# interpreter/app shutdown, and closing it fires matplotlib's
		# "close_event" - which by then can be trying to reject() a dialog
		# (e.g. the toolbar's "Subplots" dialog) whose C++ object our own
		# window has already destroyed, raising a RuntimeError. Detaching
		# eagerly - before our own toolbar/dialogs even exist - means that
		# close_event fires harmlessly, once, right here.
		Gcf.destroy_fig(self.fig)

	def _build_toolbar(self):

		# Matplotlib's own pan/zoom/subplots/customize/save-as-image toolbar.
		# Its x/y readout is routed to the status bar (see _NavigationToolbar)
		# so it can't jostle the buttons we append below.
		self._coord_label = QLabel("")
		if _SHOW_COORDINATES:
			self.statusBar().addPermanentWidget(self._coord_label)

		nav = _NavigationToolbar(self.canvas, self, message_target=self._set_message)
		self.nav = nav
		self.addToolBar(nav)

		nav.addSeparator()

		edit_axes_button = QPushButton("Edit Axes")
		edit_axes_button.clicked.connect(self._on_edit_axes)
		nav.addWidget(edit_axes_button)

		save_button = QPushButton("Save GrAF")
		save_button.clicked.connect(self._on_save)
		nav.addWidget(save_button)

		nav.addSeparator()

		scale_combo = QComboBox()
		for option in _SCALE_OPTIONS:
			scale_combo.addItem(f"{option:.0%}", option)
		current_index = scale_combo.findData(self.scale)
		scale_combo.setCurrentIndex(current_index if current_index >= 0 else scale_combo.findData(_DEFAULT_SCALE))
		scale_combo.currentIndexChanged.connect(lambda i: self._on_scale_changed(scale_combo.itemData(i)))
		nav.addWidget(scale_combo)
		self._scale_combo = scale_combo

	def _set_message(self, text:str):
		''' Receives the toolbar's status text (the cursor's x/y readout, plus
		matplotlib's own pan/zoom hints) and shows it in the status bar. '''

		if _SHOW_COORDINATES:
			self._coord_label.setText(text)

	def _build_menubar(self):
		''' Builds the window's menu bar. Every window gets its own (on macOS
		Qt merges whichever belongs to the focused window into the system menu
		bar), which is also what gives us the platform-standard Close/Quit
		shortcuts: Cmd-W/Cmd-Q on macOS, Ctrl-W/Ctrl-Q on Windows and Linux. '''

		menubar = self.menuBar()

		file_menu = menubar.addMenu("&File")

		save_graf_action = QAction("Save GrAF...", self)
		save_graf_action.setShortcut(QKeySequence.StandardKey.Save)
		save_graf_action.triggered.connect(self._on_save)
		file_menu.addAction(save_graf_action)

		save_image_action = QAction("Save Image...", self)
		save_image_action.setShortcut(QKeySequence.StandardKey.SaveAs)
		save_image_action.triggered.connect(lambda: self.nav.save_figure())
		file_menu.addAction(save_image_action)

		file_menu.addSeparator()

		close_action = QAction("Close Window", self)
		close_action.setShortcut(QKeySequence.StandardKey.Close)
		close_action.triggered.connect(self.close)
		file_menu.addAction(close_action)

		quit_action = QAction("Quit", self)
		quit_action.setShortcut(QKeySequence.StandardKey.Quit)
		quit_action.setMenuRole(QAction.MenuRole.QuitRole)
		quit_action.triggered.connect(self._on_quit)
		file_menu.addAction(quit_action)

		view_menu = menubar.addMenu("&View")

		edit_axes_action = QAction("Edit Axes...", self)
		edit_axes_action.triggered.connect(self._on_edit_axes)
		view_menu.addAction(edit_axes_action)

		reset_action = QAction("Reset Axes", self)
		reset_action.triggered.connect(self._on_reset_axes)
		view_menu.addAction(reset_action)

		view_menu.addSeparator()

		self.grid_action = QAction("Grid", self, checkable=True)
		self.grid_action.setChecked(self.grid_checked)
		self.grid_action.toggled.connect(self._on_toggle_grid)
		view_menu.addAction(self.grid_action)

		self.legend_action = QAction("Legend", self, checkable=True)
		self.legend_action.setChecked(self.legend_checked)
		self.legend_action.toggled.connect(self._on_toggle_legend)
		view_menu.addAction(self.legend_action)

		view_menu.addSeparator()

		scale_menu = view_menu.addMenu("UI Scale")
		self._scale_group = QActionGroup(self)
		self._scale_group.setExclusive(True)
		self._scale_actions = {}
		for option in _SCALE_OPTIONS:
			action = QAction(f"{option:.0%}", self, checkable=True)
			action.setChecked(option == self.scale)
			action.triggered.connect(lambda _checked, s=option: self._on_scale_changed(s))
			self._scale_group.addAction(action)
			scale_menu.addAction(action)
			self._scale_actions[option] = action

		window_menu = menubar.addMenu("&Window")

		minimize_action = QAction("Minimize", self)
		minimize_action.setShortcut("Ctrl+M")
		minimize_action.triggered.connect(self.showMinimized)
		window_menu.addAction(minimize_action)

		close_all_action = QAction("Close All Windows", self)
		close_all_action.triggered.connect(self._on_quit)
		window_menu.addAction(close_all_action)

	def _on_quit(self):
		''' Closes every open window, which ends the Qt event loop and returns
		control to the caller of rich_show(). '''

		self._app.closeAllWindows()
		self._app.quit()

	def _apply_scale(self, scale: float):
		''' Applies a UI scale on top of the figure's true (unscaled) dpi,
		combined with whatever HiDPI device-pixel-ratio matplotlib has
		already applied. Overwriting figure._original_dpi (rather than just
		figure.dpi) makes this survive future automatic dpi updates, e.g. if
		the window is dragged to a screen with a different pixel ratio. '''

		self.scale = scale
		self.fig._original_dpi = self._true_base_dpi * scale
		ratio = self.canvas.device_pixel_ratio
		self.fig._set_dpi(ratio * self.fig._original_dpi, forward=True)
		self._redraw()

	def _redraw(self):
		''' Re-applies tight_layout (titles/labels/legends can change size with
		the scale, axis bounds, grid/legend toggles, or the window itself being
		resized, so spacing needs to be recomputed each time) and redraws. '''

		self.fig.tight_layout()
		self.canvas.draw()

	def resizeEvent(self, event):

		super().resizeEvent(event)
		if hasattr(self, "fig"):
			self._redraw()

	def _on_scale_changed(self, scale: float):

		if scale is None or scale == self.scale:
			return

		self._apply_scale(scale)
		_save_scale(scale)
		self._sync_scale_widgets(scale)

	def _sync_scale_widgets(self, scale: float):
		''' Keeps the toolbar's scale selector and the View > UI Scale menu in
		agreement, whichever of the two the change came from. '''

		combo = getattr(self, "_scale_combo", None)
		if combo is not None:
			index = combo.findData(scale)
			if index >= 0 and index != combo.currentIndex():
				combo.blockSignals(True)
				combo.setCurrentIndex(index)
				combo.blockSignals(False)

		action = getattr(self, "_scale_actions", {}).get(scale)
		if action is not None and not action.isChecked():
			action.setChecked(True)

	def _grid_is_on(self) -> bool:

		axes = self.fig.get_axes()
		if not axes:
			return False
		gridlines = axes[0].get_xgridlines()
		return bool(gridlines) and gridlines[0].get_visible()

	def _legend_is_on(self) -> bool:

		return any(ax.get_legend() is not None and ax.get_legend().get_visible() for ax in self.fig.get_axes())

	def _sync_toggle(self, action, checkbox, checked):
		''' Mirrors a grid/legend state change into the widget it didn't come
		from (menu action <-> Edit Axes dialog checkbox), without re-firing
		the handler that's already running. '''

		for widget in (action, checkbox):
			if widget is not None and widget.isChecked() != checked:
				widget.blockSignals(True)
				widget.setChecked(checked)
				widget.blockSignals(False)

	def _on_toggle_grid(self, checked):

		self.grid_checked = checked
		self._sync_toggle(
			getattr(self, "grid_action", None),
			self._axis_dialog.grid_checkbox if self._axis_dialog is not None else None,
			checked,
		)
		for ax in self.fig.get_axes():
			ax.grid(checked)
		self._redraw()

	def _on_toggle_legend(self, checked):

		self.legend_checked = checked
		self._sync_toggle(
			getattr(self, "legend_action", None),
			self._axis_dialog.legend_checkbox if self._axis_dialog is not None else None,
			checked,
		)
		for ax in self.fig.get_axes():
			legend = ax.get_legend()
			if checked:
				if legend is None:
					ax.legend()
				else:
					legend.set_visible(True)
			elif legend is not None:
				legend.set_visible(False)
		self._redraw()

	def _on_save(self):

		filename, selected_filter = QFileDialog.getSaveFileName(
			self, "Save GrAF", self.default_filename, _GRAF_FILTER, _GRAF_FILTER.split(";;")[0],
		)
		if not filename:
			return

		ext = _EXT_BY_FILTER.get(selected_filter)
		if ext and os.path.splitext(filename)[1].lower() != ext:
			filename += ext

		try:
			self.write_graf(self.fig, filename)
		except Exception as e:
			QMessageBox.critical(self, "Save failed", str(e))

	def _on_edit_axes(self):

		if self._axis_dialog is None:
			self._axis_dialog = AxisBoundsDialog(
				self, self.fig, on_apply=self._redraw, on_reset=self._on_reset_axes,
				grid_checked=self.grid_checked, legend_checked=self.legend_checked,
				on_toggle_grid=self._on_toggle_grid, on_toggle_legend=self._on_toggle_legend,
			)

		self._axis_dialog.show()
		self._axis_dialog.raise_()
		self._axis_dialog.activateWindow()

	def _on_reset_axes(self):

		for ax, (xlim, ylim) in self._original_limits.items():
			ax.set_xlim(xlim)
			ax.set_ylim(ylim)
		self._redraw()

		if self._axis_dialog is not None:
			self._axis_dialog.refresh()

	def show(self):
		''' Displays the window and starts the Qt event loop. Blocks until the window is closed. '''
		super().show()
		self._app.exec()


def _attach_cursor(fig:Figure):
	''' Attaches an mplcursors cursor that snaps only to actual data points.

	mplcursors' default Line2D picker also projects the cursor onto the
	rendered path (see mplcursors/_pick_info.py, compute_pick for Line2D),
	and that projected point almost always beats the nearest-vertex match
	except exactly at a vertex - that's why hovering anywhere along a plain
	connecting line matches. That projection branch only runs when the
	artist's linestyle isn't "None", so instead of attaching to the visible
	line, we attach to an invisible, marker-only companion artist per line
	(same data, linestyle="None") - that leaves only the nearest-vertex
	branch, and the original line's look is untouched. '''

	pickable = []
	label_by_marker = {}
	for ax in fig.get_axes():
		for line in list(ax.get_lines()):
			marker_artist, = ax.plot(
				*line.get_data(), linestyle="None", marker="o", markersize=4,
				color=line.get_color(), alpha=0, label="_nolegend_",
			)
			marker_artist.set_gid(CURSOR_MARKER_GID)
			pickable.append(marker_artist)
			label_by_marker[marker_artist] = line.get_label()

	c = cursor(pickable, multiple=True)

	@c.connect("add")
	def _(sel):
		label = label_by_marker.get(sel.artist)
		if label and not label.startswith("_"):
			sel.annotation.set_text(f"{label}\n{sel.annotation.get_text()}")


def rich_show(fig:Figure=None, save_graf=None, title:str=None, default_filename:str="figure"):
	''' Convenience wrapper: builds a GrafWindow around fig and immediately shows it.

	If fig is None, shows every currently open matplotlib figure at once,
	mirroring plt.show(). Each window is titled "<app title>: Figure N"
	(see set_app_title) unless an explicit title is given. '''

	if fig is None:
		# Read the figure numbers before building any window: GrafWindow
		# detaches each figure from pyplot, which clears its manager.
		numbered = [(manager.num, manager.canvas.figure) for manager in Gcf.get_all_fig_managers()]
		if not numbered:
			return

		windows = []
		for number, f in numbered:
			_attach_cursor(f)
			window = GrafWindow(
				f, save_graf=save_graf, title=title, default_filename=default_filename,
				figure_number=number,
			)
			QMainWindow.show(window)
			windows.append(window)

		windows[0]._app.exec()
		return

	_attach_cursor(fig)
	GrafWindow(
		fig, save_graf=save_graf, title=title, default_filename=default_filename,
		figure_number=getattr(fig, "number", None),
	).show()
