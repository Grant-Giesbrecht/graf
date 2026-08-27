# Test fixtures

`legacy_format_0_0_0.graf` was written by the pre-release GrAF at commit
`2d8f59a`, using that version's own code — not synthesised to look old. It is
the regression test for reading files that predate format 1.0.

Do not regenerate or "fix" it. Its value is precisely that it is a genuine
artefact of the old layout: `Font` carries `font`/`bold`/`italic` instead of
`family`/`weight`/`style`, and `Axis` has no `legend_on`. If a future format
change breaks it, that is real information about real files on real disks.
