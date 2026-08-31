# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from importlib.metadata import PackageNotFoundError, version as _pkg_version

# Document the source tree, not whatever happens to be installed.
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------

project = 'graf'
copyright = '2026, Grant Giesbrecht'
author = 'Grant Giesbrecht'

# Read the version from the installed package rather than hardcoding it, so the
# docs cannot drift from the release they describe.
try:
	release = _pkg_version("graf-format")
except PackageNotFoundError:
	release = "0.0.0+unknown"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.autosummary',
	'sphinx.ext.napoleon',
	'sphinx.ext.viewcode',
	'sphinx.ext.intersphinx',
	'myst_parser',
	'nbsphinx',
]

templates_path = ['_templates']
exclude_patterns = ['.DS_Store', '**.ipynb_checkpoints']
language = 'en'
pygments_style = 'sphinx'

# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
	'members': True,
	'undoc-members': True,
	'show-inheritance': True,
	'member-order': 'bysource',
}
autodoc_typehints = 'description'
autosummary_generate = True

# The Qt viewer is not importable in a headless docs build, and mplcursors is
# only needed by it. Mocking them keeps the rest of the API documentable.
autodoc_mock_imports = ['PyQt6', 'mplcursors']

# -- Notebooks ---------------------------------------------------------------


def _ensure_pandoc_on_path():
	"""Guarantee nbsphinx can find pandoc.

	nbsphinx converts notebooks by shelling out to pandoc (via
	nbconvert.utils.pandoc), so it only ever looks on PATH -- installing the
	pypandoc wheel is not enough on its own. If pandoc is missing, nbsphinx
	raises and the *entire* build dies, producing no HTML at all. On Read the
	Docs that is especially misleading: the previous successful build stays
	published, so new pages simply 404 while the dashboard shows a recent build.

	System pandoc is preferred (.readthedocs.yaml installs it via apt_packages).
	This falls back to the copy bundled with pypandoc-binary, so the docs build
	on any machine without anyone having to install pandoc system-wide.
	"""

	import shutil

	if shutil.which('pandoc'):
		return

	try:
		import pypandoc
		bundled = os.path.dirname(pypandoc.get_pandoc_path())
	except Exception as e:
		raise RuntimeError(
			"pandoc was not found and the pypandoc fallback is unavailable "
			f"({e}). nbsphinx needs pandoc to convert the tutorial notebooks. "
			"Install it with your package manager (brew install pandoc / "
			"apt install pandoc), or pip install pypandoc-binary."
		) from e

	os.environ['PATH'] = bundled + os.pathsep + os.environ.get('PATH', '')


_ensure_pandoc_on_path()

# Notebooks are executed at build time so their output always matches the
# version being documented.
nbsphinx_execute = 'always'
nbsphinx_allow_errors = False   # a tutorial that no longer runs must fail loudly
nbsphinx_kernel_name = 'python3'
nbsphinx_timeout = 300

# -- MyST --------------------------------------------------------------------

myst_enable_extensions = ['colon_fence', 'deflist']
myst_heading_anchors = 3

# -- Cross-project references ------------------------------------------------

intersphinx_mapping = {
	'python': ('https://docs.python.org/3', None),
	'matplotlib': ('https://matplotlib.org/stable/', None),
	'numpy': ('https://numpy.org/doc/stable/', None),
}

# -- HTML output -------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f"GrAF {release}"
