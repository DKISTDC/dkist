# /// script
# requires-python = ">=3.11"
# ///

"""
This script adds and updates the appropriate files to update the version of an ASDF schema.
"""

import sys
import shutil
import pathlib
import argparse


def get_latest(name, dir):
    # ? here for the major number so that it only matches one character and "dkist" doesn't match "dkist-wcs-"
    # This will break if major version numbers exceed 9 but that's a problem for future Drew
    old_files = list(dir.glob(f"{name}-?.*.*.yaml"))
    old_files.sort()
    if old_files:
        return old_files[-1]


def increment_version(old_version, increment):
    if increment == "major":
        new_version = f"{int(old_version[0])+1}.0.0"
    elif increment == "minor":
        new_version = f"{old_version[:2]}{int(old_version[2])+1}.0"
    elif increment == "bugfix":
        new_version = f"{old_version[:4]}{int(old_version[4])+1}"
    else:
        # obviously make this more sophisticated
        raise InputError
    return new_version


def increment_file(old_file, increment):
    old_version = old_file.name[-10:-5]
    new_version = increment_version(old_version, increment)
    new_file = old_file.parent / old_file.name.replace(old_version, new_version)
    shutil.copy(old_file, new_file)
    return new_file, old_version, new_version


def make_new_file(dir, name):
    new_file = dir / f"{name}-0.1.0.yaml"
    new_file.touch()
    return new_file


def pascalcase(string):
    parts = string.split("_")
    return "".join([p.title() for p in parts])


def add_increment_line(file_, old_line, old_ver, new_ver, extra=""):
    with open(file_, mode="r+") as f:
        lines = f.readlines()
        new_line = old_line[:-1].replace(old_ver, new_ver) + extra + "\n"
        linenum = lines.index(old_line)
        lines.insert(linenum, new_line)
        f.seek(0)
        f.write("".join(lines))


def replace_line(file_, old_lines, old_ver, new_ver):
    if not isinstance(old_lines, list):
        old_lines = [old_lines]
    with open(file_, mode="r+") as f:
        lines = f.readlines()
        for old_line in old_lines:
            linenum = lines.index(old_line)
            lines[linenum] = lines[linenum].replace(old_ver, new_ver)
        f.seek(0)
        f.write("".join(lines))


