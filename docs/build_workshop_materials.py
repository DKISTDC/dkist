# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "nbformat",
#   "markdown-it-py",
#   "myst_parser",
#   "sphinx",
#   "jupytext",
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

import nbformat
from markdown_it import MarkdownIt
from myst_parser.parsers.directives import parse_directive_text
from sphinx.directives.other import TocTree


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
    for name, (source, instructor, learner) in toc_files.items():
        titles[name] = get_first_h1(source)

    links = []
    for name, title in titles.items():
        _, instructor, learner = toc_files[name]
        links.append(f"[{title}]({learner!s}) - [Instructor]({instructor!s})")

    return "\n".join(["## Contents"] + [f"1. {link}" for link in links])


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


if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("tutorial_dir", nargs=1, help="path to the tutorial directory")
    argp.add_argument("output_dir", nargs=1, help="path to the output directory")

    args = argp.parse_args(sys.argv[1:])

    tutorial_dir = Path(args.tutorial_dir[0])
    output_dir = Path(args.output_dir[0])
    output_dir.mkdir(exist_ok=True)

    index_filename = tutorial_dir / "index.md"

    file_stems = parse_toctree_directive(index_filename)

    # For each file in the toc tree make an instructor notebook, then make a learner
    # notebook without the source cells.
    toc_files = {}
    for stem in [*file_stems, index_filename.stem]:
        input_file = list(tutorial_dir.glob(stem + ".*"))
        if len(input_file) > 1:
            raise ValueError(f"More than one input file matching {stem}.* found")
        if not input_file:
            raise ValueError(f"File {stem} not found")

        input_file = input_file[0]
        instructor_file = output_dir / "instructor"
        instructor_file.mkdir(exist_ok=True)
        instructor_file /= (input_file.stem + ".ipynb")
        learner_file = output_dir / (input_file.stem + ".ipynb")
        if input_file.name != "index.md":
            toc_files[stem] = (input_file,
                               instructor_file.relative_to(output_dir),
                               learner_file.relative_to(output_dir))

        subprocess.run([sys.executable, "-m", "jupytext", "--to", "ipynb", input_file, "-o", instructor_file])
        # Replace the sphinx toctree with a simple list of links
        if input_file.name == "index.md":
            add_toctree_to_index(toc_files, instructor_file, instructor_file)
        print(f"[learner] transforming {instructor_file} to {learner_file}")  # noqa: T201
        strip_code_cells(instructor_file, learner_file)
