# GrAF — road to v0.1.0

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

**Current state:** 532 tests passing (was 209), plus 178 in stardust. All six release blockers fixed
and verified against a clean-venv install of the built wheel. Version is
`0.1.0.dev0`; format version `1.0`. Remaining work is documentation and the two
untested GUI modules.

---

## 1. Blockers (must be fixed before tagging)

- [x] **Asset packaging is broken — the wheel does not import.** FIXED &
      verified: wheel now ships 28 files (was 12); clean-venv install +
      `import graf.base` + full round-trip all succeed.
      `[tool.setuptools.package-data]` uses arbitrary keys (`portable_fonts`,
      `font_suse_reg`, …) where setuptools expects *package names*. Result: the
      built wheel contains 12 files and no `assets/` directory, so the
      module-level `load_fonts(...)` call in `base.py` raises `FileNotFoundError`
      on import for every pip-installed user.
      Also note `SplineSansMono-*` was never listed at all, even incorrectly.
      Fix: `"graf" = ["assets/*.json", "assets/*.png", "assets/fonts/*", ...]`.
      Verify by installing the built wheel into a clean venv and importing.
- [x] **Undeclared dependencies.** FIXED: added `numpy`, `pylogfile`,
      `colorama`; pinned `stardust-tools >= 0.1.0`. Verified in a clean venv
      resolving against *published* PyPI wheels, not the local checkout. `pylogfile` and `colorama` are imported by
      `base.py` but absent from `pyproject.toml`. `numpy` is used directly and
      only arrives transitively via matplotlib. Pin `stardust-tools >= 0.1.0`
      (currently `>= 0.0.0`) and test against the *published* wheel, not the
      local `~/Documents/GitHub/stardust` checkout.
- [x] **Library prints to stdout on every save.** FIXED: gated behind
      `write_graf(..., debug_print=False)`. Verified: a save+load+`to_fig()`
      cycle now emits 0 chars on stdout and stderr; `debug_print=True` still
      gives the full 10 KB dump.
      OLD: `write_graf` calls
      `dict_summary(datapacket, verbose=1)` unconditionally (~10 KB of
      ANSI-coloured output per save). Gate behind a `debug_print=False` argument.
- [x] **Stray debug prints** FIXED — all routed to `log.debug()` or `warnings`.
      No raw `print()` remains in library code (CLI output in `grafviewer.py` is
      intentional). Also replaced the import-time `print(__name__)` /
      colorama error prints around `mod_path` with a real fallback + warning.
      OLD:
      `base.py:1440` `"Initializing scales."` · `base.py:1728-1729` (prints the
      LogPile object and its terminal level) · `base.py:1938` (prints axis key).
      Route through the LogPile / the new debug flag, or delete.
- [x] **Remove all non-GrAF save/load formats.** DONE: deleted `save_pklfig`
      and the commented `write_json_GrAF`; stripped the `.json` / `.pklfig` /
      "Other" branches from `grafviewer.py`; removed the now-unused `pickle`
      and `h5py` imports and dropped `h5py` from dependencies. (`json` stays —
      it is used internally for content hashing and the font manifest, not as a
      save format.)
      OLD: Delete `save_pklfig` (also
      simply broken: opens `'w'` text mode then `pickle.dump`). Strip the
      `.json` / `.pklfig` / "Other" branches and the commented-out
      `write_json_GrAF`. GrAF is the only format this library reads or writes.
- [x] **Version strings are unsynchronised and unvalidated.** FIXED. Split the
      two conflated concepts: `GRAF_FORMAT_VERSION = "1.0"` (on-disk layout,
      what a reader validates) vs the library version, now read from installed
      distribution metadata so `pyproject.toml` is the single source of truth.
      `read_graf` now validates existence, type, parseability, GrAF structure
      and format version, raising `GrafFormatError` / `GrafVersionError` (both
      under a `GrafError` base) instead of half-loading. Compatibility rule:
      different MAJOR refuses, newer MINOR warns and reads, same/older is
      silent. `pyproject` version set to `0.1.0.dev0`.
      OLD:
      `GRAF_VERSION = "0.0.0"`, `MetaInfo.source_version = "0.0.0"` (a separate
      hardcoded literal), and `pyproject` at `0.0.0.dev4`. Establish one source
      of truth. Critically: `read_graf` does **no** version check, no
      file-existence check, and no "is this actually a GrAF file" check — for a
      format whose promise is *opening this in ten years*, the reader must fail
      loudly on a version it does not understand.

### Bugs found and fixed while doing the above

