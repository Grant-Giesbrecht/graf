# The GrAF file format

**Format version: 1.0**

This document defines what a `.graf` file contains. It is the reference an
implementation in any language should be able to work from — GrAF's central
promise is that the data outlives the tool that wrote it, and that promise is
only as good as this document.

> **Changing anything here changes the file format.** See
> [Changing the format](#changing-the-format) at the end before you do.

---

## 1. Versioning

Two versions travel with every file and they move independently:

| Field | Meaning | Used for |
|---|---|---|
| `info.version` | **Format version** — the layout described here | Deciding whether a reader can read the file |
| `info.source_version` | The version of the library that wrote it | Provenance only |

The format version is `MAJOR.MINOR`:

- **MAJOR** changes on any removal, rename, or type change. Files of a different
  MAJOR must be refused, not guessed at.
- **MINOR** changes on purely additive changes. A reader seeing a newer MINOR
  reads the file and ignores fields it does not know.

A conforming reader must:

1. refuse a file whose MAJOR differs from its own (GrAF raises
   `GrafVersionError`), **unless** it has an explicit migration for that
   version (see §11);
2. warn, but proceed, on a newer MINOR;
3. proceed silently on the same or an older MINOR.

### Requirements on readers

**A missing field must take its default, not abort the load.** Population order
means an early field can shadow everything after it, so abandoning an object on
the first unresolved field would let a single added field silently empty every
file written before it. Tolerating absence is what makes it safe to add fields,
which is how the format is expected to grow.

**A reader must never partially load a file and report success.** Tolerance is
only safe if the caller can discover what was tolerated. GrAF surfaces this two
ways: `Graf.unpack_report` lists every field that fell back to a default, and
after loading, the number of axes, traces and surfaces is compared against what
the document actually contained — a shortfall raises `GrafFormatError`.

Both requirements come from the same incident: adding one cosmetic field
(`Axis.legend_on`) once caused pre-1.0 files to load with **every trace
missing** and no error raised. For an archive format, quietly returning less
data than the file contains is the worst failure available.

## 2. Container

A GrAF file is a [TOME](https://github.com/Grant-Giesbrecht/stardust) document —
a self-describing, language-agnostic tree of named values. Everything below
describes the tree inside it. All numeric data is stored as plain lists of
floats: reading the numbers back must never require reconstructing an object
graph.

Top level:

```
supertitle       str     figure-wide title ("" if none)
fig_width_cm     float   figure width in centimetres
fig_height_cm    float   figure height in centimetres
style            object  GraphStyle  (§4)
info             object  MetaInfo    (§3)
axes             map     name -> Axis (§5), keys "Ax0", "Ax1", ...
```

## 3. `info` — metadata and provenance

```
version           str     format version of this file, e.g. "1.0"
source_language   str     e.g. "Python"
source_library    str     e.g. "GrAF"
source_version    str     writing library's version
description       str     free text
conditions        map     arbitrary experimental conditions
provenance        map     creation record — written ONCE, never rewritten
history           list    append-only mutation records
```

### `provenance`

Written on first save and immutable thereafter. All values are flat scalars so
they survive any round trip and stay readable in a structure browser.

```
provenance_schema      str    layout version of provenance/history ("1.0")
created_utc            str    ISO-8601 UTC
created_by             str    library identity
created_by_app         str    calling application, if it identified itself
graf_format_version    str    format version at creation
graf_library_version   str    library version at creation
source_language        str
creating_script        str    basename only — never a full path
source_file            str    basename of a converted-from file, if any
source_file_sha256     str
source_format          str    e.g. "matplotlib_figure", "csv"
hostname               str  ┐
os_platform            str  ├ omitted entirely when the writer asks for
machine_arch           str  ├ include_system_info = false
cpu_model              str  ┘
```

### `history`

Append-only. One record per save **that changed the data** — an unchanged
re-save appends nothing. Earlier records are never modified.

```
utc              str    ISO-8601 UTC
action           str    "created", "saved", or a caller-supplied label
by               str    library identity
content_sha256   str    hash of the plot data at that save
app              str    calling application, if identified
```

## 4. `style` — typography

Five font slots, each an independent `Font` object:

```
supertitle_font   figure suptitle
title_font        axes titles
graph_font        tick labels
label_font        axis labels
legend_font       legend entries
```

### `Font`

```
use_native        bool    if true, ignore the rest; use the renderer's default
size              float   points
family            list    FONT STACK — ordered, see below
weight            int     100-900 (400 normal, 700 bold)
style             str     "normal" | "italic" | "oblique"
resolved_family   str     family actually in use when the file was written
```

**`family` is a stack, not a name.** It is an ordered list of candidates, most
specific first, ending in a generic role:

```json
["MFB Oldstyle", "Georgia", "serif"]
```

The generic roles are exactly `serif`, `sans-serif`, `monospace`. They are
roles, never family names, and a reader must not treat them as aliases of any
particular family. A stack always ends in one, so a reader that has none of the
named families still knows what class of type the figure was set in.

Resolution walks the stack and takes the first candidate available locally. If
none is, the trailing role decides — so a serif request degrades to a different
serif rather than to a sans face. `resolved_family` records what the writer
actually used, so a reader can distinguish faithful reproduction from
substitution.

> Note: `bold` and `italic` are **not** stored. They are computed views over
> `weight` and `style` in the Python implementation, and other implementations
> should treat them the same way if they offer them at all.

## 5. `axes` — a set of axes

```
axis_type         str     "AXIS_LINE2D" | "AXIS_LINE3D" | "AXIS_IMAGE" | "AXIS_SURFACE"
position          list    [row, column] from top-left
span              list    [row span, column span]
relative_size     list    optional relative sizing
grid_on           bool
legend_on         bool    whether a legend was displayed
legend_location   str     "best", "upper right", ... (see §7)
title             str
x_axis            object  Scale (§6)
y_axis_L          object  Scale — left y axis
y_axis_R          object  Scale — right (twin) y axis; is_valid false if unused
z_axis            object  Scale — 3D only
traces            map     name -> Trace, keys "Tr0", "Tr1", ...
surfaces          map     name -> Surface
```

`legend_on` says whether a legend was shown; each trace's `include_in_legend`
says which entries belong in it. Both are needed: without `legend_on` a reader
cannot tell a figure with no legend from one whose legend was simply empty.

## 6. `Scale` — one axis

```
is_valid           bool    false means this axis is unused (e.g. no twin, no z)
val_min            float
val_max            float
tick_list          list    major tick positions
minor_tick_list    list
tick_label_list    list    strings, parallel to tick_list
label              str
scale_type         str     "linear" | "log"
```

## 7. `Trace` — one data series

```
trace_type          str     "TRACE_LINE2D" | "TRACE_LINE3D"
use_yaxis_R         bool    plotted against the right-hand y axis
x_data              list    floats
y_data              list    floats
z_data              list    floats — empty for 2D
line_type           str     "-" | "-." | ":" | "--" | "None"
marker_type         str     "." "+" "^" "v" "o" "x" "[]" "|" "_" "*" "None"
marker_size         float
line_width          float
display_name        str     legend label
include_in_legend   bool
line_color          list    [r, g, b], each 0-1
alpha               float   0-1
marker_color        list    [r, g, b]
has_error_bars      bool
x_err_neg           list  ┐
x_err_pos           list  ├ per-point error magnitudes; empty when unused
y_err_neg           list  ├
y_err_pos           list  ┘
err_line_color      list    [r, g, b]
err_line_width      float
err_cap_size        float
err_cap_color       list    [r, g, b]
err_cap_width       float
err_cap_visible     bool
```

## 8. `Surface` — image or surface data

```
surf_type              str     surface / image discriminator
cmap                   list    sampled colormap, list of [r, g, b]
uniform_grid           bool    true if x_grid/y_grid are regularly spaced
x_grid                 list
y_grid                 list
z_grid                 list    the values being displayed
line_type              str
line_width             float
display_name           str
include_in_legend      bool
line_color             list
alpha                  float
antialias              bool
has_colorbar           bool
colorbar_label         str
colorbar_orientation   str     "vertical" | "horizontal"
colorbar_ticks         list
colorbar_tick_labels   list
colorbar_vmin          float
colorbar_vmax          float
```

## 9. Enumerated values

**Line types** — `-`, `-.`, `:`, `--`, `None`

**Marker types** — `.`, `+`, `^`, `v`, `o`, `x`, `[]`, `|`, `_`, `*`, `None`

**Legend locations** — `best`, `upper right`, `upper left`, `lower left`,
`lower right`, `right`, `center left`, `center right`, `lower center`,
`upper center`, `center`

**Font roles** — `serif`, `sans-serif`, `monospace`

**Scale types** — `linear`, `log`

## 10. What GrAF does and does not promise

**Promised.** The data comes back as plain floats. Axis limits and scales, line
and marker types, colours, labels, titles, legend presence and placement, and
the class of type the figure was set in all survive.

**Not promised.** Pixel-identical rendering. Fonts may be substituted (which is
why `resolved_family` is recorded), and exact metrics, DPI, and anti-aliasing
vary between platforms and renderers.

## 11. Reading pre-1.0 files

Files written before format 1.0 declare `0.0.0`. They are not refused: GrAF's
promise is that the data outlives the tool, and refusing to open an archive
because its *typography* was stored differently would break that promise for
cosmetics.

There is **no migration code**, and none is needed. Because a missing field
takes its default (§1), the fields added in 1.0 simply default and everything
else loads normally. The file on disk is never modified by reading it.

| Pre-1.0 field | In format 1.0 | Result |
|---|---|---|
| `Font.font` (string) | replaced by `Font.family` (a stack) | ignored; family defaults to `["sans-serif"]` |
| `Font.bold` (bool) | replaced by `Font.weight` | ignored; weight defaults to `400` |
| `Font.italic` (bool) | replaced by `Font.style` | ignored; style defaults to `"normal"` |
| — | `Font.resolved_family` | defaults to `""` |
| — | `GraphStyle.legend_font` | defaults |
| — | `Axis.legend_on` | defaults to `false` — see below |
| — | `Axis.legend_location` | defaults to `"best"` |

**Everything else transfers unchanged** — all numeric data, axis configuration,
scales, trace styling, titles, description, and provenance. Only typography and
legend visibility fall back, and both are cosmetic.

**Why legends default to hidden.** Pre-1.0 never recorded legend visibility and
never drew a legend on reload, so `false` reproduces how the file actually
rendered. Inferring one from trace labels would add content the file does not
contain, and for an archive format fabricating is worse than omitting.

`Graf.unpack_report` lists exactly which fields defaulted, so the fallback is
inspectable rather than assumed.

### Making it permanent

`graf-upgrade` rewrites a file in the current format, replacing the defaults
above with recorded values:

```bash
graf-upgrade figure.graf          # writes figure.graf.bak alongside
graf-upgrade -r -n ./figures      # recurse, dry run
```

The upgrade appends a history entry and leaves the creation record untouched.

This is also what allows old-format support to be **retired**. Read-time
tolerance cannot be removed while unupgraded files are still in use; once they
have been converted, a future major version can stop accepting `0.0.0`
altogether. Support for a legacy version is kept for at least one MAJOR release
after the tool to migrate away from it ships.

---

## Changing the format

Changing this document means changing the format, which is a promise to every
file already written and to every implementation in every language.

`tests/test_format_schema.py` locks the on-disk field list. It fails on any
addition, removal, or rename. That failure is the mechanism, not an obstacle:

1. Decide whether the change is genuinely necessary.
2. Bump `GRAF_FORMAT_VERSION` in `graf/base.py`:
   - additive → MINOR (`1.0` → `1.1`)
   - removal, rename, or type change → MAJOR (`1.0` → `2.0`), which makes every
     existing file unreadable by this library
3. Update this document, including the history below.
4. Add a `CHANGELOG.md` entry under a **File format** heading.
5. Only then update the expected schema in the test.

### Version history

| Version | Changes |
|---|---|
| **1.0** | First defined version. Supersedes the unversioned pre-release layout (which declared `0.0.0`): `Font.font`/`bold`/`italic` were replaced by `family`/`weight`/`style`; `Font.resolved_family`, `GraphStyle.legend_font`, `Axis.legend_on` and `Axis.legend_location` were added; `info.version` became the format version rather than a library version; provenance `graf_version` split into `graf_format_version` and `graf_library_version`. **Pre-1.0 files remain readable** via the migration in §11. |
| `0.0.0` | Unversioned pre-release. Not a released format; documented only insofar as §11 defines how to read it. |
