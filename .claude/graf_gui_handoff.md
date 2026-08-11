# graf_gui — handoff notes

Built in the `stardust` repo (`stardust/graf_gui.py`), intended to move into the
`GrAF` repo. This doc summarizes what exists, the API, and what still needs
finishing once it lands in GrAF.

## What it is

A Tkinter wrapper that embeds a matplotlib `Figure` in a window with:

- matplotlib's own pan/zoom/home/save-as-image toolbar (`NavigationToolbar2Tk`)
- **Save Graf** button — native save dialog with a filetype dropdown
  (`.graf` / `.png` / `.svg` / `.pdf` / `.jpg`, `.graf` is the default),
  calls `save_graf(fig, filename)`
- **Edit Axes** button — popup listing every `Axes` in the figure with
  x min / x max / y min / y max entry fields. Each row applies on `<Return>`
  or when a field loses focus (no separate Apply button)
- **Reset Axes** button — restores every `Axes` to the limits it had when
  the window was first built
- **Grid** / **Legend** checkboxes — toggle `ax.grid()` / legend visibility
  across every `Axes`, initialized from the figure's actual state

## Public API

```python
show_graf(fig, save_graf=None, title="Graf", default_filename="figure")
```
Builds a `GrafWindow` and blocks on `mainloop()`.

```python
GrafWindow(fig, save_graf=None, title="Graf", default_filename="figure")
w.show()  # starts mainloop
```

`save_graf` is optional — if omitted, `GrafWindow` resolves it via:

```python
try:
    from graf import save_graf as _save_graf   # real implementation, once GrAF exists
except ImportError:
    _save_graf = _default_save_graf            # local fallback, see below
```

## TODO once moved into GrAF

1. **Delete the import-shim fallback** (or keep it as a last-resort default —
   your call). Once `graf_gui.py` lives inside GrAF, `from graf import save_graf`
   should resolve to the real function and `_default_save_graf` becomes dead
   code, unless you want it kept as a safety net for standalone use.
2. **Verify signature compatibility**: `GrafWindow` calls
   `self.write_graf(self.fig, filename)` — two positional args, filename
   includes the extension the user picked in the save dialog. Confirm this
   still matches the real `save_graf`.
3. `_default_save_graf`'s `.graf` handling is a placeholder (just pickles the
   `Figure` object) — it does **not** replicate whatever your real `.graf`
   format actually is. Fine as a fallback, not fine as a real implementation.
4. Drop the `matplotlib` dependency added to `stardust/pyproject.toml` when
   the module leaves that repo (add it to GrAF's own dependencies instead).

## Known limitations (not bugs, just scope)

- Grid/legend toggles are figure-wide, not per-`Axes`.
- Legend toggle calls `ax.legend()` with no args when turning on a
  previously-legend-less `Axes` — relies on plotted artists already having
  `label=` set.
- Only one `AxisBoundsDialog` at a time; re-clicking "Edit Axes" refocuses
  the existing popup instead of opening a duplicate.
- Tested logic-only (calling internal methods / synthetic Tk events) in a
  headless shell with no window manager — `mainloop()` itself and real
  mouse/keyboard interaction weren't exercised end-to-end. Worth a real
  interactive smoke test after porting.

## Full current source

`stardust/graf_gui.py`:

```python
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


def _default_save_graf(fig:Figure, filename:str):
	''' Placeholder used until the real save_graf (from the GrAF package) is
	importable. Handles the standard matplotlib formats directly, and falls
	back to pickling the Figure for the ".graf" extension. '''

	ext = os.path.splitext(filename)[1].lower().lstrip(".")
	if ext == "graf":
		with open(filename, "wb") as f:
			pickle.dump(fig, f)
	else:
		fig.savefig(filename)


try:
	from graf import save_graf as _save_graf  # real implementation, once GrAF exists
except ImportError:
	_save_graf = _default_save_graf


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
		self.write_graf = save_graf if save_graf is not None else _save_graf
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
			self.write_graf(self.fig, filename)
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
```

`examples/graf_gui_demo.py`:

```python
import matplotlib.pyplot as plt

from stardust.graf_gui import show_graf

fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="y = x^2")
ax.set_title("Demo")

# No save_graf needed - falls back to the GrAF package's implementation
# if importable, otherwise a local default that handles .graf/.png/.svg/.pdf/.jpg.
show_graf(fig, title="Demo Graf", default_filename="demo")
```
