# -*- coding: utf-8 -*-
import os
import sys
import pathlib
import datetime
from configparser import ConfigParser

from pkg_resources import get_distribution
from sphinx_astropy.conf.v1 import *

conf = ConfigParser()

conf.read([os.path.join(os.path.dirname(__file__), '..', 'setup.cfg')])
setup_cfg = dict(conf.items('metadata'))

# -- General configuration ----------------------------------------------------

# By default, highlight as Python 3.
highlight_language = 'python3'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns.append('_templates')

# This is added to the end of RST files - a good place to put substitutions to
# be used globally.
rst_epilog += """
"""

intersphinx_mapping.pop("h5py")
intersphinx_mapping['sunpy'] = ('http://docs.sunpy.org/en/latest/', None)
intersphinx_mapping['ndcube'] = ('http://docs.sunpy.org/projects/ndcube/en/latest/', None)
intersphinx_mapping['gwcs'] = ('http://gwcs.readthedocs.io/en/latest/', None)
intersphinx_mapping['asdf'] = ('http://asdf.readthedocs.io/en/latest/', None)
intersphinx_mapping['dask'] = ('http://dask.pydata.org/en/latest/', None)

automodsumm_inherited_members = True

# -- Project information ------------------------------------------------------

# This does not *have* to match the package name, but typically does
project = setup_cfg['name']
author = setup_cfg['author']
copyright = '{0}, {1}'.format(
    datetime.datetime.now().year, setup_cfg['author'])

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.


release = get_distribution(setup_cfg['name']).version
version = '.'.join(release.split('.')[:3])
is_development = '.dev' in release

# -- Options for HTML output --------------------------------------------------

try:
    from dkist_sphinx_theme.conf import *
except ImportError:
    html_theme = 'default'

# Disable the links to the internal projects
html_theme_options = {'navbar_links': []}

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = '{0} v{1}'.format(project, release)

# Output file base name for HTML help builder.
htmlhelp_basename = project + 'doc'

# Remove numpydoc
extensions.remove('numpydoc')
extensions.append('sphinx.ext.napoleon')

# Disable having a separate return type row
napoleon_use_rtype = False
# Disable google style docstrings
napoleon_google_docstring = False

# -- Options for LaTeX output -------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [('index', project + '.tex', project + u' Documentation',
                    author, 'manual')]

# -- Options for the edit_on_github extension ---------------------------------

if str(setup_cfg.get('edit_on_github')).lower() == "true":
    extensions += ['sphinx_astropy.ext.edit_on_github']

    edit_on_github_project = setup_cfg['github_project']
    if release == version:
        edit_on_github_branch = "v" + release
    else:
        edit_on_github_branch = "master"

    edit_on_github_source_root = ""
    edit_on_github_doc_root = "docs"

# -- Resolving issue number to links in changelog -----------------------------
github_issues_url = 'https://github.com/{0}/issues/'.format(setup_cfg['github_project'])


# -- Sphinx Gallery -----------------------------
extensions += ["sphinx_gallery.gen_gallery"]
path = pathlib.Path.cwd()
example_dir = path.parent.joinpath('examples')

sphinx_gallery_conf = {
    # path to store the module using example template
    'backreferences_dir': path.joinpath('generated', 'modules'),
    # execute all examples except those that start with "skip_"
    'filename_pattern': '^((?!skip_).)*$',
    'examples_dirs': example_dir,  # path to the examples scripts
    'gallery_dirs': path.joinpath('generated', 'gallery'),  # path to save gallery generated examples
    'default_thumb_file': str(path.joinpath('logo', 'icon_square.jpg')),
    # 'reference_url': {
    #     'sunpy': 'http://docs.sunpy.org/en/latest',
    #     'astropy': 'http://docs.astropy.org/en/latest',
    #     'matplotlib': 'https://matplotlib.org',
    #     'numpy': 'http://docs.scipy.org/doc/numpy',
    # },
    'abort_on_example_error': True,
    'plot_gallery': True,
    'download_all_examples': False
}

"""
Write the latest changelog into the documentation.
"""
target_file = os.path.abspath("./whatsnew/latest_changelog.txt")
try:
    from sunpy.util.towncrier import generate_changelog_for_docs
    if is_development:
        generate_changelog_for_docs("../", target_file)
except Exception as e:
    print(f"Failed to add changelog to docs with error {e}.")

# Make sure the file exists or else sphinx will complain.
open(target_file, 'a').close()
