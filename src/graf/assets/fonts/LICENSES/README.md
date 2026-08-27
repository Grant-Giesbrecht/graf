# Bundled font licences

GrAF ships a small set of "portable" fonts so that a `.graf` file renders
consistently on a machine that does not have the original author's fonts
installed. Every font redistributed here is under a licence that permits
redistribution, and each family's licence text sits beside it in this
directory.

| Family | Files | Licence | Text |
|---|---|---|---|
| SUSE | `SUSE-Regular.ttf`, `SUSE-Bold.ttf` | SIL OFL 1.1 | `OFL-SUSE.txt` |
| Spline Sans Mono | `SplineSansMono-{Regular,Bold,Italic}.ttf` | SIL OFL 1.1 | `OFL-SplineSansMono.txt` |
| MFB Oldstyle | `MFBOldstyle-{Regular,Bold,Italic}.otf` | CC0 1.0 | `CC0-MFBOldstyle.txt` |

Licence facts above were read from each file's embedded `name` table, not from
a third-party summary.

## Policy

GrAF bundles a font only if it is under **SIL OFL 1.1, CC0, Apache-2.0, or
MIT/X11**. These are the licences that unambiguously permit redistributing the
font inside a larger package. Anything merely "free to download", "free for
personal use", or licensed per-seat is out, regardless of how good it looks.

This list is enforced in code: `ALLOWED_FONT_LICENSES` in `graf/base.py`, and
`tests/test_fonts.py` fails if any declared family falls outside it.

## Adding a font

Before adding a family, confirm all of the following:

1. **The licence is on the allow-list above** and permits redistribution inside
   another package.
2. **The licence text ships with the font.** OFL 1.1 requires it. Add the text
   to this directory, prefixed with the family's own copyright line, and add a
   row to the table above.
3. **`portable_fonts.json` records the metadata.** Every family must carry
   `license`, `copyright`, `source_url`, and `license_file`. `test_fonts.py`
   asserts these are present and that the referenced licence file actually
   exists in the built wheel.
4. **The reserved font name, if any, is respected.** OFL families may declare a
   Reserved Font Name; if GrAF ever modifies or subsets such a font, the result
   must be renamed. GrAF currently ships fonts unmodified, so this does not
   apply.
5. **Trademarks are noted but not assumed.** "SUSE", for example, is a SUSE
   trademark; the OFL licenses the font files, not the mark.
6. **The file pattern is covered in `pyproject.toml`.** `[tool.setuptools.package-data]`
   lists the extensions that ship; a new format (e.g. `.woff2`) needs a new
   entry or it will be silently dropped from the wheel.

Note that OFL 1.1 forbids selling the fonts *by themselves*, which does not
restrict GrAF: they are bundled as part of a larger work and GrAF is MIT.

## Fallback

When a `.graf` file names a family this installation does not bundle, GrAF falls
back to `FALLBACK_FONT` (currently `sanserif`) and emits a warning. This is
deliberate: GrAF promises the data and the scientific message survive, and
explicitly does not promise identical typography across machines. A missing
typeface degrades the look; it must never block reconstruction. The warning
exists so the drift is visible rather than silent.
