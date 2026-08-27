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
   `family`, `role`, `faces`, `license`, `copyright`, `source_url`, and
   `license_file`. `test_fonts.py` asserts these are present and that the
   referenced licence file actually exists in the built wheel.
4. **Aliases must not include a generic role.** `serif`, `sans-serif` and
   `monospace` are roles, bound to a family by `role_defaults` and overridable
   by the user. A family claiming one as an alias would make "any serif"
   inexpressible. This is enforced in `load_manifest` and tested.
5. **The reserved font name, if any, is respected.** OFL families may declare a
   Reserved Font Name; if GrAF ever modifies or subsets such a font, the result
   must be renamed. GrAF currently ships fonts unmodified, so this does not
   apply.
6. **Trademarks are noted but not assumed.** "SUSE", for example, is a SUSE
   trademark; the OFL licenses the font files, not the mark.
7. **The file pattern is covered in `pyproject.toml`.** `[tool.setuptools.package-data]`
   lists the extensions that ship; a new format (e.g. `.woff2`) needs a new
   entry or it will be silently dropped from the wheel.

Note that OFL 1.1 forbids selling the fonts *by themselves*, which does not
restrict GrAF: they are bundled as part of a larger work and GrAF is MIT.

## How a request is resolved

A `.graf` stores an ordered *font stack*, most specific first, ending in a
generic role — `["MFB Oldstyle", "Georgia", "serif"]`. For each candidate GrAF
looks in:

1. fonts bundled here,
2. directories in the user's `font_paths`,
3. fonts installed on the system.

First hit wins. If nothing matches, the trailing role decides, so a serif
request degrades to another serif rather than jumping font class. GrAF warns
once, naming what was asked for and what was used.

This is deliberate: GrAF promises the data and the scientific message survive,
and explicitly does not promise identical typography across machines. A missing
typeface must degrade the look, never block reconstruction — and the file
records `resolved_family` so a reader can always tell reproduction from
substitution.

## Adding fonts without bundling them

Bundled fonts cost every user download size forever, so the bar is high. Users
who want their own typefaces should not need a GrAF release:

```python
graf.add_font_path("~/Library/Fonts")
graf.set_font_default("serif", "EB Garamond")
```

Both persist to the per-user config (`graf.user_config_path()`).
