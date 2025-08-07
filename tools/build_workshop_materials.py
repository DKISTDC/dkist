# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "nbformat",
#   "markdown-it-py",
#   "myst_parser",
#   "sphinx",
#   "jupytext",
#   "sphobjinv",
#   "mdformat",
#   "mdformat_myst",
# ]
# ///
"""
This script converts the tutorial from the documentation into workshop.

The learner notebooks will have all the code stripped from the code cells unless
they have "keep-inputs" in their tags.
"""

import sys
import argparse
import subprocess
from pathlib import Path
from textwrap import dedent
from functools import cache
from collections import defaultdict
from urllib.parse import urljoin

import mdformat.plugins
import nbformat
from markdown_it import MarkdownIt
from mdformat.renderer import MDRenderer
from mdformat_myst.plugin import _role_renderer
from myst_parser.config.main import MdParserConfig
from myst_parser.parsers.directives import parse_directive_text
from myst_parser.parsers.mdit import create_md_parser
from sphinx.directives.other import TocTree
from sphobjinv import Inventory

HREF_TEMPLATE = '<a href="{url}" target="_blank" style="text-decoration: underline">{name}</a>'


def strip_code_cells(input_notebook, output_notebook):
    with open(input_notebook) as fp:
        raw_notebook = nbformat.read(fp, as_version=4)

    for i, cell in enumerate(raw_notebook.get("cells")):
        if cell.cell_type == "code" and "keep-input" not in cell.metadata.get("tags", []):
            cell.source = []
        # Make the id predictable to reduce diffs
        cell["id"] = str(i)

    with open(output_notebook, "w") as fp:
        nbformat.write(raw_notebook, fp)


def get_first_h1(markdown_file):
    with open(markdown_file) as fobj:
        for line in fobj.readlines():
            if line.startswith("# "):
                return line.split("# ")[1].strip()
    return ""


def build_toc_links(toc_files):
    titles = {}
    for name, (source, *_) in toc_files.items():
        titles[name] = get_first_h1(source)

    links = defaultdict(list)
    for name, title in titles.items():
        _, instructor, learner, section = toc_files[name]
        links[section].append(
            HREF_TEMPLATE.format(url=str(learner), name=title)
            + " - "
            + HREF_TEMPLATE.format(url=str(instructor), name="Instructor")
        )

    parts = ["## Contents"]
    for section, slinks in links.items():
        parts += [f"### {section.capitalize()}"]
        parts += [f"1. {link}" for link in slinks]

    return "\n".join(parts)


def add_toctree_to_index(toc_files, input_notebook, output_notebook):
    with open(input_notebook) as fp:
        raw_notebook = nbformat.read(fp, as_version=4)

    for cell in raw_notebook.get("cells"):
        if "{toctree}" in cell.source:
            cell.source = build_toc_links(toc_files)

    with open(output_notebook, "w") as fp:
        nbformat.write(raw_notebook, fp)


def parse_toctree_directive(filepath):
    content = filepath.read_text()
    tokens = MarkdownIt("commonmark").parse(content)
    toctrees = [token for token in tokens if token.info == "{toctree}"]
    toctree_info = parse_directive_text(TocTree, "", toctrees[0].content)
    return toctree_info.body


@cache
def build_inventory_map():
    inventory_map = {}
    urls = (
        "https://docs.dkist.nso.edu/projects/python-tools/en/stable/",
        "https://docs.python.org/3/",
        "https://numpy.org/doc/stable/",
        "https://docs.scipy.org/doc/scipy/",
        "https://matplotlib.org/stable/",
        "https://docs.astropy.org/en/stable/",
        "https://parfive.readthedocs.io/en/stable/",
        "https://docs.sunpy.org/en/stable/",
        "https://docs.sunpy.org/projects/ndcube/en/stable/",
        "https://gwcs.readthedocs.io/en/latest/",
        "https://asdf.readthedocs.io/en/stable/",
        "https://dask.pydata.org/en/stable/",
        "https://reproject.readthedocs.io/en/stable/",
        "https://docs.dkist.nso.edu/projects/data-products/en/stable/",
    )
    for url in urls:
        inv = Inventory(url=url + "objects.inv")
        for i in inv.objects:
            ourl = i.uri
            if i.uri.endswith("$"):
                ourl = i.uri.replace("$", i.name)
            ourl = urljoin(url, ourl)
            name = i.name if i.dispname == "-" else i.dispname
            inventory_map[i.name] = (name, ourl)

    return inventory_map


def intersphinx_role_renderer(node, context):
    role_name = node.meta["name"]
    node_content = node.content.removeprefix("~")

    inv_map = build_inventory_map()

    # If it's not a special lookup then don't bother
    if role_name not in ("ref", "obj") or node_content not in inv_map:
        return _role_renderer(node, context)

    name, url = inv_map[node_content]
    if role_name == "obj":
        name = f"`{name}`"
    return HREF_TEMPLATE.format(url=url, name=name)