- [x] **`load_fonts` silently substituted the wrong face.** `font_path` was
      assigned only inside the `else` branch, so a family declaring a style as
      `[]` fell through and reloaded the path left over from the previous loop
      iteration. Concretely: SUSE declares no italic, so **SUSE italic resolved
      to SUSE-Bold** — asking for italic rendered bold. Fixed, with a named
      regression test.
- [x] **`graf-script` console entry point pointed at a deleted module** — it
      would have installed a command raising `ModuleNotFoundError`. Removed.
- [x] **`grafviewer.py` parsed `sys.argv` at import time**, so importing the
      module could exit the interpreter. Moved into `main(argv=None)`.
- [x] **`grafviewer.py` `NameError` on a non-GrAF filename** — `graf1` was
      referenced unbound after the non-matching branches. Gone with those
      branches; unreadable/missing files are now skipped with a clear message.
- [x] **`load_graf` docstring said it writes a file.** Fixed.
- [x] Resolved the `#TODO: Validate that font family exists` at :495, and the
      copy-paste `#TODO: Validate that font family exists` on
      `set_all_font_sizes` (which now validates the *size*, as intended).

## 1a. Legacy file compatibility

- [x] **Root cause fixed in stardust 0.2.0**, not worked around in GrAF.
      `Packable.unpack` now keeps the `__init__` default for any absent field
      and continues, returning an `UnpackReport` (with dotted paths for nested
      objects) and accepting `strict=True` to raise `UnpackError`. 24 new tests
      there; all 178 pass. GrAF pins `stardust-tools >= 0.2.0`.
      **Consequence: adding a field to the format is now backward compatible by
      default, so MINOR format bumps need no migration code at all.**
- [x] **Migration code deleted entirely.** Pre-1.0 files load with no
      per-version code: data, scales, labels and trace styling all transfer;
      fonts and legend visibility fall back to defaults, as agreed. Format
      version stays `1.0`.
- [x] **CRITICAL: silent total data loss found and fixed.** stardust's
      `Packable.unpack` `return`s on the first missing field, so the cosmetic
      `Axis.legend_on` field aborted the whole Axis before reaching
      `obj_manifest` (scales) or `dict_manifest` (traces). A legacy file loaded
      with **zero traces and no error raised**. `read_graf` now verifies the
      loaded axes/traces/surfaces counts against the file's own and raises
      `GrafFormatError` on any shortfall.
- [x] **Real legacy fixture committed** — `tests/data/legacy_format_0_0_0.graf`,
      generated by the pre-session code at commit `2d8f59a`, not synthesised.
      27 tests in `tests/test_legacy_compat.py`, including one that disables the
      migration to prove the data-loss guard actually fires.

- [x] **`graf-upgrade` CLI** — rewrites files in the current format. Writes a
      `.bak`, refuses to overwrite an existing one, writes via a temp file so an
      interrupted run cannot truncate an archive, never touches a file it could
      not fully read, is idempotent, supports `--dry-run` / `--recursive`, and
      appends to the file's history while leaving the creation record immutable.
      28 tests.
- [x] **Bug found while testing the CLI:** `write_graf` preserved whatever
      `info.version` had been read, so an upgraded file was written in the 1.0
      layout while still declaring `0.0.0` — a file lying about its own format,
      and the upgrade was not idempotent. `write_graf` now stamps
      `GRAF_FORMAT_VERSION` and the library version at the write choke point.
- [x] **Sunset policy documented** in FORMAT.md: legacy support is kept for at
      least one MAJOR release after the tool to migrate away from it ships.

### Release ordering

- [x] **stardust-tools 0.2.0 published to PyPI.** Verified: a clean venv install
      of the GrAF wheel resolves `stardust-tools 0.2.0` from PyPI (not the local
      checkout), and legacy reads, font defaulting and `graf-upgrade` all work
      against it.

## 1b. Font model (redesigned before format 1.0 froze)

The old model made generic roles *aliases* of specific families
(`["mfb_oldstyle", "mfb", "serif"]`), so the format could not distinguish "I want
MFB Oldstyle" from "I want any serif" — and a user's preferred serif could never
take effect. Redesigned on CSS's model, in a new `graf/fonts.py`:

- [x] **Generic roles decoupled from family names.** `serif` / `sans-serif` /
      `monospace` are a closed set of roles, bound to families by
      `role_defaults` and overridable per machine. `load_manifest` rejects any
      family claiming a role as an alias, and a test enforces it.
- [x] **Font stacks.** A file stores an ordered list ending in a role —
      `["MFB Oldstyle", "Georgia", "serif"]`. Naming one font and asking for a
      type are the same mechanism; `["serif"]` is the degenerate stack.
