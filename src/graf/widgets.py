''' GUI wrapper for matplotlib figures.

Embeds a Figure in a Tkinter window alongside matplotlib's own pan/zoom
toolbar, plus:

* "Save Graf" - opens a native save dialog (format chosen via the
  filetype dropdown, defaulting to .graf) and calls save_graf(fig, filename).
* "Edit Axes" - opens a popup window with entry fields for editing the
  x/y bounds of every Axes in the figure; changes apply on Enter or when
  a field loses focus.
* "Reset Axes" - restores every Axes to the limits it had when the
  window was first built.
* "Grid" / "Legend" checkboxes - toggle the grid and legend for every
  Axes in the figure.
'''

import os
import pickle
from graf.base import save_graf as _save_graf

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


# Save-dialog filetype dropdown, in display order. ".graf" is listed first
# so it's the dialog's default selection.
_GRAF_FORMATS = [
	("GrAF format", "*.graf"),
	("PNG image", "*.png"),
	("SVG vector", "*.svg"),
	("PDF document", "*.pdf"),
	("JPEG image", "*.jpg"),
]


# def _default_save_graf(fig:Figure, filename:str):
# 	''' Placeholder used until the real save_graf (from the GrAF package) is
# 	importable. Handles the standard matplotlib formats directly, and falls
# 	back to pickling the Figure for the ".graf" extension. '''
# 
# 	ext = os.path.splitext(filename)[1].lower().lstrip(".")
# 	if ext == "graf":
# 		with open(filename, "wb") as f:
# 			pickle.dump(fig, f)
# 	else:
# 		fig.savefig(filename)





class AxisBoundsDialog(tk.Toplevel):
	''' Popup window for editing the x/y limits of every Axes in a figure.
	Each row applies independently when its fields are submitted (Enter)
	or lose focus (clicking elsewhere). '''

	def __init__(self, master, fig:Figure, on_apply=None):
		super().__init__(master)
		self.title("Edit Axis Bounds")
		self.resizable(False, False)

		self.fig = fig
		self.on_apply = on_apply
		self.entries = {}  # Axes -> (x_min, x_max, y_min, y_max) Entry widgets

		self._build()

	def _build(self):

		axes = self.fig.get_axes()

		header = ("", "x min", "x max", "y min", "y max")
		for col, text in enumerate(header):
			tk.Label(self, text=text, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=col, padx=4, pady=(6, 2))

		for row, ax in enumerate(axes, start=1):

			label = ax.get_title() or ax.get_label() or f"Axes {row}"
			tk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=4)

			x_min, x_max = ax.get_xlim()
			y_min, y_max = ax.get_ylim()

			field_entries = []
			for col, value in enumerate((x_min, x_max, y_min, y_max), start=1):
				entry = tk.Entry(self, width=10)
				entry.insert(0, f"{value:g}")
				entry.grid(row=row, column=col, padx=4, pady=2)
				entry.bind("<Return>", lambda event, ax=ax: self._apply_axes(ax))
				entry.bind("<FocusOut>", lambda event, ax=ax: self._apply_axes(ax))
				field_entries.append(entry)

			self.entries[ax] = tuple(field_entries)

		button_row = len(axes) + 1
		ttk.Button(self, text="Close", command=self.destroy).grid(row=button_row, column=0, columnspan=5, pady=8)

	def _apply_axes(self, ax):

		e_xmin, e_xmax, e_ymin, e_ymax = self.entries[ax]
		try:
			x_min = float(e_xmin.get())
			x_max = float(e_xmax.get())
			y_min = float(e_ymin.get())
			y_max = float(e_ymax.get())
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
				entry.delete(0, tk.END)
				entry.insert(0, f"{value:g}")


