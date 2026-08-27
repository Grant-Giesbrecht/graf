"""GrAF -- Graph Archive Format.

A file format for preserving scientific graphs together with their underlying
data, in a way that stays readable across languages and across the years.

The public API is re-exported here so callers can write::

    import graf
    graf.save_graf(fig, "figure.graf")
    fig = graf.load_graf("figure.graf")

Two versions matter and are deliberately kept separate:

  __version__          the version of this Python library
  GRAF_FORMAT_VERSION  the version of the on-disk file layout

They move independently. A library release that only fixes a bug does not
change the format, and a reader must judge a file by the format version alone.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
	__version__ = _pkg_version("graf-format")
except PackageNotFoundError:  # running from a source tree without an install
	__version__ = "0.0.0+unknown"

from graf.base import (
	GRAF_FORMAT_VERSION,
	GrafFormatError,
	GrafVersionError,
	Graf,
	GraphStyle,
	Font,
	Axis,
	Trace,
	Surface,
	Scale,
	MetaInfo,
	save_graf,
	load_graf,
	available_font_families,
)

__all__ = [
	"__version__",
	"GRAF_FORMAT_VERSION",
	"GrafFormatError",
	"GrafVersionError",
	"Graf",
	"GraphStyle",
	"Font",
	"Axis",
	"Trace",
	"Surface",
	"Scale",
	"MetaInfo",
	"save_graf",
	"load_graf",
	"available_font_families",
]