- [x] **`resolved_family` recorded** — the typeface actually in use at save
      time, so a reader can tell reproduction from substitution.
- [x] **Resolution chain**: bundled → user `font_paths` → system fonts (via
      matplotlib, with `fallback_to_default=False`, which is essential — without
      it matplotlib silently returns DejaVu Sans for anything missing and every
      lookup "succeeds").
- [x] **Fallback stays within font class.** The earlier `FALLBACK_FONT =
      "sanserif"` sent an unavailable *serif* to a *sans* face; now the stack's
      trailing role decides.
- [x] **Warns once per substitution**, and only on genuine substitution — not
      when a bundled alias or a user-configured alias resolves the author's
      first choice.
- [x] **`weight` + `style` replace `bold`/`italic` booleans** (CSS model:
      100–900, `normal`/`italic`/`oblique`), so semibold and light faces are
      expressible. `.bold` / `.italic` remain as properties.
- [x] **Per-user config** at `graf.user_config_path()` (XDG / `%APPDATA%`, plain
      JSON — deliberately not Qt's `QSettings`, which `widgets.py` uses, since
      `base.py` must work headless): `defaults`, `font_paths`, `aliases`. With
      `graf.set_font_default()` and `graf.add_font_path()`.
- [x] **`sanserif` → `sans-serif`**, the standard spelling; the old one is still
      accepted on read.
- [x] 117 tests in `tests/test_fonts.py`.

### Font capture/apply defects found by inspecting the mimic path

- [x] **`supertitle_font` was captured but never applied** — `to_fig` called
      `gen_fig.suptitle(text)` with no font at all, so a 20 pt monospace
      supertitle came back as 12 pt default.
- [x] **`graph_font` (tick labels) was captured but never applied** — tick
      labels were set with no fontproperties. Now applied via
      `Scale._apply_tick_font`, using `tick_params` for size (which survives a
      redraw) and per-artist properties for the family, with the log-scale
      caveat documented: matplotlib regenerates tick Texts on draw there.
- [x] **The legend had no font slot of its own** — it borrowed `label_font`.
      Added `legend_font`, captured from the source legend, and falling back to
      the label font when the source had no legend (so a legend added later
      matches the figure instead of reverting to a default).
- [x] **Legend size was silently dropped.** `_apply_legend` passed both `prop`
      and `fontsize`; matplotlib ignores `fontsize` when `prop` is given, so a
      14 pt legend reloaded at 10 pt. Size now goes onto the FontProperties.
- [x] **`set_all_font_sizes` missed two slots** (supertitle and legend).
- [x] **Capture read a blind `axes[0]`**, which may be empty or a colorbar.
      Now picks the first axes actually carrying a title or axis label, and
      falls back to the y-label when no x-label is set.
- [x] **GrAF never captured fonts from the source figure at all.** `Graf.mimic`
      had a commented-out `# self.style = ...`, so every file was written with
      default typography no matter how the figure looked. Now captured via
      `GraphStyle.mimic` / `Font.mimic_text`.

### Still open

- [ ] **`GraphStyle` is figure-global, matplotlib is per-artist.** One axes has
      to speak for the whole figure, so a multi-subplot figure with genuinely
      different typography per subplot collapses to one style. Fine for the
      common case; a real limitation to document in the format spec, or to fix
      by moving font slots onto `Axis`.
- [ ] Tick-label *family* on log scales is best-effort only — matplotlib's
      locator regenerates those Text artists on every draw. Size survives via
      `tick_params`; family may not.
- [ ] Decide whether to ship a separate `graf-fonts` distribution for users who
      want more bundled families, rather than growing the core wheel (~700 KB of
      fonts today).

## 2. Test suite gaps

209 tests pass in ~5 s. The *capture* path (`mimic`) is well covered: 2D/3D
lines, errorbars, pcolormesh (uniform + non-uniform), imshow, colorbars,
subplot grid inference, twin axes, figure sizing, and a real edge-case file.
The gaps below are what stands between that and a release-quality suite.

- [x] **`to_fig()` reconstruction fidelity** — FIXED: `tests/test_reconstruction.py`,
      47 tests asserting on the *rebuilt* figure: data, trace order, line style /
      width / colour / marker / size / alpha, axis labels, titles, unicode,
      limits, log scales, grid, subplots, twin axes, and a save→load→save→load
      idempotence test that would catch accumulating drift.
      OLD:
      `roundtrip_fig` is called ~25 times; outside `test_figure_size.py` the only
      assertion is `assert fig2 is not None`. Every `fig2.` attribute access in
      the whole suite is `get_size_inches()`. So `apply_to` — roughly half the
      code, and the half deciding whether a reloaded graph *looks* right — is
      tested only for "does not throw". Assert on line data, colours, styles,
      limits, labels, scales.