class GrafWindow:
	''' Embeds a matplotlib Figure in a Tkinter window with a toolbar
	that can save the figure, edit its axis bounds, reset them, and
	toggle the grid/legend.

	Args:
		fig (Figure): Figure to display.
		save_graf (callable): Function called as save_graf(fig, filename)
			when the "Save Graf" button is pressed. Defaults to the
			GrAF package's save_graf if importable, otherwise a local
			fallback that handles common matplotlib formats.
		title (str): Window title.
		default_filename (str): Filename suggested in the save dialog.
	'''

	def __init__(self, fig:Figure, save_graf=None, title:str="Graf", default_filename:str="figure"):

		self.fig = fig
		self.save_graf = save_graf if save_graf is not None else _save_graf
		self.default_filename = default_filename
		self._axis_dialog = None

		self.root = tk.Tk()
		self.root.title(title)

		self._build_canvas()
		self._original_limits = {ax: (ax.get_xlim(), ax.get_ylim()) for ax in fig.get_axes()}
		self._build_toolbar()

	def _build_canvas(self):

		self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
		self.canvas.draw()
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

	def _build_toolbar(self):

		bar = tk.Frame(self.root)
		bar.pack(side=tk.BOTTOM, fill=tk.X)

		# Matplotlib's own pan/zoom/save-as-image toolbar
		nav = NavigationToolbar2Tk(self.canvas, bar)
		nav.update()
		nav.pack(side=tk.LEFT)

		self.grid_var = tk.BooleanVar(value=self._grid_is_on())
		ttk.Checkbutton(bar, text="Grid", variable=self.grid_var, command=self._on_toggle_grid).pack(side=tk.LEFT, padx=(12, 4))

		self.legend_var = tk.BooleanVar(value=self._legend_is_on())
		ttk.Checkbutton(bar, text="Legend", variable=self.legend_var, command=self._on_toggle_legend).pack(side=tk.LEFT, padx=4)

		ttk.Button(bar, text="Save Graf", command=self._on_save).pack(side=tk.RIGHT, padx=4, pady=2)
		ttk.Button(bar, text="Edit Axes", command=self._on_edit_axes).pack(side=tk.RIGHT, padx=4, pady=2)
		ttk.Button(bar, text="Reset Axes", command=self._on_reset_axes).pack(side=tk.RIGHT, padx=4, pady=2)

	def _grid_is_on(self) -> bool:

		axes = self.fig.get_axes()
		if not axes:
			return False
		gridlines = axes[0].get_xgridlines()
		return bool(gridlines) and gridlines[0].get_visible()

	def _legend_is_on(self) -> bool:

		return any(ax.get_legend() is not None and ax.get_legend().get_visible() for ax in self.fig.get_axes())

	def _on_toggle_grid(self):

		show = self.grid_var.get()
		for ax in self.fig.get_axes():
			ax.grid(show)
		self.canvas.draw()

	def _on_toggle_legend(self):

		show = self.legend_var.get()
		for ax in self.fig.get_axes():
			legend = ax.get_legend()
			if show:
				if legend is None:
					ax.legend()
				else:
					legend.set_visible(True)
			elif legend is not None:
				legend.set_visible(False)
		self.canvas.draw()

	def _on_save(self):

		filename = filedialog.asksaveasfilename(
			initialfile=self.default_filename,
			defaultextension=".graf",
			filetypes=_GRAF_FORMATS,
		)
		if not filename:
			return

		try:
			self.save_graf(self.fig, filename)
		except Exception as e:
			messagebox.showerror("Save failed", str(e))

	def _on_edit_axes(self):

		if self._axis_dialog is not None and self._axis_dialog.winfo_exists():
			self._axis_dialog.lift()
			self._axis_dialog.focus_force()
			return

		self._axis_dialog = AxisBoundsDialog(self.root, self.fig, on_apply=self.canvas.draw)

	def _on_reset_axes(self):

		for ax, (xlim, ylim) in self._original_limits.items():
			ax.set_xlim(xlim)
			ax.set_ylim(ylim)
		self.canvas.draw()

		if self._axis_dialog is not None and self._axis_dialog.winfo_exists():
			self._axis_dialog.refresh()

	def show(self):
		''' Starts the Tkinter event loop. Blocks until the window is closed. '''
		self.root.mainloop()


def show_graf(fig:Figure, save_graf=None, title:str="Graf", default_filename:str="figure"):
	''' Convenience wrapper: builds a GrafWindow around fig and immediately shows it. '''

	GrafWindow(fig, save_graf=save_graf, title=title, default_filename=default_filename).show()
