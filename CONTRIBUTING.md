# Contributing to GrAF

Thanks for your interest. This file covers the practical things: how to get set
up, how to run the tests, and — most importantly — what to do if your change
touches the file format.

## Setting up

```bash
git clone https://github.com/Grant-Giesbrecht/graf
cd graf
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # everything, including the Qt viewer
```

GrAF requires Python 3.10+.

`[dev]` pulls in both extras. If you are not touching the viewer, `pip install
-e ".[test]"` is enough and skips a 235 MB Qt download.

### The GUI dependencies are optional

PyQt6 and mplcursors ship in the `gui` extra, not the base install — nothing in
the save/load path needs a GUI toolkit, and Qt is larger than everything else
combined. **`graf.base` and `graf/__init__.py` must never import `graf.widgets`,
directly or transitively.** `tests/test_optional_gui.py` enforces this by
importing `graf` in a subprocess and asserting PyQt6 never lands in
`sys.modules`; CI's main job installs without the extra for the same reason.

If you add a feature that needs Qt, it belongs in `graf.widgets` behind that
boundary.

## Running the tests

```bash
pytest tests/ -q                                    # the suite
pytest tests/ --cov=graf --cov-report=term-missing  # with coverage
```

The suite is headless (`tests/conftest.py` selects matplotlib's `Agg` backend
before anything else imports matplotlib) and should run in a few seconds. Please
keep it that way — a slow suite stops being run.

New behaviour needs a test. Tests that pin down a *past bug* are especially
welcome: several in this repo exist because a one-line change once silently
destroyed data, and the test is what stops it happening twice.

## Changing the file format — read this first

**A `.graf` file is a promise.** People keep figures for years and open them
with tools written in other languages. Anything that changes what is written to
disk is a change to that promise, not an implementation detail.

The on-disk schema is locked by `tests/test_format_schema.py`. It fails on any
added, removed, or renamed field. **That failure is the mechanism, not an
obstacle** — do not update the expected values to make it pass. Instead:

1. Decide whether the change is genuinely necessary. A field added is a field
   every reader must tolerate forever.
2. Bump `GRAF_FORMAT_VERSION` in `src/graf/base.py`:
   - additive (a new optional field) → MINOR, `1.0` → `1.1`
   - removal, rename, or type change → MAJOR, `1.0` → `2.0`, which makes every
     existing file unreadable by this library
3. Update `FORMAT.md`, including its version history table.
4. Add a `CHANGELOG.md` entry under a **File format** heading.
5. Only then update the expected schema in the test.

Prefer additive changes. Since stardust-tools 0.2.0, a field missing from a file
takes its default rather than aborting the load, so adding a field is backward
compatible for free. Give every new field a default that represents "this file
predates the field", and reproduces how such a file previously behaved.

If you must make a breaking change, consider the expand/contract route: write
both the old and new fields for one MINOR release, then drop the old ones at the
next MAJOR. Nobody breaks in between.

## Building the docs

```bash
pip install -r docs/requirements.txt
sphinx-build -b html docs/source docs/_build
```

**You need `pandoc` installed** — nbsphinx shells out to it to convert the
tutorial notebooks, and without it the build fails outright. On macOS,
`brew install pandoc`; on Debian/Ubuntu, `apt install pandoc`. Read the Docs
installs it via `apt_packages` in `.readthedocs.yaml`.

Notebooks are executed at build time (`nbsphinx_execute = 'always'`) with
`nbsphinx_allow_errors = False`, so a tutorial that no longer runs fails the
build rather than shipping broken output. If you change the API, check the
tutorials still work.

## Style

Match the file you are editing. In practice:

- `src/` is **tab-indented**.
- `tests/` is **4-space indented**.

Both are longstanding; please do not reformat a file wholesale as part of an
unrelated change, since it buries the real diff.

Comments should explain *why*, not restate *what*. The valuable comments in this
codebase are the ones recording a constraint that is not visible from the code —
why the library must never print on a save, why a fallback stays within a font
class, why unpacking is verified after the fact.

## Adding a bundled font

Fonts are redistributed inside the wheel, so there is a licence checklist. See
`src/graf/assets/fonts/LICENSES/README.md`. In short: the licence must be OFL
1.1, CC0, Apache-2.0, or MIT; its text must ship alongside the font; and
`portable_fonts.json` must record `license`, `copyright`, `source_url`, and
`license_file`. `tests/test_fonts.py` enforces all of it.

Bear in mind that every bundled font costs every user download size forever.
Adding a font path or setting a default (`graf.add_font_path`,
`graf.set_font_default`) solves most cases without touching the package.

## Reporting bugs

Please include the GrAF version (`python -c "import graf; print(graf.__version__)"`),
the format version of any file involved, and a minimal script. If a file fails
to load, `Graf.unpack_report` lists what could not be read and is worth
including.

Do not attach files containing unpublished data — a `.graf` contains the full
dataset, not just a picture of it.
