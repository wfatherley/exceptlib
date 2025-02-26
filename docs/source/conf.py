import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "exceptlib"
copyright = "2025, Will Fatherley"
author = "Will Fatherley"
release = "2025.1"

sys.path.insert(0, os.path.abspath("../../src"))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "classic"
body_min_width = "100%"
nodsidebar = True
html_static_path = ["_static"]
