# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'graf'
copyright = '2024, Grant Giesbrecht'
author = 'Grant Giesbrecht'
release = '0.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.napoleon',
	'nbsphinx',
]

nbsphinx_execute = 'always'
nbsphinx_allow_errors = True
nbsphinx_kernel_name = 'python3'
numpydoc_show_class_members = False
nbsphinx_timeout = 180

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

templates_path = ['_templates']
exclude_patterns = ['.DS_Store']

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
