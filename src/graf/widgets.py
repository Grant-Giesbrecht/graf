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
'''

import os
import sys
from mplcursors import cursor

from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
	QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog, QMessageBox, QComboBox,
)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib._pylab_helpers import Gcf

from graf.base import save_graf as _save_graf


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

_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "grs.png")

# Persisted (QSettings) UI scale, applied on top of the figure's own dpi.
# Lets a user compensate for e.g. an over/under-sized default on their display
# without editing rcParams; see GrafWindow._apply_scale.
_SETTINGS_ORG = "GrAF"
_SETTINGS_APP = "GrafWidgets"
_SCALE_SETTINGS_KEY = "ui_scale"
_SCALE_OPTIONS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
_DEFAULT_SCALE = 1.0


def _load_icon() -> QIcon:
	''' Loads the window/taskbar/dock icon shared by every window we open. '''

	return QIcon(_ICON_PATH)


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
		app = QApplication(sys.argv)
	app.setWindowIcon(_load_icon())
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
		title (str): Window title.
		default_filename (str): Filename suggested in the save dialog.
	'''

	def __init__(self, fig:Figure, save_graf=None, title:str="Graf", default_filename:str="figure"):

		self._app = _ensure_qapp()
		super().__init__()

		self.fig = fig
		self.save_graf = save_graf if save_graf is not None else _save_graf
		self.default_filename = default_filename
		self._axis_dialog = None

		self.setWindowTitle(title)
		self.setWindowIcon(_load_icon())

		self._build_canvas()
		self._original_limits = {ax: (ax.get_xlim(), ax.get_ylim()) for ax in fig.get_axes()}
		self.scale = _load_saved_scale()
		self._apply_scale(self.scale)
		self._build_toolbar()

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

		# Matplotlib's own pan/zoom/subplots/customize/save-as-image toolbar
		nav = NavigationToolbar2QT(self.canvas, self)
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

		self.grid_checked = self._grid_is_on()
		self.legend_checked = self._legend_is_on()

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
		self.canvas.draw()

	def _on_scale_changed(self, scale: float):

		self._apply_scale(scale)
		_save_scale(scale)

	def _grid_is_on(self) -> bool:

		axes = self.fig.get_axes()
		if not axes:
			return False
		gridlines = axes[0].get_xgridlines()
		return bool(gridlines) and gridlines[0].get_visible()

	def _legend_is_on(self) -> bool:

		return any(ax.get_legend() is not None and ax.get_legend().get_visible() for ax in self.fig.get_axes())

	def _on_toggle_grid(self, checked):

		self.grid_checked = checked
		for ax in self.fig.get_axes():
			ax.grid(checked)
		self.canvas.draw()

	def _on_toggle_legend(self, checked):

		self.legend_checked = checked
		for ax in self.fig.get_axes():
			legend = ax.get_legend()
			if checked:
				if legend is None:
					ax.legend()
				else:
					legend.set_visible(True)
			elif legend is not None:
				legend.set_visible(False)
		self.canvas.draw()

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
			self.save_graf(self.fig, filename)
		except Exception as e:
			QMessageBox.critical(self, "Save failed", str(e))

	def _on_edit_axes(self):

		if self._axis_dialog is None:
			self._axis_dialog = AxisBoundsDialog(
				self, self.fig, on_apply=self.canvas.draw, on_reset=self._on_reset_axes,
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
		self.canvas.draw()

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
			pickable.append(marker_artist)
			label_by_marker[marker_artist] = line.get_label()

	c = cursor(pickable, multiple=True)

	@c.connect("add")
	def _(sel):
		label = label_by_marker.get(sel.artist)
		if label and not label.startswith("_"):
			sel.annotation.set_text(f"{label}\n{sel.annotation.get_text()}")


def rich_show(fig:Figure, save_graf=None, title:str="Graf", default_filename:str="figure"):
	''' Convenience wrapper: builds a GrafWindow around fig and immediately shows it. '''

	_attach_cursor(fig)
	GrafWindow(fig, save_graf=save_graf, title=title, default_filename=default_filename).show()
