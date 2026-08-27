<h1 align="center">
<img src="https://github.com/Grant-Giesbrecht/graf/blob/main/docs/images/graf_logo.png?raw=True" width="600">
</h1><br>

**GrAF** (Graph Archive Format) is a file format for saving graphs — the data
and the formatting together — in a way that stays readable across languages and
across the years.

```python
import graf
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(frequency, power, label='measured')
ax.legend()

graf.save_graf(fig, 'figure1.graf')     # data + formatting, both preserved
fig = graf.load_graf('figure1.graf')    # reopen it anywhere, any time
```

## Where this fits compared to other formats

Ways of saving a graph sit on a spectrum, and the trade-off is always the same:
fidelity of appearance versus access to the underlying data.

| Format | Formatting | Data | Cross-language |
|---|---|---|---|
| PNG / bitmap | Exact | **Lost** — you must read points off the picture | Yes |
| SVG | Mostly preserved, editable | **Lost** — shapes, not measurements | Yes |
| Pickled matplotlib figure | Exact | Present, but tangled in matplotlib's object graph | **No** — Python only |
| MATLAB `.fig` | Exact | Present, similarly hard to reach | **No** — MATLAB only |
| **GrAF** | Key aspects preserved | **Plain lists of floats, trivially accessible** | **Yes** |

GrAF sits deliberately at one end of it. It does *not* promise the graph will
look pixel-identical everywhere — fonts, line weights and sizing can vary
between platforms. What it promises is that **the aspects of the figure that
carry scientific meaning survive**: the data is stored as plain floats that are
easy to read in any language, and the formatting that constitutes the visual
language of the plot — axis limits, scales, line types, markers, colours,
labels, legends — comes back with it.

That makes some things easy that are otherwise tedious:

- Reopen figures from old publications and restyle them to a single coherent
  theme for a new talk.
- Merge data from several plots into one.
- Change the plot type to better convey a point, without hunting for the
  original script.
- Pull the raw numbers back out years later, from a language that did not exist
  when you saved them.

## Provenance

Every GrAF file records where it came from. A creation record is written once
and never rewritten; a mutation history is appended to whenever the data
changes. Both are stamped automatically on save, so a file cannot be written
without them:

```python
g = graf.Graf()
g.read_graf('figure1.graf')

g.info.provenance   # who/what/when created it, and on what machine
g.info.history      # append-only record of every change since
```

Pass `include_system_info=False` to `save_graf` to omit hostname and machine
details.

## Installation

```bash
pip install graf-format
```

Python 3.10+. A `graf-viewer` command is installed alongside the library for
opening and restyling `.graf` files from the shell:

```bash
graf-viewer figure1.graf --serif --bold
```

## Fonts

GrAF bundles a small set of portable fonts so a figure renders consistently on
a machine that lacks the original author's typefaces. Every bundled font is
under a licence permitting redistribution (SIL OFL 1.1 or CC0), and each
family's licence text ships beside it — see
[`src/graf/assets/fonts/LICENSES/`](src/graf/assets/fonts/LICENSES/).

If a file names a font this installation does not bundle, GrAF falls back to a
default family and warns. The data and layout are unaffected; only the typeface
changes. That is the trade-off GrAF exists to make.

## Documentation

Full documentation, including tutorials, is at
[graf.readthedocs.io](https://graf.readthedocs.io).

## Licence

MIT — see [LICENSE](LICENSE). Bundled fonts carry their own licences, noted
above.