- [x] **Legends are silently lost.** FIXED. Root cause: `Axis` recorded only
      per-trace `include_in_legend`, never whether a legend was *shown*, and
      `to_fig()` never called `ax.legend()`. Added `legend_on` +
      `legend_location` to `Axis`, captured in both mimic paths and applied in
      `_apply_legend`. Twinned axes get one combined legend rather than two
      overlapping ones. Absence is preserved too: a labelled trace with no
      `ax.legend()` call must not gain one. Regression tests included.
      OLD: `include_in_legend` is stored per trace and
      in the manifest, but `to_fig()` never calls `ax.legend()`. Found by
      testing reconstruction directly; likely representative, not isolated.
      (Log scales *do* round-trip correctly.)
- [x] Provenance / history tested — `tests/test_provenance.py`, 22 tests
      covering the two invariants (creation record immutable, history
      append-only), the privacy switch, content hashing, flat-value portability,
      and the mutable-default isolation bug below.
- [x] Tests for fonts, `Font`, `GraphStyle`, `load_fonts` — `tests/test_fonts.py`,
      34 tests covering licence compliance, manifest resolution, fallback
      behaviour and style validation. Suite is now **243 tests**, up from 209.
- [x] Public API tested — `tests/test_format_validation.py` covers `save_graf`,
      `load_graf`, and asserts every name in `graf.__all__` is exported. Still
      to cover: `get_xdata`, `get_ydata`, `get_trace`, `get_axis`.
- [x] Corrupt / missing / wrong-version file handling tested (49 tests in
      `tests/test_format_validation.py`), including a `TestQuiet` class pinning
      the "library must not print" contract so it cannot regress.
- [ ] No tests: `widgets.py` (881 lines, Qt viewer + `rich_show`) — 0 %.
- [ ] No tests: `scripts/grafviewer.py` — 0 %.
- [x] Coverage tooling added (`pytest-cov`, `[project.optional-dependencies]
      test`, `[tool.coverage.*]`). It is now a number, not an estimate:

      | Module | Coverage |
      |---|---|
      | `base.py` | **76 %** |
      | `__init__.py` | 71 % |
      | `scripts/grafviewer.py` | 0 % |
      | `widgets.py` | 0 % |
      | **TOTAL** | **57 %** |

      Suite is **339 tests** (was 209). The remaining total is dominated by the
      two GUI modules; `base.py` is the library proper.

### Docs defects found and fixed

- [x] **The Read the Docs build was broken.** nbsphinx shells out to `pandoc`,
      which the RTD image does not include and `.readthedocs.yaml` did not
      declare. Added via `build.apt_packages`.
- [x] **Docs were built against the last PyPI release, not the source tree.**
      `docs/requirements.txt` listed `graf-format`, so the API reference would
      have documented `0.0.0.dev4` rather than the working tree. Now installs
      `.` from the repository root.
- [x] **`conf.py` hardcoded `release = '0.0.0'`** — now read from installed
      package metadata, so the docs cannot claim a different version than the
      code. Also added autosummary, viewcode, intersphinx and myst-parser,
      mocked `PyQt6`/`mplcursors` for headless builds, and set
      `nbsphinx_allow_errors = False` so a tutorial that stops working fails
      the build instead of publishing broken output.
- [x] **`How_it_works.ipynb` was an unfinished stub** duplicating
      `Introduction.ipynb` code cell for code cell, with a placeholder outline
      as its only original content — and it was orphaned from every toctree.
      Rewritten as a real tutorial on file structure (the `Ax0`/`Tr0` naming,
      subplot position/span, the four scales, twin axes) and added to the
      toctree. All code cells verified to run.
- [x] `Introduction.ipynb` updated from `from graf.base import *` to the public
      `import graf` API.
- [x] **Docs build added to CI**, with `-W` (warnings as errors) plus a check
      that the API pages are not empty — which is exactly how the previous stub
      escaped notice.

## 3. Project hygiene

- [x] **CI added** — `.github/workflows/ci.yml`. Two jobs:
      `test` (matrix: Linux/macOS/Windows x Python 3.10-3.13, with coverage) and
      `package`, which builds the wheel, runs `twine check`, asserts each
      required asset is physically inside the wheel, then installs it into a
      clean venv and runs a smoke test covering import, save/load, legend
      survival, font resolution, and stdout silence. That second job is the one
      that would have caught the packaging blocker.
