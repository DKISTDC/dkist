"""
Configuration file for the Sphinx documentation builder.
"""
# -- stdlib imports ------------------------------------------------------------

import datetime
import os
import sys

from packaging.version import Version
from pkg_resources import get_distribution

# -- Check for dependencies ----------------------------------------------------

doc_requires = get_distribution("dkist").requires(extras=("docs",))
missing_requirements = []
for requirement in doc_requires:
    try:
        get_distribution(requirement)
    except Exception:
        missing_requirements.append(requirement.name)
if missing_requirements:
    print(
        f"The {' '.join(missing_requirements)} package(s) could not be found and "
        "is needed to build the documentation, please install the 'docs' requirements."
    )
    sys.exit(1)

# -- Read the Docs Specific Configuration --------------------------------------

on_rtd = os.environ.get("READTHEDOCS", None) == "True"
if on_rtd:
    os.environ["SUNPY_CONFIGDIR"] = "/home/docs/"
    os.environ["HOME"] = "/home/docs/"
    os.environ["LANG"] = "C"
    os.environ["LC_ALL"] = "C"
    os.environ["HIDE_PARFIVE_PROGESS"] = "True"

# -- Non stdlib imports --------------------------------------------------------

import dkist  # noqa
from dkist import __version__

# -- Project information -----------------------------------------------------

# The full version, including alpha/beta/rc tags

_version = Version(__version__)
version = release = str(_version)
# Avoid "post" appearing in version string in rendered docs
if _version.is_postrelease:
    version = release = _version.base_version
# Avoid long githashes in rendered Sphinx docs
elif _version.is_devrelease:
    version = release = f"{_version.base_version}.dev{_version.dev}"
is_development = _version.is_devrelease
is_release = not(_version.is_prerelease or _version.is_devrelease)

project = "DKIST"
author = "NSO / AURA"
copyright = f"{datetime.datetime.now().year}, {author}"

# -- General configuration ---------------------------------------------------

# Suppress warnings about overriding directives as we overload some of the
# doctest extensions.
suppress_warnings = ["app.add_directive", ]

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "matplotlib.sphinxext.plot_directive",
    "sphinx_automodapi.automodapi",
    "sphinx_automodapi.smart_resolver",
    "sphinx_changelog",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",  # must be loaded after napoleon
    "sunpy.util.sphinx.doctest",
    "sunpy.util.sphinx.generate",
    "myst_nb",
    "sphinx_design",
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "jupyter_execute", "**/*_NOTES.md"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ".rst"

myst_enable_extensions = ["colon_fence", "dollarmath", "substitution"]

# The master toctree document.
master_doc = "index"

# Treat everything in single ` as a Python reference.
default_role = "py:obj"

napoleon_use_rtype = False

# Disable google style docstrings
napoleon_google_docstring = False

# Enable showing inherited members by default
automodsumm_inherited_members = True

# Type Hint Config
typehints_fully_qualified = False
typehints_use_rtype = napoleon_use_rtype
typehints_defaults = "comma"

# -- Options for intersphinx extension -----------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "parfive": ("https://parfive.readthedocs.io/en/stable/", None),
    "sunpy": ("https://docs.sunpy.org/en/stable/", None),
    "ndcube": ("https://docs.sunpy.org/projects/ndcube/en/stable/", None),
    "gwcs": ("https://gwcs.readthedocs.io/en/latest/", None),
    "asdf": ("https://asdf.readthedocs.io/en/stable/", None),
    "dask": ("https://dask.pydata.org/en/stable/", None),
    "reproject": ("https://reproject.readthedocs.io/en/stable/", None),
}

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

from dkist_sphinx_theme.conf.theme import *

# Render inheritance diagrams in SVG
graphviz_output_format = "svg"

graphviz_dot_args = [
    "-Nfontsize=10",
    "-Nfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Efontsize=10",
    "-Efontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Gfontsize=10",
    "-Gfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# By default, when rendering docstrings for classes, sphinx.ext.autodoc will
# make docs with the class-level docstring and the class-method docstrings,
# but not the __init__ docstring, which often contains the parameters to
# class constructors across the scientific Python ecosystem. The option below
# will append the __init__ docstring to the class-level docstring when rendering
# the docs. For more options, see:
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autoclass_content
autoclass_content = "both"

# Use a high-contrast code style from accessible-pygments
# Our theme isn't using the correct background colours for code blocks, so this
# isn't as high-contrast as it should be.
pygments_style = "github-light"

# -- MyST_NB -------------------------------------------------------------------

nb_execution_allow_errors = False
nb_execution_in_temp = True
nb_execution_mode = "auto"
nb_execution_timeout = 300
nb_output_stderr = "show"
nb_execution_show_tb = True