def main(schema_name, manifest="dkist", schema_increment="minor", manifest_increment="minor", base_branch="main"):
    # Sanitise your inputs
    schema_name = schema_name.replace("-", "_")

    repodir = pathlib.Path(__file__).parent.parent.resolve()
    asdf_dir = repodir / "dkist" / "io" / "asdf"

    old_schema = get_latest(schema_name, asdf_dir / "resources" / "schemas")
    old_manifest = get_latest(manifest, asdf_dir / "resources" / "manifests")

    if old_schema:
        new_sche_file, old_sche_ver, new_sche_ver = increment_file(old_schema, schema_increment)
        replace_line(new_sche_file, f'id: "asdf://dkist.nso.edu/schemas/{schema_name}-{old_sche_ver}"\n',
                     old_sche_ver, new_sche_ver)
    else:
        new_sche_file = make_new_file(asdf_dir / "resources" / "schemas", schema_name)
        with open(new_sche_file, "w") as f:
            f.write('%YAML 1.1\n'
                    '---\n'
                    '$schema: "http://stsci.edu/schemas/yaml-schema/draft-01"\n'
                    f'id: "asdf://dkist.nso.edu/schemas/{schema_name}-0.1.0"\n'
                    '\n'
                    'title: |\n'
                    '  # Title for this object\n'
                    'description:\n'
                    '  # Description of this object\n'
                    '\n'
                    'type: object\n'
                    'properties:\n'
                    '  # Properties of this object\n'
                    '\n'
                    'required: [] # Properties required byt his object\n'
                    'additionalProperties: # [true|false]\n'
                    '...')
    new_mani_file, old_mani_ver, new_mani_ver = increment_file(old_manifest, manifest_increment)

    # add ManifestExtension to entry_points.py
    add_increment_line(asdf_dir / "entry_points.py",
                       f'        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}",\n',
                       old_mani_ver, new_mani_ver, " converters=dkist_converters),")

    replace_line(new_mani_file,
                 [f"id: asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}\n",
                  f"extension_uri: asdf://dkist.nso.edu/dkist/extensions/{manifest}-{old_mani_ver}\n"],
                 old_mani_ver, new_mani_ver)

    #   increment or add schema_uri and tag_uri in manifest
    if old_schema:
        replace_line(new_mani_file,
                     [f'  - schema_uri: "asdf://dkist.nso.edu/schemas/{schema_name}-{old_sche_ver}"\n',
                      f'    tag_uri: "asdf://dkist.nso.edu/tags/{schema_name}-{old_sche_ver}"\n'],
                     old_sche_ver, new_sche_ver)
    else:
        with open(new_mani_file, mode="a") as f:
            f.write(f'  - schema_uri: "asdf://dkist.nso.edu/schemas/{schema_name}-0.1.0"\n')
            f.write(f'    tag_uri: "asdf://dkist.nso.edu/tags/{schema_name}-0.1.0"\n')

    converter = asdf_dir / "converters" / f"{schema_name}.py"
    if old_schema:
        # update tags list in converter
        add_increment_line(converter, f'        "asdf://dkist.nso.edu/tags/{schema_name}-{old_sche_ver}",\n',
                           old_sche_ver, new_sche_ver)
        # Get latest tag value (which doesn't necessarily match the schema version)
        with open(converter) as f:
            lines = f.readlines()
        latest_tag_line = [line for line in lines if f"tag:dkist.nso.edu:dkist/{schema_name}-" in line][0]
        old_tag = latest_tag_line[-8:-3] # Not robust, assumes single-digit versions
        new_tag = increment_version(old_tag, schema_increment) # assumes tag increment == schema increment
        add_increment_line(converter, f'        "tag:dkist.nso.edu:dkist/{schema_name}-{old_tag}",\n',
                           old_tag, new_tag)
    else:
        #   create converters/<schema>.py skeleton
        with open(converter, "w") as f:
            f.write("from asdf.extension import Converter\n"
                    "\n"
                    "\n"
                    f"class {pascalcase(schema_name)}Converter(Converter):\n"
                    "    tags = [\n"
                    f'        "asdf://dkist.nso.edu/tags/{schema_name}-0.1.0"\n'
                    f'        "tag:dkist.nso.edu:dkist/{schema_name}-0.1.0"\n'
                    "    ]\n"
                    "\n"
                    "    def from_yaml_tree(cls, node, tag, ctx):\n"
                    "        # Construct and return an object of the appropriate type from the asdf yaml\n"
                    "\n"
                    "        return\n"
                    "\n"
                    "    def to_yaml_tree(cls, node, tag, ctx):\n"
                    "        # Construct and return yaml tree to represent the object being serialised\n"
                    "        tree = {}\n"
                    "\n"
                    "        return tree\n"
            )
        #   import new converter in converters/__init__.py
        with open(asdf_dir / "converters" / "__init__.py", "a") as f:
            f.write(f"from .{schema_name} import {pascalcase(schema_name)}Converter")
        #   import new converter in entry_points.py
        #   add converter to dkist_converters list in entry_points.py

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("schema_name", help="Name of the schema to add or update.")
    argp.add_argument("--manifest", help="Name of the manifest to add the new schema to."
                      "Creating a new manifest is not currently supported."
                      "(Default 'dkist')",
                      default="dkist")
    argp.add_argument("--schema_increment", help="Increment to apply to the schema version."
                      "Ignored when creating a new schema."
                      "Must be 'major', 'minor' or 'bugfix'."
                      "(Default 'minor')",
                      default="minor")
    argp.add_argument("--manifest_increment", help="Increment to apply to the manifest version."
                      "Must be 'major', 'minor' or 'bugfix'."
                      "(Default 'minor')",
                      default="minor")
    argp.add_argument("--base_branch", help="Branch of the git repo used to determine latest version numbers.", default="main")

    args = argp.parse_args(sys.argv[1:])

    main(args.schema_name, args.manifest, args.schema_increment, args.manifest_increment, args.base_branch)
