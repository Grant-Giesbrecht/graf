# Changelog

All notable changes to GrAF are recorded here. This project follows
[Semantic Versioning](https://semver.org/).

Note that two versions move independently: the **library** version below, and
the **GrAF file format** version (`graf.GRAF_FORMAT_VERSION`), which changes
only when the on-disk layout changes.

## [Unreleased] — working toward 0.1.0

The first release intended for general use. Everything before this was a `dev`
prerelease, so the changes below are described relative to `0.0.0.dev4` rather
than to a supported version.

### File format — BREAKING

The on-disk layout is now **format version 1.0**, tracked separately from the
library version. It supersedes the unversioned pre-release layout, which
declared `0.0.0`.

**Pre-1.0 files remain readable**, with no migration code involved. All data,
axis configuration, scales, trace styling, titles and provenance load unchanged;
only fonts and legend visibility fall back to defaults, because those were
stored differently. `Graf.unpack_report` lists exactly which fields defaulted.
The file on disk is never modified by reading it.

The new **`graf-upgrade`** command rewrites files in the current format,
recording those defaults explicitly. It writes a `.bak` beside each file, is
idempotent, appends an entry to the file's history, and leaves the immutable
creation record alone. See section 11 of the format specification (`FORMAT.md`).

| Object | Change |
|---|---|
| `Font` | `font` (string) replaced by `family` (an ordered **font stack**) |
| `Font` | `bold` / `italic` booleans replaced by `weight` (100-900) and `style` (`normal`/`italic`/`oblique`). `.bold` / `.italic` remain as computed properties but are no longer stored |
| `Font` | added `resolved_family` — the typeface actually in use when written |
| `GraphStyle` | added `legend_font`; the legend previously borrowed `label_font` |
| `Axis` | added `legend_on` and `legend_location`; legends were previously lost entirely |
| `MetaInfo` | `version` now means the *format* version (was a library version); `source_version` now records the writing library |
| provenance | `graf_version` split into `graf_format_version` and `graf_library_version` |

The format is now specified in `FORMAT.md`, and
`tests/test_format_schema.py` locks the field list so no future change to it can
happen as a side effect of an ordinary refactor.

**Silent partial loads are now impossible.** The serializer used to abandon an
object at the first field it could not resolve and return quietly, so adding a
single cosmetic field (`Axis.legend_on`) made pre-1.0 files load with *every
trace missing* and no error raised. Fixed at the root in **stardust-tools
0.2.0** (now the minimum required version): a missing field keeps its default,
the load continues, and an `UnpackReport` records what was absent. GrAF also
verifies after loading that the number of axes, traces and surfaces matches the
document, raising `GrafFormatError` on any shortfall.
`tests/test_legacy_compat.py` regression-tests this against a real pre-release
file committed at `tests/data/`.

### Fixed

- **3-D surfaces failed to save on matplotlib 3.11.** `Poly3DCollection`'s
  internal vertex storage moved to `_faces`; GrAF looked only for the older
  `_vec` (3.9-3.10) and `_segments3d` (< 3.9), and raised
  `AttributeError: Cannot extract vertex data from Poly3DCollection`. All three
  layouts are now handled, newest first. Since `matplotlib >= 3.9` is the
  declared floor, a fresh install resolved 3.11 and 3-D surface support was
  broken out of the box.

- **The built wheel did not import.** `[tool.setuptools.package-data]` used
  arbitrary keys where setuptools expects package names, so no assets shipped —
  and `graf.base` loads the font manifest at import time. Every pip install of
  a previous prerelease raised `FileNotFoundError` on `import graf`. The wheel
  now carries all fonts, icons and licence texts, and CI installs it into a
  clean environment on every push to keep it that way.
- **Undeclared dependencies.** `pylogfile` and `colorama` were imported but not
  declared; `numpy` was used directly but only arrived transitively via
  matplotlib. `stardust-tools` is now pinned to `>= 0.1.0` rather than
  `>= 0.0.0`.
- **Legends were silently lost on reload.** `Axis` recorded which traces belonged
  in a legend but never whether one was shown, and `to_fig()` never called
  `ax.legend()`. Legends and their placement now survive; twinned axes get a
  single combined legend.
- **Italic fonts could render as bold.** `load_fonts` left a stale path between
  loop iterations, so a family declaring no italic face silently resolved
  italic to whichever face loaded last — SUSE italic resolved to SUSE-Bold.
- **The library printed on every save.** `write_graf` dumped roughly 10 KB of
  ANSI-coloured structure to stdout unconditionally. It is now silent by
  default, behind `write_graf(..., debug_print=True)`.
- **Stray debug output** on load and reconstruction has been routed to the log
  or to `warnings`.
- **Shared mutable default arguments.** `conditions:dict={}` meant conditions
  written into one figure could appear in the next one created.
- **`graf-script` console entry point** pointed at a module that was never
  implemented and has been removed; `grafviewer` no longer parses `sys.argv` at
  import time, and no longer raises `NameError` when handed a non-GrAF filename.

### Changed — packaging

- **PyQt6 and mplcursors are now an optional `gui` extra**, not required
  dependencies. Nothing in the save/load path uses them; only `graf.widgets`,
  `rich_show()` and `graf-viewer` do. A base install is **235 MB smaller** (149
  MB vs 384 MB).

  ```bash
  pip install graf-format          # read and write .graf files
  pip install 'graf-format[gui]'   # ...plus the interactive viewer
  ```

  **If you use `rich_show()` or `graf-viewer`, install the extra.** Both now
  fail with a message naming it rather than a bare `ModuleNotFoundError`, and
  `graf-viewer` detects a headless matplotlib up front instead of calling
  `plt.show()` and silently displaying nothing.

### Added

- **File validation on read.** `read_graf` now checks that the file exists,
  parses, is structurally a GrAF document, and declares a readable format
  version, raising `GrafFormatError` / `GrafVersionError` instead of
  half-loading. Compatibility rule: a different format MAJOR is refused, a newer
  MINOR warns and reads, same-or-older is silent.
- **A public API at the package root.** `import graf; graf.save_graf(...)` now
  works; `graf.__version__` is read from the installed distribution metadata.
- **Font licence compliance.** Licence texts for every bundled family ship
  inside the package, `portable_fonts.json` records `license` / `copyright` /
  `source_url` / `license_file` per family, and tests enforce that the declared
  licence is on the redistribution allow-list and that the file actually exists.
- **Font fallback.** A file naming an unbundled family now falls back to a
  default and warns, rather than failing or silently substituting.
- **Continuous integration** — the test suite across Linux/macOS/Windows and
  Python 3.10–3.13, plus a packaging job that verifies the built wheel's
  contents and smoke-tests it in a clean venv.
- **Test suite grown from 209 to 361 tests**, including the first coverage of
  the reconstruction path (`to_fig`), which was previously asserted only to not
  raise, plus provenance, fonts, versioning and file validation. Coverage is now
  measured rather than estimated.

### Changed

- The GrAF file format version is now `1.0`, and is tracked separately from the
  library version.
- Provenance records `graf_format_version` and `graf_library_version` in place
  of the single ambiguous `graf_version`.

### Removed

- `save_pklfig`, the commented-out JSON writer, and the `.json` / `.pklfig`
  branches in the viewer. GrAF is the only format this library reads or writes.
- The unused `h5py` and `pickle` imports, and the `h5py` dependency.