def md_format_cell(src):
    """
    Given some markdown text format it and transform ref roles to http links.
    """
    # To do this we build a markdown it parser, with a mdformat render
    # (to render back to markdown) but we modify the role renderer.

    mdit = create_md_parser(MdParserConfig(), MDRenderer)
    parser_extensions = mdformat.plugins.PARSER_EXTENSIONS
    parser_extensions["myst"].RENDERERS["myst_role"] = intersphinx_role_renderer
    mdit.options["parser_extension"] = list(parser_extensions.values())
    return mdit.render(src)


def parse_all_cells(input_notebook, output_notebook):
    with open(input_notebook) as fp:
        raw_notebook = nbformat.read(fp, as_version=4)

    for cell in raw_notebook.get("cells"):
        if cell["cell_type"] == "markdown":
            cell.source = md_format_cell(cell.source)

    with open(output_notebook, "w") as fp:
        nbformat.write(raw_notebook, fp)


def write_conda_env(filepath):
    env = dedent("""\
      channels:
        - conda-forge

      dependencies:
        - python=3.12
        - dkist
        - ipympl
        - ipywidgets
        - distributed
        - jupyterlab-myst
        - notebook
        - distributed
        - bokeh
    """)
    with open(filepath, "w") as fobj:
        fobj.write(env)


def write_postBuild(directory):
    content = 'python -c "from dkist.data.sample import download_all_sample_data; download_all_sample_data()"'
    with open(directory / "postBuild", "w") as fobj:
        fobj.write(content)


if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument(
        "docs_dir", nargs="?", help="path to the documentation root", default="./docs/", type=str
    )
    argp.add_argument("output_dir", nargs="?", help="path to the output directory", default="./workshop", type=str)
    argp.add_argument("extra_dirs", nargs="*", help="directories inside docs_dir to build notebooks for", default=["examples"], type=str)
    argp.add_argument("tutorial_dir", nargs="?", help="The directory name for the main tutorial", default="tutorial", type=str)

    args = argp.parse_args(sys.argv[1:])

    docs_dir = Path(args.docs_dir).absolute()
    output_dir = Path(args.output_dir).absolute()
    output_dir.mkdir(exist_ok=True)

    tutorial_dir = docs_dir / args.tutorial_dir
    tutorial_index_file = tutorial_dir / "index.md"

    toc_files = {}

    for inc_dir in [args.tutorial_dir, *args.extra_dirs]:
        input_dir = docs_dir / inc_dir
        index_filename = docs_dir / inc_dir / "index.md"

        file_stems = parse_toctree_directive(index_filename)

        # This can probably made considerably more robust and flexible, but not today
        # Copy all .png files to the new folder, both for learners and instructors
        for img_file in input_dir.glob("*png"):
            subprocess.run(["cp", img_file, output_dir])
            subprocess.run(["cp", img_file, output_dir / "instructor"])

        # For each file in the toc tree make an instructor notebook, then make a learner
        # notebook without the source cells.
        for stem in [*file_stems] + ([index_filename.stem] if args.tutorial_dir == inc_dir else []):
            input_file = list(input_dir.glob(stem + ".*"))
            if len(input_file) > 1:
                raise ValueError(f"More than one input file matching {stem}.* found")
            if not input_file:
                raise ValueError(f"File {stem} not found")

            input_file = input_file[0]
            instructor_file = output_dir / "instructor"
            instructor_file.mkdir(exist_ok=True)
            instructor_file /= input_file.stem + ".ipynb"
            learner_file = output_dir / (input_file.stem + ".ipynb")
            if input_file.name != "index.md":
                toc_files[stem] = (
                    input_file,
                    instructor_file.relative_to(output_dir),
                    learner_file.relative_to(output_dir),
                    inc_dir
                )

            subprocess.run([sys.executable, "-m", "jupytext", "--to", "ipynb", input_file, "-o", instructor_file])
            # Format the output notebook
            parse_all_cells(instructor_file, instructor_file)
            print(f"[learner] transforming {instructor_file} to {learner_file}")  # noqa: T201
            strip_code_cells(instructor_file, learner_file)

    # Write toctree to the tutorial index for all files in all dirs
    index_notebooks = [output_dir / "index.ipynb", output_dir / "instructor" / "index.ipynb"]
    # Replace the sphinx toctree with a simple list of links
    for index in index_notebooks:
        add_toctree_to_index(toc_files, index, index)

    print("Writing conda env file")  # noqa: T201
    write_conda_env(output_dir / "environment.yml")
    print("Writing postBuild file")  # noqa: T201
    write_postBuild(output_dir)
