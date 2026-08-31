# Installation

```bash
pip install graf-format
```

GrAF requires **Python 3.10 or newer**. That is all you need to read and write
`.graf` files.

The package is named `graf-format` on PyPI, but imports as `graf`:

```python
import graf
```

## Optional extras

Everything GrAF needs to *store and retrieve figures* is in the base install.
Two extras add things that not everyone wants, and they are opt-in because they
are expensive.

| Extra | Install | Adds | Cost |
|---|---|---|---|
| `gui` | `pip install 'graf-format[gui]'` | The interactive viewer | **+235 MB** |
| `test` | `pip install 'graf-format[test]'` | pytest and coverage | ~10 MB |
| `dev` | `pip install 'graf-format[dev]'` | Both of the above | +235 MB |

Quote the package name in zsh (the default shell on macOS), which otherwise
treats the square brackets as a glob pattern.

### `gui` — the interactive viewer

```bash
pip install 'graf-format[gui]'
```

Installs **PyQt6** and **mplcursors**, and enables:

* the `graf-viewer` command, for opening and restyling `.graf` files from the
  shell;
* {func}`graf.widgets.rich_show`, a drop-in replacement for `plt.show()` that
  adds a save-to-GrAF button, editable axis bounds, and data-point readouts;
* everything else in the `graf.widgets` module.

This is separate from the base install because Qt is **235 MB** — larger than
GrAF and all its other dependencies combined, which come to about 149 MB. Most
people writing and reading figures in scripts never open the viewer, and there
is no reason for them to download a GUI toolkit to do it.

Nothing in the save/load path uses Qt: `import graf` does not import PyQt6, and
a base install can save, load, and upgrade files perfectly well. Only
`import graf.widgets` needs it.

If you use the viewer without the extra, you get a message saying so rather than
a confusing traceback:

```
GrAF's interactive viewer needs the optional GUI dependencies, which are
not installed (PyQt6 is missing).

    pip install 'graf-format[gui]'

Reading and writing .graf files does not require them; only graf.widgets,
rich_show() and the graf-viewer command do.
```

### `test` — running the test suite

```bash
pip install 'graf-format[test]'
```

Installs **pytest** and **pytest-cov**. Only needed to run GrAF's own tests:

```bash
pytest tests/ -q
```

The suite runs headless and does *not* require the `gui` extra — that is
deliberate, since it means a passing run proves the GUI dependencies really are
optional.

### `dev` — contributing

```bash
git clone https://github.com/Grant-Giesbrecht/graf
cd graf
pip install -e '.[dev]'
```

Equivalent to `[gui,test]` together. See
[CONTRIBUTING.md](https://github.com/Grant-Giesbrecht/graf/blob/main/CONTRIBUTING.md)
for the rest of the development setup, including the extra step needed to build
these docs.

## What the base install pulls in

| Package | Why |
|---|---|
| `matplotlib` | Figures are captured from, and rebuilt as, matplotlib figures |
| `numpy` | Numeric data handling |
| `stardust-tools` | The TOME container a `.graf` file is written in (**0.2.0 or newer** is required) |
| `pylogfile` | Logging |
| `colorama` | Coloured terminal output for the command-line tools |

## Commands

Two commands are installed on your PATH:

```bash
graf-upgrade -r ./figures                 # rewrite old files in the current format
graf-viewer figure1.graf --serif --bold   # open and restyle        (needs [gui])
```

`graf-upgrade` works on a base install; `graf-viewer` needs the `gui` extra and
will tell you so if it is missing.

## Checking your installation

```python
import graf

print(graf.__version__)             # the library version
print(graf.GRAF_FORMAT_VERSION)     # the file format version it reads and writes
```

Those two are deliberately independent — see [the format
specification](format.md) for why.

To check whether the viewer is available:

```python
try:
    import graf.widgets
    print("viewer available")
except ImportError:
    print("viewer not installed - pip install 'graf-format[gui]'")
```
