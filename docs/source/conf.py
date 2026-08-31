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

# Notebooks are executed at build time so their output always matches the
# version being documented. nbsphinx needs pandoc, which .readthedocs.yaml
# installs via apt_packages -- without it the whole build fails.
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
