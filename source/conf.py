# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import shutil

project = 'MySlate'
copyright = '2023, TEEE'
author = 'TEEE'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

source_suffix = ['.rst', '.md']

extensions = ['recommonmark']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['pages/_static']

language = 'zh_CN'

html_show_sourcelink = False

html_context = {
    "display_github": False, # Add 'Edit on Github' link instead of 'View page source'
    "last_updated": True,
    "commit": False,
}

html_js_files = [
    'js/baidutongji.js'
]