- [x] **README rewritten.** The three editorial notes-to-self are gone;
      replaced with a working example, a comparison table against
      PNG/SVG/pickle/MATLAB, and sections on provenance, installation and
      fonts. It is the PyPI long description, so this is the shop window.
- [x] **API reference written.** `modules.rst` (an empty `toctree` producing a
      page with 0 classes and 0 functions) replaced by `docs/source/api/` —
      `graf` (the public convenience API), `base` (the file model, 71 documented
      objects), and `fonts` (22). `FORMAT.md` and `CHANGELOG.md` are now
      included in the docs site via MyST.
- [x] **Format specification written** — `FORMAT.md`, defining every field,
      the versioning rules, the enumerated values, and what GrAF does and does
      not promise. Carries a version history table.
- [x] **On-disk schema locked** — `tests/test_format_schema.py` fails on any
      added, removed, or renamed field, with a message pointing at the
      bump-version / update-spec / update-changelog procedure. Verified it
      catches a silently-added field. Format changes can no longer happen as a
      side effect of a refactor.
- [x] `CHANGELOG.md` added, written against `0.0.0.dev4` since nothing before
      this was a supported release.
- [x] `CONTRIBUTING.md` added — setup, tests, the format-change procedure, the
      docs build (including the pandoc requirement), the tabs-in-src /
      spaces-in-tests convention, and the font licence checklist.
- [x] **`src/graf/__init__.py`** now exports the public API (`import graf;
      graf.save_graf(...)`) plus `__version__`, with `__all__` pinned by a test
      so the surface is a deliberate promise rather than an accident.
      OLD: — users must write
      `from graf.base import save_graf`. v0.1.0 is the moment to fix the import
      surface, since after release it becomes a compatibility promise.
- [x] **Mutable default arguments** fixed in all three places, with tests: the
      shared `{}` meant conditions written into one figure could silently appear
      in the next one created. Supplied dicts are now copied too.
- [x] **Tracked junk cleared**: `.DS_Store` and the six committed `.graf`
      outputs under `examples/` and `docs/source/tutorials/` are untracked;
      `.gitignore` now covers `*.graf` / `*.GrAF` with a negation preserving the
      committed legacy fixture.
- [~] `TODO:` comments in `base.py`: the three font ones and the
      `dict_summary` flag are resolved. Remaining: line/marker error-checking in
      `Trace.mimic_2dline` / `mimic_errorbar`, the two "normalize these to one
      somehow" notes, subplot bounds in `Graf.mimic`, and twin-axis iteration.

## 4. Font licensing (needs a decision — see §Fonts below)

- [x] Bundle the required licence texts alongside the font files —
      `assets/fonts/LICENSES/` (OFL-SUSE, OFL-SplineSansMono, CC0-MFBOldstyle),
      plus a README with the add-a-font checklist. Ships in the wheel.
- [x] Font licence policy DECIDED & enforced: OFL 1.1 / CC0 / Apache-2.0 /
      MIT only, as `ALLOWED_FONT_LICENSES` in `base.py`, checked by
      `tests/test_fonts.py` and documented in `assets/fonts/LICENSES/README.md`.
- [x] Licence metadata (`license`, `copyright`, `source_url`, `license_file`)
      added to every family in `portable_fonts.json`, with tests asserting the
      fields exist AND that the referenced licence file actually ships.
- [x] Fallback DECIDED & implemented: unknown family falls back to
      `FALLBACK_FONT` ('sanserif') and warns. Resolves the `#TODO: Apply a
      default font if family not found`.

### Bundled font licence status (verified from embedded `name` tables)

| Family | Licence | Redistributable | Obligation |
|---|---|---|---|
| SUSE (Regular, Bold) | SIL OFL 1.1 | Yes | Ship OFL text + copyright notice; "SUSE" is a SUSE trademark |
| Spline Sans Mono (Reg, Bold, Italic) | SIL OFL 1.1 | Yes | Ship OFL text + copyright notice |
| MFB Oldstyle (Reg, Bold, Italic) | CC0 1.0 | Yes | None (public domain); attribution is courtesy |

No licence file is currently bundled with any of them — that is the compliance
gap, not the redistribution right itself.

---

## Done

- [x] Remove the `matlab/` folder (moved to its own project).
- [x] Remove `scripts/grafscript.py` (never implemented) — also removed the now
      dangling `graf-script` console-script entry point from `pyproject.toml`,
      which would have installed a command that raised `ModuleNotFoundError`.
- [x] Add `MANIFEST.in` so the sdist carries assets and licences too.
