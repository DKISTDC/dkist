"""
Configuration file for the Sphinx documentation builder.
"""
# -- stdlib imports ------------------------------------------------------------
import datetime
import os
import sys
import warnings

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
# This needs to be done before sunpy is imported
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

# -- Project information -------------------------------------------------------
project = "DKIST"
author = "NSO / AURA"
copyright = f"{datetime.datetime.now().year}, {author}"

# The full version, including alpha/beta/rc tags
release = __version__
dkist_version = Version(__version__)
is_release = not(dkist_version.is_prerelease or dkist_version.is_devrelease)

# We want to ignore all warnings in a release version.
if is_release:
    warnings.simplefilter("ignore")

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
# templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "jupyter_execute", "**/*_NOTES.md"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ".rst"

myst_enable_extensions = ["colon_fence", "dollarmath", "substitution"]

# The master toctree document.
master_doc = "index"

# The reST default role (used for this markup: `text`) to use for all
# documents. Set to the "smart" one.
default_role = "obj"

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
    "python": (
        "https://docs.python.org/3/",
        (None, "http://www.astropy.org/astropy-data/intersphinx/python3.inv"),
    ),
    "numpy": (
        "https://numpy.org/doc/stable/",
        (None, "http://www.astropy.org/astropy-data/intersphinx/numpy.inv"),
    ),
    "scipy": (
        "https://docs.scipy.org/doc/scipy/",
        (None, "http://www.astropy.org/astropy-data/intersphinx/scipy.inv"),
    ),
    "matplotlib": (
        "https://matplotlib.org/stable/",
        (None, "http://www.astropy.org/astropy-data/intersphinx/matplotlib.inv"),
    ),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "parfive": ("https://parfive.readthedocs.io/en/stable/", None),
    "sunpy": ("https://docs.sunpy.org/en/stable/", None),
    "ndcube": ("https://docs.sunpy.org/projects/ndcube/en/latest/", None),
    "gwcs": ("https://gwcs.readthedocs.io/en/latest/", None),
    "asdf": ("https://asdf.readthedocs.io/en/latest/", None),
    "dask": ("https://dask.pydata.org/en/latest/", None),
}

# -- Options for HTML output ---------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

from dkist_sphinx_theme.conf.theme import *

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# Render inheritance diagrams in SVG
graphviz_output_format = "svg"

graphviz_dot_args = [
    "-Nfontsize=10",
    "-Nfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Efontsize=10",
    "-Efontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Gfontsize=10",
    "-Gfontname=Helvetica Neue, Helvetica, Arial, sans-serif"
]

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
